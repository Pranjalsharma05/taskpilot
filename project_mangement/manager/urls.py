
from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_user, name='login'),
    path('register/', views.register, name='register'),
    path('logout/',views.user_logout, name='logout'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('manager_dashboard/', views.manager_dashboard, name='manager_dashboard'),
    path('employee_dashboard/', views.employee_dashboard, name='employee_dashboard'),
    path('profile/', views.profile_view, name='profile_view'),
    path('skills/', views.skill_manage, name='skill_manage'),
    path('add_role/', views.add_role, name='add_role'),
    path('users_data/', views.user_list_view, name='users_data'),
    path('users_data/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    path('delete/skill/<int:skill_id>/', views.skill_delete, name='skill_delete'),
    path('add_project/', views.add_project, name='add_project'),
    path('<int:pk>/', views.project_detail, name='project_detail'),
    path('<int:pk>/edit/', views.update_project, name='update_project'),
    path('<int:pk>/delete/', views.delete_project, name='delete_project'),
    path('manager_home/', views.manager_home, name="manager_home"),
    path('project/<int:project_id>/add_task/', views.add_task, name='add_task'),
    path('task/<int:task_id>/', views.task_detail, name='task_detail'),
    path('recommend/', views.recommend_project, name='recommend_project'),
    path('project/<int:project_id>/recommend_task/', views.recommend_task, name='recommend_task'),
    path('project/<int:project_id>/add_suggested_task/', views.add_suggested_task, name='add_suggested_task'),  
]
