
from django.db import models
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
