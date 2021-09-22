from copy import copy

from django.db import transaction
from django.db.models import Q
from django.db.models.expressions import Exists, OuterRef
from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist, ValidationError as DjangoValidationError
from django.utils.translation import gettext_lazy as _

from rest_framework import viewsets, status as response_status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination

from .serializers import CreateInteractionSerializer, ListInteractionSerializer, RetrieveInteractionSerializer, UpdateInteractionSerializer
from ....helpers import build_result_pagination

Interaction = apps.get_registered_model('feeder', 'Interaction')
Suggest = apps.get_registered_model('feeder', 'Suggest')
Product = apps.get_registered_model('feeder', 'Product')

# Define to avoid used ...().paginate__
_PAGINATOR = LimitOffsetPagination()


class BaseViewSet(viewsets.ViewSet):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.context = dict()

    def initialize_request(self, request, *args, **kwargs):
        self.context.update({'request': request})
        return super().initialize_request(request, *args, **kwargs)


class InteractionViewSet(BaseViewSet):
    """
    GET
    -----

        .../?suggest=<uuid4>


    POST
    -----

        {
            "suggest": "uuid4",
            "type": "info, respond",
            "description": "Sell all not food"
        }

    """
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)
    throttle_classes = (UserRateThrottle,)

    def queryset(self):
        product_queryset = Product.objects \
            .filter(
                fragments__spreads__suggests__interactions__id=OuterRef('id'),
                listing__user_id=OuterRef('user__id')
            )

        return Interaction.objects \
            .prefetch_related('user', 'user__profile') \
            .select_related('user', 'user__profile') \
            .annotate(is_product_owner=Exists(product_queryset)) \
            .filter(
                Q(suggest__user_id=self.request.user.id)
                | Q(suggest__spread__fragment__listing__user_id=self.request.user.id)
            )

    def queryset_instance(self, uuid, for_update=False):
        try:
            if for_update:
                return self.queryset().select_for_update() \
                    .get(uuid=uuid, user_id=self.request.user.id)
            return self.queryset().get(uuid=uuid)
        except ObjectDoesNotExist:
            raise NotFound()

    @transaction.atomic
    def create(self, request, format=None):
        serializer = CreateInteractionSerializer(
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
        serializer = UpdateInteractionSerializer(
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
                .get(uuid=uuid, user_id=request.user.id)
        except ObjectDoesNotExist:
            raise NotFound()

        # copy for response
        instance_copy = copy(instance)

        # run delete
        instance.delete()

        # return object
        serializer = RetrieveInteractionSerializer(
            instance_copy,
            context=self.context
        )
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    def list(self, request, format=None):
        queryset = self.queryset()
        suggest = request.query_params.get('suggest')

        if not suggest:
            raise ValidationError(detail={
                'suggest': _("Suggest required")
            })

        try:
            queryset = queryset.filter(suggest__uuid=suggest)
        except Exception as e:
            raise ValidationError(detail=str(e))

        paginator = _PAGINATOR.paginate_queryset(queryset, request)
        serializer = ListInteractionSerializer(
            paginator,
            context=self.context,
            many=True
        )

        results = build_result_pagination(self, _PAGINATOR, serializer)
        return Response(results, status=response_status.HTTP_200_OK)

    def retrieve(self, request, uuid=None, format=None):
        instance = self.queryset_instance(uuid)
        serializer = RetrieveInteractionSerializer(
            instance, context=self.context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)
