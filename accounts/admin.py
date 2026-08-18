from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    CustomUser,
    FarmerProfile,
    AdminProfile,
    OTPVerification,
)


# =========================================================
# Custom User Admin
# =========================================================
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser

    list_display = (
        "id",
        "username",
        "first_name",
        "last_name",
        "email",
        "country_code",
        "mobile_number",
        "role",
        "language_preference",
        "is_active",
        "is_staff",
        "is_superuser",
        "last_login",
        "date_joined",
    )

    list_filter = (
        "role",
        "language_preference",
        "is_active",
        "is_staff",
        "is_superuser",
        "last_login",
        "date_joined",
    )

    search_fields = (
        "username",
        "first_name",
        "last_name",
        "email",
        "mobile_number",
    )

    ordering = ("-date_joined",)
    list_per_page = 25
    date_hierarchy = "date_joined"

    readonly_fields = (
        "last_login",
        "date_joined",
    )

    fieldsets = (
        ("Login Credentials", {
            "fields": (
                "username",
                "password",
            )
        }),
        ("Personal Information", {
            "fields": (
                "first_name",
                "last_name",
                "email",
                "country_code",
                "mobile_number",
                "language_preference",
                "role",
            )
        }),
        ("Permissions", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            )
        }),
        ("Important Dates", {
            "fields": (
                "last_login",
                "date_joined",
            )
        }),
    )

    add_fieldsets = (
        ("Create User", {
            "classes": ("wide",),
            "fields": (
                "first_name",
                "last_name",
                "username",
                "email",
                "country_code",
                "mobile_number",
                "language_preference",
                "role",
                "password1",
                "password2",
                "is_active",
                "is_staff",
                "is_superuser",
            ),
        }),
    )

    filter_horizontal = (
        "groups",
        "user_permissions",
    )


# =========================================================
# Farmer Profile Admin
# =========================================================
@admin.register(FarmerProfile)
class FarmerProfileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "gender",
        "village",
        "taluka",
        "district",
        "state",
        "pincode",
        "created_by_user",
        "updated_by_user",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "gender",
        "district",
        "state",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__email",
        "user__mobile_number",
        "village",
        "taluka",
        "district",
        "state",
        "pincode",
    )

    ordering = ("user__username",)
    list_per_page = 25
    date_hierarchy = "created_at"

    readonly_fields = (
        "created_by_user",
        "updated_by_user",
        "created_at",
        "updated_at",
    )

    autocomplete_fields = ("user",)

    fieldsets = (
        ("Farmer User", {
            "fields": (
                "user",
            )
        }),
        ("Farmer Details", {
            "fields": (
                "gender",
                "village",
                "taluka",
                "district",
                "state",
                "pincode",
                "full_address",
            )
        }),
        ("Tracking Information", {
            "fields": (
                "created_by_user",
                "updated_by_user",
                "created_at",
                "updated_at",
            )
        }),
    )


# =========================================================
# Admin Profile Admin
# =========================================================
@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "admin_secret_code",
        "created_by_user",
        "updated_by_user",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "created_at",
        "updated_at",
    )

    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__email",
        "user__mobile_number",
        "admin_secret_code",
    )

    ordering = ("user__username",)
    list_per_page = 25
    date_hierarchy = "created_at"

    readonly_fields = (
        "created_by_user",
        "updated_by_user",
        "created_at",
        "updated_at",
    )

    autocomplete_fields = ("user",)

    fieldsets = (
        ("Admin User", {
            "fields": (
                "user",
                "admin_secret_code",
            )
        }),
        ("Tracking Information", {
            "fields": (
                "created_by_user",
                "updated_by_user",
                "created_at",
                "updated_at",
            )
        }),
    )


# =========================================================
# OTP Verification Admin
# =========================================================
@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "email",
        "mobile_number",
        "email_otp",
        "mobile_otp",
        "is_email_verified",
        "is_mobile_verified",
        "expires_at",
        "created_by_user",
        "updated_by_user",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "is_email_verified",
        "is_mobile_verified",
        "created_at",
        "updated_at",
        "expires_at",
    )

    search_fields = (
        "email",
        "mobile_number",
        "email_otp",
        "mobile_otp",
    )

    ordering = ("-created_at",)
    list_per_page = 25
    date_hierarchy = "created_at"

    readonly_fields = (
        "created_by_user",
        "updated_by_user",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        ("OTP Details", {
            "fields": (
                "email",
                "mobile_number",
                "email_otp",
                "mobile_otp",
            )
        }),
        ("Verification Status", {
            "fields": (
                "is_email_verified",
                "is_mobile_verified",
                "expires_at",
            )
        }),
        ("Tracking Information", {
            "fields": (
                "created_by_user",
                "updated_by_user",
                "created_at",
                "updated_at",
            )
        }),
    )