from django.apps import apps
from django.db import transaction

Coupon = apps.get_registered_model('feeder', 'Coupon')


@transaction.atomic
def suggest_save_handler(sender, instance, created, **kwargs):
    if created:
        # create coupon
        _ = Coupon.objects.get_or_create(suggest=instance)
