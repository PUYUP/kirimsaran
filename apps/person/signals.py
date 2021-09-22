from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction, IntegrityError
from django.db.models import Q
from django.contrib.auth.models import Group
from django.utils import timezone
from django.conf import settings

from .tasks import send_securecode_email, send_securecode_msisdn
from .utils import get_users

Profile = apps.get_model('person', 'Profile')


@transaction.atomic
def user_save_handler(sender, instance, created, **kwargs):
    if created:
        # set default group
        try:
            group = Group.objects.get(is_default=True)
            group.user_set.add(instance)
        except ObjectDoesNotExist:
            pass

    # create Profile if not exist
    if not hasattr(instance, 'profile'):
        try:
            Profile.objects.create(user=instance)
        except IntegrityError:
            pass


@transaction.atomic
def group_save_handler(sender, instance, created, **kwargs):
    is_default = getattr(instance, 'is_default')
    if is_default:
        groups = Group.objects.exclude(id=instance.id)
        if groups.exists():
            groups.update(is_default=False)


@transaction.atomic
def securecode_save_handler(sender, instance, created, **kwargs):
    # run only on resend and created
    if instance.is_used == False and instance.is_verified == False:
        data = {'passcode': getattr(instance, 'passcode', None)}
        issuer = instance.issuer
        issuer_type = instance.issuer_type
        challenges = instance._meta.model.Challenges

        if issuer_type == 'email':
            # Send via email
            data.update({'email': issuer})

            if instance.challenge == challenges.PASSWORD_RECOVERY:
                for user in get_users(instance.issuer):
                    # send to multiple users
                    if settings.DEBUG:
                        send_securecode_email(data)  # without celery
                    else:
                        send_securecode_email.delay(data)  # with celery
            else:
                # send to single user
                if settings.DEBUG:
                    send_securecode_email(data)  # without celery
                else:
                    send_securecode_email.delay(data)  # with celery
        elif issuer_type == 'msisdn':
            # Send via SMS
            data.update({'msisdn': issuer})

            if instance.challenge == challenges.PASSWORD_RECOVERY:
                for user in get_users(instance.issuer):
                    # send to multiple users
                    if settings.DEBUG:
                        send_securecode_msisdn(data)  # without celery
                    else:
                        send_securecode_msisdn.delay(data)  # with celery
            else:
                # send to single user
                if settings.DEBUG:
                    send_securecode_msisdn(data)  # without celery
                else:
                    send_securecode_msisdn.delay(data)  # with celery

        # mark oldest SecureCode as expired
        cls = instance.__class__
        oldest = cls.objects \
            .filter(
                Q(challenge=instance.challenge),
                Q(issuer=instance.issuer),
                Q(is_used=False), Q(valid_until__gt=timezone.now())
            ).exclude(passcode=instance.passcode)

        if oldest.exists():
            oldest.update(valid_until=timezone.now())
