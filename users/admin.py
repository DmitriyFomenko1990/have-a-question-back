from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "username", "is_email_verified", "is_staff", "is_active", "date_joined")
    list_filter = ("is_email_verified", "is_staff", "is_active")
    search_fields = ("email", "username")
    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        ("Permissions", {"fields": ("is_email_verified", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined", "created_at", "updated_at")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "username", "password1", "password2", "is_email_verified", "is_staff", "is_active"),
        }),
    )

    readonly_fields = ("created_at", "updated_at", "last_login", "date_joined")
