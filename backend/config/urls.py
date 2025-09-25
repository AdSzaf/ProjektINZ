"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from myapp.views import (auto_complete_sprints, register_user , 
    login_user , 
    current_user , 
    projects_view , 
    list_users , 
    create_issue , 
    global_issue_types,
    project_epics,
    project_sprints,
    project_users,
    project_invite,
    project_member_statuses,
    set_project_member_status,
    project_issues,
    update_issue_status,
    project_workflow_statuses,
    add_workflow_status,
    delete_workflow_status,
    update_sprint,
    update_issue,
    get_user_short,
    update_user_settings,
    sprint_burndown,
    project_velocity,
    sprint_breakdown,
    sprint_team_performance,
    project_dashboard,
    organization_users,
    create_checkout_session, 
    stripe_webhook,
    ai_chat,
    suggest_task_priority,
    project_tags,
    update_tag,
    issues_by_tag,
    project_worklogs,
    log_time
)



urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/register/', register_user, name='register'),
    path('api/login/', login_user, name='login'),
    path('api/me/', current_user, name='current_user'),
    path('api/projects/', projects_view, name='projects'),
    path('api/users/', list_users, name='list_users'),
    path('api/issues/', create_issue, name='create_issue'),
    path('api/issue-types/', global_issue_types, name='global_issue_types'),
    path('api/projects/<uuid:project_id>/epics/', project_epics, name='project_epics'),
    path('api/projects/<uuid:project_id>/sprints/', project_sprints, name='project_sprints'),
    path('api/projects/<uuid:project_id>/users/', project_users, name='project_users'),
    path('api/projects/<uuid:project_id>/invite/', project_invite, name='project_invite'),
    path('api/projects/<uuid:project_id>/member-statuses/', project_member_statuses, name='project_member_statuses'),
    path('api/projects/<uuid:project_id>/member-statuses/<uuid:user_id>/', set_project_member_status, name='set_project_member_status'),
    path('api/projects/<uuid:project_id>/issues/', project_issues, name='project_issues'),
    path('api/issues/<uuid:issue_id>/status/', update_issue_status, name='update_issue_status'),
    path('api/projects/<uuid:project_id>/workflow-statuses/', project_workflow_statuses, name='project_workflow_statuses'),
    path('api/projects/<uuid:project_id>/workflow-statuses/add/', add_workflow_status, name='add_workflow_status'),
    path('api/projects/<uuid:project_id>/workflow-statuses/<str:category>/', delete_workflow_status, name='delete_workflow_status'),
    path('api/issues/<uuid:issue_id>/', update_issue, name='update_issue'),
    path('api/sprints/<uuid:sprint_id>/', update_sprint, name='update_sprint'),
    path('api/users/<uuid:user_id>/short/', get_user_short, name='get_user_short'),
    path('api/me/update/', update_user_settings, name='update_user_settings'),

    path('api/sprints/<uuid:sprint_id>/burndown/', sprint_burndown, name='sprint_burndown'),
    path('api/projects/<uuid:project_id>/velocity/', project_velocity, name='project_velocity'),
    path('api/sprints/<uuid:sprint_id>/breakdown/', sprint_breakdown, name='sprint_breakdown'),
    path('api/sprints/<uuid:sprint_id>/team-performance/', sprint_team_performance, name='sprint_team_performance'),

    path('api/sprints/auto-complete/', auto_complete_sprints, name='auto_complete_sprints'),
    path('api/projects/<uuid:project_id>/dashboard/', project_dashboard, name='project_dashboard'),

    path('api/organizations/<uuid:org_id>/users/', organization_users, name='organization_users'),

    #Stripe urls
    path('api/payments/create-checkout-session/', create_checkout_session, name='create_checkout_session'),
    path('api/payments/webhook/', stripe_webhook, name='stripe_webhook'),

    #AI urls
    path('api/ai/chat/', ai_chat, name='ai_chat'),
    path('api/ai/suggest-priority/', suggest_task_priority, name='suggest_task_priority'),

    #Tag urls
    path('api/projects/<uuid:project_id>/tags/', project_tags, name='project_tags'),
    path('api/tags/<uuid:tag_id>/', update_tag, name='update_tag'),
    path('api/projects/<uuid:project_id>/tags/<uuid:tag_id>/issues/', issues_by_tag, name='issues_by_tag'),

    #Tempo worklog
    path('projects/<uuid:project_id>/worklogs/', project_worklogs, name='project-worklogs'),
    path('issues/<uuid:issue_id>/log-time/', log_time, name='log-time'),
]
