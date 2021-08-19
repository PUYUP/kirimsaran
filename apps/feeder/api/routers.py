from django.urls import path, include
from .v1 import routers

urlpatterns = [
    path('feeder/v1/', include((routers, 'feeder_api'), namespace='feeder_api')),
]
