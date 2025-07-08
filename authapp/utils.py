from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

def send_otp_to_email(user):
    """
    Generates and sends a 6-digit OTP to the user's email address.
    """
    # Generate the OTP
    user.generate_email_otp()

    subject = "Your Email Verification OTP"
    message = f"Hi {user.username},\n\nYour verification OTP is: {user.email_otp}\n\nPlease enter this code in the app to verify your email address."
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]

    send_mail(subject, message, from_email, recipient_list)
