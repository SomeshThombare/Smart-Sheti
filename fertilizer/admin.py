from django.contrib import admin
from django.utils.html import format_html

from .models import FertilizerRecommendationHistory


@admin.register(FertilizerRecommendationHistory)
class FertilizerRecommendationHistoryAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "user_type_badge",
        "crop",
        "soil_color",
        "nitrogen",
        "phosphorus",
        "potassium",
        "ph",
        "rainfall",
        "temperature",
        "created_at",
    ]

    list_filter = [
        "user_type",
        "crop",
        "soil_color",
        "created_at",
    ]

    search_fields = [
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__email",
        "crop",
        "soil_color",
    ]

    readonly_fields = [
        "created_at",
        "updated_at",
        "recommendation_result_pretty",
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
                    "user_type",
                )
            },
        ),
        (
            "Crop & Soil Details",
            {
                "fields": (
                    "crop",
                    "soil_color",
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
                    "ph",
                    "rainfall",
                    "temperature",
                )
            },
        ),
        (
            "Recommendation Result",
            {
                "fields": (
                    "recommendation_result",
                    "recommendation_result_pretty",
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

    def user_type_badge(self, obj):
        if obj.user_type == "admin":
            return format_html(
                '<span style="background:#2563eb;color:white;padding:4px 10px;border-radius:12px;font-size:12px;">Admin</span>'
            )

        if obj.user_type == "farmer":
            return format_html(
                '<span style="background:#16a34a;color:white;padding:4px 10px;border-radius:12px;font-size:12px;">Farmer</span>'
            )

        return obj.user_type

    user_type_badge.short_description = "User Type"

    def recommendation_result_pretty(self, obj):
        if not obj.recommendation_result:
            return "-"

        html = "<pre style='background:#f8fafc;padding:12px;border-radius:8px;border:1px solid #e5e7eb;white-space:pre-wrap;'>"
        html += str(obj.recommendation_result)
        html += "</pre>"

        return format_html(html)

    recommendation_result_pretty.short_description = "Recommendation Result Preview"