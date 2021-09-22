from django.apps import apps
from django.db import transaction

from rest_framework import serializers

Order = apps.get_registered_model('feeder', 'Order')
OrderMeta = apps.get_registered_model('feeder', 'OrderMeta')
OrderItem = apps.get_registered_model('feeder', 'OrderItem')
Broadcast = apps.get_registered_model('feeder', 'Broadcast')
Fragment = apps.get_registered_model('feeder', 'Fragment')
Target = apps.get_registered_model('feeder', 'Target')

"""
CART META
"""


class BaseOrderMetaSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderMeta
        fields = '__all__'


class CreateOrderMetaSerializer(BaseOrderMetaSerializer):
    class Meta(BaseOrderMetaSerializer.Meta):
        fields = ('meta_key', 'meta_value',)


"""
CART ITEM
"""


class BaseOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = '__all__'


class ListOrderItemSerializer(BaseOrderItemSerializer):
    class Meta(BaseOrderItemSerializer.Meta):
        fields = ('uuid', 'price', 'method', 'value',)


class CreateOrderItemSerializer(BaseOrderItemSerializer):
    target = serializers.SlugRelatedField(
        slug_field='uuid',
        queryset=Target.objects.all()
    )

    class Meta(BaseOrderItemSerializer.Meta):
        fields = ('target',)


"""
CART
"""


class BaseOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'


class ListOrderSerializer(BaseOrderSerializer):
    permalink = serializers.HyperlinkedIdentityField(
        view_name='feeder_api:order-detail',
        lookup_field='uuid'
    )

    class Meta(BaseOrderSerializer.Meta):
        fields = ('permalink', 'uuid', 'identifier',)


class RetrieveOrderSerializer(ListOrderSerializer):
    class Meta(ListOrderSerializer.Meta):
        fields = ('permalink', 'uuid', 'identifier',
                  'broadcast', 'metas',)
        depth = 1


class CreateOrderSerializer(BaseOrderSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    metas = CreateOrderMetaSerializer(required=False, many=True)
    items = CreateOrderItemSerializer(required=True, many=True)

    broadcast = serializers.SlugRelatedField(
        slug_field='uuid',
        queryset=Broadcast.objects.all()
    )
    fragment = serializers.SlugRelatedField(
        slug_field='uuid',
        queryset=Fragment.objects.all()
    )

    class Meta(BaseOrderSerializer.Meta):
        fields = ('user', 'broadcast', 'fragment', 'metas', 'items',)
        extra_kwargs = {
            'broadcast': {'allow_empty': False, 'required': True},
            'fragment': {'allow_empty': False, 'required': True},
        }

    def to_representation(self, instance):
        serializer = RetrieveOrderSerializer(instance, context=self.context)
        return serializer.data

    @transaction.atomic
    def create(self, validated_data):
        metas = validated_data.pop('metas', None)
        items = validated_data.pop('items', None)

        instance = self.Meta.model.objects.create(**validated_data)
        if instance:
            # create meta
            instance.insert_meta(metas)

            # create items
            instance.insert_order_item(items)

        return instance
