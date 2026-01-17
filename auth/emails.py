from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
import logging

logger = logging.getLogger(__name__)

def send_welcome_email(user):
    """
    Sends a welcome email to a newly registered user.
    """
    subject = "Welcome to Code of Clans!"
    
    # Simple text message for now. 
    # In the future, we can use a proper HTML template.
    message = f"""
    Hi {user.first_name or user.username},

    Welcome to Code of Clans! We're excited to have you on board.

    Get ready to code, battle, and level up!

    Best regards,
    The Code of Clans Team
    """
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False, 
        )
        logger.info(f"Welcome email sent to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")
