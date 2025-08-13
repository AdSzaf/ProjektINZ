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
from myapp.views import (register_user , 
    login_user , 
    current_user , 
    projects_view , 
    list_users , 
    create_issue , 
    global_issue_types,
    project_epics,
    project_sprints,
    project_users,
    project_issues,
    update_issue_status,)



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
    path('api/projects/<uuid:project_id>/issues/', project_issues, name='project_issues'),
    path('api/issues/<uuid:issue_id>/status/', update_issue_status, name='update_issue_status'),
]
