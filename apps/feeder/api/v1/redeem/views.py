from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist, ValidationError as DjangoValidationError
from django.db.models.expressions import Exists
from django.utils.translation import gettext_lazy as _
from django.db.models import OuterRef, Subquery

from rest_framework import viewsets, status as response_status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination

from .serializers import ListRedeemSerializer, RetrieveRedeemSerializer
from ....helpers import build_result_pagination

Redeem = apps.get_registered_model('feeder', 'Redeem')
Taken = apps.get_registered_model('feeder', 'Taken')

# Define to avoid used ...().paginate__
_PAGINATOR = LimitOffsetPagination()


class BaseViewSet(viewsets.ViewSet):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.context = dict()

    def initialize_request(self, request, *args, **kwargs):
        self.context.update({'request': request})
        return super().initialize_request(request, *args, **kwargs)


class RedeemViewSet(BaseViewSet):
    """
    GET
    -----
        ../redeems/?identifier=ZaWBiG
    """
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)
    throttle_classes = (UserRateThrottle,)

    def queryset(self):
        taken_subquery = Taken.objects.filter(redeem_id=OuterRef('id'))

        return Redeem.objects \
            .prefetch_related('user', 'coupon', 'coupon__reward') \
            .select_related('user', 'coupon', 'coupon__reward') \
            .annotate(is_taken=Exists(taken_subquery)) \
            .filter(
                coupon__reward__fragment__listing__user_id=self.request.user.id,
                coupon__is_active=True
            )

    def queryset_instance(self, uuid, for_update=False):
        try:
            if for_update:
                return self.queryset().select_for_update() \
                    .get(uuid=uuid)
            return self.queryset().get(uuid=uuid)
        except ObjectDoesNotExist:
            raise NotFound()

    def list(self, request, format=None):
        queryset = self.queryset()
        identifier = request.query_params.get('identifier', None)

        if identifier:
            queryset = queryset.filter(
                coupon__identifier__icontains=identifier
            )

        paginator = _PAGINATOR.paginate_queryset(queryset, request)
        serializer = ListRedeemSerializer(
            paginator,
            context=self.context,
            many=True
        )

        results = build_result_pagination(self, _PAGINATOR, serializer)
        return Response(results, status=response_status.HTTP_200_OK)

    def retrieve(self, request, uuid=None, format=None):
        instance = self.queryset_instance(uuid)
        serializer = RetrieveRedeemSerializer(instance, context=self.context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)
