from django.core.validators import RegexValidator
from django.db import models, transaction
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from .abstract import AbstractCommonField
from ..utils import save_random_identifier


class AbstractSuggest(AbstractCommonField):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='suggests',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    spread = models.ForeignKey(
        'feeder.Spread',
        related_name='suggests',
        on_delete=models.CASCADE
    )
    fragment = models.ForeignKey(
        'feeder.Fragment',
        related_name='suggests',
        on_delete=models.CASCADE,
        editable=False
    )

    rating = models.IntegerField()
    description = models.TextField()
    msisdn = models.CharField(null=True, blank=True, max_length=14)
    email = models.EmailField(null=True, blank=True)
    extra = models.JSONField(null=True, blank=True)

    class Meta:
        abstract = True
        app_label = 'feeder'
        ordering = ['-create_at']

    def __str__(self) -> str:
        return '{} {}'.format(self.rating, self.description)

    @transaction.atomic
    def save(self, *args, **kwargs):
        self.fragment = self.spread.fragment
        return super().save(*args, **kwargs)


class AbstractCoupon(AbstractCommonField):
    suggest = models.OneToOneField(
        'feeder.Suggest',
        related_name='coupons',
        on_delete=models.CASCADE
    )
    fragment = models.ForeignKey(
        'feeder.Fragment',
        related_name='coupons',
        on_delete=models.CASCADE,
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
    is_used = models.BooleanField(default=False)

    class Meta:
        abstract = True
        app_label = 'feeder'
        ordering = ['-create_at']

    def __str__(self) -> str:
        return self.identifier

    @transaction.atomic
    def save(self, *args, **kwargs):
        self.fragment = self.suggest.fragment

        # Generate random identifier
        if not self.pk and not self.identifier:
            # We pass the model instance that is being saved
            self.identifier = save_random_identifier(self)
        return super().save(*args, **kwargs)
