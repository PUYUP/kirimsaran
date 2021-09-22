from django.apps import apps
from django.db import transaction

from rest_framework import serializers

from apps.person.api.v1.profile.serializers import RetrieveProfileSerializer

Listing = apps.get_registered_model('feeder', 'Listing')


class BaseListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Listing
        fields = '__all__'


class ListListingSerializer(BaseListingSerializer):
    profile = RetrieveProfileSerializer(source='user.profile')
    permalink = serializers.HyperlinkedIdentityField(
        view_name='feeder_api:listing-detail',
        lookup_field='uuid'
    )

    class Meta(BaseListingSerializer.Meta):
        fields = ('permalink', 'uuid', 'label', 'description', 'profile',)


class RetrieveListingSerializer(ListListingSerializer):
    class Meta(ListListingSerializer.Meta):
        pass


class CreateListingSerializer(BaseListingSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta(BaseListingSerializer.Meta):
        fields = ('user', 'label', 'description',)

    def to_representation(self, instance):
        serializer = RetrieveListingSerializer(instance, context=self.context)
        return serializer.data

    @transaction.atomic
    def create(self, validated_data):
        label = validated_data.pop('label', None)
        instance, _created = Listing.objects \
            .update_or_create(label=label, defaults=validated_data)
        return instance


class UpdateListingSerializer(BaseListingSerializer):
    class Meta(BaseListingSerializer.Meta):
        fields = ('label', 'description',)

    def to_representation(self, instance):
        serializer = RetrieveListingSerializer(instance, context=self.context)
        return serializer.data
