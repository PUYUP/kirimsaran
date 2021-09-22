from django.utils.translation import gettext_lazy as _

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.permissions import AllowAny
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class RootAPIView(APIView):
    permission_classes = (AllowAny,)
    throttle_classes = (AnonRateThrottle, UserRateThrottle,)

    def get(self, request, format=None):
        return Response({
            'person': {
                'securecode': reverse('person_api:securecode-list', request=request,
                                      format=format, current_app='person'),
                'user': reverse('person_api:user-list', request=request,
                                format=format, current_app='person'),
                'password-recovery': reverse('person_api:password-recovery', request=request,
                                             format=format, current_app='person'),
                'token': reverse('person_api:token-obtain', request=request,
                                 format=format, current_app='person'),
            },
            'feeder': {
                'stat': reverse('feeder_api:stat', request=request,
                                format=format, current_app='feeder'),
                'listing': reverse('feeder_api:listing-list', request=request,
                                   format=format, current_app='feeder'),
                'product': reverse('feeder_api:product-list', request=request,
                                   format=format, current_app='feeder'),
                'fragment': reverse('feeder_api:fragment-list', request=request,
                                    format=format, current_app='feeder'),
                'spread': reverse('feeder_api:spread-list', request=request,
                                  format=format, current_app='feeder'),
                'suggest': reverse('feeder_api:suggest-list', request=request,
                                   format=format, current_app='feeder'),
                'broadcast': reverse('feeder_api:broadcast-list', request=request,
                                     format=format, current_app='feeder'),
                'target': reverse('feeder_api:target-list', request=request,
                                  format=format, current_app='feeder'),
                'reward': reverse('feeder_api:reward-list', request=request,
                                  format=format, current_app='feeder'),
                'redeem': reverse('feeder_api:redeem-list', request=request,
                                  format=format, current_app='feeder'),
                'taken': reverse('feeder_api:taken-list', request=request,
                                 format=format, current_app='feeder'),
                'order': reverse('feeder_api:order-list', request=request,
                                 format=format, current_app='feeder'),
                'interaction': reverse('feeder_api:interaction-list', request=request,
                                       format=format, current_app='feeder'),
            }
        })
