from django.contrib import admin
from .models import DiseasePrediction


@admin.register(DiseasePrediction)
class DiseasePredictionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "crop_name",
        "disease_name",
        "confidence",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "crop_name",
        "disease_name",
        "created_at",
    )

    search_fields = (
        "user__username",
        "user__email",
        "crop_name",
        "disease_name",
        "class_name",
    )

    readonly_fields = (
        "user",
        "image",
        "crop_name",
        "disease_name",
        "confidence",
        "treatment",
        "suggestion",
        "class_name",
        "predicted_index",
        "status",
        "error_message",
        "created_at",
    )

    list_per_page = 25