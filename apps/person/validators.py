import phonenumbers

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils.translation import gettext_lazy as _


def validate_msisdn(value):
    """
    Checks msisdn valid with locale format
    """
    if value:
        error_msg = _('Enter a valid msisdn number')

        if not value.isnumeric():
            raise ValidationError(error_msg)

        try:
            parsed = phonenumbers.parse(value, 'ID')
        except phonenumbers.NumberParseException as e:
            pass

        if phonenumbers.is_valid_number(parsed):
            error_msg = None

        if error_msg:
            raise ValidationError(error_msg)
    return value


def validate_issuer(value):
    """
    Validate issuer email or msisdn
    """
    error_msg = _('Enter a valid issuer (email or msisdn)')

    if value.isnumeric():
        # Msisdn
        try:
            locale_number = phonenumbers.parse(value, 'ID')
        except phonenumbers.NumberParseException as e:
            raise ValidationError(error_msg)

        if not phonenumbers.is_valid_number(locale_number):
            raise ValidationError(error_msg)
    else:
        # Email
        try:
            validate_email(value)
        except ValidationError:
            raise ValidationError(error_msg)
    return value
