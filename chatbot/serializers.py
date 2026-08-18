from rest_framework import serializers

from .models import ChatbotConversation


class ChatbotMessageSerializer(serializers.Serializer):
    message = serializers.CharField(
        required=False,
        allow_blank=True,
        trim_whitespace=True,
    )

    image = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
    )

    image_mime = serializers.CharField(
        required=False,
        allow_blank=True,
        default="image/jpeg",
    )

    pdf = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
    )

    def validate(self, attrs):
        message = attrs.get("message", "")
        image = attrs.get("image", "")
        pdf = attrs.get("pdf", "")

        if not message and not image and not pdf:
            raise serializers.ValidationError(
                {
                    "detail": [
                        "At least one input is required: message, image, or pdf."
                    ]
                }
            )

        return attrs


class ChatbotConversationSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        source="user.username",
        read_only=True,
    )

    user_full_name = serializers.SerializerMethodField()

    short_message = serializers.CharField(
        read_only=True,
    )

    short_response = serializers.CharField(
        read_only=True,
    )

    class Meta:
        model = ChatbotConversation

        fields = [
            "id",
            "user",
            "username",
            "user_full_name",
            "user_type",
            "message",
            "short_message",
            "bot_response",
            "short_response",
            "has_image",
            "has_pdf",
            "status",
            "error_message",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "user",
            "username",
            "user_full_name",
            "short_message",
            "short_response",
            "created_at",
            "updated_at",
        ]

    def get_user_full_name(self, obj):
        full_name = obj.user.get_full_name()

        if full_name:
            return full_name

        return obj.user.username