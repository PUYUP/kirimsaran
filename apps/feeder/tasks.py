import logging
from django.utils.translation import ugettext_lazy as _

# Celery config
from celery import shared_task
from .utils import digihub_send_sms


@shared_task
def send_sms(data):
    logging.info(_("Send sms run"))

    msisdn = data.get('msisdn', None)
    message = data.get('message', None)

    if msisdn and message:
        _response = digihub_send_sms(msisdn, message)
    else:
        logging.warning(
            _("Msisdn and Message empty")
        )
