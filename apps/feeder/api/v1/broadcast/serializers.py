from django.utils.translation import gettext_lazy as _
from django.apps import apps
from django.db import transaction

from rest_framework import serializers

Listing = apps.get_registered_model('feeder', 'Listing')
Broadcast = apps.get_registered_model('feeder', 'Broadcast')


class BaseBroadcastSerializer(serializers.ModelSerializer):
    class Meta:
        model = Broadcast
        fields = '__all__'


class ListBroadcastSerializer(BaseBroadcastSerializer):
    has_addressed = serializers.BooleanField(read_only=True)
    permalink = serializers.HyperlinkedIdentityField(
        view_name='feeder_api:broadcast-detail',
        lookup_field='uuid'
    )

    class Meta(BaseBroadcastSerializer.Meta):
        fields = ('permalink', 'uuid', 'label',
                  'description', 'reward', 'message', 'has_addressed',)


class RetrieveBroadcastSerializer(BaseBroadcastSerializer):
    has_addressed = serializers.BooleanField(read_only=True)

    class Meta(BaseBroadcastSerializer.Meta):
        fields = '__all__'


class CreateBroadcastSerializer(BaseBroadcastSerializer):
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )

    class Meta(BaseBroadcastSerializer.Meta):
        fields = ('user', 'label', 'description', 'reward', 'message',)

    def to_representation(self, instance):
        serializer = RetrieveBroadcastSerializer(
            instance,
            context=self.context
        )
        return serializer.data

    @transaction.atomic
    def create(self, validated_data):
        label = validated_data.pop('label', None)

        instance, _created = Broadcast.objects \
            .update_or_create(label=label, defaults=validated_data)
        return instance


class UpdateBroadcastSerializer(BaseBroadcastSerializer):
    class Meta(BaseBroadcastSerializer.Meta):
        fields = ('label', 'description', 'reward', 'message',)

    def to_representation(self, instance):
        serializer = RetrieveBroadcastSerializer(
            instance,
            context=self.context
        )
        return serializer.data
