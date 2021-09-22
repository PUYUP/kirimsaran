from copy import copy
from uuid import UUID

from django.db import transaction
from django.db.models import Q
from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist, ValidationError as DjangoValidationError
from django.utils.translation import gettext_lazy as _

from rest_framework import viewsets, status as response_status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination

from .serializers import (
    CreateSpreadSerializer,
    ListSpreadSerializer,
    RetrieveSpreadSerializer,
    RetrievePublicSpreadSerializer,
    UpdateSpreadSerializer
)
from ....helpers import build_result_pagination

Spread = apps.get_registered_model('feeder', 'Spread')

# Define to avoid used ...().paginate__
_PAGINATOR = LimitOffsetPagination()


class BaseViewSet(viewsets.ViewSet):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.context = dict()

    def initialize_request(self, request, *args, **kwargs):
        self.context.update({'request': request})
        return super().initialize_request(request, *args, **kwargs)


class SpreadViewSet(BaseViewSet):
    """
    GET
    -----

        .../spreads/?fragment=uuid4&broadcast=uuid4


    POST
    -----

        {   
            "content_type": "fragment",
            "object_id": "uuid4",
            "allocation": 14,
            "expiry_at": "Date time",
            "introduction": "A something..."
        }


    PATCH
    -----

        {
            "allocation": 14,
            "expiry_at": "Date time",
            "introduction": "A something..."
        }
    """
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)
    throttle_classes = (UserRateThrottle, AnonRateThrottle,)
    permission_action = {
        'retrieve': (AllowAny,),
    }

    def get_permissions(self):
        """
        Instantiates and returns
        the list of permissions that this view requires.
        """
        try:
            # return permission_classes depending on `action`
            return [permission() for permission in self.permission_action[self.action]]
        except KeyError:
            # action is not set return default permission_classes
            return [permission() for permission in self.permission_classes]

    def queryset(self):
        return Spread.objects \
            .prefetch_related('content_type', 'content_object') \
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

    def queryset_public_instance(self, identifier):
        try:
            return self.queryset().get(identifier=identifier)
        except ObjectDoesNotExist:
            raise NotFound()

    @transaction.atomic
    def create(self, request, format=None):
        serializer = CreateSpreadSerializer(
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
        serializer = UpdateSpreadSerializer(
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
        serializer = RetrieveSpreadSerializer(
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
        serializer = ListSpreadSerializer(
            paginator,
            context=self.context,
            many=True
        )

        results = build_result_pagination(self, _PAGINATOR, serializer)
        return Response(results, status=response_status.HTTP_200_OK)

    def retrieve(self, request, uuid=None, format=None):
        valid_uuid = True
        try:
            UUID(uuid).version
        except ValueError:
            valid_uuid = False

        if valid_uuid:
            instance = self.queryset_instance(uuid)
            serializer = RetrieveSpreadSerializer(
                instance,
                context=self.context
            )
        else:
            instance = self.queryset_public_instance(uuid)
            serializer = RetrievePublicSpreadSerializer(
                instance,
                context=self.context
            )

        return Response(serializer.data, status=response_status.HTTP_200_OK)
