# https://pypi.org/project/django-appconf/
from django.conf import settings  # noqa
from appconf import AppConf


class FeederAppConf(AppConf):
    MAXIMUM_PRODUCT_CODE_LENGTH = 6

    class Meta:
        perefix = 'feeder'
