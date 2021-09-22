from django.core.validators import RegexValidator
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericRelation
from .abstract import AbstractCommonField
from ..conf import settings
from ..utils import save_random_identifier


class AbstractBroadcast(AbstractCommonField):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='broadcasts',
        on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        'feeder.Product',
        related_name='broadcasts',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    fragment = models.ForeignKey(
        'feeder.Fragment',
        related_name='broadcasts',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    listing = models.ForeignKey(
        'feeder.Listing',
        related_name='broadcasts',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        editable=False
    )

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
    label = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    message = models.TextField(max_length=255)

    spreads = GenericRelation('feeder.Spread', related_query_name='broadcast')
    rewards = GenericRelation('feeder.Reward', related_query_name='broadcast')

    class Meta:
        abstract = True
        app_label = 'feeder'
        ordering = ['-create_at']

    def __str__(self) -> str:
        return self.label

    @transaction.atomic
    def save(self, *args, **kwargs):
        if not self.pk:
            # auto set listing from product
            if self.product:
                self.listing = self.product.listing

            if not self.identifier:
                # We pass the model instance that is being saved
                self.identifier = save_random_identifier(self)

        return super().save(*args, **kwargs)


class TargetManager(models.Manager):
    @transaction.atomic
    def bulk_create(self, objs, **kwargs):
        methods = [method.value for method in self.model.Method]

        for obj in objs:
            # suggest canal
            canal = None

            try:
                canal = obj.suggest.canals.get(method=obj.method)
            except Exception as e:
                print(e)

            if canal:
                for method in methods:
                    # get method from :suggest and insert to :target
                    setattr(obj, 'method', method)
                    setattr(obj, 'value', canal.value)

            # pricing...
            price = 0

            if obj.method == self.model.Method.EMAIL:
                price = settings.FEEDER_PRICE_EMAIL_METHOD
            elif self.method == self.model.Method.PHONE:
                price = settings.FEEDER_PRICE_PHONE_METHOD
            elif self.method == self.model.Method.WHATSAPP:
                price = settings.FEEDER_PRICE_WHATSAPP_METHOD
            elif self.method == self.model.Method.TELEGRAM:
                price = settings.FEEDER_PRICE_TELEGRAM_METHOD

            setattr(obj, 'price', price)
        return super().bulk_create(objs, **kwargs)


class AbstractTarget(AbstractCommonField):
    """Target customer picked manually by the owner.
    Maybe owner will give a gift or discount For that wee need a method code 
    such as invitation code"""
    class Method(models.TextChoices):
        PHONE = 'phone', _("Phone")
        WHATSAPP = 'whatsapp', _("WhatsApp")
        TELEGRAM = 'telegram', _("Telegram")
        EMAIL = 'email', _("Email")

    broadcast = models.ForeignKey(
        'feeder.Broadcast',
        related_name='targets',
        on_delete=models.CASCADE
    )
    suggest = models.ForeignKey(
        'feeder.Suggest',
        related_name='target',
        on_delete=models.CASCADE
    )

    moment = models.CharField(max_length=255, null=True, blank=True)
    method = models.CharField(
        choices=Method.choices,
        default=Method.EMAIL,
        max_length=15
    )
    value = models.CharField(max_length=255)
    price = models.IntegerField(default=0)

    objects = TargetManager()

    class Meta:
        abstract = True
        app_label = 'feeder'
        ordering = ['-create_at']

    def __str__(self) -> str:
        return self.suggest.description

    @transaction.atomic
    def save(self, *args, **kwargs):
        if not self.pk:
            methods = [method.value for method in self.Method]

            # suggest canal
            canal = None

            try:
                canal = self.suggest.canals.get(method=self.method)
            except Exception as e:
                print(e)

            if canal:
                for method in methods:
                    # get method from :suggest and insert to :target
                    setattr(self, 'method', method)
                    setattr(self, 'value', canal.value)

            # pricing...
            price = 0

            if self.method == self.Method.EMAIL:
                price = settings.FEEDER_PRICE_EMAIL_METHOD
            elif self.method == self.Method.PHONE:
                price = settings.FEEDER_PRICE_PHONE_METHOD
            elif self.method == self.Method.WHATSAPP:
                price = settings.FEEDER_PRICE_WHATSAPP_METHOD
            elif self.method == self.Method.TELEGRAM:
                price = settings.FEEDER_PRICE_TELEGRAM_METHOD

            self.price = price
        return super().save(*args, **kwargs)
