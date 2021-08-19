from django.apps import apps
from django.contrib import admin
from django.contrib.admin.filters import DateFieldListFilter
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import ugettext_lazy as _

from .forms import UserChangeFormExtend, UserCreationFormExtend

User = apps.get_registered_model('person', 'User')
Attribute = apps.get_registered_model('person', 'Attribute')
AttributeValue = apps.get_registered_model('person', 'AttributeValue')
Profile = apps.get_registered_model('person', 'Profile')
SecureCode = apps.get_registered_model('person', 'SecureCode')
Permission = apps.get_registered_model('auth', 'Permission')


class ProfileInline(admin.StackedInline):
    model = Profile


class UserExtend(UserAdmin):
    form = UserChangeFormExtend
    add_form = UserCreationFormExtend
    inlines = [ProfileInline, ]
    readonly_fields = ('hexid',)
    list_display = ('username', 'first_name', 'email', 'msisdn', 'is_staff')
    list_filter = UserAdmin.list_filter + \
        (('date_joined', DateFieldListFilter), 'last_login',)
    fieldsets = (
        (None, {'fields': ('hexid', 'username', 'password', 'email', 'is_email_verified',
                           'msisdn', 'is_msisdn_verified',)}),
        (_("Personal info"), {'fields': ('first_name', 'last_name',)}),
        (_("Permissions"), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups',),
        }),
        (_("Important dates"), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'fields': ('username', 'email', 'is_email_verified',
                       'msisdn', 'is_msisdn_verified',
                       'password1', 'password2', 'groups',)
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        queryset = qs \
            .prefetch_related('profile') \
            .select_related('profile')
        return queryset


class SecureCodeExtend(admin.ModelAdmin):
    model = SecureCode
    list_display = (
        'issuer', 'issuer_type', 'passcode', 'challenge',
        'is_verified', 'is_used', 'is_expired', 'token',
        'user_agent',
    )
    list_display_links = ('issuer',)
    readonly_fields = (
        'passcode', 'token', 'valid_until',
        'valid_until_timestamp',
    )
    list_filter = ('challenge', 'is_verified',)

    def get_readonly_fields(self, request, obj=None):
        # Disallow edit
        if obj:
            return list(set(
                [field.name for field in self.opts.local_fields] +
                [field.name for field in self.opts.local_many_to_many]))
        return super().get_readonly_fields(request, obj)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


admin.site.register(User, UserExtend)
admin.site.register(SecureCode, SecureCodeExtend)
admin.site.register(Attribute)
admin.site.register(AttributeValue)
