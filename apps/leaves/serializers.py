from rest_framework import fields as drf_fields, serializers as drf_serializers
from rest_framework_mongoengine import serializers as mongo_serializers
from rest_framework_mongoengine.fields import ReferenceField

from apps.leaves.models import Leave
from apps.users.models import User


class LeaveSerializer(mongo_serializers.DocumentSerializer):
    user = ReferenceField(read_only=True)
    approved_by = ReferenceField(read_only=True)

    user_id = drf_fields.CharField(write_only=True)
    approved_by_id = drf_fields.CharField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Leave
        fields = (
            'id',
            'user',
            'user_id',
            'type',
            'start_date',
            'end_date',
            'number_of_days',
            'reason',
            'status',
            'approved_by',
            'approved_by_id',
            'approved_at',
            'rejection_reason',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'user',
            'approved_by',
            'created_at',
            'updated_at',
        )

    def _get_user(self, user_id: str) -> User:
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist as exc:
            raise drf_serializers.ValidationError(
                {'detail': f'User with id {user_id} not found'}
            ) from exc

    def create(self, validated_data):
        user_id = validated_data.pop('user_id')
        approved_by_id = validated_data.pop('approved_by_id', None)

        validated_data['user'] = self._get_user(user_id)
        if approved_by_id:
            validated_data['approved_by'] = self._get_user(approved_by_id)

        leave = Leave(**validated_data)
        leave.save()
        return leave

    def update(self, instance, validated_data):
        user_id = validated_data.pop('user_id', None)
        if user_id:
            instance.user = self._get_user(user_id)

        approved_by_id = validated_data.pop('approved_by_id', None)
        if approved_by_id is not None:
            instance.approved_by = self._get_user(approved_by_id) if approved_by_id else None

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

