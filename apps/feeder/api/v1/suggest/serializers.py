from django.core.validators import validate_email
from django.db import transaction
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.apps import apps

from rest_framework import serializers
from apps.feeder.utils import censor_email, censor_msisdn
from apps.feeder.validators import validate_msisdn

Spread = apps.get_registered_model('feeder', 'Spread')
Suggest = apps.get_registered_model('feeder', 'Suggest')
Canal = apps.get_registered_model('feeder', 'Canal')
Coupon = apps.get_registered_model('feeder', 'Coupon')
Reward = apps.get_registered_model('feeder', 'Reward')

"""
CANAL
"""


class BaseCanalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Canal
        fields = '__all__'


class ListCanalSerializer(BaseCanalSerializer):
    value = serializers.SerializerMethodField()

    class Meta(BaseCanalSerializer.Meta):
        fields = ('method', 'value',)

    def get_value(self, instance):
        method = instance.Method
        try:
            if instance.method != method.EMAIL:
                return censor_msisdn(instance.value)
            else:
                return censor_email(instance.value)
        except Exception:
            return None


class CreateCanalSerializer(BaseCanalSerializer):
    class Meta(BaseCanalSerializer.Meta):
        fields = ('method', 'value',)

    def validate(self, attrs):
        method = attrs.get('method')
        value = attrs.get('value')

        validator = getattr(self, 'validate_%s' % method)
        validator(value)

        return super().validate(attrs)

    def validate_email(self, value):
        return validate_email(value)

    def validate_msisdn(self, value):
        return validate_msisdn(value)

    validate_phone = validate_msisdn
    validate_whatsapp = validate_msisdn
    validate_telegram = validate_msisdn


"""
SUGGEST
"""


class BaseSuggestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Suggest
        fields = '__all__'


"""
FOR PUBLIC RESPONSE
"""


class _RewardPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reward
        fields = ('label', 'provider', 'description', 'term',
                  'amount', 'unit_label', 'unit_slug',)


class _CouponsPublicSerializer(serializers.ModelSerializer):
    reward = _RewardPublicSerializer(many=False)

    class Meta:
        model = Coupon
        fields = ('identifier', 'is_active', 'is_used', 'reward', )


class ListSuggestSerializer(BaseSuggestSerializer):
    permalink = serializers.HyperlinkedIdentityField(
        view_name='feeder_api:suggest-detail',
        lookup_field='uuid'
    )
    product_label = serializers.SerializerMethodField()
    canals = ListCanalSerializer(many=True)
    count_interaction = serializers.IntegerField(read_only=True)

    class Meta(BaseSuggestSerializer.Meta):
        fields = ('permalink', 'uuid', 'rating', 'description',
                  'canals', 'product_label', 'count_interaction',)

    def get_product_label(self, instance):
        return instance.spread.product('label')

    def to_representation(self, instance):
        request = self.context.get('request')
        ret = super().to_representation(instance)

        user = request.user
        suggester = getattr(instance, 'user')

        # only suggester can see coupons
        if user and user.is_authenticated and suggester and user.id == suggester.id:
            coupons = instance.coupons.all()
            ret.update(
                {'coupons': _CouponsPublicSerializer(coupons, many=True).data}
            )

        return ret


class RetrieveSuggestSerializer(ListSuggestSerializer):
    # spread = serializers.UUIDField(source='spread.uuid')
    # spread_identifier = serializers.CharField(source='spread.identifier')

    class Meta(ListSuggestSerializer.Meta):
        pass


class RetrieveSuggestPublicSerializer(ListSuggestSerializer):
    coupons = _CouponsPublicSerializer(many=True)

    class Meta(ListSuggestSerializer.Meta):
        fields = ListSuggestSerializer.Meta.fields + ('coupons',)


class CreateSuggestSerializer(BaseSuggestSerializer):
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault(),
        required=False
    )
    spread = serializers.SlugRelatedField(
        slug_field='identifier',
        queryset=Spread.objects.all()
    )
    canals = CreateCanalSerializer(many=True)

    class Meta(BaseSuggestSerializer.Meta):
        fields = ('user', 'spread', 'rating', 'description', 'canals',)

    def to_representation(self, instance):
        ret = {}
        serializer = RetrieveSuggestPublicSerializer(
            instance,
            context=self.context
        )

        ret.update(serializer.data)
        return ret

    def to_internal_value(self, data):
        return super().to_internal_value(data)

    def validate(self, attrs):
        data = super().validate(attrs)
        spread = data.get('spread', None)
        rewards = spread.fragment.first().rewards.all()

        if rewards.exists():
            # if has rewards user only can 1 time give suggest
            canals = self.initial_data.get('canals', None)
            q_coupon_canals = Q()
            q_canals = Q()
            q_value = []

            for canal in canals:
                m = canal.get('method')
                v = canal.get('value')

                q_value.append(v)

                q_canals |= Q(
                    canals__method=m,
                    canals__value=v
                )

                # only suggest has coupons restrict send multiple times
                q_coupon_canals |= Q(
                    coupons__suggest__canals__method=m,
                    coupons__suggest__canals__value=v,
                    coupons__is_active=True
                )

            suggets = spread.suggests.filter(
                q_coupon_canals,
                q_canals
            ).distinct()

            if suggets.exists():
                raise serializers.ValidationError({
                    'canals': _("%s telah digunakan memberi saran" % ' atau '.join(q_value))
                })

        return data

    def validate_spread(self, value):
        total_suggest = getattr(value, 'total_suggest', 0)
        allocation = getattr(value, 'allocation', 0)
        expiry_at = getattr(value, 'expiry_at')

        if timezone.localdate(timezone.now()) > timezone.localdate(expiry_at):
            raise serializers.ValidationError(
                _("Has expired at %s" % expiry_at)
            )

        if allocation != 0 and total_suggest >= allocation:
            raise serializers.ValidationError(
                _("Allocation excessed. Max %s suggest" % allocation)
            )

        return value

    @transaction.atomic
    def create(self, validated_data):
        canals = validated_data.pop('canals', None)

        # validate the user
        user = validated_data.pop('user')
        user = None if user.is_anonymous else user

        instance = self.Meta.model.objects.create(user=user, **validated_data)

        if instance:
            # insert canal
            try:
                instance.insert_canal(canals)
            except Exception as e:
                raise serializers.ValidationError(detail=str(e))

        instance.refresh_from_db()

        # redeem coupon!
        instance.redeem_coupon()

        return instance


class UpdateSuggestSerializer(BaseSuggestSerializer):
    class Meta(BaseSuggestSerializer.Meta):
        fields = ('rating', 'description',)

    def to_representation(self, instance):
        serializer = RetrieveSuggestSerializer(instance, context=self.context)
        return serializer.data
