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

from .serializers import (
    CreateAddressedSerializer,
    ListAddressedSerializer,
    RetrieveAddressedSerializer
)
from ....helpers import build_result_pagination

Addressed = apps.get_registered_model('feeder', 'Addressed')

# Define to avoid used ...().paginate__
_PAGINATOR = LimitOffsetPagination()


class BaseViewSet(viewsets.ViewSet):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.context = dict()

    def initialize_request(self, request, *args, **kwargs):
        self.context.update({'request': request})
        return super().initialize_request(request, *args, **kwargs)


class AddressedViewSet(BaseViewSet):
    """
    GET
    -----

        .../addresseds/?broadcast=uuid64


    POST
    -----

        [
            {
                "broadcast": "uuid64",
                "suggest": "uuid64""
            }
        ]

    """
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)
    throttle_classes = (UserRateThrottle,)

    def queryset(self):
        return Addressed.objects \
            .prefetch_related('broadcast', 'suggest') \
            .select_related('broadcast', 'suggest') \
            .all()

    def queryset_instance(self, uuid, for_update=False):
        try:
            if for_update:
                return self.queryset().select_for_update() \
                    .get(uuid=uuid, listing__user_id=self.request.user.id)
            return self.queryset().get(uuid=uuid)
        except ObjectDoesNotExist:
            raise NotFound()

    @transaction.atomic
    def create(self, request, format=None):
        serializer = CreateAddressedSerializer(
            data=request.data,
            context=self.context,
            many=True
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
            instance = self.queryset() \
                .get(uuid=uuid, listing__user_id=request.user.id)
        except ObjectDoesNotExist:
            raise NotFound()

        # copy for response
        instance_copy = copy(instance)

        # run delete
        instance.delete()

        # return object
        serializer = RetrieveAddressedSerializer(
            instance_copy,
            context=self.context
        )
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    def list(self, request, format=None):
        # only owner can see data
        queryset = self.queryset().filter(broadcast__user_id=request.user.id)
        broadcast = request.query_params.get('broadcast', None)
        if not broadcast:
            raise ValidationError(detail={
                'broadcast': _("Broadcast required")
            })

        try:
            queryset = queryset.filter(broadcast__uuid=broadcast)
        except DjangoValidationError as e:
            raise ValidationError(detail={
                'spread': str(e)
            })

        paginator = _PAGINATOR.paginate_queryset(queryset, request)
        serializer = ListAddressedSerializer(
            paginator,
            context=self.context,
            many=True
        )

        results = build_result_pagination(self, _PAGINATOR, serializer)
        return Response(results, status=response_status.HTTP_200_OK)

    def retrieve(self, request, uuid=None, format=None):
        instance = self.queryset_instance(uuid)
        serializer = RetrieveAddressedSerializer(
            instance, context=self.context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)
