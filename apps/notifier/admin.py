from django.contrib import admin
from django.apps import apps

Notification = apps.get_registered_model('notifier', 'Notification')


class NotificationExtend(admin.ModelAdmin):
    model = Notification
    raw_id_fields = ('recipient',)
    list_display = ('recipient', 'actor', 'level', 'target',
                    'unread', 'public')
    list_filter = ('level', 'unread', 'public', 'timestamp',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('actor')


admin.site.register(Notification, NotificationExtend)
