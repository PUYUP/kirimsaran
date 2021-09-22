from simple_history.models import HistoricalRecords

from ..utils import is_model_registered
from .listing import *
from .generic import *
from .suggest import *
from .broadcast import *
from .interaction import *
from .order import *

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
if not is_model_registered('feeder', 'Broadcast'):
    class Broadcast(AbstractBroadcast):
        history = HistoricalRecords(inherit=True)

        class Meta(AbstractBroadcast.Meta):
            pass

    __all__.append('Broadcast')


# 5
if not is_model_registered('feeder', 'Target'):
    class Target(AbstractTarget):
        history = HistoricalRecords(inherit=True)

        class Meta(AbstractTarget.Meta):
            pass

    __all__.append('Target')


# 6
if not is_model_registered('feeder', 'Reward'):
    class Reward(AbstractReward):
        history = HistoricalRecords(inherit=True)

        class Meta(AbstractReward.Meta):
            pass

    __all__.append('Reward')


# 7
if not is_model_registered('feeder', 'Spread'):
    class Spread(AbstractSpread):
        history = HistoricalRecords(inherit=True)

        class Meta(AbstractSpread.Meta):
            pass

    __all__.append('Spread')


# 8
if not is_model_registered('feeder', 'Suggest'):
    class Suggest(AbstractSuggest):
        history = HistoricalRecords(inherit=True)

        class Meta(AbstractSuggest.Meta):
            pass

    __all__.append('Suggest')


# 9
if not is_model_registered('feeder', 'Canal'):
    class Canal(AbstractCanal):
        history = HistoricalRecords(inherit=True)

        class Meta(AbstractCanal.Meta):
            pass

    __all__.append('Canal')


# 10
if not is_model_registered('feeder', 'Coupon'):
    class Coupon(AbstractCoupon):
        history = HistoricalRecords(inherit=True)

        class Meta(AbstractCoupon.Meta):
            pass

    __all__.append('Coupon')


# 11
if not is_model_registered('feeder', 'Redeem'):
    class Redeem(AbstractRedeem):
        history = HistoricalRecords(inherit=True)

        class Meta(AbstractRedeem.Meta):
            pass

    __all__.append('Redeem')


# 12
if not is_model_registered('feeder', 'Taken'):
    class Taken(AbstractTaken):
        history = HistoricalRecords(inherit=True)

        class Meta(AbstractTaken.Meta):
            pass

    __all__.append('Taken')


# 13
if not is_model_registered('feeder', 'Interaction'):
    class Interaction(AbstractInteraction):
        history = HistoricalRecords(inherit=True)

        class Meta(AbstractInteraction.Meta):
            pass

    __all__.append('Interaction')


# 14
if not is_model_registered('feeder', 'Order'):
    class Order(AbstractOrder):
        history = HistoricalRecords(inherit=True)

        class Meta(AbstractOrder.Meta):
            pass

    __all__.append('Order')


# 16
if not is_model_registered('feeder', 'OrderMeta'):
    class OrderMeta(AbstractOrderMeta):
        history = HistoricalRecords(inherit=True)

        class Meta(AbstractOrderMeta.Meta):
            pass

    __all__.append('OrderMeta')


# 17
if not is_model_registered('feeder', 'OrderItem'):
    class OrderItem(AbstractOrderItem):
        history = HistoricalRecords(inherit=True)

        class Meta(AbstractOrderItem.Meta):
            pass

    __all__.append('OrderItem')
