from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.core.exceptions import ObjectDoesNotExist
from django.db import models, transaction
from django.conf import settings
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.utils.text import Truncator
from django.apps import apps
from django.db.models import Case, When, Value

from .abstract import AbstractCommonField
from ..utils import save_random_identifier


class AbstractSuggest(AbstractCommonField):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='suggests',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    spread = models.ForeignKey(
        'feeder.Spread',
        related_name='suggests',
        on_delete=models.CASCADE
    )

    rating = models.IntegerField(
        validators=[
            MaxValueValidator(5),
            MinValueValidator(1)
        ]
    )
    description = models.TextField()

    class Meta:
        abstract = True
        app_label = 'feeder'
        ordering = ['-create_at']

    def __str__(self) -> str:
        text = '{} {}'.format(self.rating, self.description)
        return Truncator(text).words(10)

    @transaction.atomic
    def create_coupon(self):
        Fragment = apps.get_registered_model('feeder', 'Fragment')
        Coupon = apps.get_registered_model('feeder', 'Coupon')

        cto = self.spread.content_object

        # how many for spread related to suggest?
        current_suggest_count = self.spread.suggests.count()

        # fragment
        if isinstance(cto, Fragment):
            if cto.rewards.exists():
                coupon_bulk = []

                # filter reward by allocation, start_at and expiry_at
                active_rewards = cto.rewards \
                    .prefetch_related('content_type') \
                    .select_related('content_type') \
                    .filter(
                        allocation__gt=Case(
                            When(
                                allocation__gt=Value(0),
                                then=current_suggest_count
                            )
                        ),
                        start_at__lte=timezone.now(),
                        expiry_at__gte=timezone.now()
                    )

                # check has user then user must have validated msisdn
                is_active = False
                user = self.user
                if user and user.is_msisdn_verified:
                    is_active = True

                # create coupons
                for reward in active_rewards:
                    c = Coupon(
                        suggest=self,
                        reward=reward,
                        is_active=is_active
                    )
                    coupon_bulk.append(c)

                if len(coupon_bulk) > 0:
                    try:
                        Coupon.objects.bulk_create(
                            coupon_bulk,
                            ignore_conflicts=False
                        )
                    except Exception as e:
                        print(e)

    @transaction.atomic
    def redeem_coupon(self):
        Redeem = apps.get_registered_model('feeder', 'Redeem')

        if self.coupons.exists():
            bulk_redeem = []
            coupons = self.coupons \
                .prefetch_related('redeem', 'reward', 'suggest') \
                .select_related('redeem', 'reward', 'suggest') \
                .filter(redeem__isnull=True)

            for c in coupons:
                o = Redeem(user=self.user, coupon=c)
                bulk_redeem.append(o)

            if len(bulk_redeem) > 0:
                try:
                    Redeem.objects.bulk_create(
                        bulk_redeem,
                        ignore_conflicts=False
                    )
                except Exception as e:
                    print(e)

    @transaction.atomic
    def insert_canal(self, canal_dict):
        Canal = apps.get_registered_model('feeder', 'Canal')
        bulk_canal = []
        phones = []

        for canal in canal_dict:
            o = Canal(suggest=self, **canal)
            bulk_canal.append(o)
            phones.append(canal.get('value'))

        if len(bulk_canal) > 0:
            try:
                Canal.objects.bulk_create(
                    bulk_canal,
                    ignore_conflicts=False
                )
            except Exception as e:
                print(e)

        # if has reward we need phone validation
        # why phone? because more individual than email
        """
        has_reward = self.has_reward
        if has_reward and len(phones) > 0:
            SecureCode = apps.get_registered_model('person', 'SecureCode')
            uniq_phone = list(set(phones))[0]

            data = {
                'is_used': False,
                'is_verified': False,
                'issuer': uniq_phone,
                'challenge': SecureCode.Challenges.VALIDATE_MSISDN
            }

            # If `valid_until` greater than time now we update SecureCode Code
            SecureCode.objects.generate(data={**data})
        """

    @property
    def has_reward(self):
        Fragment = apps.get_registered_model('feeder', 'Fragment')
        cto = self.spread.content_object

        # fragment
        if isinstance(cto, Fragment):
            return cto.rewards.exists()
        return False


class AbstractCanal(AbstractCommonField):
    class Method(models.TextChoices):
        PHONE = 'phone', _("Phone")
        WHATSAPP = 'whatsapp', _("WhatsApp")
        TELEGRAM = 'telegram', _("Telegram")
        EMAIL = 'email', _("Email")

    suggest = models.ForeignKey(
        'feeder.Suggest',
        related_name='canals',
        on_delete=models.CASCADE
    )

    method = models.CharField(choices=Method.choices, max_length=15)
    value = models.CharField(max_length=255)
    extra = models.JSONField(null=True, blank=True)

    class Meta:
        abstract = True
        app_label = 'feeder'
        ordering = ['-create_at']

    def __str__(self) -> str:
        return self.value


class CouponManager(models.Manager):
    @transaction.atomic
    def bulk_create(self, objs, **kwargs):
        for obj in objs:
            identifier = save_random_identifier(obj)
            setattr(obj, 'identifier', identifier)
        return super().bulk_create(objs, **kwargs)


class AbstractCoupon(AbstractCommonField):
    suggest = models.ForeignKey(
        'feeder.Suggest',
        related_name='coupons',
        on_delete=models.CASCADE
    )
    reward = models.ForeignKey(
        'feeder.Reward',
        related_name='coupons',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    identifier = models.CharField(
        max_length=7,
        editable=False,
        validators=[
            RegexValidator(
                regex='^[a-zA-Z0-9]*$',
                message=_("Can only contain the letters a-Z and 0-9."),
                code='invalid_identifier'
            ),
        ]
    )

    # user must validate their :canals with otp code then change this as True
    is_active = models.BooleanField(default=False)
    is_used = models.BooleanField(default=False)

    objects = CouponManager()

    class Meta:
        abstract = True
        app_label = 'feeder'
        ordering = ['-create_at']

    def __str__(self) -> str:
        return self.identifier

    @transaction.atomic
    def save(self, *args, **kwargs):
        # Generate random identifier
        if not self.pk and not self.identifier:
            # We pass the model instance that is being saved
            self.identifier = save_random_identifier(self)
        return super().save(*args, **kwargs)


class AbstractRedeem(AbstractCommonField):
    coupon = models.OneToOneField(
        'feeder.Coupon',
        related_name='redeem',
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='redeems',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    note = models.TextField(null=True, blank=True)

    class Meta:
        abstract = True
        app_label = 'feeder'
        ordering = ['-create_at']

    def __str__(self) -> str:
        return self.coupon.identifier


class AbstractTaken(AbstractCommonField):
    redeem = models.ForeignKey(
        'feeder.Redeem',
        related_name='takens',
        on_delete=models.CASCADE
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='takens',
        on_delete=models.CASCADE
    )

    note = models.TextField(null=True, blank=True)

    class Meta:
        abstract = True
        app_label = 'feeder'
        ordering = ['-create_at']

    def __str__(self) -> str:
        return self.redeem.coupon.identifier

    @transaction.atomic
    def mark_coupon_used(self):
        coupon = self.redeem.coupon
        coupon.is_used = True
        coupon.save()
