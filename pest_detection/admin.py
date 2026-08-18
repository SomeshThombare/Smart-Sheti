# pest_detection/admin.py

from django.contrib import admin
from django.utils.html import format_html

from .models import PestPrediction


@admin.register(PestPrediction)
class PestPredictionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "image_preview",
        "farmer_name",
        "pest_name",
        "confidence",
        "class_name",
        "predicted_index",
        "severity",
        "treatment_priority",
        "status",
        "created_at",
    ]

    list_filter = [
        "status",
        "severity",
        "created_at",
    ]

    search_fields = [
        "pest_name",
        "class_name",
        "user__username",
        "user__email",
        "user__first_name",
        "user__last_name",
    ]

    readonly_fields = [
        "image_preview_large",
        "created_at",
        "updated_at",
    ]

    ordering = [
        "-created_at",
    ]

    list_per_page = 25

    fieldsets = (
        (
            "Farmer Information",
            {
                "fields": (
                    "user",
                )
            },
        ),
        (
            "Uploaded Image",
            {
                "fields": (
                    "image",
                    "image_preview_large",
                )
            },
        ),
        (
            "Prediction Result",
            {
                "fields": (
                    "pest_name",
                    "confidence",
                    "solution",
                    "class_name",
                    "predicted_index",
                    "top_predictions",
                )
            },
        ),
        (
            "Treatment Information",
            {
                "fields": (
                    "severity",
                    "treatment_priority",
                )
            },
        ),
        (
            "Status & Error",
            {
                "fields": (
                    "status",
                    "error_message",
                )
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    def farmer_name(self, obj):
        if not obj.user:
            return "-"

        full_name = obj.user.get_full_name()

        if full_name:
            return full_name

        return obj.user.username

    farmer_name.short_description = "Farmer"

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="60" height="60" '
                'style="object-fit:cover;border-radius:8px;border:1px solid #ddd;" />',
                obj.image.url,
            )

        return "-"

    image_preview.short_description = "Image"

    def image_preview_large(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="320" '
                'style="object-fit:cover;border-radius:12px;border:1px solid #ddd;" />',
                obj.image.url,
            )

        return "No image available"

    image_preview_large.short_description = "Image Preview"