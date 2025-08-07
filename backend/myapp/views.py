from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from .models import Project, IssueType, Epic, Sprint, User, Issue
from django.contrib.auth import get_user_model
from .serializers import (RegisterSerializer
                          , LoginSerializer
                          , ProjectCreateSerializer
                          , ProjectGetSerializer
                          , IssueCreateSerializer)


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

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def projects_view(request):
    if request.method == 'GET':
        user = request.user
        projects = user.projects.all().distinct()
        serializer = ProjectGetSerializer(projects, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        data = request.data.copy()
        if not data.get('lead'):
            data['lead'] = str(request.user.id)
        if not data.get('organization'):
            data['organization'] = None
        serializer = ProjectCreateSerializer(data=data)
        if serializer.is_valid():
            project = serializer.save()
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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_issue(request):
    data = request.data.copy()
    # Optionally, set reporter to request.user.id if not provided
    if not data.get('reporter'):
        data['reporter'] = str(request.user.id)
    serializer = IssueCreateSerializer(data=data)
    if serializer.is_valid():
        issue = serializer.save()
        return Response({'id': str(issue.id), 'key': issue.key, 'title': issue.title}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def global_issue_types(request):
    issue_types = IssueType.objects.all()
    data = [
        {'id': str(it.id), 'name': it.name, 'icon': it.icon, 'color': it.color}
        for it in issue_types
    ]
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def project_epics(request, project_id):
    epics = Epic.objects.filter(project_id=project_id)
    data = [
        {'id': str(e.id), 'name': e.title, 'key': e.id}
        for e in epics
    ]
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def project_sprints(request, project_id):
    sprints = Sprint.objects.filter(project_id=project_id)
    data = [
        {'id': str(s.id), 'name': s.name, 'status': s.status}
        for s in sprints
    ]
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def project_users(request, project_id):
    project = Project.objects.get(id=project_id)
    users = project.members.all()
    data = [
        {'id': str(u.id), 'name': f"{u.first_name} {u.last_name}", 'email': u.email}
        for u in users
    ]
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def project_issues(request, project_id):
    issues = Issue.objects.filter(project_id=project_id)
    serializer = IssueCreateSerializer(issues, many=True)
    return Response(serializer.data)