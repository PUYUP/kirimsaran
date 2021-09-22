from copy import copy

from django.db import transaction
from django.db.models import Q
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
    CreateRewardSerializer,
    ListRewardSerializer,
    RetrieveRewardSerializer,
    UpdateRewardSerializer
)
from ....helpers import build_result_pagination

Reward = apps.get_registered_model('feeder', 'Reward')

# Define to avoid used ...().paginate__
_PAGINATOR = LimitOffsetPagination()


class BaseViewSet(viewsets.ViewSet):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.context = dict()

    def initialize_request(self, request, *args, **kwargs):
        self.context.update({'request': request})
        return super().initialize_request(request, *args, **kwargs)


class RewardViewSet(BaseViewSet):
    """
    GET
    -----

        .../rewards/?fragment=uuid4&broadcast=uuid4


    POST
    -----

        {   
            "content_type": "fragment",
            "object_id": "uuid4",
            "provider": "string",
            "label": "string",
            "description": "string", [optional]
            "term": "string",
            "allocation": 14,
            "expiry_at": "Date time",
            "type": "gift, etc",
            "value": "string",
            "unit_slug": "slug string",
            "unit_label": "string"
        }


    PATCH
    -----

        {
            "provider": "string",
            "label": "string",
            "description": "string", [optional]
            "term": "string",
            "allocation": 14,
            "expiry_at": "Date time",
            "type": "gift, etc",
            "value": "string",
            "unit_slug": "slug string",
            "unit_label": "string"
        }
    """
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)
    throttle_classes = (UserRateThrottle,)

    def queryset(self):
        return Reward.objects \
            .prefetch_related('content_type') \
            .select_related('content_type') \
            .filter(
                Q(fragment__user_id=self.request.user.id)
                | Q(broadcast__user_id=self.request.user.id)
            )

    def queryset_instance(self, uuid, for_update=False):
        try:
            if for_update:
                return self.queryset().select_for_update().get(uuid=uuid)
            return self.queryset().get(uuid=uuid)
        except ObjectDoesNotExist:
            raise NotFound()

    @transaction.atomic
    def create(self, request, format=None):
        serializer = CreateRewardSerializer(
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
        serializer = UpdateRewardSerializer(
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
            instance = self.queryset().get(uuid=uuid)
        except ObjectDoesNotExist:
            raise NotFound()

        # copy for response
        instance_copy = copy(instance)

        # run delete
        instance.delete()

        # return object
        serializer = RetrieveRewardSerializer(
            instance_copy,
            context=self.context
        )
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    def list(self, request, format=None):
        queryset = self.queryset()
        fragment = request.query_params.get('fragment', None)
        broadcast = request.query_params.get('broadcast', None)

        if not fragment and not broadcast:
            raise ValidationError(detail={
                'param': _("Fragment or Broadcast required")
            })

        if fragment and broadcast:
            raise ValidationError(detail={
                'param': _("Can't use both Fragment and Broadcast")
            })

        try:
            # validate uuid here
            # read this docs: https://docs.djangoproject.com/en/3.2/ref/contrib/contenttypes/
            if fragment:
                queryset = queryset.filter(
                    Q(fragment__isnull=False) & Q(fragment__uuid=fragment)
                )

            if broadcast:
                queryset = queryset.filter(
                    Q(broadcast__isnull=False) & Q(broadcast__uuid=broadcast)
                )
        except DjangoValidationError as e:
            raise ValidationError(detail={
                'param': str(e)
            })

        paginator = _PAGINATOR.paginate_queryset(queryset, request)
        serializer = ListRewardSerializer(
            paginator,
            context=self.context,
            many=True
        )

        results = build_result_pagination(self, _PAGINATOR, serializer)
        return Response(results, status=response_status.HTTP_200_OK)

    def retrieve(self, request, uuid=None, format=None):
        instance = self.queryset_instance(uuid)
        serializer = RetrieveRewardSerializer(instance, context=self.context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)
