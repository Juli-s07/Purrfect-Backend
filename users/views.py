from django.contrib.auth import get_user_model
User = get_user_model()
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import UserSerializer

class RegisterView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if User.objects.filter(email__iexact=serializer.validated_data["email"]).exists():
            return Response({"email": ["This email has already been taken."]},
                            status=status.HTTP_409_CONFLICT)
        user = serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        u = request.user
        breeder = getattr(u, "breeder", None)
        return Response({
            "id": u.id,
            "username": u.username,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "email": u.email,
            "role": u.role,
            "is_staff": u.is_staff,
            "breeder_id": breeder.id if breeder else None,
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
