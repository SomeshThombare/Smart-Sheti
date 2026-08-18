from django.contrib import admin
from django.utils.html import format_html

from .models import CropPredictionHistory


@admin.register(CropPredictionHistory)
class CropPredictionHistoryAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "predicted_crop_badge",
        "nitrogen",
        "phosphorus",
        "potassium",
        "temperature",
        "humidity",
        "ph",
        "rainfall",
        "created_at",
    ]

    list_filter = [
        "predicted_crop",
        "created_at",
    ]

    search_fields = [
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__email",
        "predicted_crop",
    ]

    readonly_fields = [
        "created_at",
        "updated_at",
    ]

    ordering = [
        "-created_at",
    ]

    date_hierarchy = "created_at"

    fieldsets = (
        (
            "User Details",
            {
                "fields": (
                    "user",
                )
            },
        ),
        (
            "NPK Values",
            {
                "fields": (
                    "nitrogen",
                    "phosphorus",
                    "potassium",
                )
            },
        ),
        (
            "Environment Details",
            {
                "fields": (
                    "temperature",
                    "humidity",
                    "ph",
                    "rainfall",
                )
            },
        ),
        (
            "Prediction Result",
            {
                "fields": (
                    "predicted_crop",
                )
            },
        ),
        (
            "System Dates",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    def predicted_crop_badge(self, obj):
        if not obj.predicted_crop:
            return "-"

        return format_html(
            '<span style="background:#16a34a;color:white;padding:4px 10px;'
            'border-radius:12px;font-size:12px;font-weight:600;">{}</span>',
            obj.predicted_crop,
        )

    predicted_crop_badge.short_description = "Predicted Crop"