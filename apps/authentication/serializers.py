from rest_framework import serializers, fields as drf_fields

from apps.users.models import User
from apps.users.serializers import ProfileSerializer, LeaveBalanceDataSerializer


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=6)
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES)
    profile = ProfileSerializer()
    teamId = serializers.CharField(required=False, allow_null=True)
    managerId = serializers.CharField(required=False, allow_null=True)
    leaveBalance = drf_fields.DictField(child=LeaveBalanceDataSerializer(), required=False)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class ChangePasswordSerializer(serializers.Serializer):
    user_id = serializers.CharField()
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=6)


class ForceResetPasswordSerializer(serializers.Serializer):
    user_id = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=6)

