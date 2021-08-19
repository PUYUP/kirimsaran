from simple_history.models import HistoricalRecords

from ..utils import is_model_registered
from .listing import *
from .fragment import *
from .suggest import *
from .broadcast import *

__all__ = list()


# 1
if not is_model_registered('feeder', 'Listing'):
    class Listing(AbstractListing):
        history = HistoricalRecords(inherit=True)

        class Meta(AbstractListing.Meta):
            pass

    __all__.append('Listing')


# 2
if not is_model_registered('feeder', 'Product'):
    class Product(AbstractProduct):
        history = HistoricalRecords(inherit=True)

        class Meta(AbstractProduct.Meta):
            pass

    __all__.append('Product')


# 3
if not is_model_registered('feeder', 'Fragment'):
    class Fragment(AbstractFragment):
        history = HistoricalRecords(inherit=True)

        class Meta(AbstractFragment.Meta):
            pass

    __all__.append('Fragment')


# 4
if not is_model_registered('feeder', 'Spread'):
    class Spread(AbstractSpread):
        history = HistoricalRecords(inherit=True)

        class Meta(AbstractSpread.Meta):
            pass

    __all__.append('Spread')


# 5
if not is_model_registered('feeder', 'Suggest'):
    class Suggest(AbstractSuggest):
        history = HistoricalRecords(inherit=True)

        class Meta(AbstractSuggest.Meta):
            pass

    __all__.append('Suggest')


# 6
if not is_model_registered('feeder', 'Coupon'):
    class Coupon(AbstractCoupon):
        history = HistoricalRecords(inherit=True)

        class Meta(AbstractCoupon.Meta):
            pass

    __all__.append('Coupon')


# 7
if not is_model_registered('feeder', 'Broadcast'):
    class Broadcast(AbstractBroadcast):
        history = HistoricalRecords(inherit=True)

        class Meta(AbstractBroadcast.Meta):
            pass

    __all__.append('Broadcast')


# 8
if not is_model_registered('feeder', 'Addressed'):
    class Addressed(AbstractAddressed):
        history = HistoricalRecords(inherit=True)

        class Meta(AbstractAddressed.Meta):
            pass

    __all__.append('Addressed')
