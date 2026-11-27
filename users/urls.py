from django.contrib.auth.views import LogoutView
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import EmailVerification
from .views import RegisterView, MeView, LogoutView, VerifyEmailView, ResendCodeView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", TokenObtainPairView.as_view(), name='login'),
    path("login/refresh/", TokenRefreshView.as_view(), name='token_refresh'),
    path("logout/", LogoutView.as_view(), name='logout'),
    path("users/me/", MeView.as_view(), name="me"),
    path("verify-email/", VerifyEmailView.as_view(), name="verify_email"),
    path("resend-code/", ResendCodeView.as_view(), name="resend_code"),
]
