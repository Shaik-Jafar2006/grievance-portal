"""
Django Admin configuration for CivicPulse Grievance Portal
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Complaint, StatusHistory, Feedback, Notification


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'name', 'role', 'is_active', 'created_at')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('email', 'name', 'phone')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('name', 'phone')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login',)}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'phone', 'role', 'password1', 'password2'),
        }),
    )


class StatusHistoryInline(admin.TabularInline):
    model = StatusHistory
    extra = 0
    readonly_fields = ('old_status', 'new_status', 'changed_by', 'created_at')


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('complaint_id', 'title', 'category', 'status', 'citizen', 'assigned_officer', 'created_at')
    list_filter = ('status', 'category', 'created_at')
    search_fields = ('complaint_id', 'title', 'description', 'citizen__name')
    readonly_fields = ('complaint_id', 'created_at', 'updated_at')
    inlines = [StatusHistoryInline]
    
    fieldsets = (
        ('Complaint Info', {
            'fields': ('complaint_id', 'citizen', 'title', 'description', 'category')
        }),
        ('Location', {
            'fields': ('address', 'latitude', 'longitude')
        }),
        ('Media & AI', {
            'fields': ('image', 'ai_detected_issue', 'ai_confidence')
        }),
        ('Status', {
            'fields': ('status', 'assigned_officer', 'officer_remarks')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'resolved_at')
        }),
    )


@admin.register(StatusHistory)
class StatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('complaint', 'old_status', 'new_status', 'changed_by', 'created_at')
    list_filter = ('new_status', 'created_at')
    search_fields = ('complaint__complaint_id',)


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('complaint', 'citizen', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('complaint__complaint_id', 'citizen__name')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('title', 'user__name')
