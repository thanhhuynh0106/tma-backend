from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import AttendanceSerializer
from .services import AttendanceService
from .models import Attendance
from apps.core.exceptions import AppError
from datetime import date


class AttendanceListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        user_id = request.query_params.get("user_id")
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        start_date_obj = None
        end_date_obj = None
        if start_date:
            start_date_obj = date.fromisoformat(start_date)
        if end_date:
            end_date_obj = date.fromisoformat(end_date)

        attendances = AttendanceService.list_attendance(
            user_id=user_id,
            start_date=start_date_obj,
            end_date=end_date_obj,
            page=page,
            page_size=page_size,
        )
        
        serializer = AttendanceSerializer(attendances, many=True)
        total = attendances.count() if hasattr(attendances, 'count') else len(attendances)
        
        return Response({
            "success": True,
            "data": serializer.data,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
            },
        })


class ClockInView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user_id = request.data.get("user_id", str(request.user.id))
            location = request.data.get("location")
            
            if not location or "lat" not in location or "lng" not in location:
                return Response(
                    {"success": False, "message": "location with 'lat' and 'lng' is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            attendance = AttendanceService.clock_in(user_id, location)
            return Response({
                "success": True,
                "data": AttendanceSerializer(attendance).data,
            }, status=status.HTTP_201_CREATED)
        except AppError as exc:
            return Response(
                {"success": False, "message": exc.message},
                status=exc.status_code,
            )


class ClockOutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user_id = request.data.get("user_id", str(request.user.id))
            attendance = AttendanceService.clock_out(user_id)
            return Response({
                "success": True,
                "data": AttendanceSerializer(attendance).data,
            })
        except AppError as exc:
            return Response(
                {"success": False, "message": exc.message},
                status=exc.status_code,
            )


class UserAttendanceView(APIView):
    """Get attendance records for a specific user"""
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        try:
            page = int(request.query_params.get("page", 1))
            page_size = int(request.query_params.get("page_size", 20))
            start_date = request.query_params.get("start_date")
            end_date = request.query_params.get("end_date")

            start_date_obj = None
            end_date_obj = None
            if start_date:
                start_date_obj = date.fromisoformat(start_date)
            if end_date:
                end_date_obj = date.fromisoformat(end_date)

            attendances = AttendanceService.list_attendance(
                user_id=user_id,
                start_date=start_date_obj,
                end_date=end_date_obj,
                page=page,
                page_size=page_size,
            )
            
            serializer = AttendanceSerializer(attendances, many=True)
            total = attendances.count() if hasattr(attendances, 'count') else len(attendances)
            
            return Response({
                "success": True,
                "data": serializer.data,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                },
            })
        except AppError as exc:
            return Response(
                {"success": False, "message": exc.message},
                status=exc.status_code,
            )


class MyAttendanceView(APIView):
    """Get attendance records for current authenticated user"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user_id = str(request.user.id)
            page = int(request.query_params.get("page", 1))
            page_size = int(request.query_params.get("page_size", 20))
            start_date = request.query_params.get("start_date")
            end_date = request.query_params.get("end_date")

            start_date_obj = None
            end_date_obj = None
            if start_date:
                start_date_obj = date.fromisoformat(start_date)
            if end_date:
                end_date_obj = date.fromisoformat(end_date)

            attendances = AttendanceService.list_attendance(
                user_id=user_id,
                start_date=start_date_obj,
                end_date=end_date_obj,
                page=page,
                page_size=page_size,
            )
            
            serializer = AttendanceSerializer(attendances, many=True)
            total = attendances.count() if hasattr(attendances, 'count') else len(attendances)
            
            return Response({
                "success": True,
                "data": serializer.data,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                },
            })
        except AppError as exc:
            return Response(
                {"success": False, "message": exc.message},
                status=exc.status_code,
            )


class AttendanceDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, attendance_id):
        try:
            attendance = Attendance.objects(id=attendance_id).first()
            if not attendance:
                return Response(
                    {"success": False, "message": f"Attendance {attendance_id} not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            return Response({
                "success": True,
                "data": AttendanceSerializer(attendance).data,
            })
        except AppError as exc:
            return Response(
                {"success": False, "message": exc.message},
                status=exc.status_code,
            )

    def put(self, request, attendance_id):
        try:
            serializer = AttendanceSerializer(data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            
            update_data = serializer.validated_data.copy()
            if 'location' in update_data:
                update_data['location'] = update_data['location']
            
            attendance = AttendanceService.update_attendance(attendance_id, **update_data)
            return Response({
                "success": True,
                "data": AttendanceSerializer(attendance).data,
            })
        except AppError as exc:
            return Response(
                {"success": False, "message": exc.message},
                status=exc.status_code,
            )

    def delete(self, request, attendance_id):
        try:
            AttendanceService.delete_attendance(attendance_id)
            return Response({
                "success": True,
                "message": "Attendance deleted successfully",
            })
        except AppError as exc:
            return Response(
                {"success": False, "message": exc.message},
                status=exc.status_code,
            )
