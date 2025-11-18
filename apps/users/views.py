from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import UserSerializer
from .services import UserService
from rest_framework.permissions import AllowAny

from apps.authentication.serializers import RegisterSerializer
from apps.authentication.services import AuthService
from apps.core.exceptions import AppError


class UserListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        role = request.query_params.get("role")
        team_id = request.query_params.get("team_id")

        users, total = UserService.list_users(page=page, page_size=page_size, role=role, team_id=team_id)
        serializer = UserSerializer(users, many=True)
        return Response(
            {
                "success": True,
                "data": serializer.data,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                },
            }
        )

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


class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        try:
            user = UserService.get_user_by_id(user_id)
            return Response({"success": True, "data": UserSerializer(user).data})
        except AppError as exc:
            return Response({"success": False, "message": exc.message}, status=exc.status_code)

    def put(self, request, user_id):
        """
        Update user bằng serializer để xử lý đúng embedded documents.
        """
        try:
            user = UserService.get_user_by_id(user_id)
            serializer = UserSerializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            updated_user = serializer.save()
            return Response({"success": True, "data": UserSerializer(updated_user).data})
        except AppError as exc:
            return Response({"success": False, "message": exc.message}, status=exc.status_code)
        except Exception as e:
            return Response(
                {"success": False, "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def delete(self, request, user_id):
        try:
            UserService.delete_user(user_id)
            return Response({"success": True, "message": "User deleted"})
        except AppError as exc:
            return Response({"success": False, "message": exc.message}, status=exc.status_code)


class UserMeView(APIView):
    """
    Trả về thông tin user hiện tại từ JWT token.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Lấy thông tin user hiện tại từ request.user (được set bởi JWT authentication).
        """
        try:
            # request.user được set bởi MongoJWTAuthentication
            user = request.user
            serializer = UserSerializer(user)
            return Response({"success": True, "data": serializer.data})
        except Exception as e:
            return Response(
                {"success": False, "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    
    def put(self, request):
        """
        Update thông tin user hiện tại.
        """
        try:
            user = request.user
            serializer = UserSerializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            updated_user = serializer.save()
            return Response({"success": True, "data": UserSerializer(updated_user).data})
        except AppError as exc:
            return Response({"success": False, "message": exc.message}, status=exc.status_code)
        except Exception as e:
            return Response(
                {"success": False, "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
