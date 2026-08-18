# pest_detection/serializers.py

from rest_framework import serializers

from .models import PestPrediction


class PestPredictionSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(
        source="user.id",
        read_only=True,
    )

    username = serializers.CharField(
        source="user.username",
        read_only=True,
    )

    farmer_name = serializers.SerializerMethodField()
    farmer_email = serializers.EmailField(
        source="user.email",
        read_only=True,
    )

    image_url = serializers.SerializerMethodField()
    is_success = serializers.BooleanField(read_only=True)
    is_failed = serializers.BooleanField(read_only=True)

    class Meta:
        model = PestPrediction
        fields = [
            "id",
            "user_id",
            "username",
            "farmer_name",
            "farmer_email",
            "image",
            "image_url",
            "pest_name",
            "confidence",
            "solution",
            "class_name",
            "predicted_index",
            "severity",
            "treatment_priority",
            "top_predictions",
            "status",
            "error_message",
            "is_success",
            "is_failed",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "user_id",
            "username",
            "farmer_name",
            "farmer_email",
            "image_url",
            "pest_name",
            "confidence",
            "solution",
            "class_name",
            "predicted_index",
            "severity",
            "treatment_priority",
            "top_predictions",
            "status",
            "error_message",
            "is_success",
            "is_failed",
            "created_at",
            "updated_at",
        ]

    def get_farmer_name(self, obj):
        if not obj.user:
            return ""

        full_name = obj.user.get_full_name()

        if full_name:
            return full_name

        return obj.user.username

    def get_image_url(self, obj):
        request = self.context.get("request")

        if not obj.image:
            return ""

        if request:
            return request.build_absolute_uri(obj.image.url)

        return obj.image.url


class PestPredictionListSerializer(serializers.ModelSerializer):
    farmer_name = serializers.SerializerMethodField()
    farmer_email = serializers.EmailField(
        source="user.email",
        read_only=True,
    )
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = PestPrediction
        fields = [
            "id",
            "farmer_name",
            "farmer_email",
            "image_url",
            "pest_name",
            "confidence",
            "class_name",
            "predicted_index",
            "severity",
            "treatment_priority",
            "status",
            "created_at",
        ]

    def get_farmer_name(self, obj):
        if not obj.user:
            return ""

        full_name = obj.user.get_full_name()

        if full_name:
            return full_name

        return obj.user.username

    def get_image_url(self, obj):
        request = self.context.get("request")

        if not obj.image:
            return ""

        if request:
            return request.build_absolute_uri(obj.image.url)

        return obj.image.url


class PestPredictionDetailSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(
        source="user.id",
        read_only=True,
    )
    username = serializers.CharField(
        source="user.username",
        read_only=True,
    )
    farmer_name = serializers.SerializerMethodField()
    farmer_email = serializers.EmailField(
        source="user.email",
        read_only=True,
    )
    image_url = serializers.SerializerMethodField()
    is_success = serializers.BooleanField(read_only=True)
    is_failed = serializers.BooleanField(read_only=True)

    class Meta:
        model = PestPrediction
        fields = [
            "id",
            "user_id",
            "username",
            "farmer_name",
            "farmer_email",
            "image",
            "image_url",
            "pest_name",
            "confidence",
            "solution",
            "class_name",
            "predicted_index",
            "severity",
            "treatment_priority",
            "top_predictions",
            "status",
            "error_message",
            "is_success",
            "is_failed",
            "created_at",
            "updated_at",
        ]

    def get_farmer_name(self, obj):
        if not obj.user:
            return ""

        full_name = obj.user.get_full_name()

        if full_name:
            return full_name

        return obj.user.username

    def get_image_url(self, obj):
        request = self.context.get("request")

        if not obj.image:
            return ""

        if request:
            return request.build_absolute_uri(obj.image.url)

        return obj.image.url


class PestUploadSerializer(serializers.Serializer):
    image = serializers.ImageField(required=True)

    def validate_image(self, image):
        allowed_content_types = [
            "image/jpeg",
            "image/jpg",
            "image/png",
            "image/webp",
        ]

        allowed_extensions = [
            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
        ]

        max_size = 5 * 1024 * 1024

        content_type = getattr(image, "content_type", "")

        if content_type not in allowed_content_types:
            raise serializers.ValidationError(
                "Only JPG, JPEG, PNG and WEBP images are allowed."
            )

        file_name = image.name.lower()

        if not any(file_name.endswith(ext) for ext in allowed_extensions):
            raise serializers.ValidationError(
                "Only .jpg, .jpeg, .png and .webp files are allowed."
            )

        if image.size > max_size:
            raise serializers.ValidationError(
                "Image size must be less than 5 MB."
            )

        return image


class PestPredictionSearchSerializer(serializers.Serializer):
    search = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=255,
    )

    status = serializers.ChoiceField(
        required=False,
        allow_blank=True,
        choices=[
            ("", "All Status"),
            ("SUCCESS", "Success"),
            ("FAILED", "Failed"),
        ],
    )

    pest_name = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=255,
    )

    date_from = serializers.DateField(
        required=False,
    )

    date_to = serializers.DateField(
        required=False,
    )

    min_confidence = serializers.FloatField(
        required=False,
        min_value=0,
        max_value=100,
    )

    max_confidence = serializers.FloatField(
        required=False,
        min_value=0,
        max_value=100,
    )

    sort = serializers.ChoiceField(
        required=False,
        allow_blank=True,
        choices=[
            ("-date", "Newest First"),
            ("date", "Oldest First"),
            ("-confidence", "High Confidence"),
            ("confidence", "Low Confidence"),
            ("pest_name", "Pest Name A-Z"),
            ("-pest_name", "Pest Name Z-A"),
            ("status", "Status A-Z"),
            ("-status", "Status Z-A"),
        ],
    )

    page = serializers.IntegerField(
        required=False,
        min_value=1,
    )

    page_size = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=100,
    )

    def validate(self, attrs):
        date_from = attrs.get("date_from")
        date_to = attrs.get("date_to")
        min_confidence = attrs.get("min_confidence")
        max_confidence = attrs.get("max_confidence")

        if date_from and date_to and date_from > date_to:
            raise serializers.ValidationError(
                "date_from cannot be greater than date_to."
            )

        if (
            min_confidence is not None
            and max_confidence is not None
            and min_confidence > max_confidence
        ):
            raise serializers.ValidationError(
                "min_confidence cannot be greater than max_confidence."
            )

        return attrs


class PestDashboardStatsSerializer(serializers.Serializer):
    total_predictions = serializers.IntegerField()
    success_count = serializers.IntegerField()
    failed_count = serializers.IntegerField()
    today_predictions = serializers.IntegerField()
    monthly_predictions = serializers.IntegerField()
    success_rate = serializers.FloatField()

    most_detected_pest = serializers.DictField(
        required=False,
        allow_null=True,
    )

    top_pests = serializers.ListField(
        child=serializers.DictField(),
        required=False,
    )

    top_farmers = serializers.ListField(
        child=serializers.DictField(),
        required=False,
    )

    monthly_trend = serializers.ListField(
        child=serializers.DictField(),
        required=False,
    )

    district_report = serializers.ListField(
        child=serializers.DictField(),
        required=False,
    )

    recent_predictions = PestPredictionListSerializer(
        many=True,
        required=False,
    )