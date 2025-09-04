from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from .models import Project, IssueType, Epic, Sprint, User, Issue, WorkflowStatus
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from .serializers import (RegisterSerializer
                          , LoginSerializer
                          , ProjectCreateSerializer
                          , ProjectGetSerializer
                          , IssueCreateSerializer
                          , EpicCreateSerializer
                          , SprintSerializer
                          , IssueSerializer)
# In-memory status store (no DB changes). Keys: project_id -> { user_id -> { 'status': str, 'updated_at': datetime } }
ALLOWED_MEMBER_STATUSES = {'active', 'busy', 'away', 'offline'}
MEMBER_STATUS_STORE = {}

def _get_member_status(project_id, user_id, default='active'):
    project_map = MEMBER_STATUS_STORE.get(str(project_id))
    if not project_map:
        return default
    data = project_map.get(str(user_id))
    if not data:
        return default
    status_value = data.get('status')
    return status_value if status_value in ALLOWED_MEMBER_STATUSES else default

def _set_member_status(project_id, user_id, status_value):
    if status_value not in ALLOWED_MEMBER_STATUSES:
        raise ValueError('Invalid status')
    key = str(project_id)
    if key not in MEMBER_STATUS_STORE:
        MEMBER_STATUS_STORE[key] = {}
    MEMBER_STATUS_STORE[key][str(user_id)] = {
        'status': status_value,
        'updated_at': timezone.now()
    }



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
    issues = Issue.objects.filter(project=project)
    sprints = Sprint.objects.filter(project=project, status='active')
    active_sprint = sprints.first() if sprints.exists() else None

    data = []
    for u in users:
        assigned_issues = issues.filter(assignee=u).count()
        completed_issues = issues.filter(assignee=u, status__iexact='done').count()
        # Workload: percent of assigned issues that are not done
        workload = 0
        if assigned_issues:
            open_issues = issues.filter(assignee=u).exclude(status__iexact='done').count()
            workload = int((open_issues / assigned_issues) * 100)
        # Current sprint: count of issues assigned in active sprint
        current_sprint_issues = 0
        if active_sprint:
            current_sprint_issues = issues.filter(assignee=u, sprint=active_sprint).count()
        data.append({
            'id': str(u.id),
            'name': f"{u.first_name} {u.last_name}",
            'email': u.email,
            'first_name': u.first_name,
            'last_name': u.last_name,
            'role': u.role,
            'status': _get_member_status(project_id, u.id, default='active'),
            'location': '',  # Add if you have this field
            'timezone': '',  # Add if you have this field
            'joined_at': '', # Add if you have this field
            'assigned_issues': assigned_issues,
            'completed_issues': completed_issues,
            'workload': workload,
            'current_sprint': current_sprint_issues,
            'skills': [],    # Add if you have this field
            'bio': '',       # Add if you have this field
            'recent_activity': [], # Add if you want to implement
            'social_links': {},    # Add if you want to implement
        })
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def project_member_statuses(request, project_id):
    # Return map of user_id -> status for given project
    try:
        Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return Response({'detail': 'Project not found.'}, status=status.HTTP_404_NOT_FOUND)
    project_map = MEMBER_STATUS_STORE.get(str(project_id), {})
    # Only include users that are members of the project
    members = Project.objects.get(id=project_id).members.values_list('id', flat=True)
    result = {}
    for uid in members:
        result[str(uid)] = _get_member_status(project_id, uid, default='active')
    return Response(result)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_project_member_status(request, project_id, user_id):
    # Allow setting status for a member; simple for localhost projects
    status_value = (request.data.get('status') or '').strip().lower()
    if status_value not in ALLOWED_MEMBER_STATUSES:
        return Response({'detail': 'Invalid status.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return Response({'detail': 'Project not found.'}, status=status.HTTP_404_NOT_FOUND)
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
    # Only allow users to update their own status
    if str(request.user.id) != str(user.id):
        return Response({'detail': 'You can only update your own status.'}, status=status.HTTP_403_FORBIDDEN)
    # Ensure the user is a project member
    if not project.members.filter(id=user.id).exists():
        return Response({'detail': 'User is not a member of this project.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        _set_member_status(project_id, user_id, status_value)
    except ValueError:
        return Response({'detail': 'Invalid status.'}, status=status.HTTP_400_BAD_REQUEST)
    return Response({'detail': 'Status updated.', 'user': str(user_id), 'status': status_value})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def project_invite(request, project_id):
    """Invite/add an existing user (by email) to the project immediately.
    Does not change models or handle email workflows. If the user exists, they are added.
    """
    email = request.data.get('email')
    role = (request.data.get('role') or 'developer').strip().lower()
    if not email:
        return Response({'detail': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return Response({'detail': 'Project not found.'}, status=status.HTTP_404_NOT_FOUND)
    try:
        user = User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        return Response({'detail': 'User with this email was not found.'}, status=status.HTTP_404_NOT_FOUND)

    # Map incoming roles to ProjectMembership choices
    role_map = {
        'product-manager': 'product_owner',
        'product_manager': 'product_owner',
        'product owner': 'product_owner',
        'scrum-master': 'scrum_master',
        'scrum_master': 'scrum_master',
        'qa': 'tester',
        'tester': 'tester',
        'designer': 'designer',
        'developer': 'developer',
        # Fallback mappings
        'devops': 'developer',
        'admin': 'developer',
    }
    membership_role = role_map.get(role, 'developer')

    from .models import ProjectMembership
    membership, created = ProjectMembership.objects.get_or_create(
        user=user,
        project=project,
        defaults={'role': membership_role}
    )

    # If already exists and a different valid role provided, update it
    if not created and membership.role != membership_role and membership_role in {
        'product_owner', 'scrum_master', 'developer', 'designer', 'tester'
    }:
        membership.role = membership_role
        membership.save()

    return Response({
        'detail': 'Member added to project.' if created else 'Member already in project. Role updated.' if membership.role == membership_role else 'Member already in project.',
        'added': created,
        'user': {
            'id': str(user.id),
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
        },
        'role': membership.role,
    }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def project_issues(request, project_id):
    issues = Issue.objects.filter(project_id=project_id)
    serializer = IssueSerializer(issues, many=True)
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
     # Set resolved_at if moving to 'done', clear if moving out of 'done'
    if status_value == 'done' and issue.status != 'done':
        issue.resolved_at = timezone.now()
    elif status_value != 'done':
        issue.resolved_at = None
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

@api_view(['GET', 'PATCH', 'DELETE'])
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
    elif request.method == 'DELETE':
        issue.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sprint_burndown(request, sprint_id):
    sprint = Sprint.objects.get(id=sprint_id)
    issues = Issue.objects.filter(sprint=sprint)
    total_points = sum(i.story_points or 0 for i in issues)
    days = (sprint.end_date.date() - sprint.start_date.date()).days + 1
    ideal_per_day = total_points / (days - 1) if days > 1 else total_points

    # Build burndown data
    burndown = []
    for i in range(days):
        day = sprint.start_date.date() + timedelta(days=i)
        # Issues done by this day
        done_points = sum(
            i.story_points or 0
            for i in issues
            if i.status.lower() == 'done' and i.resolved_at and i.resolved_at.date() <= day
        )
        actual = total_points - done_points
        ideal = total_points - int(i * ideal_per_day)
        burndown.append({
            'date': day.isoformat(),
            'ideal': max(ideal, 0),
            'actual': max(actual, 0)
        })
    return Response(burndown)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def project_velocity(request, project_id):
    sprints = Sprint.objects.filter(project_id=project_id).order_by('-start_date')[:6][::-1]
    data = []
    for sprint in sprints:
        issues = Issue.objects.filter(sprint=sprint)
        planned = sum(i.story_points or 0 for i in issues)
        completed = sum(i.story_points or 0 for i in issues if i.status.lower() == 'done')
        data.append({
            'sprint': sprint.name,
            'planned': planned,
            'completed': completed
        })
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sprint_breakdown(request, sprint_id):
    sprint = Sprint.objects.get(id=sprint_id)
    issues = Issue.objects.filter(sprint=sprint)
    # By status
    status_map = {s.category: s for s in WorkflowStatus.objects.filter(project=sprint.project)}
    by_status = []
    for cat, s in status_map.items():
        count = issues.filter(status=cat).count()
        by_status.append({'status': s.name, 'count': count, 'color': s.color})
    # By type
    types = IssueType.objects.all()
    by_type = []
    for t in types:
        count = issues.filter(issue_type=t).count()
        by_type.append({'type': t.name, 'count': count, 'color': t.color})
    return Response({'byStatus': by_status, 'byType': by_type})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sprint_team_performance(request, sprint_id):
    sprint = Sprint.objects.get(id=sprint_id)
    issues = Issue.objects.filter(sprint=sprint)
    members = sprint.project.members.all()
    data = []
    for member in members:
        assigned = issues.filter(assignee=member).count()
        completed = issues.filter(assignee=member, status__iexact='done').count()
        efficiency = int((completed / assigned) * 100) if assigned else 0
        data.append({
            'member': f"{member.first_name} {member.last_name}".strip(),
            'completed': completed,
            'assigned': assigned,
            'efficiency': efficiency
        })
    return Response(data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def auto_complete_sprints(request):
    now = timezone.now()
    updated = 0
    sprints = Sprint.objects.filter(status='active', end_date__lt=now)
    for sprint in sprints:
        sprint.status = 'completed'
        sprint.save()
        updated += 1
    return Response({'updated': updated})