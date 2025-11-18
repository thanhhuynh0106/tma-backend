from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import MessageSerializer
from .services import MessageService
from apps.core.exceptions import AppError


class MessageListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, conversation_id):
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))

        messages = MessageService.list_messages(
            conversation_id=conversation_id,
            page=page,
            page_size=page_size,
        )
        
        serializer = MessageSerializer(messages, many=True)
        total = messages.count() if hasattr(messages, 'count') else len(messages)
        
        return Response({
            "success": True,
            "data": serializer.data,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
            },
        })

    def post(self, request, conversation_id):
        data = request.data.copy()
        data['conversation_id'] = conversation_id
        if 'sender_id' not in data:
            data['sender_id'] = str(request.user.id)
        
        serializer = MessageSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        try:
            message = serializer.save()
            return Response({
                "success": True,
                "data": MessageSerializer(message).data,
            }, status=status.HTTP_201_CREATED)
        except AppError as exc:
            return Response(
                {"success": False, "message": exc.message},
                status=exc.status_code,
            )


class MessageDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, message_id):
        try:
            message = MessageService._get_message(message_id)
            return Response({
                "success": True,
                "data": MessageSerializer(message).data,
            })
        except AppError as exc:
            return Response(
                {"success": False, "message": exc.message},
                status=exc.status_code,
            )

    def delete(self, request, message_id):
        try:
            message = MessageService._get_message(message_id)
            message.delete()
            return Response({
                "success": True,
                "message": "Message deleted successfully",
            })
        except AppError as exc:
            return Response(
                {"success": False, "message": exc.message},
                status=exc.status_code,
            )


class MessageMarkReadView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, message_id):
        try:
            message = MessageService.mark_as_read(message_id)
            return Response({
                "success": True,
                "data": MessageSerializer(message).data,
            })
        except AppError as exc:
            return Response(
                {"success": False, "message": exc.message},
                status=exc.status_code,
            )
