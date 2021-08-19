from django.urls import path, include

from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .user.views import TokenObtainPairViewExtend, UserViewSet
from .securecode.views import SecureCodeViewSet
from .password.views import RecoveryPasswordAPIView

router = DefaultRouter(trailing_slash=True)
router.register('users', UserViewSet, basename='user')
router.register('securecodes', SecureCodeViewSet, basename='securecode')

urlpatterns = [
    path('', include(router.urls)),
    path('token/', TokenObtainPairViewExtend.as_view(), name='token_obtain'),
    path('token-refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('password-recovery/', RecoveryPasswordAPIView.as_view(),
         name='password-recovery'),
]
