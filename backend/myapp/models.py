from django.db import models
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid

class User(AbstractUser):
    """Extended user model for team members"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    role = models.CharField(max_length=50, choices=[
        ('product_owner', 'Product Owner'),
        ('project_manager', 'Project Manager'),
        ('scrum_master', 'Scrum Master'),
        ('developer', 'Developer'),
        ('designer', 'Designer'),
        ('tester', 'Tester'),
    ], default='developer')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Organization(models.Model):
    """Top-level organization/company"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    members = models.ManyToManyField(User, through='OrganizationMembership')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class OrganizationMembership(models.Model):
    """Membership relationship between users and organizations"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    role = models.CharField(max_length=50, choices=[
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('member', 'Member'),
    ], default='member')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'organization']

class Project(models.Model):
    """Main project container"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    key = models.CharField(max_length=10, unique=True)  # e.g., 'PROJ', 'WEB'
    description = models.TextField(blank=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='projects', null=True, blank=True)
    lead = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='led_projects')
    members = models.ManyToManyField(User, through='ProjectMembership', related_name='projects')
    
    methodology = models.CharField(max_length=20, choices=[
        ('scrum', 'Scrum'),
        ('kanban', 'Kanban'),
        ('hybrid', 'Hybrid'),
    ], default='scrum')
    
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('archived', 'Archived'),
        ('on_hold', 'On Hold'),
    ], default='active')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.key} - {self.name}"

class ProjectMembership(models.Model):
    """Project membership with roles"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    role = models.CharField(max_length=50, choices=[
        ('product_owner', 'Product Owner'),
        ('scrum_master', 'Scrum Master'),
        ('developer', 'Developer'),
        ('designer', 'Designer'),
        ('tester', 'Tester'),
    ], default='developer')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'project']

class Epic(models.Model):
    """Large work items that span multiple sprints"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='epics')
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=[
        ('to_do', 'To Do'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
    ], default='to_do')
    
    priority = models.CharField(max_length=20, choices=[
        ('lowest', 'Lowest'),
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('highest', 'Highest'),
    ], default='medium')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Sprint(models.Model):
    """Scrum sprints"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='sprints')
    goal = models.TextField(blank=True)
    
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    status = models.CharField(max_length=20, choices=[
        ('future', 'Future'),
        ('active', 'Active'),
        ('completed', 'Completed'),
    ], default='future')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']
        unique_together = ['project', 'name']

    def __str__(self):
        return f"{self.project.key} - {self.name}"

class IssueType(models.Model):
    """Global issue types: Story, Bug, Task, etc."""
    name = models.CharField(max_length=50, unique=True)
    icon = models.CharField(max_length=50, blank=True)  # Icon class or emoji
    color = models.CharField(max_length=7, default='#0052CC')  # Hex color
    created_at = models.DateTimeField(auto_now_add=True)
#TODO MUSISZ USTALIC JAK SPRAWIC BY TYPY BYLY GLOBALNE I POBIERALNE. MASZ ROZMOWE Z SZATGPT I COPILOTEM O TYM
    def __str__(self):
        return self.name

class Issue(models.Model):
    """Main issue/ticket model (Stories, Tasks, Bugs, etc.)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.CharField(max_length=20, unique=True, editable=False)  # AUTO: PROJ-123
    
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='issues')
    issue_type = models.ForeignKey(IssueType, on_delete=models.CASCADE)
    epic = models.ForeignKey(Epic, on_delete=models.SET_NULL, null=True, blank=True, related_name='issues')
    sprint = models.ForeignKey(Sprint, on_delete=models.SET_NULL, null=True, blank=True, related_name='issues')
    
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reported_issues')
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_issues')
    
    status = models.CharField(max_length=50, default='to_do')  # Will be linked to workflow
    priority = models.CharField(max_length=20, choices=[
        ('lowest', 'Lowest'),
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('highest', 'Highest'),
    ], default='medium')
    
    # Story points for estimation
    story_points = models.PositiveIntegerField(null=True, blank=True)
    
    # Time tracking
    original_estimate = models.PositiveIntegerField(null=True, blank=True, help_text="Minutes")
    remaining_estimate = models.PositiveIntegerField(null=True, blank=True, help_text="Minutes")
    time_spent = models.PositiveIntegerField(default=0, help_text="Minutes")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.key:
            # Auto-generate issue key like PROJ-123
            last_issue = Issue.objects.filter(project=self.project).order_by('-created_at').first()
            if last_issue and last_issue.key:
                try:
                    last_number = int(last_issue.key.split('-')[1])
                    new_number = last_number + 1
                except (IndexError, ValueError):
                    new_number = 1
            else:
                new_number = 1
            self.key = f"{self.project.key}-{new_number}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.key}: {self.title}"

class WorkflowStatus(models.Model):
    """Workflow statuses for projects (To Do, In Progress, Done, etc.)"""
    name = models.CharField(max_length=50)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='workflow_statuses')
    category = models.CharField(max_length=20, choices=[
        ('to_do', 'To Do'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
    ])
    order = models.PositiveIntegerField(default=0)
    color = models.CharField(max_length=7, default='#0052CC')

    class Meta:
        ordering = ['order']
        unique_together = ['name', 'project']

    def __str__(self):
        return f"{self.project.key} - {self.name}"

class Comment(models.Model):
    """Comments on issues"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment on {self.issue.key} by {self.author.username}"

class Attachment(models.Model):
    """File attachments for issues"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='attachments')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to='attachments/')
    filename = models.CharField(max_length=255)
    size = models.PositiveIntegerField()  # in bytes
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.filename} on {self.issue.key}"

class IssueHistory(models.Model):
    """Track all changes to issues"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='history')
    changed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    field_name = models.CharField(max_length=50)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-changed_at']

    def __str__(self):
        return f"{self.issue.key} - {self.field_name} changed"
