from django.contrib.auth import get_user_model
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from .emails import send_verification_code
from .serializers import UserSerializer
from datetime import timedelta
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from django.contrib.auth.hashers import check_password
from django.db.models import Q

User = get_user_model()

CODE_TIME = timedelta(minutes=10)       # код діє 10 хвилин
MAX_ATTEMPTS = 5
RESEND_COOLDOWN = timedelta(seconds=60)

class VerifyEmailView(APIView):
    def post(self, request):
        email = request.data.get("email")
        code = str(request.data.get("code", "")).strip()

        user = User.objects.filter(email__iexact=email).first()
        if user and user.is_active:
            raise ValidationError({"code": "This email is already verified. Please log in."})

        user = User.objects.filter(email__iexact=email, is_active=False).first()
        verification = getattr(user, "email_verification", None) if user else None
        if verification is None:
            raise ValidationError({"code": "No pending verification for this email. Please register or request a new code."})
        if timezone.now() - verification.sent_at > CODE_TIME:
            raise ValidationError({"code": "This code has expired. Please request a new one."})
        if verification.attempts >= MAX_ATTEMPTS:
            raise ValidationError({"code": "Too many attempts. Please request a new code."})
        verification.attempts += 1
        verification.save(update_fields=["attempts"])

        if not check_password(code, verification.code_hash):
            left = MAX_ATTEMPTS - verification.attempts
            if left <= 0:
                raise ValidationError({"code": "Too many attempts. Please request a new code."})
            raise ValidationError({"code": f"Incorrect code. Attempts left: {left}."})

        user.is_active = True
        user.save(update_fields=["is_active"])
        verification.delete()
        return Response({"detail": "Email verified"})

class ResendCodeView(APIView):
    def post(self, request):
        user = User.objects.filter(email__iexact=request.data.get("email", ""), is_active=False).first()
        verification = getattr(user, "email_verification", None) if user else None
        if verification:
            if timezone.now() - verification.sent_at < RESEND_COOLDOWN:
                return Response({"detail": "Please wait a minute before requesting a new code."}, status=429,)
            send_verification_code(user) # відлік часу на фронтенді
        return Response({"detail": "If the account exists, a new code was sent"})

class RegisterView(APIView):
    def post(self, request):
        email = str(request.data.get("email", "")).strip()
        username = str(request.data.get("username", "")).strip()

        User.objects.filter(
            Q(email__iexact=email) | Q(username__iexact=username),
            is_active=False,
            email_verification__isnull=False,
        ).delete() #видалення покинутих реєстрацій

        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if User.objects.filter(email__iexact=serializer.validated_data["email"]).exists():
            return Response({"email": ["This email has already been taken."]},
                            status=status.HTTP_409_CONFLICT)
        user = serializer.save()
        user.is_active = False
        user.save(update_fields=["is_active"])
        send_verification_code(user)
        return Response({"email": user.email, "detail": "Verification code sent"}, status=status.HTTP_201_CREATED,)

class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        u = request.user
        return Response({
            "username": u.username,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "email": u.email,
            "date_joined": u.date_joined,
        })

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            RefreshToken(request.data.get("refresh")).blacklist()
        except TokenError:
            return Response({"detail": ["Invalid token"]},)
        return Response(status=205)
