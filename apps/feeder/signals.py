from django.apps import apps
from django.db import transaction


@transaction.atomic
def suggest_save_handler(sender, instance, created, **kwargs):
    if created:
        instance.create_coupon()
