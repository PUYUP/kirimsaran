from django.apps import apps
from django.db.models import Count

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

Listing = apps.get_registered_model('feeder', 'Listing')
Suggest = apps.get_registered_model('feeder', 'Suggest')
Redeem = apps.get_registered_model('feeder', 'Redeem')


class StatAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        listing = Listing.objects \
            .prefetch_related('user', 'products') \
            .select_related('user') \
            .filter(user_id=request.user.id)

        product_stat = listing.aggregate(
            product_count=Count('products', distinct=True)
        )

        suggest = Suggest.objects \
            .prefetch_related('spread') \
            .select_related('spread') \
            .filter(spread__fragment__listing__user_id=request.user.id)

        redeem = Redeem.objects \
            .prefetch_related('user', 'coupon', 'coupon__reward') \
            .select_related('user', 'coupon', 'coupon__reward') \
            .filter(coupon__reward__fragment__listing__user_id=request.user.id)

        return Response({
            'count': {
                'listing': listing.count(),
                'product': product_stat.get('product_count', 0),
                'suggest': suggest.count(),
                'redeem_total': redeem.count(),
                'redeem_requested': redeem.filter(takens__isnull=True).count(),
                'redeem_accepted': redeem.filter(takens__isnull=False).count(),
            }
        })
