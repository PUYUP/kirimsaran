from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator

from rest_framework import serializers
from rest_framework.exceptions import NotFound

from ..securecode.serializers import ValidationSerializer

UserModel = get_user_model()
SecureCode = apps.get_model('person', 'SecureCode')


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(
        validators=[validate_password],
        write_only=True
    )
    retype_password = serializers.CharField(
        validators=[validate_password],
        write_only=True
    )

    def validate_current_password(self, value):
        check_password = self.instance.check_password(value)
        if not check_password:
            raise serializers.ValidationError(
                detail=_("%s invalid current password" % value)
            )
        return value

    def validate_retype_password(self, value):
        if self.initial_data.get('new_password') != value:
            raise serializers.ValidationError(_("Password mismatch."))
        return value

    def to_representation(self, instance):
        return {'current_password': _("Successfull changed. Login with new password.")}

    @transaction.atomic
    def update(self, instance, validated_data):
        retype_password = validated_data.pop('retype_password', None)
        if retype_password:
            instance.set_password(retype_password)
            instance.save()
        return instance


class RecoveryPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(validators=[validate_password])
    retype_password = serializers.CharField(validators=[validate_password])

    token = serializers.CharField()
    uidb64 = serializers.CharField()

    # Securecode validation
    # Each custom field must write_only
    validation = ValidationSerializer(write_only=True)

    def validate_retype_password(self, value):
        if self.initial_data.get('new_password') != value:
            raise serializers.ValidationError(_("Password mismatch"))
        return value

    def validate_uidb64(self, value):
        try:
            urlsafe_base64_decode(value).decode()
        except Exception as e:
            raise serializers.ValidationError(detail=str(e))
        return value

    def get_and_validate_user(self, uidb64, token):
        uid = urlsafe_base64_decode(uidb64).decode()

        try:
            user = UserModel._default_manager.get(pk=uid)
        except ObjectDoesNotExist:
            raise NotFound(_("User not found"))

        # Validate user token
        is_token_valid = default_token_generator.check_token(user, token)
        if not is_token_valid:
            raise serializers.ValidationError(
                detail={'token': _("Invalid token")}
            )

        return user

    def to_internal_value(self, data):
        ret = super().to_internal_value(data)

        # get and validate user
        uidb64 = ret.pop('uidb64')
        token = ret.pop('token')
        user = self.get_and_validate_user(uidb64, token)

        ret.update({'user': user})
        return ret

    def to_representation(self, instance):
        return {'password': _("Successfull recovered. Login using new password.")}

    @transaction.atomic()
    def create(self, validated_data):
        validation = validated_data.pop('validation', None)
        user = validated_data.pop('user', None)

        # check issuer same as user field
        user_field_value = getattr(user, validation.issuer_type, None)
        if user_field_value != validation.issuer:
            raise serializers.ValidationError(
                detail={
                    'validation': _('%s mismatch validation issuer %s' % (user_field_value, validation.issuer))
                }
            )

        # mark securecode as used
        if validation:
            validation.mark_used()

        # set user password
        user.set_password(validated_data.pop('retype_password'))

        # set user field based on issuer_type to verified
        update_issuer_field = 'is_%s_verified' % validation.issuer_type
        setattr(user, update_issuer_field, True)

        user.save(update_fields=['password', update_issuer_field])
        return user
