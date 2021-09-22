import phonenumbers

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_msisdn(value):
    error_msg = _('Enter a valid msisdn')

    try:
        locale_number = phonenumbers.parse(value, 'ID')
    except phonenumbers.NumberParseException as e:
        raise ValidationError(error_msg)

    if not phonenumbers.is_valid_number(locale_number):
        raise ValidationError(error_msg)
