from django.apps import apps
from django.db import transaction
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers

from ....conf import settings
from ..securecode.serializers import ValidationSerializer
from ..profile.serializers import RetrieveProfileSerializer

UserModel = get_user_model()
SecureCode = apps.get_model('person', 'SecureCode')


class BaseUserSerializer(serializers.ModelSerializer):
    # Each custom field must write_only
    validation = ValidationSerializer(write_only=True, required=False)

    class Meta:
        model = UserModel
        fields = '__all__'

    def matching_validation_field(self, validation, validated_data):
        # issuer_type must match with some user field
        # this case use email field
        issuer_type = validation.issuer_type
        if issuer_type not in validated_data.keys():
            raise serializers.ValidationError(
                detail={
                    'validation': _('%s not exist in user field' % issuer_type.upper())
                }
            )

        # check user param same value in issuer
        field_validation = validated_data.get(issuer_type.lower(), None)
        if validation.issuer != field_validation:
            raise serializers.ValidationError(
                detail={
                    'validation': _('%s mismatch validation issuer %s' % (field_validation, validation.issuer))
                }
            )

        # now mark as used!
        validation.mark_used()

        # set is_<issuer_type>_verified
        # eg: is_email_verified
        validated_data.update({'is_%s_verified' % issuer_type.lower(): True})
        return validated_data

    def validate(self, attrs):
        # if has verification field :validation required
        has_verification_field = any(
            [field in settings.PERSON_VERIFICATION_FIELDS for field in attrs.keys()]
        )

        if has_verification_field and 'validation' not in attrs.keys():
            raise serializers.ValidationError(
                detail={
                    'validation': _("This field is required.")
                }
            )

        return super().validate(attrs)


class RetrieveUserSerializer(BaseUserSerializer):
    profile = RetrieveProfileSerializer(many=False, required=False)

    class Meta(BaseUserSerializer.Meta):
        fields = ('hexid', 'username', 'email', 'msisdn',
                  'is_email_verified', 'is_msisdn_verified',
                  'profile',)


class CreateUserSerializer(BaseUserSerializer):
    """
    Rules;
    - :email or :msisdn must validate with securecode
    """
    # Each custom field must write_only
    # will return error at serializer because field not exists in model
    retype_password = serializers.CharField(
        write_only=True,
        validators=[validate_password]
    )

    class Meta(BaseUserSerializer.Meta):
        fields = ('email', 'msisdn', 'username', 'password',
                  'retype_password', 'validation',)
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def validate_retype_password(self, value):
        if self.initial_data.get('password') != value:
            raise serializers.ValidationError(_("Password mismatch."))

        return value

    def to_representation(self, instance):
        serializer = RetrieveUserSerializer(
            instance,
            many=False,
            context=self.context
        )
        return serializer.data

    @transaction.atomic
    def create(self, validated_data):
        retype_password = validated_data.pop('retype_password')  # not used
        validated_data.update({'password': retype_password})

        # validation issuer checker
        validation = validated_data.pop('validation', None)
        if validation:
            validated_data = self.matching_validation_field(
                validation,
                validated_data
            )

        # ready to create user
        instance = UserModel.objects.create_user(**validated_data)
        return instance


class UpdateUserSerializer(BaseUserSerializer):
    """
    Rules;
    - update :email and :msisdn required verification (send and validate securecode)
    """
    class Meta(BaseUserSerializer.Meta):
        fields = ('email', 'msisdn', 'username', 'validation',)

    def validate(self, attrs):
        # can't update email and msisdn at same time
        restrict_fields = ['email', 'msisdn']
        check_fields_same = list(
            set(restrict_fields) & set(list(attrs.keys()))
        )

        if set(check_fields_same) == set(restrict_fields):
            raise serializers.ValidationError(
                detail=_("Can't update email and msisdn same time")
            )

        return super().validate(attrs)

    def to_representation(self, instance):
        serializer = RetrieveUserSerializer(
            instance,
            many=False,
            context=self.context
        )
        return serializer.data

    @transaction.atomic
    def update(self, instance, validated_data):
        # validation issuer checker
        validation = validated_data.pop('validation', None)
        if validation:
            validated_data = self.matching_validation_field(
                validation,
                validated_data
            )

        for key, value in validated_data.items():
            if hasattr(instance, key):
                old_value = getattr(instance, key, None)
                if old_value != value:
                    # if validation not present then email or msisdn changed
                    # mark them as unverified
                    if not validation:
                        if key == 'email' or key == 'msisdn':
                            setattr(instance, 'is_%s_verified' % key, False)
                    setattr(instance, key, value)

        instance.save()
        return instance


class TokenObtainPairSerializerExtend(TokenObtainPairSerializer):
    def validate(self, attrs):
        context = {}
        data = super().validate(attrs)
        user = RetrieveUserSerializer(
            self.user,
            many=False,
            context=self.context
        )

        context.update({
            'token': data,
            'user': user.data
        })
        return context
