from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from .serializers import RegisterSerializer, LoginSerializer, ProjectCreateSerializer, ProjectGetSerializer
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model

@api_view(['POST'])
def register_user(request):
    """Register a new user"""
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def login_user(request):
    """Login user and return token"""
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    serializer = RegisterSerializer(request.user)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_project(request):
    data = request.data.copy()
    if not data.get('lead'):
        data['lead'] = str(request.user.id)
    # Only set organization if present
    if not data.get('organization'):
        data['organization'] = None
    serializer = ProjectCreateSerializer(data=data)
    if serializer.is_valid():
        project = serializer.save()
        # Ensure the lead is a member
        from .models import ProjectMembership, User
        lead_user = User.objects.get(id=data['lead'])
        ProjectMembership.objects.get_or_create(user=lead_user, project=project, defaults={'role': 'developer'})
        return Response({'id': str(project.id), 'key': project.key, 'name': project.name}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_users(request):
    User = get_user_model()
    users = User.objects.all()
    data = [
        {
            'id': str(u.id),
            'first_name': u.first_name,
            'last_name': u.last_name,
            'email': u.email,
        }
        for u in users
    ]
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_projects(request):
    user = request.user
    # Projects where user is a member or lead
    projects = user.projects.all().distinct()
    serializer = ProjectGetSerializer(projects, many=True)
    return Response(serializer.data)