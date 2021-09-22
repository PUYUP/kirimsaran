from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _
from django.apps import apps
from django.contrib.contenttypes.models import ContentType

from rest_framework import serializers
from rest_framework.exceptions import NotFound

Fragment = apps.get_registered_model('feeder', 'Fragment')
Reward = apps.get_registered_model('feeder', 'Reward')


class BaseRewardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reward
        fields = '__all__'


class ListRewardSerializer(BaseRewardSerializer):
    permalink = serializers.HyperlinkedIdentityField(
        view_name='feeder_api:reward-detail',
        lookup_field='uuid'
    )

    class Meta(BaseRewardSerializer.Meta):
        fields = ('permalink', 'uuid', 'allocation', 'start_at', 'expiry_at',
                  'amount', 'label', 'description', 'provider', 'term', 'type',
                  'unit_label', 'unit_slug',)


class RetrieveRewardSerializer(BaseRewardSerializer):
    content_object_label = serializers.CharField()
    content_object_uuid = serializers.URLField()

    class Meta(BaseRewardSerializer.Meta):
        fields = '__all__'


class CreateRewardSerializer(BaseRewardSerializer):
    content_type = serializers.CharField(write_only=True)
    object_id = serializers.UUIDField(write_only=True)

    class Meta(BaseRewardSerializer.Meta):
        fields = ('content_type', 'object_id', 'allocation', 'start_at', 'expiry_at',
                  'amount', 'label', 'description', 'provider', 'term', 'type',
                  'unit_label', 'unit_slug',)

    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        ct = data.pop('content_type', None)
        obj_id = data.pop('object_id', None)

        try:
            ct_obj = ContentType.objects.get(app_label='feeder', model=ct)
        except ObjectDoesNotExist:
            raise NotFound(detail={
                'content_object': _("Content object invalid")
            })

        try:
            _obj = ct_obj.get_object_for_this_type(uuid=obj_id)
        except ObjectDoesNotExist:
            raise NotFound()

        data.update({
            'content_type': ct_obj,
            'object_id': _obj.id
        })

        return data

    def to_representation(self, instance):
        serializer = RetrieveRewardSerializer(instance, context=self.context)
        return serializer.data


class UpdateRewardSerializer(BaseRewardSerializer):
    class Meta(BaseRewardSerializer.Meta):
        fields = ('allocation', 'start_at', 'expiry_at', 'amount', 'label',
                  'description', 'provider', 'term', 'type',
                  'unit_label', 'unit_slug',)

    def to_representation(self, instance):
        serializer = RetrieveRewardSerializer(instance, context=self.context)
        return serializer.data
