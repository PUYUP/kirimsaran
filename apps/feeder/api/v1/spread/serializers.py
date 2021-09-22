from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _
from django.apps import apps
from django.contrib.contenttypes.models import ContentType

from rest_framework import serializers
from rest_framework.exceptions import NotFound

Fragment = apps.get_registered_model('feeder', 'Fragment')
Spread = apps.get_registered_model('feeder', 'Spread')


class BaseSpreadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Spread
        fields = '__all__'


class ListSpreadSerializer(BaseSpreadSerializer):
    permalink = serializers.HyperlinkedIdentityField(
        view_name='feeder_api:spread-detail',
        lookup_field='uuid'
    )

    class Meta(BaseSpreadSerializer.Meta):
        fields = ('permalink', 'uuid', 'allocation', 'expiry_at',
                  'identifier', 'qrcode', 'url', 'introduction',)


class RetrieveSpreadSerializer(BaseSpreadSerializer):
    content_object_label = serializers.CharField()
    content_object_uuid = serializers.URLField()

    class Meta(BaseSpreadSerializer.Meta):
        fields = '__all__'


class RetrievePublicSpreadSerializer(BaseSpreadSerializer):
    content_object_label = serializers.CharField()
    content_object_uuid = serializers.URLField()
    rewards = serializers.SerializerMethodField()
    product = serializers.SerializerMethodField()

    class Meta(BaseSpreadSerializer.Meta):
        fields = (
            'content_object_label',
            'content_object_uuid',
            'identifier',
            'rewards',
            'product',
            'introduction'
        )

    def get_rewards(self, instance):
        try:
            fragment = instance.fragment.first()
        except ObjectDoesNotExist:
            return None

        rewards = fragment.rewards.all()
        ret = []

        for data in rewards:
            ret.append({
                'provider': data.provider,
                'label': data.label,
                'description': data.description,
                'term': data.term,
                'amount': data.amount,
                'unit_label': data.unit_label,
                'unit_slug': data.unit_slug,
            })

        return ret

    def get_product(self, instance):
        return instance.product('label')


class CreateSpreadSerializer(BaseSpreadSerializer):
    content_type = serializers.CharField(write_only=True)
    object_id = serializers.UUIDField(write_only=True)

    class Meta(BaseSpreadSerializer.Meta):
        fields = ('content_type', 'object_id', 'allocation',
                  'expiry_at', 'introduction',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.co_obj = None
        self.ct_obj = None

    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        ct = data.pop('content_type', None)
        obj_id = data.pop('object_id', None)

        try:
            self.ct_obj = ContentType.objects.get(app_label='feeder', model=ct)
        except ObjectDoesNotExist:
            raise NotFound(detail={
                'content_object': _("Content object invalid")
            })

        try:
            self.co_obj = self.ct_obj.get_object_for_this_type(uuid=obj_id)
        except ObjectDoesNotExist:
            raise NotFound()

        data.update({
            'content_type': self.ct_obj,
            'object_id': self.co_obj.id
        })

        return data

    def validate(self, attrs):
        data = super().validate(attrs)

        if isinstance(self.co_obj, Fragment):
            expiry_at = self.co_obj.expiry_at
            if data.get('expiry_at') > expiry_at:
                raise serializers.ValidationError({
                    'expiry_at': _("Expiry larger than fragment expiry at %s" % expiry_at)
                })

        return data

    def to_representation(self, instance):
        serializer = RetrieveSpreadSerializer(instance, context=self.context)
        return serializer.data


class UpdateSpreadSerializer(BaseSpreadSerializer):
    class Meta(BaseSpreadSerializer.Meta):
        fields = ('allocation', 'expiry_at', 'introduction',)

    def to_representation(self, instance):
        serializer = RetrieveSpreadSerializer(instance, context=self.context)
        return serializer.data

    def validate_expiry_at(self, value):
        co_obj = self.instance.content_object
        if isinstance(co_obj, Fragment):
            expiry_at = co_obj.expiry_at
            if value > expiry_at:
                raise serializers.ValidationError(
                    _("Expiry larger than fragment expiry at %s" % expiry_at)
                )

        return value
