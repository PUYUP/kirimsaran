from django.core.validators import RegexValidator
from django.db import models, transaction
from django.conf import settings
from django.apps import apps
from django.utils.translation import ugettext_lazy as _

from .abstract import AbstractCommonField
from ..utils import save_random_identifier


class AbstractOrder(AbstractCommonField):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    broadcast = models.ForeignKey(
        'feeder.Broadcast',
        on_delete=models.SET_NULL,
        related_name='orders',
        null=True,
        blank=True
    )
    fragment = models.ForeignKey(
        'feeder.Fragment',
        on_delete=models.SET_NULL,
        related_name='orders',
        null=True,
        blank=True
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

    class Meta:
        abstract = True
        app_label = 'feeder'
        ordering = ['-create_at']

    def __str__(self) -> str:
        return self.broadcast.label

    @transaction.atomic
    def save(self, *args, **kwargs):
        # Generate random identifier
        if not self.pk and not self.identifier:
            # We pass the model instance that is being saved
            self.identifier = save_random_identifier(self)

        return super().save(*args, **kwargs)

    @transaction.atomic
    def insert_meta(self, meta_dict):
        OrderMeta = apps.get_registered_model('feeder', 'OrderMeta')
        bulk_meta = []

        for meta in meta_dict:
            o = OrderMeta(order=self, **meta)
            bulk_meta.append(o)

        if len(meta_dict) > 0:
            try:
                OrderMeta.objects.bulk_create(
                    bulk_meta,
                    ignore_conflicts=False
                )
            except Exception as e:
                print(e)

    @transaction.atomic
    def insert_order_item(self, item_dict):
        OrderItem = apps.get_registered_model('feeder', 'OrderItem')
        bulk_item = []

        for item in item_dict:
            target = item.get('target', None)
            if target:
                o = OrderItem(order=self, target=target)
                bulk_item.append(o)

        if len(bulk_item) > 0:
            try:
                OrderItem.objects.bulk_create(
                    bulk_item,
                    ignore_conflicts=False
                )
            except Exception as e:
                print(e)


class AbstractOrderMeta(AbstractCommonField):
    order = models.ForeignKey(
        'feeder.Order',
        on_delete=models.CASCADE,
        related_name='metas'
    )

    meta_key = models.CharField(max_length=255)
    meta_value = models.TextField()

    class Meta:
        abstract = True
        app_label = 'feeder'
        ordering = ['-create_at']

    def __str__(self) -> str:
        return self.meta_key


class OrderItemManager(models.Manager):
    @transaction.atomic
    def bulk_create(self, objs, **kwargs):
        for obj in objs:
            target = getattr(obj, 'target', None)

            if target:
                setattr(obj, 'price', target.price)
                setattr(obj, 'method', target.method)
                setattr(obj, 'value', target.value)
        return super().bulk_create(objs, **kwargs)


class AbstractOrderItem(AbstractCommonField):
    order = models.ForeignKey(
        'feeder.Order',
        on_delete=models.CASCADE,
        related_name='items'
    )
    target = models.ForeignKey(
        'feeder.Target',
        on_delete=models.SET_NULL,
        related_name='items',
        null=True,
        blank=True
    )

    price = models.IntegerField(default=0)
    method = models.CharField(max_length=255)
    value = models.CharField(max_length=255)

    objects = OrderItemManager()

    class Meta:
        abstract = True
        app_label = 'feeder'
        ordering = ['-create_at']

    def __str__(self) -> str:
        return str(self.price)

    @transaction.atomic
    def save(self, *args, **kwargs):
        if not self.pk:
            self.price = self.target.price
            self.method = self.target.method
            self.value = self.target.value

        return super().save(*args, **kwargs)
