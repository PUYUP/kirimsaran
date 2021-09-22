from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from .abstract import AbstractCommonField


"""
IMAGINE

:suggest as Room
:interaction as Participant
"""


class AbstractInteraction(AbstractCommonField):
    class Type(models.TextChoices):
        INFO = 'info', _("Information")
        CONVERSATION = 'conversation', _("Conversation")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='interactions'
    )
    suggest = models.ForeignKey(
        'feeder.Suggest',
        on_delete=models.CASCADE,
        related_name='interactions'
    )

    type = models.CharField(
        max_length=15,
        choices=Type.choices,
        default=Type.CONVERSATION
    )
    label = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField()

    class Meta:
        abstract = True
        app_label = 'feeder'
        ordering = ['-create_at']

    def __str__(self) -> str:
        text = '{}: {}'.format(self.get_type_display(), self.label)
        return text
