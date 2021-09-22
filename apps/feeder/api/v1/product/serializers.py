from django.utils.translation import gettext_lazy as _
from django.apps import apps
from django.db import transaction

from rest_framework import serializers

Listing = apps.get_registered_model('feeder', 'Listing')
Product = apps.get_registered_model('feeder', 'Product')


class BaseProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


class ListProductSerializer(BaseProductSerializer):
    permalink = serializers.HyperlinkedIdentityField(
        view_name='feeder_api:product-detail',
        lookup_field='uuid'
    )
    listing = serializers.UUIDField(source='listing.uuid')
    listing_label = serializers.CharField(source='listing.label')

    class Meta(BaseProductSerializer.Meta):
        fields = ('permalink', 'uuid', 'listing', 'listing_label',
                  'label', 'description',)


class RetrieveProductSerializer(ListProductSerializer):
    class Meta(ListProductSerializer.Meta):
        fields = '__all__'


class CreateProductSerializer(BaseProductSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    listing = serializers.SlugRelatedField(
        slug_field='uuid',
        queryset=Listing.objects.all()
    )

    class Meta(BaseProductSerializer.Meta):
        fields = ('user', 'listing', 'label', 'description',)

    def to_representation(self, instance):
        serializer = RetrieveProductSerializer(instance, context=self.context)
        return serializer.data

    @transaction.atomic
    def create(self, validated_data):
        label = validated_data.pop('label', None)
        listing = validated_data.pop('listing', None)
        user = validated_data.pop('user', None)

        instance, _created = Product.objects \
            .update_or_create(
                label=label,
                user=user,
                listing=listing,
                defaults=validated_data
            )

        return instance


class UpdateProductSerializer(BaseProductSerializer):
    class Meta(BaseProductSerializer.Meta):
        fields = ('label', 'description',)

    def to_representation(self, instance):
        serializer = RetrieveProductSerializer(instance, context=self.context)
        return serializer.data
