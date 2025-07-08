from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.crypto import get_random_string

class CustomUser(AbstractUser):
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    is_email_verified = models.BooleanField(default=False)
    email_otp = models.CharField(max_length=6, blank=True, null=True)
    # models.py
    partner_email = models.EmailField(blank=True, null=True)
    partner_verification_code = models.CharField(max_length=8, blank=True, null=True)
    is_restriction_enabled = models.BooleanField(default=True)


    def generate_email_otp(self):
        """
        Generates a 6-digit numeric OTP and saves it to the user's email_otp field.
        """
        self.email_otp = get_random_string(length=6, allowed_chars='0123456789')
        self.save()
