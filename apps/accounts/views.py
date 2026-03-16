from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.exceptions import TokenError

from .models import User
from .permissions import IsCompanyAdmin
from .serializers import UserCreateSerializer, UserListSerializer, UserProfileSerializer, UserUpdateSerializer


class LoginView(TokenObtainPairView):
    """
    POST /api/v1/auth/login/
    Returns access + refresh JWT tokens on valid credentials.
    AllowAny because the user is not authenticated yet at this point.
    """
    permission_classes = [AllowAny]


class LogoutView(APIView):
    """
    POST /api/v1/auth/logout/
    Blacklists the refresh token so it cannot be reused after logout.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"detail": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response({"detail": "Token is invalid or already blacklisted."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TokenRefreshAPIView(TokenRefreshView):
    """
    POST /api/v1/auth/token/refresh/
    Exchanges a valid refresh token for a new access token.
    """
    permission_classes = [AllowAny]


class MeView(APIView):
    """
    GET /api/v1/auth/me/
    Returns the currently authenticated user's profile and role.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)


class UserListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/v1/users/  — Company Admin lists all users.
    POST /api/v1/users/  — Company Admin creates (invites) a new user.
    """
    permission_classes = [IsCompanyAdmin]
    queryset = User.objects.all().order_by("date_joined")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return UserCreateSerializer
        return UserListSerializer


class UserDetailView(generics.RetrieveUpdateAPIView):
    """
    GET   /api/v1/users/{id}/  — Company Admin retrieves a user's details.
    PATCH /api/v1/users/{id}/  — Company Admin updates role or is_active status.
    """
    permission_classes = [IsCompanyAdmin]
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return UserUpdateSerializer
        return UserListSerializer
