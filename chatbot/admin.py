from django.contrib import admin
from .models import ChatbotConversation


@admin.register(ChatbotConversation)
class ChatbotConversationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "user_type",
        "status",
        "has_image",
        "has_pdf",
        "created_at",
    )

    list_filter = (
        "user_type",
        "status",
        "has_image",
        "has_pdf",
        "created_at",
    )

    search_fields = (
        "user__username",
        "message",
        "bot_response",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = (
        "-created_at",
    )