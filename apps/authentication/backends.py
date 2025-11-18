"""
Custom JWT Authentication Backend cho MongoDB User model.
"""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed, InvalidToken
from rest_framework_simplejwt.settings import api_settings
from apps.users.models import User


class MongoJWTAuthentication(JWTAuthentication):
    """
    Custom JWT Authentication cho MongoDB User model.
    Override get_user() để query MongoDB User thay vì Django User.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Không dùng Django's get_user_model(), dùng MongoDB User trực tiếp
        self.user_model = User
    
    def get_user(self, validated_token):
        """
        Lấy user từ MongoDB dựa trên user_id trong token.
        """
        try:
            user_id = validated_token[api_settings.USER_ID_CLAIM]
        except KeyError:
            raise InvalidToken("Token contained no recognizable user identification")
        
        try:
            # Query MongoDB User với ObjectId string
            user = User.objects(id=user_id).first()
            if not user:
                raise AuthenticationFailed("User not found", code="user_not_found")
        except Exception as e:
            raise AuthenticationFailed("User not found", code="user_not_found") from e
        
        # Kiểm tra user có active không (dùng isActive thay vì is_active)
        if api_settings.CHECK_USER_IS_ACTIVE and not user.isActive:
            raise AuthenticationFailed("User is inactive", code="user_inactive")
        
        return user

