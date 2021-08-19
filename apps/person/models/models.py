from simple_history.models import HistoricalRecords

from ..utils import is_model_registered
from .user import *
from .attribute import *
from .securecode import *

__all__ = list()


# 1
# https://docs.djangoproject.com/en/3.1/topics/auth/customizing/#auth-custom-user
if not is_model_registered('person', 'User'):
    class User(User):
        history = HistoricalRecords(inherit=True)

        class Meta(User.Meta):
            pass

    __all__.append('User')


# 2
if not is_model_registered('person', 'Profile'):
    class Profile(AbstractProfile):
        history = HistoricalRecords(inherit=True)

        class Meta(AbstractProfile.Meta):
            pass

    __all__.append('Profile')

# 3
if not is_model_registered('person', 'Attribute'):
    class Attribute(AbstractAttribute):
        history = HistoricalRecords(inherit=True)

        class Meta(AbstractAttribute.Meta):
            pass

    __all__.append('Attribute')


# 4
if not is_model_registered('person', 'AttributeValue'):
    class AttributeValue(AbstractAttributeValue):
        history = HistoricalRecords(inherit=True)

        class Meta(AbstractAttributeValue.Meta):
            pass

    __all__.append('AttributeValue')


# 5
if not is_model_registered('person', 'SecureCode'):
    class SecureCode(AbstractSecureCode):
        history = HistoricalRecords(inherit=True)

        class Meta(AbstractSecureCode.Meta):
            pass

    __all__.append('SecureCode')
