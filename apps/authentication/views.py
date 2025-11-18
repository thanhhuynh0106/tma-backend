from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.serializers import (
    RegisterSerializer,
    LoginSerializer,
    ChangePasswordSerializer,
    ForceResetPasswordSerializer,
)
from apps.authentication.services import AuthService
from apps.core.exceptions import AppError
from apps.users.serializers import UserSerializer


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user, tokens = AuthService.register_user(serializer.validated_data)
            return Response(
                {
                    "success": True,
                    "data": {
                        "user": UserSerializer(user).data,
                        "tokens": tokens,
                    },
                },
                status=status.HTTP_201_CREATED,
            )
        except AppError as exc:
            return Response(
                {"success": False, "message": exc.message},
                status=exc.status_code,
            )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user, tokens = AuthService.login(**serializer.validated_data)
            return Response(
                {
                    "success": True,
                    "data": {
                        "user": UserSerializer(user).data,
                        "tokens": tokens,
                    },
                }
            )
        except AppError as exc:
            return Response(
                {"success": False, "message": exc.message},
                status=exc.status_code,
            )


class ChangePasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            AuthService.change_password(**serializer.validated_data)
            return Response({"success": True, "message": "Password updated successfully"})
        except AppError as exc:
            return Response(
                {"success": False, "message": exc.message},
                status=exc.status_code,
            )


class ForceResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForceResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            AuthService.force_reset_password(**serializer.validated_data)
            return Response({"success": True, "message": "Password reset successfully"})
        except AppError as exc:
            return Response(
                {"success": False, "message": exc.message},
                status=exc.status_code,
            )


class DeactivateUserView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user_id = request.data.get("user_id")
        if not user_id:
            return Response(
                {"success": False, "message": "user_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            user = AuthService.deactivate_user(user_id)
            return Response(
                {"success": True, "data": UserSerializer(user).data, "message": "User deactivated"}
            )
        except AppError as exc:
            return Response(
                {"success": False, "message": exc.message},
                status=exc.status_code,
            )


class ReactivateUserView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user_id = request.data.get("user_id")
        if not user_id:
            return Response(
                {"success": False, "message": "user_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            user = AuthService.reactivate_user(user_id)
            return Response(
                {"success": True, "data": UserSerializer(user).data, "message": "User reactivated"}
            )
        except AppError as exc:
            return Response(
                {"success": False, "message": exc.message},
                status=exc.status_code,
            )
