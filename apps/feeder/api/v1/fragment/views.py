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
    CreateFragmentSerializer,
    ListFragmentSerializer,
    RetrieveFragmentSerializer,
    UpdateFragmentSerializer
)
from ....helpers import build_result_pagination

Fragment = apps.get_registered_model('feeder', 'Fragment')

# Define to avoid used ...().paginate__
_PAGINATOR = LimitOffsetPagination()


class BaseViewSet(viewsets.ViewSet):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.context = dict()

    def initialize_request(self, request, *args, **kwargs):
        self.context.update({'request': request})
        return super().initialize_request(request, *args, **kwargs)


class FragmentViewSet(BaseViewSet):
    """
    GET
    -----

        .../fragments/?product=uuid4


    POST & PATCH
    -----

        {
            "product": "uuid4",
            "label": "My business name",
            "description": "Sell all not food",
            "reward": "Some gift!"
        }

    """
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)
    throttle_classes = (UserRateThrottle,)

    def queryset(self):
        return Fragment.objects \
            .prefetch_related('product', 'listing') \
            .select_related('product', 'listing') \
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
        serializer = CreateFragmentSerializer(
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

    @transaction.atomic
    def partial_update(self, request, uuid=None, format=None):
        instance = self.queryset_instance(uuid, for_update=True)
        serializer = UpdateFragmentSerializer(
            instance,
            data=request.data,
            context=self.context,
            partial=True
        )

        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except DjangoValidationError as e:
                raise ValidationError(detail=str(e))
            return Response(serializer.data, status=response_status.HTTP_200_OK)
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
        serializer = RetrieveFragmentSerializer(
            instance_copy,
            context=self.context
        )
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    def list(self, request, format=None):
        product = request.query_params.get('product', None)
        if not product:
            raise ValidationError(detail={
                'product': _("Product required")
            })

        try:
            queryset = self.queryset().filter(product__uuid=product)
        except DjangoValidationError as e:
            raise ValidationError(detail={
                'product': str(e)
            })

        paginator = _PAGINATOR.paginate_queryset(queryset, request)
        serializer = ListFragmentSerializer(
            paginator,
            context=self.context,
            many=True
        )

        results = build_result_pagination(self, _PAGINATOR, serializer)
        return Response(results, status=response_status.HTTP_200_OK)

    def retrieve(self, request, uuid=None, format=None):
        instance = self.queryset_instance(uuid)
        serializer = RetrieveFragmentSerializer(instance, context=self.context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)
