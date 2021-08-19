from django.urls import path, include

from api.views import RootAPIView
from apps.person.api import routers as person_routers
from apps.feeder.api import routers as feeder_routers

urlpatterns = [
    path('', RootAPIView.as_view(), name='api'),
    path('', include(person_routers)),
    path('', include(feeder_routers)),
]
