from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .stat.views import StatAPIView
from .listing.views import ListingViewSet
from .product.views import ProductViewSet
from .fragment.views import FragmentViewSet
from .spread.views import SpreadViewSet
from .suggest.views import SuggestViewSet
from .broadcast.views import BroadcastViewSet
from .target.views import TargetViewSet
from .reward.views import RewardViewSet
from .redeem.views import RedeemViewSet
from .taken.views import TakenViewSet
from .order.views import OrderViewSet
from .interaction.views import InteractionViewSet

router = DefaultRouter(trailing_slash=True)
router.register('listings', ListingViewSet, basename='listing')
router.register('products', ProductViewSet, basename='product')
router.register('fragments', FragmentViewSet, basename='fragment')
router.register('spreads', SpreadViewSet, basename='spread')
router.register('suggests', SuggestViewSet, basename='suggest')
router.register('broadcasts', BroadcastViewSet, basename='broadcast')
router.register('targets', TargetViewSet, basename='target')
router.register('rewards', RewardViewSet, basename='reward')
router.register('redeems', RedeemViewSet, basename='redeem')
router.register('takens', TakenViewSet, basename='taken')
router.register('orders', OrderViewSet, basename='order')
router.register('interactions', InteractionViewSet, basename='interaction')

urlpatterns = [
    path('', include(router.urls)),
    path('stats/', StatAPIView.as_view(), name='stat')
]
