from copy import copy

from django.db import transaction
from django.db.models import Count, Q
from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist, ValidationError as DjangoValidationError
from django.utils.translation import gettext_lazy as _

from rest_framework import viewsets, status as response_status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import AnonRateThrottle
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination

from .serializers import (
    CreateSuggestSerializer,
    ListSuggestSerializer,
    RetrieveSuggestSerializer,
    UpdateSuggestSerializer
)
from ....helpers import build_result_pagination

Suggest = apps.get_registered_model('feeder', 'Suggest')

# Define to avoid used ...().paginate__
_PAGINATOR = LimitOffsetPagination()


class BaseViewSet(viewsets.ViewSet):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.context = dict()

    def initialize_request(self, request, *args, **kwargs):
        self.context.update({'request': request})
        return super().initialize_request(request, *args, **kwargs)


class SuggestViewSet(BaseViewSet):
    """
    GET
    -----

        .../suggests/?product=uuid4&fragment=uuid4&canal=<msisdn,email,telegram,whatsapp>&rating=<1-5>&permit=<public,private>


    POST & PATCH
    -----

        {
            "spread":"W8hgVg",
            "rating": "1",
            "description": "pahit",
            "canals": [
                {
                    "method": "phone", 
                    "value": "08979614343"
                }
            ]
        }

    """
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)
    throttle_classes = (AnonRateThrottle,)
    permission_action = {
        'create': (AllowAny,),
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
        return Suggest.objects \
            .prefetch_related('user', 'spread', 'spread__content_object', 'canals',
                              'coupons', 'coupons__reward', 'interactions') \
            .select_related('user', 'spread') \
            .annotate(count_interaction=Count('interactions'))

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
        serializer = CreateSuggestSerializer(
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
        serializer = UpdateSuggestSerializer(
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
        serializer = RetrieveSuggestSerializer(
            instance_copy,
            context=self.context
        )
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    def list(self, request, format=None):
        permit = request.query_params.get('permit', 'private')
        canal = request.query_params.get('canal', None)
        rating = request.query_params.get('rating', None)
        product = request.query_params.get('product', None)
        fragment = request.query_params.get('fragment', None)
        keyword = request.query_params.get('keyword', None)

        if permit == 'private':
            # only owner can see data
            queryset = self.queryset().filter(
                spread__fragment__listing__user_id=request.user.id
            ).order_by('-create_at')

            if canal:
                try:
                    queryset = queryset.filter(canals__method=canal)
                except Exception as e:
                    raise ValidationError(detail=str(e))

            if rating:
                try:
                    queryset = queryset.filter(rating=rating)
                except Exception as e:
                    raise ValidationError(detail=str(e))

            if product:
                try:
                    queryset = queryset.filter(
                        spread__fragment__product__uuid=product
                    )
                except Exception as e:
                    raise ValidationError(detail=str(e))

            if fragment:
                try:
                    queryset = queryset.filter(spread__fragment__uuid=fragment)
                except Exception as e:
                    raise ValidationError(detail=str(e))

            if keyword:
                # make list
                keyword_list = keyword.split(',')

                # clean space
                keywords = [k.strip() for k in keyword_list]

                # querying
                q_description = Q()
                for q in keywords:
                    q_description |= Q(description__icontains=q)

                queryset = queryset.filter(q_description)

        elif permit == 'public':
            queryset = self.queryset().filter(user_id=request.user.id) \
                .order_by('-create_at')

        paginator = _PAGINATOR.paginate_queryset(queryset, request)
        serializer = ListSuggestSerializer(
            paginator,
            context=self.context,
            many=True
        )

        results = build_result_pagination(self, _PAGINATOR, serializer)
        return Response(results, status=response_status.HTTP_200_OK)

    def retrieve(self, request, uuid=None, format=None):
        instance = self.queryset_instance(uuid)
        serializer = RetrieveSuggestSerializer(instance, context=self.context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)
