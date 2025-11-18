from django.db import models
from mongoengine import Document, fields
from apps.core.models import BaseDocument
from apps.users.models import User


class Notification(BaseDocument):
    NOTIFICATION_TYPES = [
        ('task_assigned', 'Task Assigned'),
        ('task_updated', 'Task Updated'),
        ('comment_added', 'Comment Added'),
        ('deadline_reminder', 'Deadline Reminder'),
    ]

    user = fields.ReferenceField(User, required=True)
    type = fields.StringField(choices=NOTIFICATION_TYPES, required=True)
    title = fields.StringField(required=True)
    message = fields.StringField(required=True)
    related_id = fields.ObjectIdField(default=None)
    is_read = fields.BooleanField(default=False)

    meta = {
        'collection': 'notifications',
        'indexes': [
            'user',
            'is_read',
        ],
        'ordering': ['-created_at'],
    }