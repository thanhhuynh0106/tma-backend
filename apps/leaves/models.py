from django.db import models
from mongoengine import Document, fields
from apps.core.models import BaseDocument
from apps.users.models import User


class Leave(BaseDocument):
    LEAVE_TYPE_CHOICES = [
        ('sick', 'Sick'),
        ('vacation', 'Vacation'),
        ('personal', 'Personal'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = fields.ReferenceField(User, required=True)
    type = fields.StringField(choices=LEAVE_TYPE_CHOICES, required=True)
    start_date = fields.DateTimeField(required=True)
    end_date = fields.DateTimeField(required=True)
    number_of_days = fields.IntField(required=True)
    reason = fields.StringField()
    status = fields.StringField(choices=STATUS_CHOICES, default='pending')
    approved_by = fields.ReferenceField(User)
    approved_at = fields.DateTimeField()
    rejection_reason = fields.StringField()

    meta = {
        'collection': 'leaves',
        'indexes': [
            'user',
            'status',
        ],
        'ordering': ['-created_at'],
    }
    
