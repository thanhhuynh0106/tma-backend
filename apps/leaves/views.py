from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import LeaveSerializer
from .services import LeaveService
from rest_framework.permissions import AllowAny

from apps.core.exceptions import AppError


class LeaveListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        user_id = request.query_params.get("user_id")
        status_filter = request.query_params.get("status")

        leaves, total = LeaveService.list_leaves(page=page, page_size=page_size, user_id=user_id, status=status_filter)
        serializer = LeaveSerializer(leaves, many=True)
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
        serializer = LeaveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            # Extract user_id từ validated_data
            validated_data = serializer.validated_data.copy()
            user_id = validated_data.pop('user_id')
            
            # Truyền user_id riêng và các data khác
            leave = LeaveService.request_leave(user_id=user_id, **validated_data)
            return Response(
                {
                    "success": True,
                    "data": LeaveSerializer(leave).data,
                },
                status=status.HTTP_201_CREATED,
            )
        except AppError as exc:
            return Response(
                {"success": False, "message": exc.message},
                status=exc.status_code,
            )
        


class LeaveDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, leave_id):
        try:
            leave = LeaveService._get_leave(leave_id)
            serializer = LeaveSerializer(leave)
            return Response(
                {
                    "success": True,
                    "data": serializer.data,
                }
            )
        except AppError as exc:
            return Response(
                {"success": False, "message": exc.message},
                status=exc.status_code,
            )
    

    def put(self, request, leave_id):
        try:
            leave = LeaveService._get_leave(leave_id)
            serializer = LeaveSerializer(leave, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)

            update_data = serializer.validated_data.copy()
            if 'user_id' in update_data:
                update_data['user_id'] = update_data.pop('user_id')
            
            updated_leave = LeaveService.update_leave(leave_id, **update_data)
            return Response({
                "success": True,
                "data": LeaveSerializer(updated_leave).data,
            })
        except AppError as exc:
            return Response(
                {"success": False, "message": exc.message},
                status=exc.status_code,
            )
    

    def delete(self, request, leave_id):
        try:
            LeaveService.delete_leave(leave_id)
            return Response(
                {
                    "success": True,
                    "message": "Leave deleted",
                }
            )
        except AppError as exc:
            return Response(
                {"success": False, "message": exc.message},
                status=exc.status_code,
            )
        

class LeaveApprovalView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, leave_id):
        try:
            approver_id = request.data.get("approver_id")
            if not approver_id:
                approver_id = str(request.user.id)
            

            leave = LeaveService.approve_leave(leave_id, approver_id)
            return Response(
                {
                    "success": True,
                    "data": LeaveSerializer(leave).data,
                }
            )
        except AppError as exc:
            return Response(
                {"success": False, "message": exc.message},
                status=exc.status_code,
            )


class LeaveRejectionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, leave_id):
        try:
            approver_id = request.data.get("approver_id")
            reason = request.data.get("reason")

            if not approver_id:
                approver_id = str(request.user.id)

            if not reason:
                return Response(
                    {"success": False, "message": "Rejection reason is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            leave = LeaveService.reject_leave(leave_id, approver_id, reason)
            return Response(
                {
                    "success": True,
                    "data": LeaveSerializer(leave).data,
                }
            )
        except AppError as exc:
            return Response(
                {"success": False, "message": exc.message},
                status=exc.status_code,
            )
        

class MyLeaveView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        status_filter = request.query_params.get("status")

        user_id = str(request.user.id)

        leaves, total = LeaveService.list_leaves(page=page, page_size=page_size, user_id=user_id, status=status_filter)
        serializer = LeaveSerializer(leaves, many=True)

        return Response({
            "success": True,
            "data": serializer.data,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
            },
        })