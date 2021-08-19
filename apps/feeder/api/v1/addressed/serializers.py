from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django.apps import apps

from rest_framework import serializers

Broadcast = apps.get_registered_model('feeder', 'Broadcast')
Suggest = apps.get_registered_model('feeder', 'Suggest')
Addressed = apps.get_registered_model('feeder', 'Addressed')


class BaseAddressedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Addressed
        fields = '__all__'


class AddressedListSerializer(serializers.ListSerializer):
    def create(self, validated_data):
        addresseds = [Addressed(**item) for item in validated_data]
        return Addressed.objects.bulk_create(addresseds)


class ListAddressedSerializer(BaseAddressedSerializer):
    permalink = serializers.HyperlinkedIdentityField(
        view_name='feeder_api:addressed-detail',
        lookup_field='uuid'
    )

    msisdn = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()

    class Meta(BaseAddressedSerializer.Meta):
        fields = ('permalink', 'uuid', 'msisdn', 'email',)

    def get_msisdn(self, instance):
        if instance.msisdn:
            total_length = len(instance.msisdn)
            get_begining = instance.msisdn[:3]
            rest = total_length - len(get_begining)
            z = instance.msisdn[-rest:]
            c = [x.replace(x, '*') for x in z]

            return get_begining + ''.join(c)
        return None

    def get_email(self, instance):
        if instance.email:
            x = instance.email.split('@')
            y = [x.replace(x, '*') for x in x[0]]
            z = x[1]

            return ''.join(y) + '@' + z
        return None


class RetrieveAddressedSerializer(ListAddressedSerializer):
    broadcast = serializers.UUIDField(source='broadcast.uuid')

    class Meta(ListAddressedSerializer.Meta):
        fields = '__all__'


class CreateAddressedSerializer(BaseAddressedSerializer):
    broadcast = serializers.SlugRelatedField(
        slug_field='uuid',
        queryset=Broadcast.objects.all()
    )

    suggest = serializers.SlugRelatedField(
        slug_field='uuid',
        queryset=Suggest.objects.all()
    )

    class Meta(BaseAddressedSerializer.Meta):
        fields = ('broadcast', 'suggest',)
        list_serializer_class = AddressedListSerializer

    def to_representation(self, instance):
        serializer = RetrieveAddressedSerializer(
            instance,
            context=self.context
        )
        return serializer.data
