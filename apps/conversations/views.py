from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import ConversationSerializer
from .services import ConversationService
from apps.core.exceptions import AppError


class ConversationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        user_id = request.query_params.get("user_id", str(request.user.id))

        conversations = ConversationService.list_conversations(
            user_id=user_id,
            page=page,
            page_size=page_size,
        )
        
        serializer = ConversationSerializer(conversations, many=True)
        total = conversations.count() if hasattr(conversations, 'count') else len(conversations)
        
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
        serializer = ConversationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            conversation = serializer.save()
            return Response({
                "success": True,
                "data": ConversationSerializer(conversation).data,
            }, status=status.HTTP_201_CREATED)
        except AppError as exc:
            return Response(
                {"success": False, "message": exc.message},
                status=exc.status_code,
            )


class ConversationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, conversation_id):
        try:
            conversation = ConversationService._get_conversation(conversation_id)
            return Response({
                "success": True,
                "data": ConversationSerializer(conversation).data,
            })
        except AppError as exc:
            return Response(
                {"success": False, "message": exc.message},
                status=exc.status_code,
            )

    def put(self, request, conversation_id):
        try:
            conversation = ConversationService._get_conversation(conversation_id)
            serializer = ConversationSerializer(conversation, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            updated_conversation = serializer.save()
            return Response({
                "success": True,
                "data": ConversationSerializer(updated_conversation).data,
            })
        except AppError as exc:
            return Response(
                {"success": False, "message": exc.message},
                status=exc.status_code,
            )

    def delete(self, request, conversation_id):
        try:
            conversation = ConversationService._get_conversation(conversation_id)
            conversation.delete()
            return Response({
                "success": True,
                "message": "Conversation deleted successfully",
            })
        except AppError as exc:
            return Response(
                {"success": False, "message": exc.message},
                status=exc.status_code,
            )
