import calendar
import time

from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django.apps import apps

from rest_framework import serializers

Broadcast = apps.get_registered_model('feeder', 'Broadcast')
Suggest = apps.get_registered_model('feeder', 'Suggest')
Target = apps.get_registered_model('feeder', 'Target')


class BaseTargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Target
        fields = '__all__'


class ListTargetSerializer(BaseTargetSerializer):
    permalink = serializers.HyperlinkedIdentityField(
        view_name='feeder_api:target-detail',
        lookup_field='uuid'
    )

    class Meta(BaseTargetSerializer.Meta):
        fields = ('permalink', 'uuid',)


class RetrieveTargetSerializer(ListTargetSerializer):
    broadcast = serializers.UUIDField(source='broadcast.uuid')

    class Meta(ListTargetSerializer.Meta):
        fields = '__all__'


class CreateTargetListSerializer(serializers.ListSerializer):
    @transaction.atomic
    def create(self, validated_data):
        # grouping by timestamp?
        # no idea for now how to get latest target created
        # for insert to order
        gmt = time.gmtime()
        ts = calendar.timegm(gmt)

        # create target
        bulk_target = [Target(moment=ts, **item) for item in validated_data]
        return Target.objects.bulk_create(bulk_target, ignore_conflicts=False)


class CreateTargetSerializer(BaseTargetSerializer):
    broadcast = serializers.SlugRelatedField(
        slug_field='uuid',
        queryset=Broadcast.objects.all()
    )

    suggest = serializers.SlugRelatedField(
        slug_field='uuid',
        queryset=Suggest.objects.all()
    )

    class Meta(BaseTargetSerializer.Meta):
        fields = ('broadcast', 'suggest', 'method',)
        list_serializer_class = CreateTargetListSerializer

    def to_representation(self, instance):
        serializer = RetrieveTargetSerializer(
            instance,
            context=self.context
        )
        return serializer.data
