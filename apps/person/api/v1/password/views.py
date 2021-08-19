from django.db import transaction
from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import status as response_status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from .serializers import RecoveryPasswordSerializer


class RecoveryPasswordAPIView(APIView):
    """
    POST
    -----
        {
            "new_password": "string",
            "retype_password": "string",
            "token": "password recovery token",
            "uidb64": "password recovery uidb64",
            "validation": {
                "token": "token (securecode)",
                "passcode": "passcode (securecode)",
                "challenge": "password_recovery"
            }
        }
    """
    permission_classes = (AllowAny,)
    throttle_classes = (AnonRateThrottle,)

    @transaction.atomic()
    def post(self, request, format=None):
        serializer = RecoveryPasswordSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except (DjangoValidationError, Exception) as e:
                return Response(str(e), status=response_status.HTTP_403_FORBIDDEN)
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_406_NOT_ACCEPTABLE)
