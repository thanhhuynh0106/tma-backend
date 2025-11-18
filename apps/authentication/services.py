import copy
import hashlib
from typing import Dict, Tuple, Optional

from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.exceptions import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from apps.users.models import User, Profile, LeaveBalanceData
from apps.teams.models import Team


class AuthService:
    """
    Business logic cho authentication (register, login, password operations).
    """

    # ------------------------------------------------------------------ #
    # Helpers                                                            #
    # ------------------------------------------------------------------ #
    @staticmethod
    def hash_password(raw_password: str) -> str:
        """
        Hash password bằng SHA256 (tạm thời thay thế bcrypt).
        Lưu ý: SHA256 không an toàn bằng bcrypt, chỉ dùng cho development.
        """
        if not raw_password:
            raise ValidationError("Password is required")
        # Dùng SHA256 thay vì bcrypt để tránh lỗi DLL trên Windows
        return hashlib.sha256(raw_password.encode("utf-8")).hexdigest()

    @staticmethod
    def verify_password(raw_password: str, hashed_password: str) -> bool:
        """
        Verify password với SHA256 hash.
        """
        if not hashed_password:
            return False
        # Hash password mới và so sánh với hash đã lưu
        new_hash = hashlib.sha256(raw_password.encode("utf-8")).hexdigest()
        return new_hash == hashed_password

    @staticmethod
    def generate_tokens(user: User) -> Dict[str, str]:
        refresh = RefreshToken.for_user(user)
        return {"refresh": str(refresh), "access": str(refresh.access_token)}

    @staticmethod
    def _get_user_by_email(email: str) -> User:
        user = User.objects(email=email.lower()).first()
        if not user:
            raise NotFoundError("Invalid credentials")
        return user

    @staticmethod
    def _get_user_by_id(user_id: str) -> User:
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

    @staticmethod
    def _build_leave_balance_map(leave_balance_data: Optional[Dict]) -> Dict[str, LeaveBalanceData]:
        if not leave_balance_data:
            return {}
        result = {}
        for year, data in leave_balance_data.items():
            result[str(year)] = LeaveBalanceData(**data)
        return result

    # ------------------------------------------------------------------ #
    # Public API                                                         #
    # ------------------------------------------------------------------ #
    @staticmethod
    def register_user(payload: Dict) -> Tuple[User, Dict[str, str]]:
        """
        Tạo user mới + trả về JWT tokens.
        payload yêu cầu các field:
            - email, password, role
            - profile (fullName, employeeID, ...)
            - optional: teamId, managerId, leaveBalance
        """
        data = copy.deepcopy(payload)
        email = data.pop("email", "").lower()
        password = data.pop("password", None)
        profile_data = data.pop("profile", None)
        team_id = data.pop("teamId", data.pop("team_id", None))
        manager_id = data.pop("managerId", data.pop("manager_id", None))
        leave_balance_data = data.pop("leaveBalance", data.pop("leave_balance", None))

        if not email:
            raise ValidationError("Email is required")
        if not profile_data:
            raise ValidationError("Profile is required")
        if User.objects(email=email).first():
            raise ConflictError(f"Email {email} already exists")

        profile = Profile(**profile_data)
        user = User(
            email=email,
            password=AuthService.hash_password(password),
            profile=profile,
            teamId=AuthService._get_team(team_id),
            managerId=AuthService._get_user_by_id(manager_id) if manager_id else None,
            **data,
        )
        user.leaveBalance = AuthService._build_leave_balance_map(leave_balance_data)
        user.save()

        tokens = AuthService.generate_tokens(user)
        return user, tokens

    @staticmethod
    def login(email: str, password: str) -> Tuple[User, Dict[str, str]]:
        """
        Xác thực user bằng email/password và trả về tokens.
        """
        if not email or not password:
            raise ValidationError("Email and password are required")

        user = AuthService._get_user_by_email(email)
        if not AuthService.verify_password(password, user.password):
            raise ValidationError("Invalid credentials")

        tokens = AuthService.generate_tokens(user)
        return user, tokens

    @staticmethod
    def change_password(user_id: str, current_password: str, new_password: str) -> None:
        """
        Đổi password với xác thực current_password.
        """
        user = AuthService._get_user_by_id(user_id)
        if not AuthService.verify_password(current_password, user.password):
            raise ValidationError("Current password is incorrect")

        user.password = AuthService.hash_password(new_password)
        user.save()

    @staticmethod
    def force_reset_password(user_id: str, new_password: str) -> None:
        """
        Reset password không cần current_password (ví dụ: admin reset).
        """
        user = AuthService._get_user_by_id(user_id)
        user.password = AuthService.hash_password(new_password)
        user.save()

    @staticmethod
    def deactivate_user(user_id: str) -> User:
        """
        Vô hiệu hóa user (ví dụ: khi nghỉ việc).
        """
        user = AuthService._get_user_by_id(user_id)
        user.isActive = False
        user.save()
        return user

    @staticmethod
    def reactivate_user(user_id: str) -> User:
        """
        Kích hoạt lại user.
        """
        user = AuthService._get_user_by_id(user_id)
        user.isActive = True
        user.save()
        return user

