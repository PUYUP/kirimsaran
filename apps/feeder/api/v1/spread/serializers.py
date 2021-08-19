from django.utils.translation import gettext_lazy as _
from django.apps import apps

from rest_framework import serializers

Fragment = apps.get_registered_model('feeder', 'Fragment')
Spread = apps.get_registered_model('feeder', 'Spread')


class BaseSpreadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Spread
        fields = '__all__'


class ListSpreadSerializer(BaseSpreadSerializer):
    shorturl = serializers.URLField()
    permalink = serializers.HyperlinkedIdentityField(
        view_name='feeder_api:spread-detail',
        lookup_field='uuid'
    )

    class Meta(BaseSpreadSerializer.Meta):
        fields = ('permalink', 'uuid', 'allowed_used',
                  'valid_until', 'identifier', 'qrcode',
                  'shorturl',)


class RetrieveSpreadSerializer(BaseSpreadSerializer):
    shorturl = serializers.URLField()
    fragment = serializers.UUIDField(source='fragment.uuid')
    fragment_label = serializers.CharField(source='fragment.label')

    class Meta(BaseSpreadSerializer.Meta):
        fields = '__all__'


class CreateSpreadSerializer(BaseSpreadSerializer):
    fragment = serializers.SlugRelatedField(
        slug_field='uuid',
        queryset=Fragment.objects.all()
    )

    class Meta(BaseSpreadSerializer.Meta):
        fields = ('fragment', 'allowed_used', 'valid_until',)

    def to_representation(self, instance):
        serializer = RetrieveSpreadSerializer(instance, context=self.context)
        return serializer.data


class UpdateSpreadSerializer(BaseSpreadSerializer):
    class Meta(BaseSpreadSerializer.Meta):
        fields = ('allowed_used', 'valid_until',)

    def to_representation(self, instance):
        serializer = RetrieveSpreadSerializer(instance, context=self.context)
        return serializer.data
