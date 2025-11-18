from datetime import datetime
from typing import Optional

from mongoengine.queryset import QuerySet

from apps.leaves.models import Leave
from apps.users.models import User
from apps.core.exceptions import NotFoundError, ValidationError, ConflictError


class LeaveService:
    """Business logic cho Leave requests."""

    @staticmethod
    def _get_leave(leave_id: str) -> Leave:
        leave = Leave.objects(id=leave_id).first()
        if not leave:
            raise NotFoundError(f"Leave {leave_id} not found")
        return leave

    @staticmethod
    def _get_user(user_id: str) -> User:
        user = User.objects(id=user_id).first()
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        return user

    # --------- CRUD ---------
    @staticmethod
    def list_leaves(
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[QuerySet, int]:
        query = {}
        if user_id:
            query["user"] = LeaveService._get_user(user_id)
        if status:
            query["status"] = status

        # Đếm total trước khi paginate
        total = Leave.objects(**query).count()
        
        skip = (page - 1) * page_size
        leaves = Leave.objects(**query).skip(skip).limit(page_size).order_by("-created_at")
        
        return leaves, total

    @staticmethod
    def request_leave(user_id: str, **data) -> Leave:
        user = LeaveService._get_user(user_id)
        # Loại bỏ status và user_id từ data để tránh conflict
        data.pop('status', None)  # Remove status nếu có, luôn set thành "pending"
        data.pop('user_id', None)  # Remove user_id vì đã có user object
        data.pop('approved_by_id', None)  # Remove approved_by_id vì mới request chưa có approver
        leave = Leave(user=user, status="pending", **data)
        leave.save()
        return leave

    @staticmethod
    def update_leave(leave_id: str, **data) -> Leave:
        leave = LeaveService._get_leave(leave_id)
        if leave.status != "pending":
            raise ConflictError("Only pending leaves can be updated")

        if "user_id" in data:
            leave.user = LeaveService._get_user(data.pop("user_id"))

        for attr, value in data.items():
            setattr(leave, attr, value)

        leave.save()
        return leave

    @staticmethod
    def delete_leave(leave_id: str) -> None:
        leave = LeaveService._get_leave(leave_id)
        leave.delete()

    # --------- Approval flow ---------
    @staticmethod
    def approve_leave(leave_id: str, approver_id: str) -> Leave:
        leave = LeaveService._get_leave(leave_id)
        if leave.status != "pending":
            raise ConflictError("Leave already processed")

        approver = LeaveService._get_user(approver_id)
        leave.status = "approved"
        leave.approved_by = approver
        leave.approved_at = datetime.utcnow()
        leave.rejection_reason = None
        leave.save()
        return leave

    @staticmethod
    def reject_leave(leave_id: str, approver_id: str, reason: str) -> Leave:
        leave = LeaveService._get_leave(leave_id)
        if leave.status != "pending":
            raise ConflictError("Leave already processed")

        approver = LeaveService._get_user(approver_id)
        leave.status = "rejected"
        leave.approved_by = approver
        leave.approved_at = datetime.utcnow()
        leave.rejection_reason = reason
        leave.save()
        return leave

