import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


class AbstractCommonField(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_at = models.DateTimeField(auto_now_add=True, db_index=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
