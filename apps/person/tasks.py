import logging
import smtplib

from django.utils.translation import ugettext_lazy as _
from django.core.mail import BadHeaderError, EmailMultiAlternatives

# Celery config
from celery import shared_task

APP_NAME = 'CLI Exec'


@shared_task
def send_securecode_email(data):
    logging.info(_("Send secure code email run"))

    to = data.get('email', None)
    passcode = data.get('passcode', None)

    if to and passcode:
        subject = _("Secure Code")
        from_email = '%s <cliexecboarding@gmail.com>' % APP_NAME

        # Message
        text = _(
            "Don't share this Secure Code to everyone "
            "Including %(app_label)s team. Your Secure Code is: " +
            passcode
        ) % {'app_label': APP_NAME}

        html = _(
            "Don't share this Secure Code to everyone "
            "Including %(app_label)s team.<br />"
            "Your Secure Code is: "
            "<strong>" + passcode + "</strong>"
            "<br /><br />"
            "Happy Coding, <br /> <strong>%(app_label)s</strong>"
        ) % {'app_label': APP_NAME}

        if subject and from_email:
            try:
                msg = EmailMultiAlternatives(subject, text, from_email, [to])
                msg.attach_alternative(html, "text/html")
                msg.send()
                logging.info(_("SecureCode email success"))
            except smtplib.SMTPConnectError as e:
                logging.error('SMTPConnectError: %s' % e)
            except smtplib.SMTPAuthenticationError as e:
                logging.error('SMTPAuthenticationError: %s' % e)
            except smtplib.SMTPSenderRefused as e:
                logging.error('SMTPSenderRefused: %s' % e)
            except smtplib.SMTPRecipientsRefused as e:
                logging.error('SMTPRecipientsRefused: %s' % e)
            except smtplib.SMTPDataError as e:
                logging.error('SMTPDataError: %s' % e)
            except smtplib.SMTPException as e:
                logging.error('SMTPException: %s' % e)
            except BadHeaderError:
                logging.warning(_("Invalid header found"))
    else:
        logging.warning(
            _("Tried to send email to non-existing SecureCode Code"))


@shared_task
def send_securecode_msisdn(data):
    logging.info(_("Send secure code msisdn run"))

    to = data.get('msisdn', None)
    passcode = data.get('passcode', None)

    if to and passcode:
        pass
    else:
        logging.warning(
            _("Tried to send email to non-existing SecureCode Code"))
