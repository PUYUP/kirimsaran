import uuid
from decimal import Decimal

from django.core.validators import RegexValidator
from django.db import models, transaction
from django.contrib.auth.models import AbstractUser, UserManager
from django.db.models.expressions import Exists, OuterRef, Subquery
from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify
from django.utils import timezone
from django.contrib.auth.models import Group

from ..conf import settings
from ..validators import validate_msisdn


class UserManagerExtend(UserManager):
    @transaction.atomic
    def create_user(self, username, password, **extra_fields):
        """
        If verification fields settings has defined value
        we check again incoming data has fields verification to
        """
        fields = settings.PERSON_VERIFICATION_FIELDS
        if len(fields) > 0:
            has_verification_field = any(
                [field in fields for field in extra_fields.keys()]
            )

            if not has_verification_field:
                raise ValueError(
                    _("The given {} must be set".format(' or '.join(fields)))
                )

        return super().create_user(username, password=password, **extra_fields)


# Extend User
# https://docs.djangoproject.com/en/3.1/topics/auth/customizing/#substituting-a-custom-user-model
class User(AbstractUser):
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True
    )
    hexid = models.CharField(max_length=255, editable=False, db_index=True)
    msisdn = models.CharField(
        db_index=True,
        blank=True,
        max_length=14,
        verbose_name=_("Phone number"),
        error_messages={
            'unique': _("A user with that msisdn already exists."),
        },
        validators=[validate_msisdn]
    )
    email = models.EmailField(
        _('email address'),
        db_index=True,
        blank=True,
        error_messages={
            'unique': _("A user with that email already exists."),
        },
    )
    is_email_verified = models.BooleanField(default=False, null=True)
    is_msisdn_verified = models.BooleanField(default=False, null=True)

    objects = UserManagerExtend()

    class Meta(AbstractUser.Meta):
        app_label = 'person'

    def clean(self, *args, **kwargs) -> None:
        return super().clean()

    @property
    def name(self):
        full_name = '{}{}'.format(self.first_name, ' ' + self.last_name)
        return full_name if self.first_name else self.username

    @property
    def roles_by_group(self):
        group_annotate = self.groups.filter(name=OuterRef('name'))
        all_groups = self.groups.model.objects.all()
        user_groups = self.groups.all()

        # generate slug for group
        # ie is_group_name
        groups_role = {
            'is_{}'.format(slugify(v.name)): Exists(Subquery(group_annotate.values('name')[:1]))
            for i, v in enumerate(user_groups)
        }

        groups = all_groups.annotate(**groups_role)
        ret = dict()

        for group in groups:
            slug = 'is_%s' % slugify(group.name)
            ret.update({slug: getattr(group, slug, False)})
        return ret

    def mark_email_verified(self):
        self.is_email_verified = True
        self.save(update_fields=['is_email_verified'])

    def mark_msisdn_verified(self):
        self.is_msisdn_verified = True
        self.save(update_fields=['is_msisdn_verified'])

    def unique_hexid(self):
        while True:
            object_id = id(timezone.now().timestamp())
            hexid = hex(object_id)

            if not self._meta.model.objects.filter(hexid=hexid).exists():
                return hexid

    def save(self, *args, **kwargs) -> None:
        # generate hex from uuid
        if not self.id:
            self.hexid = self.unique_hexid()

        return super().save(*args, **kwargs)


class AbstractProfile(models.Model):
    class GenderChoice(models.TextChoices):
        UNDEFINED = 'unknown', _("Unknown")
        MALE = 'male', _("Male")
        FEMALE = 'female', _("Female")

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_at = models.DateTimeField(auto_now_add=True, db_index=True)
    update_at = models.DateTimeField(auto_now=True)

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )

    headline = models.CharField(max_length=255, null=True, blank=True)
    gender = models.CharField(
        choices=GenderChoice.choices,
        blank=True,
        null=True,
        default=GenderChoice.UNDEFINED,
        max_length=255,
        validators=[
            RegexValidator(
                regex='^[a-zA-Z_]*$',
                message=_("Can only contain the letters a-z and underscores."),
                code='invalid_identifier'
            ),
        ]
    )
    birthdate = models.DateField(blank=True, null=True)
    about = models.TextField(blank=True, null=True)
    picture = models.ImageField(
        upload_to='images/person',
        max_length=500,
        null=True,
        blank=True
    )
    address = models.TextField(blank=True, null=True)
    latitude = models.FloatField(default=Decimal(0.0), db_index=True)
    longitude = models.FloatField(default=Decimal(0.0), db_index=True)

    class Meta:
        abstract = True
        app_label = 'person'
        ordering = ['-user__date_joined']
        verbose_name = _("Profile")
        verbose_name_plural = _("Profiles")

    def __str__(self):
        return self.name

    @property
    def name(self):
        full_name = '{}{}'.format(
            self.user.first_name, ' ' + self.user.last_name
        )
        return full_name if self.user.first_name else self.user.username


# Add custom field to group
Group.add_to_class('is_default', models.BooleanField(default=False))
