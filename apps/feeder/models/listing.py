
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models, transaction
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from .abstract import AbstractCommonField


class AbstractListing(AbstractCommonField):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='listings',
        on_delete=models.CASCADE
    )

    label = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)

    class Meta:
        abstract = True
        app_label = 'feeder'
        ordering = ['-create_at']

    def __str__(self):
        return self.label


class AbstractProduct(AbstractCommonField):
    # we need know who add the :product
    # TODO: someday :listing allowed to organized with many user
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='products',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    listing = models.ForeignKey(
        'feeder.Listing',
        on_delete=models.CASCADE,
        related_name='products'
    )

    label = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)

    class Meta:
        abstract = True
        app_label = 'feeder'
        ordering = ['-create_at']

    def __str__(self) -> str:
        return self.label


class AbstractFragment(AbstractCommonField):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='fragments',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
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
    start_at = models.DateTimeField(auto_now_add=True)
    expiry_at = models.DateTimeField(null=True, blank=True)

    spreads = GenericRelation('feeder.Spread', related_query_name='fragment')
    rewards = GenericRelation('feeder.Reward', related_query_name='fragment')

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
