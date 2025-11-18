from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import TaskSerializer
from .services import TaskService
from apps.core.exceptions import AppError


class TaskListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        status_filter = request.query_params.get("status")
        team_id = request.query_params.get("team_id")
        assigned_to = request.query_params.get("assigned_to")

        tasks = TaskService.list_tasks(
            page=page,
            page_size=page_size,
            status=status_filter,
            team_id=team_id,
            assigned_to=assigned_to,
        )
        
        serializer = TaskSerializer(tasks, many=True)
        total = tasks.count() if hasattr(tasks, 'count') else len(tasks)
        
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
        # Chuẩn hóa request.data: map assigned_to thành assigned_to_ids nếu có
        data = dict(request.data)
        if 'assigned_to' in data and 'assigned_to_ids' not in data:
            assigned_to_value = data.pop('assigned_to', [])
            if assigned_to_value:
                data['assigned_to_ids'] = assigned_to_value
        
        serializer = TaskSerializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        try:
            task = serializer.save()
            return Response({
                "success": True,
                "data": TaskSerializer(task).data,
            }, status=status.HTTP_201_CREATED)
        except AppError as exc:
            return Response(
                {"success": False, "message": exc.message},
                status=exc.status_code,
            )


class TaskDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, task_id):
        try:
            task = TaskService._get_task(task_id)
            return Response({
                "success": True,
                "data": TaskSerializer(task).data,
            })
        except AppError as exc:
            return Response(
                {"success": False, "message": exc.message},
                status=exc.status_code,
            )

    def put(self, request, task_id):
        try:
            task = TaskService._get_task(task_id)
            serializer = TaskSerializer(task, data=request.data, partial=True, context={'request': request})
            serializer.is_valid(raise_exception=True)
            updated_task = serializer.save()
            return Response({
                "success": True,
                "data": TaskSerializer(updated_task).data,
            })
        except AppError as exc:
            return Response(
                {"success": False, "message": exc.message},
                status=exc.status_code,
            )

    def delete(self, request, task_id):
        try:
            TaskService.delete_task(task_id)
            return Response({
                "success": True,
                "message": "Task deleted successfully",
            })
        except AppError as exc:
            return Response(
                {"success": False, "message": exc.message},
                status=exc.status_code,
            )


class TaskStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, task_id):
        try:
            status_value = request.data.get("status")
            if not status_value:
                return Response(
                    {"success": False, "message": "status is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            task = TaskService.change_status(task_id, status_value)
            return Response({
                "success": True,
                "data": TaskSerializer(task).data,
            })
        except AppError as exc:
            return Response(
                {"success": False, "message": exc.message},
                status=exc.status_code,
            )


class TaskCommentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, task_id):
        try:
            text = request.data.get("text")
            user_id = request.data.get("user_id", str(request.user.id))
            
            if not text:
                return Response(
                    {"success": False, "message": "text is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            task = TaskService.add_comment(task_id, user_id, text)
            return Response({
                "success": True,
                "data": TaskSerializer(task).data,
            })
        except AppError as exc:
            return Response(
                {"success": False, "message": exc.message},
                status=exc.status_code,
            )


class TaskAttachmentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, task_id):
        try:
            attachment_data = request.data.get("attachment")
            if not attachment_data or "name" not in attachment_data or "url" not in attachment_data:
                return Response(
                    {"success": False, "message": "attachment with 'name' and 'url' is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            task = TaskService.add_attachment(task_id, attachment_data)
            return Response({
                "success": True,
                "data": TaskSerializer(task).data,
            })
        except AppError as exc:
            return Response(
                {"success": False, "message": exc.message},
                status=exc.status_code,
            )
