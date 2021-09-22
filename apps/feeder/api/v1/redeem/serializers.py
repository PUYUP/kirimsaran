from django.apps import apps

from rest_framework import serializers

Redeem = apps.get_registered_model('feeder', 'Redeem')
Reward = apps.get_registered_model('feeder', 'Reward')


"""
REWARD
"""


class RewardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reward
        fields = ('provider', 'label', 'description', 'term', 'allocation',
                  'start_at', 'expiry_at', 'type', 'amount', 'unit_slug',
                  'unit_label',)


class BaseRedeemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Redeem
        fields = '__all__'


class ListRedeemSerializer(BaseRedeemSerializer):
    permalink = serializers.HyperlinkedIdentityField(
        view_name='feeder_api:redeem-detail',
        lookup_field='uuid'
    )

    coupon_identifier = serializers.CharField(source='coupon.identifier')
    coupon_reward = RewardSerializer(source='coupon.reward')
    is_taken = serializers.BooleanField()

    class Meta(BaseRedeemSerializer.Meta):
        fields = ('uuid', 'permalink', 'coupon', 'coupon_identifier',
                  'coupon_reward', 'is_taken',)


class RetrieveRedeemSerializer(ListRedeemSerializer):
    class Meta(ListRedeemSerializer.Meta):
        pass
