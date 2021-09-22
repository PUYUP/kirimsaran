from django.apps import apps
from rest_framework import serializers

Interaction = apps.get_registered_model('feeder', 'Interaction')
Suggest = apps.get_registered_model('feeder', 'Suggest')


class BaseInteractionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interaction
        fields = '__all__'


class ListInteractionSerializer(BaseInteractionSerializer):
    is_product_owner = serializers.BooleanField(read_only=True)

    class Meta(BaseInteractionSerializer.Meta):
        fields = ('description', 'create_at', 'is_product_owner',)


class RetrieveInteractionSerializer(ListInteractionSerializer):
    class Meta(ListInteractionSerializer.Meta):
        fields = ('suggest', 'description', 'create_at', 'is_product_owner',)


class CreateInteractionSerializer(BaseInteractionSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    suggest = serializers.SlugRelatedField(
        slug_field='uuid',
        queryset=Suggest.objects.all()
    )

    class Meta(BaseInteractionSerializer.Meta):
        fields = ('user', 'suggest', 'description',)
        extra_kwargs = {
            'description': {'required': True}
        }

    def to_representation(self, instance):
        data = {
            'is_product_owner': instance.suggest.spread.content_object.product.listing.user.id == instance.user.id
        }

        serializer = RetrieveInteractionSerializer(
            instance,
            context=self.context
        )

        data.update(serializer.data)
        return data


class UpdateInteractionSerializer(BaseInteractionSerializer):
    class Meta(BaseInteractionSerializer.Meta):
        fields = ('description',)

    def to_representation(self, instance):
        serializer = RetrieveInteractionSerializer(
            instance,
            context=self.context
        )
        return serializer.data
