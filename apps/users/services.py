from typing import Dict, Optional, Tuple

from mongoengine.queryset import QuerySet

from apps.users.models import User
from apps.core.exceptions import NotFoundError, ConflictError, ValidationError
from apps.authentication.services import AuthService
from apps.teams.models import Team


class UserService:
    """Business logic cho user management (ngoài authentication)."""

    # ------------------------------------------------------------------ #
    # Helpers                                                            #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _get_user(user_id: str) -> User:
        user = User.objects(id=user_id).first()
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        return user

    @staticmethod
    def _get_team(team_id: Optional[str]) -> Optional[Team]:
        if not team_id:
            return None
        team = Team.objects(id=team_id).first()
        if not team:
            raise ValidationError(f"Team {team_id} not found")
        return team

    # ------------------------------------------------------------------ #
    # CRUD                                                               #
    # ------------------------------------------------------------------ #
    @staticmethod
    def list_users(
        page: int = 1,
        page_size: int = 20,
        role: Optional[str] = None,
        team_id: Optional[str] = None,
    ) -> Tuple[QuerySet, int]:
        query: Dict = {}
        if role:
            query["role"] = role
        if team_id:
            query["teamId"] = UserService._get_team(team_id)

        skip = (page - 1) * page_size
        qs = User.objects(**query).order_by("-created_at")
        total = qs.count()
        return qs.skip(skip).limit(page_size), total

    @staticmethod
    def get_user_by_id(user_id: str) -> User:
        return UserService._get_user(user_id)

    @staticmethod
    def update_user(user_id: str, update_data: Dict) -> User:
        user = UserService._get_user(user_id)

        if "email" in update_data:
            new_email = update_data["email"].lower()
            existing_user = User.objects(email=new_email).first()
            if existing_user and str(existing_user.id) != str(user.id):
                raise ConflictError(f"Email {new_email} is already in use")
            user.email = new_email
            update_data.pop("email")

        if "password" in update_data:
            user.password = AuthService.hash_password(update_data.pop("password"))

        if "teamId" in update_data:
            user.teamId = UserService._get_team(update_data.pop("teamId"))

        if "managerId" in update_data:
            manager_id = update_data.pop("managerId")
            user.managerId = UserService._get_user(manager_id) if manager_id else None

        for key, value in update_data.items():
            setattr(user, key, value)

        user.save()
        return user

    @staticmethod
    def delete_user(user_id: str) -> None:
        user = UserService._get_user(user_id)
        user.delete()
