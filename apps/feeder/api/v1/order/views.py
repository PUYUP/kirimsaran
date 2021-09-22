from copy import copy

from django.db import transaction
from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist, ValidationError as DjangoValidationError
from django.utils.translation import gettext_lazy as _

from rest_framework import viewsets, status as response_status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination

from .serializers import CreateOrderSerializer, ListOrderSerializer, RetrieveOrderSerializer
from ....helpers import build_result_pagination

Order = apps.get_registered_model('feeder', 'Order')

# Define to avoid used ...().paginate__
_PAGINATOR = LimitOffsetPagination()


class BaseViewSet(viewsets.ViewSet):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.context = dict()

    def initialize_request(self, request, *args, **kwargs):
        self.context.update({'request': request})
        return super().initialize_request(request, *args, **kwargs)


class OrderViewSet(BaseViewSet):
    """
    GET
    -----

        No-params


    POST
    -----

        {
            "user": "<hidden field>",
            "broadcast": "01688d70-ede1-46a3-938d-d2f21809c3ae",
            "fragment": "114de3ea-65cb-4f32-b406-2afcd96b5921",
            "metas": [
                {"meta_key": "rating", "meta_value": "1"}
            ],
            "items": [
                {"target": "72f5eb83-7d71-4c80-8b34-55dcea635587"}
            ]
        }
    """
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)
    throttle_classes = (UserRateThrottle,)

    def queryset(self):
        return Order.objects \
            .prefetch_related('user', 'broadcast', 'fragment') \
            .select_related('user', 'broadcast', 'fragment') \
            .filter(user_id=self.request.user.id)

    def queryset_instance(self, uuid, for_update=False):
        try:
            if for_update:
                return self.queryset().select_for_update().get(uuid=uuid)
            return self.queryset().get(uuid=uuid)
        except ObjectDoesNotExist:
            raise NotFound()

    @transaction.atomic
    def create(self, request, format=None):
        serializer = CreateOrderSerializer(
            data=request.data,
            context=self.context
        )

        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except DjangoValidationError as e:
                raise ValidationError(detail=str(e))
            return Response(serializer.data, status=response_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=response_status.HTTP_406_NOT_ACCEPTABLE)

    @transaction.atomic()
    def delete(self, request, uuid=None):
        try:
            instance = self.queryset().get(uuid=uuid)
        except ObjectDoesNotExist:
            raise NotFound()

        # copy for response
        instance_copy = copy(instance)

        # run delete
        instance.delete()

        # return object
        serializer = RetrieveOrderSerializer(
            instance_copy,
            context=self.context
        )
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    def list(self, request, format=None):
        queryset = self.queryset()
        paginator = _PAGINATOR.paginate_queryset(queryset, request)
        serializer = ListOrderSerializer(
            paginator,
            context=self.context,
            many=True
        )

        results = build_result_pagination(self, _PAGINATOR, serializer)
        return Response(results, status=response_status.HTTP_200_OK)

    def retrieve(self, request, uuid=None, format=None):
        instance = self.queryset_instance(uuid)
        serializer = RetrieveOrderSerializer(instance, context=self.context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)
