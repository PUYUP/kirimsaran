import qrcode
import time
import calendar

from django.core.validators import RegexValidator
from django.db import models, transaction
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from .abstract import AbstractCommonField
from ..utils import save_random_identifier


class AbstractSpread(AbstractCommonField):
    class Cause(models.TextChoices):
        N = 'n', _("New")
        R = 'r', _("Re")

    # :fragment or :broadcast
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        limit_choices_to={'app_label': 'feeder'}
    )
    object_id = models.CharField(max_length=255)
    content_object = GenericForeignKey('content_type', 'object_id')

    # identified this new or re
    # new = become from :fragment
    # re = become from :broadcast
    cause = models.CharField(
        max_length=15,
        choices=Cause.choices,
        default=Cause.N
    )
    # set to 0 for unlimited
    allocation = models.BigIntegerField(default=0)
    start_at = models.DateTimeField(auto_now_add=True)
    expiry_at = models.DateTimeField(null=True, blank=True)
    identifier = models.CharField(
        max_length=7,
        editable=False,
        validators=[
            RegexValidator(
                regex='^[a-zA-Z0-9]*$',
                message=_("Can only contain the letters a-Z and 0-9."),
                code='invalid_identifier'
            ),
        ]
    )
    qrcode = models.ImageField(
        upload_to='images/qrcodes',
        max_length=500,
        null=True,
        blank=True
    )
    protocol = models.CharField(max_length=10, default='https')
    domain = models.CharField(
        max_length=255,
        default='kirimsaran.com',
        help_text=_("Without http and slash")
    )
    url = models.URLField(editable=False)

    class Meta:
        abstract = True
        app_label = 'feeder'
        ordering = ['-create_at']

    @property
    def content_object_label(self):
        return getattr(self.content_object, 'label', None)

    @property
    def content_object_uuid(self):
        return getattr(self.content_object, 'uuid', None)

    @property
    def total_suggest(self):
        return self.suggests.count()

    def product(self, field='uuid'):
        product = getattr(self.content_object, 'product', None)
        if product is None:
            return None

        return getattr(product, field, None)

    def __str__(self) -> str:
        return self.identifier

    @transaction.atomic
    def save(self, *args, **kwargs):
        # Generate random identifier
        if not self.pk and not self.identifier:
            # We pass the model instance that is being saved
            self.identifier = save_random_identifier(self)

            # set url <protocol><domain><identifier>
            _url = '{}://{}/{}'.format(self.protocol,
                                       self.domain,
                                       self.identifier)
            self.url = _url

            # generate qrcode
            self.generate_qrcode()
        return super().save(*args, **kwargs)

    def generate_qrcode(self):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=2,
        )
        qr.add_data(self.url)
        qr.make(fit=True)
        img = qr.make_image()

        timestamp = calendar.timegm(time.gmtime())
        file = open('qrcode.png', 'w+b')
        img.save(file)

        filename = '%s-%s.png' % (self.identifier, timestamp)
        filebuffer = InMemoryUploadedFile(
            file, None, filename, 'image/png', file.tell(), None
        )

        self.qrcode.save(filename, filebuffer, save=False)
        file.close()


class AbstractReward(AbstractCommonField):
    class Type(models.TextChoices):
        GIFT = 'gift', _("Gift")
        CASHBACK = 'cashback', _("Cashback")
        DISCOUNT = 'discount', _("Discount")

    # :fragment or :broadcast
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        limit_choices_to={'app_label': 'feeder'}
    )
    object_id = models.CharField(max_length=255)
    content_object = GenericForeignKey('content_type', 'object_id')

    provider = models.CharField(
        max_length=255,
        help_text=_("Who giver this reward?")
    )
    label = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    term = models.TextField(null=True, blank=True)
    allocation = models.BigIntegerField(default=0)
    start_at = models.DateTimeField(auto_now_add=True)
    expiry_at = models.DateTimeField(null=True, blank=True)
    type = models.CharField(
        max_length=25,
        choices=Type.choices,
        default=Type.GIFT
    )
    amount = models.CharField(max_length=255)
    unit_slug = models.SlugField(help_text=_("Ex: %, GB, piece"))
    unit_label = models.CharField(max_length=255, help_text=_("Ex: Percent"))

    class Meta:
        abstract = True
        app_label = 'feeder'
        ordering = ['-create_at']

    @property
    def content_object_label(self):
        return getattr(self.content_object, 'label', None)

    @property
    def content_object_uuid(self):
        return getattr(self.content_object, 'uuid', None)

    def __str__(self) -> str:
        return self.label
