from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django.apps import apps

from rest_framework import serializers

Redeem = apps.get_registered_model('feeder', 'Redeem')
Taken = apps.get_registered_model('feeder', 'Taken')


class BaseTakenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Taken
        fields = '__all__'


class ListTakenSerializer(BaseTakenSerializer):
    redeem_uuid = serializers.UUIDField(source='redeem.uuid')

    permalink = serializers.HyperlinkedIdentityField(
        view_name='feeder_api:taken-detail',
        lookup_field='uuid'
    )

    class Meta(BaseTakenSerializer.Meta):
        fields = ('permalink', 'uuid', 'redeem', 'redeem_uuid', 'note',)


class RetrieveTakenSerializer(ListTakenSerializer):
    class Meta(ListTakenSerializer.Meta):
        fields = '__all__'


class CreateTakenSerializer(BaseTakenSerializer):
    actor = serializers.HiddenField(default=serializers.CurrentUserDefault())
    redeem = serializers.SlugRelatedField(
        slug_field='uuid',
        queryset=Redeem.objects.all()
    )

    class Meta(BaseTakenSerializer.Meta):
        fields = ('actor', 'redeem', 'note',)

    def to_representation(self, instance):
        ret = {}
        serializer = RetrieveTakenSerializer(instance, context=self.context)
        ret.update(serializer.data)

        return ret

    @transaction.atomic
    def create(self, validated_data):
        instance, _created = self.Meta.model.objects \
            .get_or_create(**validated_data)

        if _created:
            instance.mark_coupon_used()

        return instance
