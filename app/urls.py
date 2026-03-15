"""
URL patterns for CivicPulse Grievance Portal
"""
from django.urls import path
from . import views

urlpatterns = [
    # Public pages
    path('', views.home, name='home'),
    path('track/', views.track_complaint, name='track_complaint'),
    
    # Authentication
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('officer/login/', views.officer_login, name='officer_login'),
    path('admin-login/', views.admin_login, name='admin_login'),
    path('logout/', views.user_logout, name='logout'),
    
    # Dashboard (redirects based on role)
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/citizen/', views.citizen_dashboard, name='citizen_dashboard'),
    path('dashboard/officer/', views.officer_dashboard, name='officer_dashboard'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    
    # Citizen complaint management
    path('complaints/submit/', views.submit_complaint, name='submit_complaint'),
    path('complaints/my/', views.my_complaints, name='my_complaints'),
    path('complaints/<str:complaint_id>/', views.complaint_detail, name='complaint_detail'),
    path('complaints/<str:complaint_id>/feedback/', views.submit_feedback, name='submit_feedback'),
    
    # Officer complaint management
    path('officer/complaints/', views.assigned_complaints, name='assigned_complaints'),
    path('officer/complaints/<str:complaint_id>/update/', views.update_complaint_status, name='update_complaint_status'),
    
    # Admin management
    path('admin-panel/complaints/', views.all_complaints, name='all_complaints'),
    path('admin-panel/complaints/<str:complaint_id>/assign/', views.assign_officer, name='assign_officer'),
    path('admin-panel/users/', views.manage_users, name='manage_users'),
    path('admin-panel/users/<int:user_id>/role/', views.update_user_role, name='update_user_role'),
    
    # Profile & Notifications
    path('profile/', views.profile, name='profile'),
    path('notifications/', views.notifications, name='notifications'),
    
    # API endpoints
    path('api/stats/', views.api_complaints_stats, name='api_stats'),
    path('api/categories/', views.api_category_stats, name='api_categories'),
    path('setup-admin/', views.create_admin_once, name='create_admin_once'),
]
