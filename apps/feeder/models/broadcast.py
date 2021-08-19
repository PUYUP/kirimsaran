from django.db import models
from django.conf import settings

from .abstract import AbstractCommonField
from ..tasks import send_sms


class AbstractBroadcast(AbstractCommonField):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='broadcasts',
        on_delete=models.CASCADE
    )

    label = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    reward = models.TextField(null=True, blank=True)
    message = models.TextField()

    class Meta:
        abstract = True
        app_label = 'feeder'
        ordering = ['-create_at']

    def __str__(self) -> str:
        return self.label


class AddressedManager(models.Manager):
    def bulk_create(self, objs, **kwargs):
        for obj in objs:
            data = {
                'msisdn': obj.suggest.msisdn,
                'message': obj.broadcast.message
            }

            # send_sms.delay(data)  # with celery
            send_sms(data)  # without celery
        return super().bulk_create(objs, **kwargs)


class AbstractAddressed(AbstractCommonField):
    broadcast = models.ForeignKey(
        'feeder.Broadcast',
        related_name='addresseds',
        on_delete=models.CASCADE
    )
    suggest = models.ForeignKey(
        'feeder.Suggest',
        related_name='addresseds',
        on_delete=models.CASCADE
    )

    objects = AddressedManager()

    class Meta:
        abstract = True
        app_label = 'feeder'
        ordering = ['-create_at']

    def __str__(self) -> str:
        return self.suggest.description

    @property
    def email(self):
        return self.suggest.email

    @property
    def msisdn(self):
        return self.suggest.msisdn
