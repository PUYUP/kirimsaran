from django.utils.translation import gettext_lazy as _
from django.apps import apps

from rest_framework import serializers

Spread = apps.get_registered_model('feeder', 'Spread')
Suggest = apps.get_registered_model('feeder', 'Suggest')


class BaseSuggestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Suggest
        fields = '__all__'


class ListSuggestSerializer(BaseSuggestSerializer):
    permalink = serializers.HyperlinkedIdentityField(
        view_name='feeder_api:suggest-detail',
        lookup_field='uuid'
    )

    msisdn = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    product_label = serializers.CharField(source='fragment.product.label')

    class Meta(BaseSuggestSerializer.Meta):
        fields = ('permalink', 'uuid', 'rating',
                  'description', 'msisdn', 'email',
                  'product_label', 'extra',)

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


class RetrieveSuggestSerializer(ListSuggestSerializer):
    spread = serializers.UUIDField(source='spread.uuid')
    spread_identifier = serializers.CharField(source='spread.identifier')

    class Meta(ListSuggestSerializer.Meta):
        fields = '__all__'


class CreateSuggestSerializer(BaseSuggestSerializer):
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )

    spread = serializers.SlugRelatedField(
        slug_field='identifier',
        queryset=Spread.objects.all()
    )

    class Meta(BaseSuggestSerializer.Meta):
        fields = ('user', 'spread', 'rating',
                  'description', 'msisdn', 'email',)

    def to_representation(self, instance):
        request = self.context.get('request')

        # show coupon for submitter
        ret = {}
        if request.user.id != instance.fragment.listing.user.id:
            ret.update({'coupon': instance.coupons.identifier})

        serializer = RetrieveSuggestSerializer(instance, context=self.context)
        ret.update(serializer.data)

        return ret


class UpdateSuggestSerializer(BaseSuggestSerializer):
    class Meta(BaseSuggestSerializer.Meta):
        fields = ('rating', 'description', 'msisdn', 'email',)

    def to_representation(self, instance):
        serializer = RetrieveSuggestSerializer(instance, context=self.context)
        return serializer.data
