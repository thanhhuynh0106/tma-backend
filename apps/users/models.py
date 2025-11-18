from django.db import models
from mongoengine import Document, StringField, EmailField, BooleanField, DateTimeField, EmbeddedDocument, fields
from mongoengine.fields import ReferenceField
from datetime import datetime
from apps.core.models import BaseDocument


class Profile(EmbeddedDocument):
    fullName = fields.StringField(required=True, min_length=3)
    avatar = fields.StringField(default=None)
    phone = fields.StringField(default=None)
    department = fields.StringField(default=None)
    position = fields.StringField(default=None)

    employeeID = fields.StringField(required=True, unique=True)


class LeaveBalanceData(EmbeddedDocument):
    total = fields.IntField(default=12)
    used = fields.IntField(default=0)
    remaining = fields.IntField(default=12)


class User(BaseDocument):
    email = fields.StringField(required=True, unique=True, lowercase=True)
    password = fields.StringField(required=True, min_length=6, select=False)
    
    ROLE_CHOICES = ('hr_manager', 'team_lead', 'employee')
    role = fields.StringField(required=True, choices=ROLE_CHOICES, default='employee')
    
    profile = fields.EmbeddedDocumentField(Profile, required=True)
    teamId = fields.ReferenceField('Team', default=None) 
    managerId = fields.ReferenceField('self', default=None) 
    
    isActive = fields.BooleanField(default=True)
    
    leaveBalance = fields.MapField(fields.EmbeddedDocumentField(LeaveBalanceData))
    
    meta = {
        'collection': 'users', 
        'indexes': ['email', 'profile.employeeID'],
        'strict': False
    }
    
    # Django authentication compatibility properties
    @property
    def is_authenticated(self):
        """
        Always return True for authenticated users.
        Required by Django REST Framework's IsAuthenticated permission.
        """
        return True
    
    @property
    def is_anonymous(self):
        """
        Always return False for authenticated users.
        Required by Django authentication system.
        """
        return False
    
    @property
    def is_active(self):
        """
        Map isActive to is_active for Django compatibility.
        """
        return self.isActive
    
    def get_username(self):
        """
        Return the username (email) for this User.
        Required by Django authentication system.
        """
        return self.email