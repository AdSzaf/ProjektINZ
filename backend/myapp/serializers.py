from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from .models import Project, Issue, Epic, Sprint
import re

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'role', 'password')

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value

    def validate_password(self, value):
        errors = []
        if len(value) < 8:
            errors.append("Password must be at least 8 characters.")
        if not re.search(r"[A-Z]", value):
            errors.append("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", value):
            errors.append("Password must contain at least one lowercase letter.")
        if not re.search(r"\d", value):
            errors.append("Password must contain at least one digit.")
        if not re.search(r"[!@#$%^&*]", value):
            errors.append("Password must contain at least one special character (!@#$%^&*).")
        if errors:
            raise serializers.ValidationError(errors)
        return value

    def create(self, validated_data):
        user = User(
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            email=validated_data['email'],
            username=validated_data['email'],
            role=validated_data['role'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data['email'], password=data['password'])
        if not user:
            raise serializers.ValidationError("Invalid credentials")
        data['user'] = user
        return data

class ProjectCreateSerializer(serializers.ModelSerializer):
    members = serializers.ListField(child=serializers.UUIDField(), required=False)

    class Meta:
        model = Project
        fields = [
            'name', 'key', 'description', 'methodology', 'lead', 'organization', 'members'
        ]
        extra_kwargs = {
            'lead': {'required': True},
            'organization': {'required': False},
        }

    def create(self, validated_data):
        members = validated_data.pop('members', [])
        project = super().create(validated_data)
        # Add lead as member if not already
        if project.lead and project.lead.id not in members:
            members.append(project.lead.id)
        # Add members to project
        from .models import ProjectMembership, User
        for user_id in members:
            user = User.objects.get(id=user_id)
            ProjectMembership.objects.get_or_create(user=user, project=project, defaults={'role': 'developer'})
        return project

class ProjectGetSerializer(serializers.ModelSerializer):
    lead = serializers.StringRelatedField()
    organization = serializers.StringRelatedField()

    class Meta:
        model = Project
        fields = ['id', 'key', 'name', 'lead', 'organization', 'description', 'methodology']
        
class IssueCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Issue
        fields = [
            'id', 'key', 'title', 'description', 'project', 'issue_type', 'epic', 'sprint',
            'reporter', 'assignee', 'priority', 'story_points',
            'original_estimate', 'remaining_estimate', 'status'
        ]

class EpicCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Epic
        fields = [
            'id', 'title', 'description', 'project', 'assignee', 'status', 'priority'
        ]

class SprintSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sprint
        fields = [
            'id', 'name', 'goal', 'start_date', 'end_date', 'status', 'project'
        ]