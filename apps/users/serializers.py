import hashlib
from rest_framework import fields as drf_fields
from apps.users.models import User, Profile, LeaveBalanceData
from rest_framework_mongoengine import serializers
from rest_framework_mongoengine.fields import ReferenceField


class LeaveBalanceDataSerializer(serializers.EmbeddedDocumentSerializer):
    class Meta:
        model = LeaveBalanceData
        fields = ('total', 'used', 'remaining')
    
class ProfileSerializer(serializers.EmbeddedDocumentSerializer):
    class Meta:
        model = Profile
        fields = ('fullName', 'avatar', 'phone', 'department', 'position', 'employeeID')


class UserSerializer(serializers.DocumentSerializer):
    profile = ProfileSerializer()
    leaveBalance = drf_fields.DictField(child=LeaveBalanceDataSerializer(), required=False)

    teamId = ReferenceField(read_only=True)
    managerId = ReferenceField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'role', 'profile', 'teamId', 'managerId', 'isActive', 'leaveBalance', 'created_at', 'updated_at')

        extra_kwargs = {
            'password': {'write_only': True},
            'id': {'read_only': True},
        }

    
    def create(self, validated_data):
        profile_data = validated_data.pop('profile')
        password = validated_data.pop('password')

        profile_instance = Profile(**profile_data)
        # Dùng SHA256 thay vì bcrypt để tránh lỗi DLL trên Windows
        hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()

        user = User.objects.create(
            **validated_data,
            profile=profile_instance,
            password=hashed_password
        )

        return user
    
    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)
        if profile_data:
            # Với rest_framework_mongoengine, profile_data có thể là dict hoặc Profile instance
            # Nếu là dict, update từng field của profile hiện tại
            if isinstance(profile_data, dict):
                # Update từng field của profile hiện tại
                for key, value in profile_data.items():
                    if hasattr(instance.profile, key):
                        setattr(instance.profile, key, value)
            elif isinstance(profile_data, Profile):
                # Nếu là Profile instance, gán trực tiếp
                instance.profile = profile_data
            else:
                # Nếu là dict từ serializer validation, tạo Profile instance mới
                instance.profile = Profile(**profile_data)
        
        password = validated_data.pop('password', None)
        if password:
            # Dùng SHA256 thay vì bcrypt để tránh lỗi DLL trên Windows
            hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
            instance.password = hashed_password

        leave_balance_data = validated_data.pop('leaveBalance', None)
        if leave_balance_data:
            for year, balance in leave_balance_data.items():
                instance.leaveBalance[year] = LeaveBalanceData(**balance)

        # Xử lý các field khác
        for key, value in validated_data.items():
            setattr(instance, key, value)
        
        instance.save()
        return instance
    
    

