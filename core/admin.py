from django.contrib import admin
from .models import UserProfile, Department, Resource

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'emp_id', 'role', 'department', 'is_approved']
    list_filter  = ['role', 'is_approved', 'department']
    actions      = ['approve_users']

    def approve_users(self, request, queryset):
        queryset.update(is_approved=True)
    approve_users.short_description = "Approve selected users"

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'head', 'created_at']

@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ['title', 'resource_type', 'department', 'added_by', 'created_at']
    list_filter  = ['resource_type', 'department']
    search_fields = ['title', 'description', 'tags']