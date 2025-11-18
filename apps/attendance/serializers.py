from rest_framework import fields as drf_fields, serializers as drf_serializers
from rest_framework_mongoengine import serializers as mongo_serializers
from rest_framework_mongoengine.fields import ReferenceField
from apps.attendance.models import Attendance, Location
from apps.users.models import User


class LocationSerializer(mongo_serializers.EmbeddedDocumentSerializer):
    class Meta:
        model = Location
        fields = ('lat', 'lng')


class AttendanceSerializer(mongo_serializers.DocumentSerializer):
    location = LocationSerializer()
    user = ReferenceField(read_only=True)
    user_id = drf_fields.CharField(write_only=True)

    class Meta:
        model = Attendance
        fields = (
            'id',
            'user',
            'user_id',
            'date',
            'clock_in',
            'clock_out',
            'location',
            'status',
            'work_hours',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')

    def _get_user(self, user_id: str) -> User:
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist as exc:
            raise drf_serializers.ValidationError(
                {'user_id': f'User {user_id} not found'}
            ) from exc

    def create(self, validated_data):
        user_id = validated_data.pop('user_id')
        validated_data['user'] = self._get_user(user_id)
        attendance = Attendance(**validated_data)
        attendance.save()
        return attendance

    def update(self, instance, validated_data):
        user_id = validated_data.pop('user_id', None)
        if user_id:
            instance.user = self._get_user(user_id)

        location_data = validated_data.pop('location', None)
        if location_data:
            instance.location = Location(**location_data)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

