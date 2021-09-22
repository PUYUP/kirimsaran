# https://pypi.org/project/django-appconf/
from django.conf import settings  # noqa
from appconf import AppConf


class FeederAppConf(AppConf):
    MAXIMUM_PRODUCT_CODE_LENGTH = 6
    PRICE_EMAIL_METHOD = 100
    PRICE_PHONE_METHOD = 500
    PRICE_WHATSAPP_METHOD = 600
    PRICE_TELEGRAM_METHOD = 400

    class Meta:
        perefix = 'feeder'
