from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model, authenticate
from django.core.mail import send_mail
from django.conf import settings
from authapp.utils import send_otp_to_email
import uuid
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.crypto import get_random_string



User = get_user_model()

# ✅ Basic serializer for retrieving user data
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'country',
            'city',
            'phone_number',
            'is_email_verified',
            'is_restriction_enabled',
            'partner_verification_code',  # needed for login redirect logic
        )


# ✅ Registration serializer (you only need one)
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'first_name', 'last_name', 'country', 'city', 'phone_number']

    def create(self, validated_data):
        unique_username = str(uuid.uuid4())[:30]  # unique username
        user = User.objects.create_user(
            username=unique_username,
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            country=validated_data.get('country', ''),
            city=validated_data.get('city', ''),
            phone_number=validated_data.get('phone_number', ''),
            is_active=False
        )
        user.generate_email_otp()  # custom method from models.py

        # Send OTP email
        send_mail(
            subject="Verify Your Email with OTP",
            message=f"Your OTP is: {user.email_otp}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
        )
        return user

# ✅ Login with email/password + OTP check
class EmailTokenObtainPairSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        user = authenticate(email=email, password=password)  # Uses custom backend

        if not user:
            raise serializers.ValidationError("Invalid email or password")

        if not user.is_email_verified:
            raise serializers.ValidationError("Please verify your email before logging in.")

        refresh = RefreshToken.for_user(user)

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data,
            'is_verified': user.is_email_verified
        }



# ✅ OTP verification
class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

    def validate(self, data):
        email = data.get('email')
        otp = data.get('otp')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")

        if user.is_email_verified:
            raise serializers.ValidationError("Email is already verified.")

        if user.email_otp != otp:
            raise serializers.ValidationError("Invalid OTP.")

        return data

    def save(self, **kwargs):
        email = self.validated_data['email']
        user = User.objects.get(email=email)
        user.is_email_verified = True
        user.email_otp = None
        user.is_active = True
        user.save()
        return user

class AssignPartnerSerializer(serializers.Serializer):
    partner_email = serializers.EmailField()

    def validate_partner_email(self, email):
        # Prevent assigning yourself
        if self.context['request'].user.email == email:
            raise serializers.ValidationError("You cannot assign yourself as your accountability partner.")
        return email

    def save(self):
        user = self.context['request'].user
        partner_email = self.validated_data['partner_email']
        code = get_random_string(length=6, allowed_chars='0123456789')

        user.partner_email = partner_email
        user.partner_verification_code = code
        user.is_restriction_enabled = True  # user is now committed
        user.save()

        # Send secret code to partner only
        send_mail(
            subject="🔒 Accountability Code for Your Friend",
            message=f"""Hi,

Your friend {user.first_name or 'A user'} has committed to blocking adult content and listed you as their accountability partner.

To disable restrictions in the future, they'll need the following secret code. Please do NOT share this code with them unless absolutely necessary.

🔐 Verification Code: {code}

Thank you for supporting them in this important step.

- Accountability Team
""",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[partner_email],
        )

        return user

    
class VerifyPartnerCodeSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=8)

    def validate(self, data):
        user = self.context['request'].user
        if user.partner_verification_code != data['code']:
            raise serializers.ValidationError("Invalid verification code.")
        return data

    def save(self):
        user = self.context['request'].user
        user.is_restriction_enabled = False
        user.partner_verification_code = None
        user.partner_email = None
        user.save()
        return user
