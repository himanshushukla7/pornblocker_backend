from django.urls import path
from .views import register, verify_otp, profile, update_profile, EmailTokenObtainPairView,change_password
from . import views

urlpatterns = [
    path('register/', register, name='register'),
    path('verify-otp/', verify_otp, name='verify-otp'),
    path('login/', EmailTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('profile/', profile, name='profile'),
    path('profile/update/', update_profile, name='update-profile'),
    path('token/', EmailTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('change-password/', views.change_password),  # ✅ Add this line
    path('assign-partner/', views.assign_accountability_partner),
    path('verify-partner-code/', views.verify_partner_code),



]
