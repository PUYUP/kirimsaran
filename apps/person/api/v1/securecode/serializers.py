from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from ....utils import get_password_recovery_token_uidb64

SecureCode = apps.get_model('person', 'SecureCode')


class BaseSecureCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SecureCode
        fields = '__all__'


class RetrieveSecureCodeSerializer(BaseSecureCodeSerializer):
    class Meta(BaseSecureCodeSerializer.Meta):
        fields = ('token', 'issuer', 'issuer_type',
                  'challenge', 'valid_until', 'is_verified',)


class GenerateSecureCodeSerializer(BaseSecureCodeSerializer):
    class Meta(BaseSecureCodeSerializer.Meta):
        fields = ('issuer', 'challenge',)

    def to_representation(self, instance):
        serializer = RetrieveSecureCodeSerializer(instance)
        return serializer.data

    def validate(self, attrs):
        # Call model validation
        model_attrs = attrs
        if self.instance:
            model_attrs = {
                field.name: getattr(self.instance, field.name)
                for field in self.instance._meta.fields
            }

        self.Meta.model(**model_attrs).clean()
        return super().validate(attrs)

    @transaction.atomic()
    def create(self, validated_data):
        request = self.context.get('request')

        validated_data.update({
            'user_agent': request.META['HTTP_USER_AGENT'],
            'is_used': False,
            'is_verified': False,
        })

        # If `valid_until` greater than time now we update SecureCode Code
        instance, _created = self.Meta.model.objects \
            .generate(data={**validated_data})
        return instance


class ValidateSecureCodeSerializer(BaseSecureCodeSerializer):
    class Meta(BaseSecureCodeSerializer.Meta):
        fields = ('token', 'challenge',)
        extra_kwargs = {
            'token': {'required': True, 'allow_blank': False},
            'challenge': {'required': True, 'allow_blank': False},
        }

    def get_token_uidb64_password_recovery(self):
        """Get token from email or msisdn and raise error if user not found"""
        issuer = self.instance.issuer

        try:
            return get_password_recovery_token_uidb64(issuer)
        except ValueError as e:
            raise serializers.ValidationError(detail={'email_msisdn': str(e)})

    def validate_token(self, value):
        if self.instance.token != value:
            raise serializers.ValidationError(detail=_("Invalid token."))
        return value

    def validate_challenge(self, value):
        if self.instance.challenge != value:
            raise serializers.ValidationError(detail=_("Invalid challenge."))
        return value

    def to_internal_value(self, data):
        data = super().to_internal_value(data)

        # Update field value
        data.update({'is_verified': True})
        return data

    def to_representation(self, instance):
        ret = {'passcode': instance.passcode}
        serializer = RetrieveSecureCodeSerializer(instance)
        ret.update(serializer.data)

        # password recovery additional response
        if instance.challenge == SecureCode.Challenges.PASSWORD_RECOVERY:
            ptoken, puidb64 = self.get_token_uidb64_password_recovery()
            if ptoken and puidb64:
                ret.update({
                    instance.challenge: {
                        'token': ptoken,
                        'uidb64': puidb64
                    }
                })

        return ret


class ValidationSerializer(serializers.Serializer):
    """Global securecode validation"""
    passcode = serializers.CharField()
    token = serializers.CharField()
    challenge = serializers.CharField()

    def to_internal_value(self, data):
        try:
            return SecureCode.objects.verified(**data).get()
        except ObjectDoesNotExist:
            raise serializers.ValidationError(
                detail=_("Validation failed"))
