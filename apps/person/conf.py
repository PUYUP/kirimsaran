# https://pypi.org/project/django-appconf/
from django.conf import settings  # noqa
from appconf import AppConf


class PersonAppConf(AppConf):
    VERIFICATION_FIELDS = ['msisdn', 'email']

    class Meta:
        perefix = 'person'
