"""
EduSync — Accounts Admin Registration.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Role, Faculty, FacultyRoleMapping,
    RolePermission, Student, Parent, ParentStudentMapping,
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["email", "first_name", "last_name", "role_type", "branch", "is_active"]
    list_filter = ["role_type", "branch", "is_active", "is_staff"]
    search_fields = ["email", "first_name", "last_name"]
    ordering = ["email"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal", {"fields": ("first_name", "last_name", "phone")}),
        ("Role", {"fields": ("role_type", "branch")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "first_name", "last_name", "role_type", "password1", "password2"),
        }),
    )


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ["name", "description"]
    search_fields = ["name"]


class FacultyRoleMappingInline(admin.TabularInline):
    model = FacultyRoleMapping
    extra = 1


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ["user", "faculty_code", "branch", "level", "is_active"]
    list_filter = ["branch", "level", "is_active"]
    search_fields = ["user__first_name", "user__last_name", "faculty_code"]
    inlines = [FacultyRoleMappingInline]


@admin.register(FacultyRoleMapping)
class FacultyRoleMappingAdmin(admin.ModelAdmin):
    list_display = ["faculty", "role", "scope_type", "branch"]
    list_filter = ["role", "scope_type"]


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ["role", "permission_key", "branch_scope_allowed"]
    list_filter = ["role"]


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ["user", "admission_number", "branch", "class_assigned", "section", "is_active"]
    list_filter = ["branch", "class_assigned", "is_active"]
    search_fields = ["user__first_name", "user__last_name", "admission_number"]


@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ["user", "is_active"]
    search_fields = ["user__first_name", "user__last_name"]


@admin.register(ParentStudentMapping)
class ParentStudentMappingAdmin(admin.ModelAdmin):
    list_display = ["parent", "student"]
