import secrets
from .models import EmailVerification
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

def send_verification_code(user):
    code = f"{secrets.randbelow(1_000_000):06d}"

    EmailVerification.objects.update_or_create(
        user=user,
        defaults={
            "code_hash": make_password(code),
            "sent_at": timezone.now(),
            "attempts": 0,
        },
    )

    send_mail(
        subject="Purrfect: your verification code",
        message=(
                    f"Your verification code: {code}\n\n"
                    "This code will expire in 10 minutes.\n\n"
                    "If you didn't register on Purrfect, just ignore this email."
                ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )
