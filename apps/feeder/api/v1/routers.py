from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .listing.views import ListingViewSet
from .product.views import ProductViewSet
from .fragment.views import FragmentViewSet
from .spread.views import SpreadViewSet
from .suggest.views import SuggestViewSet
from .broadcast.views import BroadcastViewSet
from .addressed.views import AddressedViewSet

router = DefaultRouter(trailing_slash=True)
router.register('listings', ListingViewSet, basename='listing')
router.register('products', ProductViewSet, basename='product')
router.register('fragments', FragmentViewSet, basename='fragment')
router.register('spreads', SpreadViewSet, basename='spread')
router.register('suggests', SuggestViewSet, basename='suggest')
router.register('broadcasts', BroadcastViewSet, basename='broadcast')
router.register('addresseds', AddressedViewSet, basename='addressed')

urlpatterns = [
    path('', include(router.urls)),
]
