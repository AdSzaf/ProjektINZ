from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from .models import Project, IssueType, Epic, Sprint, User, Issue, WorkflowStatus
from django.contrib.auth import get_user_model
from .serializers import (RegisterSerializer
                          , LoginSerializer
                          , ProjectCreateSerializer
                          , ProjectGetSerializer
                          , IssueCreateSerializer
                          , EpicCreateSerializer
                          , SprintSerializer)


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
        if 'members' in data and isinstance(data['members'], str):
            import json
            data['members'] = json.loads(data['members'])
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
    print("ISSUE TYPES SENT TO FRONTEND:", data)  # <-- Add this log
    return Response(data)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def project_epics(request, project_id):
    if request.method == 'GET':
        epics = Epic.objects.filter(project_id=project_id)
        serializer = EpicCreateSerializer(epics, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        data = request.data.copy()
        data['project'] = project_id
        serializer = EpicCreateSerializer(data=data)
        if serializer.is_valid():
            epic = serializer.save()
            return Response(EpicCreateSerializer(epic).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
    print(f"Project {project_id} members: {[str(u) for u in users]}")
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
    print("ISSUES SENT TO FRONTEND:", serializer.data)
    return Response(serializer.data)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_issue_status(request, issue_id):
    try:
        issue = Issue.objects.get(id=issue_id)
    except Issue.DoesNotExist:
        return Response({'detail': 'Issue not found.'}, status=status.HTTP_404_NOT_FOUND)
    status_value = request.data.get('status')
    # Allow any status that exists in WorkflowStatus for this project
    valid_statuses = WorkflowStatus.objects.filter(project=issue.project).values_list('category', flat=True)
    print(valid_statuses)
    if status_value not in valid_statuses:
        return Response({'detail': 'Invalid status.'}, status=status.HTTP_400_BAD_REQUEST)
    issue.status = status_value
    issue.save()
    return Response({'id': str(issue.id), 'status': issue.status})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def project_workflow_statuses(request, project_id):
    statuses = WorkflowStatus.objects.filter(project_id=project_id).order_by('order')
    if not statuses.exists():
        # Create default columns if none exist
        WorkflowStatus.objects.bulk_create([
            WorkflowStatus(name='To Do', project_id=project_id, category='to_do', color='#6c757d', order=0),
            WorkflowStatus(name='In Progress', project_id=project_id, category='in_progress', color='#ffc107', order=1),
            WorkflowStatus(name='Done', project_id=project_id, category='done', color='#28a745', order=2),
        ])
        statuses = WorkflowStatus.objects.filter(project_id=project_id).order_by('order')
    data = [
        {
            'id': s.category,  # Use category as the column id for consistency
            'name': s.name,
            'category': s.category,
            'color': s.color,
            'order': s.order
        }
        for s in statuses
    ]
    return Response(data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_workflow_status(request, project_id):
    name = request.data.get('name')
    color = request.data.get('color', '#6f42c1')
    order = WorkflowStatus.objects.filter(project_id=project_id).count()
    category = name.lower().replace(' ', '_')
    status = WorkflowStatus.objects.create(
        name=name,
        project_id=project_id,
        category=category,
        color=color,
        order=order
    )
    return Response({
        'id': status.id,
        'name': status.name,
        'category': status.category,
        'color': status.color,
        'order': status.order
    }, status=201)

@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_issue(request, issue_id):
    try:
        issue = Issue.objects.get(id=issue_id)
    except Issue.DoesNotExist:
        return Response({'detail': 'Issue not found.'}, status=status.HTTP_404_NOT_FOUND)
    if request.method == 'GET':
        serializer = IssueCreateSerializer(issue)
        return Response(serializer.data)
    elif request.method == 'PATCH':
        serializer = IssueCreateSerializer(issue, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_workflow_status(request, project_id, category):
    try:
        status_obj = WorkflowStatus.objects.get(project_id=project_id, category=category)
    except WorkflowStatus.DoesNotExist:
        return Response({'detail': 'Column not found.'}, status=status.HTTP_404_NOT_FOUND)
    # Delete all issues in this column/status
    Issue.objects.filter(project_id=project_id, status=category).delete()
    status_obj.delete()
    return Response({'detail': 'Column and its issues deleted.'}, status=status.HTTP_204_NO_CONTENT)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def project_sprints(request, project_id):
    if request.method == 'GET':
        status_filter = request.GET.get('status')
        sprints = Sprint.objects.filter(project_id=project_id)
        if status_filter:
            sprints = sprints.filter(status=status_filter)
        serializer = SprintSerializer(sprints, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        data = request.data.copy()
        data['project'] = project_id
        serializer = SprintSerializer(data=data)
        if serializer.is_valid():
            sprint = serializer.save()
            return Response(SprintSerializer(sprint).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_sprint(request, sprint_id):
    try:
        sprint = Sprint.objects.get(id=sprint_id)
    except Sprint.DoesNotExist:
        return Response({'detail': 'Sprint not found.'}, status=status.HTTP_404_NOT_FOUND)
    serializer = SprintSerializer(sprint, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_short(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
    initials = (user.first_name[:1] if user.first_name else '') + (user.last_name[:1] if user.last_name else '')
    return Response({
        'id': str(user.id),
        'first_name': user.first_name,
        'last_name': user.last_name,
        'initials': initials.upper(),
        'name': f"{user.first_name} {user.last_name}".strip()
    })

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_user_settings(request):
    user = request.user
    data = request.data
    # Update fields if present
    if 'first_name' in data:
        user.first_name = data['first_name']
    if 'last_name' in data:
        user.last_name = data['last_name']
    if 'email' in data:
        user.email = data['email']
    if 'role' in data:
        user.role = data['role']
    # Add department if you have it in your model
    user.save()
    return Response({'detail': 'Profile updated successfully!'}, status=status.HTTP_200_OK)