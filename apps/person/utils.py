import phonenumbers
import unicodedata

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.apps import apps
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


def is_model_registered(app_label, model_name):
    """
    Checks whether a given model is registered. This is used to only
    register Oscar models if they aren't overridden by a forked app.
    """
    try:
        apps.get_registered_model(app_label, model_name)
    except LookupError:
        return False
    else:
        return True


def get_issuer_type(value):
    """
    Return issuer type by issuer value
    """
    # Msisdn
    if value.isnumeric():
        try:
            locale_number = phonenumbers.parse(value, 'ID')
            if phonenumbers.is_valid_number(locale_number):
                return 'msisdn'
        except phonenumbers.NumberParseException as e:
            pass

    # Email
    try:
        validate_email(value)
        return 'email'
    except ValidationError:
        pass

    raise ValidationError(_("Invalid issuer type"))


def unicode_ci_compare(s1, s2):
    """
    Perform case-insensitive comparison of two identifiers, using the
    recommended algorithm from Unicode Technical Report 36, section
    2.11.2(B)(2).
    """
    return unicodedata.normalize('NFKC', s1).casefold() == unicodedata.normalize('NFKC', s2).casefold()


def get_users(obtain):
    UserModel = get_user_model()

    """Given an email or msisdn, return matching user(s) who should receive a reset.
        This allows subclasses to more easily customize the default policies
        that prevent inactive users and users with unusable passwords from
        resetting their password.
        """
    email_field_name = UserModel.get_email_field_name()
    msisdn_field_name = 'msisdn'

    users = UserModel._default_manager.filter(
        Q(**{'%s__iexact' % email_field_name: obtain})
        | Q(**{'%s__iexact' % msisdn_field_name: obtain})
    )

    return (
        u for u in users
        if u.has_usable_password() and
        (
            unicode_ci_compare(obtain, getattr(u, email_field_name))
            or unicode_ci_compare(obtain, getattr(u, msisdn_field_name))
        )
    )


def get_password_recovery_token_uidb64(obtain):
    """
    :obtain can use :msisdn or :email
    Return token and uidb64 or not found error
    """
    token = None
    uidb64 = None
    for user in get_users(obtain):
        token = default_token_generator.make_token(user)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        break

    if not token and not uidb64:
        raise ValueError('User not found')
    return token, uidb64
