import uuid
import pyotp

from django.db import models, transaction
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone

from ..utils import get_issuer_type
from ..validators import validate_issuer

UserModel = get_user_model()


class SecureCodeQuerySet(models.query.QuerySet):
    def queryset(self, *args, **kwargs):
        qfields = [Q(**{k: kwargs.get(k, None)}) for k in kwargs.keys()]
        qset = self.select_for_update() \
            .filter(*qfields,  Q(valid_until__gt=timezone.now()), Q(is_used=False))

        return qset

    def verified(self, *args, **kwargs):
        return self.queryset(*args, **kwargs).filter(is_verified=True)

    def unverified(self, *args, **kwargs):
        return self.queryset(*args, **kwargs).filter(is_verified=False)

    def generate(self, *args, **kwargs):
        """Generate if valid_until greather than now"""
        data = kwargs.get('data', {})
        instance, created = self.filter(valid_until__gt=timezone.now()) \
            .update_or_create(**data, defaults=data)

        return instance, created


class AbstractSecureCode(models.Model):
    class Challenges(models.TextChoices):
        VALIDATE_EMAIL = 'validate_email', _("Validate Email")
        VALIDATE_MSISDN = 'validate_msisdn', _("Validate MSISDN")
        CHANGE_EMAIL = 'change_email', _("Change Email")
        CHANGE_MSISDN = 'change_msisdn', _("Change MSISDN")
        PASSWORD_RECOVERY = 'password_recovery', _("Password Recovery")

    class IssuerTypes(models.TextChoices):
        EMAIL = 'email', _("Email")
        MSISDN = 'msisdn', _("Msisdn")

    """
    Send SecureCode Code with;
        :email
        :msisdn (SMS or Voice Call)

    :valid_until; SecureCode Code validity max date (default 2 hour)
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    create_at = models.DateTimeField(auto_now_add=True, db_index=True)
    update_at = models.DateTimeField(auto_now=True)

    issuer = models.CharField(
        max_length=255,
        help_text=_("Email or Msisdn"),
        validators=[validate_issuer]
    )
    issuer_type = models.CharField(
        max_length=15,
        choices=IssuerTypes.choices,
        default=IssuerTypes.EMAIL,
        editable=False
    )
    token = models.CharField(max_length=64)
    passcode = models.CharField(max_length=25)
    challenge = models.SlugField(
        choices=Challenges.choices,
        max_length=128,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z_][0-9a-zA-Z_]*$',
                message=_(
                    "Code can only contain the letters a-z, A-Z, digits, "
                    "and underscores, and can't start with a digit."
                )
            )
        ]
    )
    valid_until = models.DateTimeField(blank=True, null=True, editable=False)
    valid_until_timestamp = models.IntegerField(blank=True, null=True)
    user_agent = models.TextField(null=True, blank=True)

    is_verified = models.BooleanField(default=False)
    is_used = models.BooleanField(default=False)

    objects = SecureCodeQuerySet.as_manager()

    class Meta:
        abstract = True
        app_label = 'person'
        verbose_name = _("Secure Code")
        verbose_name_plural = _("Secure Codes")

    def __str__(self):
        return self.passcode

    @property
    def is_expired(self) -> bool:
        return self.valid_until <= timezone.now()

    def clean(self) -> None:
        if not self.pk:
            # Check user exists if challenge is password_recovery
            users = UserModel.objects \
                .filter(Q(msisdn=self.issuer) | Q(email=self.issuer))

            is_validate_email = self.challenge == self.Challenges.VALIDATE_EMAIL
            is_validate_msisdn = self.challenge == self.Challenges.VALIDATE_MSISDN
            is_password_recovery = self.challenge == self.Challenges.PASSWORD_RECOVERY

            if is_password_recovery and not users.exists():
                raise ValidationError({self.challenge: _("User not found")})

            # Check email or msisdn has used
            if is_validate_email or is_validate_msisdn:
                q_verified_field = Q(
                    **{'is_%s_verified' % self.issuer_type: True}
                )

                if users.filter(q_verified_field).exists():
                    raise ValidationError(_("Email or Msisdn has used"))
        return super().clean()

    def validate_otp(self, *args, **kwargs):
        otp = pyotp.TOTP(self.token)
        passed = otp.verify(
            self.passcode,
            for_time=self.valid_until_timestamp
        )

        if not passed:
            raise ValidationError(_("Invalid"))

    def mark_verified(self):
        self.is_verified = True
        self.save(update_fields=['is_verified'])

    def mark_used(self):
        self.is_used = True
        self.save(update_fields=['is_used'])

    def generator(self):
        # Set max validity date
        # Default 2 hours since created
        self.valid_until = timezone.now() + timezone.timedelta(hours=2)
        self.valid_until_timestamp = self.valid_until \
            .replace(microsecond=0) \
            .timestamp()

        # generate token
        token = pyotp.random_base32()

        # generate passcode from token
        totp = pyotp.TOTP(token)
        passcode = totp.at(self.valid_until_timestamp)

        # prepare to save
        self.passcode = passcode
        self.token = token

    @transaction.atomic
    def save(self, *args, **kwargs):
        if not self.pk or not self.is_verified and not self.is_used:
            self.generator()

        if self.pk and self.is_verified:
            self.validate_otp()

        self.issuer_type = get_issuer_type(self.issuer)  # email or msisdn
        super().save(*args, **kwargs)
