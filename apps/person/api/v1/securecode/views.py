from django.db import transaction
from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist, ValidationError as DjangoValidationError

from rest_framework.exceptions import NotFound, ValidationError
from rest_framework import viewsets, status as response_status
from rest_framework.permissions import AllowAny
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.response import Response

from .serializers import GenerateSecureCodeSerializer, ValidateSecureCodeSerializer

SecureCode = apps.get_model('person', 'SecureCode')


class BaseViewSet(viewsets.ViewSet):
    permission_classes = (AllowAny,)
    throttle_classes = (AnonRateThrottle, UserRateThrottle,)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.context = dict()

    def initialize_request(self, request, *args, **kwargs):
        self.context.update({'request': request})
        return super().initialize_request(request, *args, **kwargs)


class SecureCodeViewSet(BaseViewSet):
    """
    POST
    -----
        {
            "issuer": "valid email or msisdn",
            "challenge": "validate_email"
        }


    PATCH
    -----
        {
            "token": "abc1415zy",
            "challenge": "validate_email"
        }
    """
    lookup_field = 'passcode'

    def queryset(self, **kwargs):
        try:
            return SecureCode.objects.unverified(**kwargs).get()
        except ObjectDoesNotExist:
            raise NotFound()

    @transaction.atomic
    def create(self, request, format=None):
        serializer = GenerateSecureCodeSerializer(
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
    def partial_update(self, request, passcode=None, format=None):
        instance = self.queryset(passcode=passcode)
        serializer = ValidateSecureCodeSerializer(
            instance,
            data=request.data,
            context=self.context
        )

        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save(update_fields=['is_verified'])
            except DjangoValidationError as e:
                raise ValidationError(detail=str(e))
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_406_NOT_ACCEPTABLE)
