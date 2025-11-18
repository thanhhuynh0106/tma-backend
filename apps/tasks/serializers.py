from rest_framework import fields as drf_fields
from rest_framework_mongoengine import serializers
from rest_framework_mongoengine.fields import ReferenceField
from .models import Task, Attachment, Comment
from apps.users.models import User


class AttachmentSerializer(serializers.EmbeddedDocumentSerializer):
    class Meta:
        model = Attachment
        fields = ('name', 'url')


class CommentSerializer(serializers.EmbeddedDocumentSerializer):
    user_id = drf_fields.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ('user_id', 'text', 'created_at')
        read_only_fields = ('created_at', 'user_id')
    
    def get_user_id(self, obj):
        """Return user id as string"""
        if obj.user:
            return str(obj.user.id)
        return None

class TaskSerializer(serializers.DocumentSerializer):
    attachments = AttachmentSerializer(many=True, required=False)
    comments = CommentSerializer(many=True, required=False)

    assigned_to = drf_fields.ListField(child=ReferenceField(read_only=True), read_only=True)
    assigned_by = ReferenceField(read_only=True)
    assigned_to_ids = drf_fields.ListField(
        child=drf_fields.CharField(),
        write_only=True,
        required=False,
        allow_empty=True,
    )
    assigned_by_id = drf_fields.CharField(write_only=True, required=False)

    class Meta:
        model = Task
        fields = (
            'id', 'title', 'description', 'status', 'priority',
            'assigned_to', 'assigned_to_ids', 'assigned_by', 'assigned_by_id',
            'team_id', 'start_date', 'due_date', 'progress', 
            'attachments', 'comments', 'tags',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'assigned_by')

    def to_internal_value(self, data):
        # Map assigned_to thành assigned_to_ids nếu có
        if isinstance(data, dict):
            if 'assigned_to' in data and 'assigned_to_ids' not in data:
                data = data.copy()
                assigned_to_value = data.pop('assigned_to', [])
                if assigned_to_value:
                    data['assigned_to_ids'] = assigned_to_value
        elif hasattr(data, 'get'):
            # QueryDict hoặc tương tự
            if 'assigned_to' in data and 'assigned_to_ids' not in data:
                assigned_to_value = data.get('assigned_to', [])
                if assigned_to_value:
                    # Tạo dict mới với assigned_to_ids
                    new_data = {}
                    for key in data:
                        if key == 'assigned_to':
                            new_data['assigned_to_ids'] = data.getlist(key) if hasattr(data, 'getlist') else data[key]
                        else:
                            new_data[key] = data.getlist(key) if hasattr(data, 'getlist') else data[key]
                    data = new_data
        return super().to_internal_value(data)
    
    def create(self, validated_data):
        attachments_data = validated_data.pop('attachments', [])
        comments_data = validated_data.pop('comments', [])
        
        # Xử lý assigned_by_id
        assigned_by_id = validated_data.pop('assigned_by_id', None)
        if assigned_by_id:
            assigned_by = User.objects.get(id=assigned_by_id)
            validated_data['assigned_by'] = assigned_by
        elif self.context.get('request') and hasattr(self.context['request'], 'user'):
            # Nếu không có assigned_by_id, dùng request.user
            validated_data['assigned_by'] = self.context['request'].user
        else:
            raise serializers.ValidationError({'assigned_by_id': 'assigned_by_id is required or user must be authenticated'})
        
        # Xử lý assigned_to_ids (đã được map từ assigned_to trong to_internal_value nếu có)
        assigned_to_ids = validated_data.pop('assigned_to_ids', None)
        
        # Kiểm tra xem có được truyền vào không (trong initial_data)
        was_provided = 'assigned_to_ids' in self.initial_data or 'assigned_to' in self.initial_data
        
        # Nếu không có trong validated_data nhưng có trong initial_data, lấy từ đó
        if not assigned_to_ids and was_provided:
            if 'assigned_to' in self.initial_data:
                assigned_to_ids = self.initial_data.get('assigned_to', [])
            elif 'assigned_to_ids' in self.initial_data:
                assigned_to_ids = self.initial_data.get('assigned_to_ids', [])
        
        # Chỉ xử lý nếu assigned_to_ids thực sự có giá trị
        if assigned_to_ids and len(assigned_to_ids) > 0:
            assigned_to = []
            for uid in assigned_to_ids:
                try:
                    user = User.objects.get(id=uid)
                    assigned_to.append(user)
                except User.DoesNotExist:
                    raise serializers.ValidationError({'assigned_to': f'User with id {uid} not found'})
            validated_data['assigned_to'] = assigned_to
        # Nếu không có assigned_to_ids hoặc là empty list, không set (để model dùng default)

        task = Task.objects.create(**validated_data)

        if attachments_data:
            task.attachments = [Attachment(**data) for data in attachments_data]

        if comments_data:
            for data in comments_data:
                user_instance = User.objects.get(id=data.pop('user'))
                task.comments.append(Comment(user=user_instance, **data))
        
        task.save()
        return task
    

    def update(self, instance, validated_data):
        attachments_data = validated_data.pop('attachments', None)
        comments_data = validated_data.pop('comments', None)
        
        # Xử lý assigned_by_id nếu có
        assigned_by_id = validated_data.pop('assigned_by_id', None)
        if assigned_by_id:
            assigned_by = User.objects.get(id=assigned_by_id)
            instance.assigned_by = assigned_by
        
        # Xử lý assigned_to_ids (đã được map từ assigned_to trong to_internal_value nếu có)
        assigned_to_ids = validated_data.pop('assigned_to_ids', None)
        
        if assigned_to_ids is not None:
            assigned_to = []
            for uid in assigned_to_ids:
                try:
                    user = User.objects.get(id=uid)
                    assigned_to.append(user)
                except User.DoesNotExist:
                    raise serializers.ValidationError({'assigned_to': f'User with id {uid} not found'})
            instance.assigned_to = assigned_to

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if attachments_data is not None:
            instance.attachments = [Attachment(**data) for data in attachments_data]

        if comments_data is not None:
            instance.comments = []
            for data in comments_data:
                user_instance = User.objects.get(id=data.pop('user'))
                instance.comments.append(Comment(user=user_instance, **data))

        instance.save()
        return instance