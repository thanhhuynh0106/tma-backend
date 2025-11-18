from typing import Optional

from mongoengine.queryset import QuerySet

from apps.notifications.models import Notification
from apps.users.models import User
from apps.core.exceptions import NotFoundError


class NotificationService:
    """Business logic cho Notification."""

    @staticmethod
    def _get_user(user_id: str) -> User:
        user = User.objects(id=user_id).first()
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        return user

    @staticmethod
    def _get_notification(notification_id: str) -> Notification:
        notification = Notification.objects(id=notification_id).first()
        if not notification:
            raise NotFoundError(f"Notification {notification_id} not found")
        return notification

    # --------- CRUD ---------
    @staticmethod
    def list_notifications(user_id: str, unread_only: bool = False, page: int = 1, page_size: int = 20) -> QuerySet:
        user = NotificationService._get_user(user_id)
        query = {"user": user}
        if unread_only:
            query["is_read"] = False

        skip = (page - 1) * page_size
        return Notification.objects(**query).skip(skip).limit(page_size).order_by("-created_at")

    @staticmethod
    def create_notification(user_id: str, **data) -> Notification:
        user = NotificationService._get_user(user_id)
        notification = Notification(user=user, **data)
        notification.save()
        return notification

    @staticmethod
    def mark_as_read(notification_id: str) -> Notification:
        notification = NotificationService._get_notification(notification_id)
        notification.is_read = True
        notification.save()
        return notification

    @staticmethod
    def mark_all_as_read(user_id: str) -> None:
        user = NotificationService._get_user(user_id)
        Notification.objects(user=user, is_read=False).update(is_read=True)

    @staticmethod
    def delete_notification(notification_id: str) -> None:
        notification = NotificationService._get_notification(notification_id)
        notification.delete()

