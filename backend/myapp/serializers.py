from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from .utils import send_issue_assignment_email
from .models import Project, Issue, Epic, Sprint, Tag, WorkLog, User, Comment
import re

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'role', 'password', 'is_premium', 'premium_until')

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
    password = serializers.CharField()

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        User = get_user_model()

        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid credentials.")

        if not user_obj.is_active:
            raise serializers.ValidationError(
                "Account not activated. Please check your email for the activation link."
            )

        user = authenticate(username=email, password=password)
        if not user:
            raise serializers.ValidationError("Invalid credentials.")

        data['user'] = user
        return data

class ProjectCreateSerializer(serializers.ModelSerializer):
    members = serializers.ListField(child=serializers.UUIDField(), required=False)

    class Meta:
        model = Project
        fields = [
            'name', 'key', 'description', 'methodology', 'lead', 'organization', 'members', 'github_repo_url', 'github_repo_full_name'
        ]
        extra_kwargs = {
            'lead': {'required': False},
            'organization': {'required': False},
            'github_repo_url': {'required': False}, 
            'github_repo_full_name': {'required': False},
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
        fields = ['id', 'key', 'name', 'lead', 'organization', 'description', 'methodology', 'github_repo_url', 'github_repo_full_name']

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'color', 'project']

class TagCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['name', 'color', 'project']
    
    def validate(self, data):
        if Tag.objects.filter(name=data['name'], project=data['project']).exists():
            raise serializers.ValidationError("A tag with this name already exists in this project.")
        return data

class IssueCreateSerializer(serializers.ModelSerializer):
    tags = serializers.ListField(
        child=serializers.UUIDField(), 
        required=False, 
        allow_empty=True,
        write_only=True
    )
    
    class Meta:
        model = Issue
        fields = [
            'id', 'key', 'title', 'description', 'project', 'issue_type', 'epic', 'sprint',
            'reporter', 'assignee', 'priority', 'story_points',
            'original_estimate', 'remaining_estimate', 'status', 'tags'
        ]
    
    def create(self, validated_data):
        tags_data = validated_data.pop('tags', [])
        issue = super().create(validated_data)
        
        if tags_data:
            tag_objects = Tag.objects.filter(id__in=tags_data, project=issue.project)
            issue.tags.set(tag_objects)
        
        if issue.assignee:
            send_issue_assignment_email(issue, issue.assignee)
        
        return issue
    
    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags', None)
        old_assignee = instance.assignee
        issue = super().update(instance, validated_data)
        
        if tags_data is not None:
            tag_objects = Tag.objects.filter(id__in=tags_data, project=issue.project)
            issue.tags.set(tag_objects)
        
        if issue.assignee and issue.assignee != old_assignee:
            send_issue_assignment_email(issue, issue.assignee)

        return issue

class IssueSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    
    class Meta:
        model = Issue
        fields = [
            'id', 'key', 'title', 'description', 'project', 'issue_type', 'epic', 'sprint',
            'reporter', 'assignee', 'priority', 'story_points',
            'original_estimate', 'remaining_estimate', 'status',
            'resolved_at', 'created_at', 'tags'
        ]
        read_only_fields = ['resolved_at']

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

class WorkLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    issue_key = serializers.CharField(source='issue.key', read_only=True)

    class Meta:
        model = WorkLog
        fields = [
            'id', 'user', 'user_name', 'issue', 'issue_key',
            'project', 'date', 'minutes', 'description', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'user_name', 'issue_key']

class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.username', read_only=True)
    class Meta:
        model = Comment
        fields = ['id', 'issue', 'author', 'author_name', 'content', 'created_at', 'updated_at']
        read_only_fields = ['id', 'author_name', 'created_at', 'updated_at']