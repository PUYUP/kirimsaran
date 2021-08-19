import qrcode
import time
import calendar

from django.core.validators import RegexValidator
from django.db import models, transaction
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils.translation import ugettext_lazy as _

from .abstract import AbstractCommonField
from ..utils import save_random_identifier


class AbstractFragment(AbstractCommonField):
    product = models.ForeignKey(
        'feeder.Product',
        related_name='fragments',
        on_delete=models.CASCADE
    )

    listing = models.ForeignKey(
        'feeder.Listing',
        on_delete=models.CASCADE,
        related_name='fragments',
        editable=False
    )

    label = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    reward = models.TextField(null=True, blank=True)

    class Meta:
        abstract = True
        app_label = 'feeder'
        ordering = ['-create_at']

    def __str__(self) -> str:
        return self.label

    @transaction.atomic
    def save(self, *args, **kwargs):
        self.listing = self.product.listing
        return super().save(*args, **kwargs)


class AbstractSpread(AbstractCommonField):
    fragment = models.ForeignKey(
        'feeder.Fragment',
        related_name='spreads',
        on_delete=models.CASCADE
    )

    listing = models.ForeignKey(
        'feeder.Listing',
        on_delete=models.CASCADE,
        related_name='spreads',
        editable=False
    )

    # set to 0 for unlimited
    allowed_used = models.IntegerField(default=0)
    valid_until = models.DateTimeField(blank=True, null=True)
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
        upload_to='qrcodes',
        max_length=500,
        null=True,
        blank=True
    )
    protocol = models.CharField(max_length=10, default='https://')
    domain = models.CharField(max_length=255, default='kirimsaran.com')
    is_used = models.BooleanField(default=False, editable=False)

    class Meta:
        abstract = True
        app_label = 'feeder'
        ordering = ['-create_at']

    def __str__(self) -> str:
        return '%s: %s' % (self.fragment.label, self.identifier)

    @property
    def shorturl(self):
        return '{}{}/{}'.format(self.protocol, self.domain, self.identifier)

    @transaction.atomic
    def save(self, *args, **kwargs):
        # Generate random identifier
        if not self.pk and not self.identifier:
            # We pass the model instance that is being saved
            self.identifier = save_random_identifier(self)

            # generate qrcode
            self.generate_qrcode()

        self.listing = self.fragment.listing

        # if allowed larger than 1 or 0, :is_used always false
        # :is_used only for allowed is 1 time
        if self.allowed_used > 1 or self.allowed_used == 0:
            self.is_used = False
        return super().save(*args, **kwargs)

    def generate_qrcode(self):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=2,
        )
        qr.add_data(self.shorturl)
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
