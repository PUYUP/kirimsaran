from django.core.mail import message
import requests
import hashlib
import calendar
import time

from django.utils.translation import gettext_lazy as _
from django.apps import apps
from django.conf import settings

from random import choice
from string import ascii_letters, digits

from .conf import settings

# Try to get the value from the settings module
SIZE = getattr(settings, 'FEEDER_MAXIMUM_PRODUCT_CODE_LENGTH', 5)
AVAIABLE_CHARS = ascii_letters + digits


def is_model_registered(app_label, model_name):
    """
    Checks whether a given model is registered. This is used to only
    register Oscar models if they aren't overridden by a forked app.
    """
    try:
        apps.get_registered_model(app_label, model_name)
    except LookupError:
        return False
    else:
        return True


def create_random_identifier(chars=AVAIABLE_CHARS):
    """
    Creates a random string with the predetermined size
    """
    return "".join(
        [choice(chars) for _ in range(SIZE)]
    )


def save_random_identifier(model_instance):
    random_identifier = create_random_identifier()
    model_class = model_instance.__class__

    if model_class.objects.filter(identifier=random_identifier).exists():
        # If exist run the function again
        return save_random_identifier(model_instance)

    return random_identifier


def digihub_send_sms(msisdn, message):
    # add 62
    if msisdn[0] == '0':
        msisdn = msisdn[1:]

    msisdn = '{}{}'.format('62', msisdn)

    api_key = 'mrmnthfehaujzndupfd59e3z'
    secret = '11gP2'
    ts = calendar.timegm(time.gmtime())
    signature = hashlib.sha256('{}{}{}'.format(
        api_key, secret, ts).encode('utf-8')
    ).hexdigest()

    url = 'https://api.digitalcore.telkomsel.com/v1/send-sms'

    payload = {
        "transaction": {
            "transaction_id": "C002190726165745657448250",
            "callback_domain": "kirimsaran.com"
        },
        "sms": {
            "sender_id": "DIGIHACK",
            "recipient": msisdn,
            "sms_text": message
        }
    }

    headers = {
        "api_key": api_key,
        "x-signature": signature,
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)
    return response
