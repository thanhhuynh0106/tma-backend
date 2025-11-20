from datetime import datetime
from typing import List, Optional, Dict

from mongoengine.queryset import QuerySet

from apps.tasks.models import Task, Attachment, Comment
from apps.users.models import User
from apps.core.exceptions import NotFoundError, ValidationError


class TaskService:

    @staticmethod
    def _get_task(task_id: str) -> Task:
        task = Task.objects(id=task_id).first()
        if not task:
            raise NotFoundError(f"Task {task_id} not found")
        return task

    @staticmethod
    def _get_user(user_id: str) -> User:
        user = User.objects(id=user_id).first()
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        return user

    # --------- CRUD ---------
    @staticmethod
    def list_tasks(
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        team_id: Optional[str] = None,
        assigned_to: Optional[str] = None,
    ) -> QuerySet:
        query: Dict = {}
        if status:
            query["status"] = status
        if team_id:
            query["team_id"] = team_id
        if assigned_to:
            user = TaskService._get_user(assigned_to)
            query["assigned_to"] = user

        skip = (page - 1) * page_size
        return Task.objects(**query).skip(skip).limit(page_size).order_by("-created_at")

    @staticmethod
    def create_task(
        title: str,
        description: str,
        assigned_by_id: str,
        team_id: str,
        assigned_to_ids: Optional[List[str]] = None,
        attachments: Optional[List[Dict]] = None,
        **extra,
    ) -> Task:
        assigned_by = TaskService._get_user(assigned_by_id)
        assigned_to = [TaskService._get_user(uid) for uid in (assigned_to_ids or [])]

        task = Task(
            title=title,
            description=description,
            assigned_by=assigned_by,
            assigned_to=assigned_to,
            team_id=team_id,
            **extra,
        )

        if attachments:
            task.attachments = [Attachment(**data) for data in attachments]

        task.save()
        return task

    @staticmethod
    def update_task(task_id: str, **data) -> Task:
        task = TaskService._get_task(task_id)

        if "assigned_to_ids" in data:
            task.assigned_to = [TaskService._get_user(uid) for uid in data.pop("assigned_to_ids")]

        if "assigned_by_id" in data:
            task.assigned_by = TaskService._get_user(data.pop("assigned_by_id"))

        attachments_data = data.pop("attachments", None)
        if attachments_data is not None:
            task.attachments = [Attachment(**att) for att in attachments_data]

        for attr, value in data.items():
            setattr(task, attr, value)

        task.save()
        return task

    @staticmethod
    def delete_task(task_id: str) -> None:
        task = TaskService._get_task(task_id)
        task.delete()



    @staticmethod
    def change_status(task_id: str, status_value: str) -> Task:
        task = TaskService._get_task(task_id)
        task.status = status_value
        task.save()
        return task

    @staticmethod
    def add_comment(task_id: str, user_id: str, text: str) -> Task:
        task = TaskService._get_task(task_id)
        user = TaskService._get_user(user_id)

        comment = Comment(user=user, text=text, created_at=datetime.utcnow())
        task.comments.append(comment)
        task.save()
        return task

    @staticmethod
    def add_attachment(task_id: str, attachment_data: Dict[str, str]) -> Task:
        if "name" not in attachment_data or "url" not in attachment_data:
            raise ValidationError("Attachment requires 'name' and 'url'")

        task = TaskService._get_task(task_id)
        task.attachments.append(Attachment(**attachment_data))
        task.save()
        return task

