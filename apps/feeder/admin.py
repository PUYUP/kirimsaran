from django.contrib import admin
from django.apps import apps
from django.contrib.auth import get_user_model

Listing = apps.get_registered_model('feeder', 'Listing')
Product = apps.get_registered_model('feeder', 'Product')
Fragment = apps.get_registered_model('feeder', 'Fragment')
Spread = apps.get_registered_model('feeder', 'Spread')
Suggest = apps.get_registered_model('feeder', 'Suggest')
Canal = apps.get_registered_model('feeder', 'Canal')
Coupon = apps.get_registered_model('feeder', 'Coupon')
Redeem = apps.get_registered_model('feeder', 'Redeem')
Taken = apps.get_registered_model('feeder', 'Taken')
Broadcast = apps.get_registered_model('feeder', 'Broadcast')
Target = apps.get_registered_model('feeder', 'Target')
Reward = apps.get_registered_model('feeder', 'Reward')
Interaction = apps.get_registered_model('feeder', 'Interaction')
Order = apps.get_registered_model('feeder', 'Order')
OrderMeta = apps.get_registered_model('feeder', 'OrderMeta')
OrderItem = apps.get_registered_model('feeder', 'OrderItem')


"""
SUGGEST
"""


class CanalInline(admin.StackedInline):
    model = Canal


class SuggestExtend(admin.ModelAdmin):
    model = Suggest
    inlines = (CanalInline,)


class SpreadExtend(admin.ModelAdmin):
    model = Spread


class TakenExtend(admin.ModelAdmin):
    model = Taken

    def get_queryset(self, request):
        qs = super().get_queryset(request) \
            .prefetch_related('actor', 'redeem') \
            .select_related('actor', 'redeem')

        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'redeem':
            kwargs['queryset'] = Redeem.objects \
                .prefetch_related('user', 'coupon') \
                .select_related('user', 'coupon')

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


"""
CART
"""


class OrderMetaInline(admin.StackedInline):
    model = OrderMeta


class OrderExtend(admin.ModelAdmin):
    model = Order
    inlines = (OrderMetaInline,)


admin.site.register(Listing)
admin.site.register(Product)
admin.site.register(Spread, SpreadExtend)
admin.site.register(Fragment)
admin.site.register(Suggest, SuggestExtend)
admin.site.register(Canal)
admin.site.register(Coupon)
admin.site.register(Redeem)
admin.site.register(Taken, TakenExtend)
admin.site.register(Broadcast)
admin.site.register(Target)
admin.site.register(Reward)
admin.site.register(Interaction)
admin.site.register(Order, OrderExtend)
admin.site.register(OrderItem)
