from django.conf import settings
from django.db import models
from django.utils import timezone


ROLE_ADMIN = "admin"
ROLE_FARMER = "farmer"

USER_TYPE_CHOICES = (
    (ROLE_ADMIN, "Admin"),
    (ROLE_FARMER, "Farmer"),
)


CHAT_STATUS_SUCCESS = "success"
CHAT_STATUS_FAILED = "failed"

CHAT_STATUS_CHOICES = (
    (CHAT_STATUS_SUCCESS, "Success"),
    (CHAT_STATUS_FAILED, "Failed"),
)


class ChatbotConversation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chatbot_conversations",
    )

    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default=ROLE_FARMER,
        db_index=True,
    )

    message = models.TextField(
        verbose_name="User Message"
    )

    bot_response = models.TextField(
        blank=True,
        null=True,
        verbose_name="Bot Response"
    )

    has_image = models.BooleanField(
        default=False
    )

    has_pdf = models.BooleanField(
        default=False
    )

    status = models.CharField(
        max_length=20,
        choices=CHAT_STATUS_CHOICES,
        default=CHAT_STATUS_SUCCESS,
        db_index=True,
    )

    error_message = models.TextField(
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "chatbot_conversation"

        ordering = ["-created_at"]

        verbose_name = "Chatbot Conversation"
        verbose_name_plural = "Chatbot Conversations"

        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["user_type"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["user", "created_at"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.status} - {self.created_at:%d-%m-%Y %H:%M}"

    @property
    def short_message(self):
        if len(self.message) > 100:
            return f"{self.message[:100]}..."
        return self.message

    @property
    def short_response(self):
        if not self.bot_response:
            return ""

        if len(self.bot_response) > 100:
            return f"{self.bot_response[:100]}..."

        return self.bot_response