from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import NotificationSerializer
from .services import NotificationService
from apps.core.exceptions import AppError


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        unread_only = request.query_params.get("unread_only", "false").lower() == "true"
        user_id = request.query_params.get("user_id", str(request.user.id))

        notifications = NotificationService.list_notifications(
            user_id=user_id,
            unread_only=unread_only,
            page=page,
            page_size=page_size,
        )
        
        serializer = NotificationSerializer(notifications, many=True)
        total = notifications.count() if hasattr(notifications, 'count') else len(notifications)
        
        return Response({
            "success": True,
            "data": serializer.data,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
            },
        })

    def post(self, request):
        serializer = NotificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            notification = serializer.save()
            return Response({
                "success": True,
                "data": NotificationSerializer(notification).data,
            }, status=status.HTTP_201_CREATED)
        except AppError as exc:
            return Response(
                {"success": False, "message": exc.message},
                status=exc.status_code,
            )


class NotificationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, notification_id):
        try:
            notification = NotificationService._get_notification(notification_id)
            return Response({
                "success": True,
                "data": NotificationSerializer(notification).data,
            })
        except AppError as exc:
            return Response(
                {"success": False, "message": exc.message},
                status=exc.status_code,
            )

    def delete(self, request, notification_id):
        try:
            NotificationService.delete_notification(notification_id)
            return Response({
                "success": True,
                "message": "Notification deleted successfully",
            })
        except AppError as exc:
            return Response(
                {"success": False, "message": exc.message},
                status=exc.status_code,
            )


class NotificationMarkReadView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, notification_id):
        try:
            notification = NotificationService.mark_as_read(notification_id)
            return Response({
                "success": True,
                "data": NotificationSerializer(notification).data,
            })
        except AppError as exc:
            return Response(
                {"success": False, "message": exc.message},
                status=exc.status_code,
            )
