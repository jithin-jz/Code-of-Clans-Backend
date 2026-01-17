from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
import logging

logger = logging.getLogger(__name__)

def send_welcome_email(user):
    subject = "Welcome to Code of Clans!"

    try:
        context = {"user": user}

        html_message = render_to_string("emails/welcome.html", context)

        plain_message = (
            f"Welcome to Code of Clans!\n\n"
            f"Hi {user.first_name or user.username},\n"
            "We're excited to have you on board.\n"
            "Log in to start your journey."
        )

        send_mail(
            subject=subject,
            message=plain_message,
            from_email="Code of Clans <noreply@codeofclans.com>",
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info("Welcome email sent to %s", user.email)

    except Exception:
        logger.exception("Failed to send welcome email to %s", user.email)
