from django.utils.translation import gettext_lazy as _
from django.apps import apps
from django.db import transaction

from rest_framework import serializers

Product = apps.get_registered_model('feeder', 'Product')
Fragment = apps.get_registered_model('feeder', 'Fragment')


class BaseFragmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fragment
        fields = '__all__'


class ListFragmentSerializer(BaseFragmentSerializer):
    permalink = serializers.HyperlinkedIdentityField(
        view_name='feeder_api:fragment-detail',
        lookup_field='uuid'
    )

    class Meta(BaseFragmentSerializer.Meta):
        fields = ('permalink', 'uuid', 'label', 'description', 'reward',)


class RetrieveFragmentSerializer(BaseFragmentSerializer):
    product = serializers.UUIDField(source='product.uuid')
    product_label = serializers.CharField(source='product.label')

    class Meta(BaseFragmentSerializer.Meta):
        fields = '__all__'


class CreateFragmentSerializer(BaseFragmentSerializer):
    product = serializers.SlugRelatedField(
        slug_field='uuid',
        queryset=Product.objects.all()
    )

    class Meta(BaseFragmentSerializer.Meta):
        fields = ('product', 'label', 'description', 'reward',)

    def to_representation(self, instance):
        serializer = RetrieveFragmentSerializer(instance, context=self.context)
        return serializer.data

    @transaction.atomic
    def create(self, validated_data):
        label = validated_data.pop('label', None)
        product = validated_data.pop('product', None)

        instance, _created = Fragment.objects \
            .update_or_create(label=label, product=product, defaults=validated_data)
        return instance


class UpdateFragmentSerializer(BaseFragmentSerializer):
    class Meta(BaseFragmentSerializer.Meta):
        fields = ('label', 'description', 'reward',)

    def to_representation(self, instance):
        serializer = RetrieveFragmentSerializer(instance, context=self.context)
        return serializer.data
