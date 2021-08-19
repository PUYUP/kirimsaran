from django.contrib import admin
from django.apps import apps

Listing = apps.get_registered_model('feeder', 'Listing')
Product = apps.get_registered_model('feeder', 'Product')
Fragment = apps.get_registered_model('feeder', 'Fragment')
Spread = apps.get_registered_model('feeder', 'Spread')
Suggest = apps.get_registered_model('feeder', 'Suggest')
Coupon = apps.get_registered_model('feeder', 'Coupon')
Addressed = apps.get_registered_model('feeder', 'Addressed')


class SpreadExtend(admin.ModelAdmin):
    model = Spread
    readonly_fields = ('identifier',)


admin.site.register(Listing)
admin.site.register(Product)
admin.site.register(Spread, SpreadExtend)
admin.site.register(Fragment)
admin.site.register(Suggest)
admin.site.register(Coupon)
admin.site.register(Addressed)
