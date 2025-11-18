from datetime import datetime, date, time
from typing import Optional

from mongoengine.queryset import QuerySet

from apps.attendance.models import Attendance, Location
from apps.users.models import User
from apps.core.exceptions import NotFoundError, ValidationError, ConflictError


class AttendanceService:
    """Business logic cho Attendance (check-in / check-out)."""

    # Phạm vi cho phép clock in
    ALLOWED_AREA = {
        "latMin": 10.869093,
        "latMax": 10.871556,
        "lngMin": 106.802012,
        "lngMax": 106.805138,
    }

    # Thời gian absent (8h sáng)
    ABSENT_TIME = time(8, 0, 0)  # 8:00 AM

    @staticmethod
    def _get_user(user_id: str) -> User:
        user = User.objects(id=user_id).first()
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        return user

    @staticmethod
    def _get_today_attendance(user: User, target_date: Optional[date] = None) -> Optional[Attendance]:
        target_date = target_date or date.today()
        return Attendance.objects(user=user, date=target_date).first()

    @staticmethod
    def _validate_location(location: dict) -> None:
        """
        Validate location có nằm trong phạm vi cho phép không.
        Raises ValidationError nếu location không hợp lệ.
        """
        if not location or "lat" not in location or "lng" not in location:
            raise ValidationError("Location must contain 'lat' and 'lng'")

        lat = float(location["lat"])
        lng = float(location["lng"])

        allowed_area = AttendanceService.ALLOWED_AREA

        if not (
            allowed_area["latMin"] <= lat <= allowed_area["latMax"]
            and allowed_area["lngMin"] <= lng <= allowed_area["lngMax"]
        ):
            raise ValidationError(
                f"Location ({lat}, {lng}) is outside the allowed area. "
                f"Allowed area: lat [{allowed_area['latMin']}, {allowed_area['latMax']}], "
                f"lng [{allowed_area['lngMin']}, {allowed_area['lngMax']}]"
            )

    @staticmethod
    def _determine_status(clock_in_time: datetime) -> str:
        """
        Xác định status dựa trên thời gian clock in.
        - Trước hoặc đúng 8h sáng: "present"
        - Sau 8h sáng: "late"
        """
        clock_in_time_only = clock_in_time.time()
        
        if clock_in_time_only <= AttendanceService.ABSENT_TIME:
            return "present"
        else:
            return "late"

    @staticmethod
    def clock_in(user_id: str, location: dict) -> Attendance:
        user = AttendanceService._get_user(user_id)
        if AttendanceService._get_today_attendance(user):
            raise ConflictError("User already clocked in today")

        # Validate location trước khi clock in
        AttendanceService._validate_location(location)

        clock_in_time = datetime.utcnow()
        status = AttendanceService._determine_status(clock_in_time)

        attendance = Attendance(
            user=user,
            date=date.today(),
            clock_in=clock_in_time,
            location=Location(**location),
            status=status,
        )
        attendance.save()
        return attendance

    @staticmethod
    def clock_out(user_id: str) -> Attendance:
        user = AttendanceService._get_user(user_id)
        attendance = AttendanceService._get_today_attendance(user)
        if not attendance:
            raise NotFoundError("No attendance record for today")
        if attendance.clock_out:
            raise ConflictError("User already clocked out")

        attendance.clock_out = datetime.utcnow()
        delta = attendance.clock_out - attendance.clock_in
        attendance.work_hours = round(delta.total_seconds() / 3600, 2)
        attendance.save()
        return attendance

    @staticmethod
    def list_attendance(
        user_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> QuerySet:
        query = {}
        if user_id:
            query["user"] = AttendanceService._get_user(user_id)
        if start_date and end_date:
            query["date__gte"] = start_date
            query["date__lte"] = end_date

        skip = (page - 1) * page_size
        return Attendance.objects(**query).skip(skip).limit(page_size).order_by("-date")

    @staticmethod
    def update_attendance(attendance_id: str, **data) -> Attendance:
        attendance = Attendance.objects(id=attendance_id).first()
        if not attendance:
            raise NotFoundError(f"Attendance {attendance_id} not found")

        if "location" in data:
            attendance.location = Location(**data.pop("location"))

        for attr, value in data.items():
            setattr(attendance, attr, value)

        attendance.save()
        return attendance

    @staticmethod
    def delete_attendance(attendance_id: str) -> None:
        attendance = Attendance.objects(id=attendance_id).first()
        if not attendance:
            raise NotFoundError(f"Attendance {attendance_id} not found")
        attendance.delete()

