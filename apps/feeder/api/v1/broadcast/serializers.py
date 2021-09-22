import calendar
import time

from django.utils.translation import gettext_lazy as _
from django.apps import apps
from django.db import transaction

from rest_framework import serializers

Listing = apps.get_registered_model('feeder', 'Listing')
Product = apps.get_registered_model('feeder', 'Product')
Broadcast = apps.get_registered_model('feeder', 'Broadcast')
Target = apps.get_registered_model('feeder', 'Target')
Suggest = apps.get_registered_model('feeder', 'Suggest')
Fragment = apps.get_registered_model('feeder', 'Fragment')


"""
TARGET
"""


class BaseTargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Target
        fields = '__all__'


class CreateTargetSerializer(BaseTargetSerializer):
    suggest = serializers.SlugRelatedField(
        slug_field='uuid',
        queryset=Suggest.objects.all()
    )

    class Meta(BaseTargetSerializer.Meta):
        fields = ('suggest',)


"""
BROADCAST
"""


class BaseBroadcastSerializer(serializers.ModelSerializer):
    class Meta:
        model = Broadcast
        fields = '__all__'


class ListBroadcastSerializer(BaseBroadcastSerializer):
    product = serializers.UUIDField(source='product.uuid', read_only=True)
    product_label = serializers.CharField(
        source='product.label',
        read_only=True
    )
    listing = serializers.UUIDField(source='listing.uuid', read_only=True)
    listing_label = serializers.CharField(
        source='listing.label',
        read_only=True
    )
    fragment = serializers.UUIDField(source='fragment.uuid', read_only=True)
    fragment_label = serializers.CharField(
        source='fragment.label',
        read_only=True
    )
    permalink = serializers.HyperlinkedIdentityField(
        view_name='feeder_api:broadcast-detail',
        lookup_field='uuid'
    )

    class Meta(BaseBroadcastSerializer.Meta):
        fields = ('permalink', 'uuid', 'label', 'listing', 'listing_label',
                  'product', 'product_label', 'fragment', 'fragment_label',
                  'description', 'message',)


class RetrieveBroadcastSerializer(ListBroadcastSerializer):
    class Meta(ListBroadcastSerializer.Meta):
        fields = '__all__'


class CreateBroadcastSerializer(BaseBroadcastSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    product = serializers.SlugRelatedField(
        slug_field='uuid',
        queryset=Product.objects.all(),
        required=False
    )
    fragment = serializers.SlugRelatedField(
        slug_field='uuid',
        queryset=Fragment.objects.all(),
        required=False
    )
    targets = CreateTargetSerializer(many=True)

    class Meta(BaseBroadcastSerializer.Meta):
        fields = ('user', 'product', 'fragment', 'label', 'description',
                  'message', 'targets',)

    def to_representation(self, instance):
        serializer = RetrieveBroadcastSerializer(
            instance,
            context=self.context
        )
        return serializer.data

    @transaction.atomic
    def create(self, validated_data):
        label = validated_data.pop('label', None)
        targets = validated_data.pop('targets', None)

        instance, _created = Broadcast.objects \
            .update_or_create(label=label, defaults=validated_data)

        if instance and targets:
            # create target
            gmt = time.gmtime()
            ts = calendar.timegm(gmt)
            bulk_target = [
                Target(
                    broadcast=instance,
                    moment=ts,
                    **item
                ) for item in targets
            ]

            if len(bulk_target) > 0:
                try:
                    Target.objects.bulk_create(
                        bulk_target,
                        ignore_conflicts=False
                    )
                except Exception as e:
                    print(e)
        return instance


class UpdateBroadcastSerializer(BaseBroadcastSerializer):
    class Meta(BaseBroadcastSerializer.Meta):
        fields = ('label', 'description', 'message',)

    def to_representation(self, instance):
        serializer = RetrieveBroadcastSerializer(
            instance,
            context=self.context
        )
        return serializer.data
