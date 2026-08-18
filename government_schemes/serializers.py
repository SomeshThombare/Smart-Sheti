from rest_framework import serializers
from .models import GovernmentScheme


class GovernmentSchemeSerializer(serializers.ModelSerializer):
    scheme_image = serializers.ImageField(required=False, allow_null=True)
    scheme_document = serializers.FileField(required=False, allow_null=True)

    scheme_image_url = serializers.SerializerMethodField(read_only=True)
    scheme_document_url = serializers.SerializerMethodField(read_only=True)

    slug = serializers.ReadOnlyField()
    created_at = serializers.ReadOnlyField()
    updated_at = serializers.ReadOnlyField()

    class Meta:
        model = GovernmentScheme
        fields = [
            "id",
            "scheme_name",
            "scheme_code",
            "slug",
            "category",
            "short_description",
            "description",
            "benefits",
            "eligibility",
            "required_documents",
            "state",
            "country",
            "start_date",
            "end_date",
            "official_link",
            "apply_link",
            "scheme_image",
            "scheme_image_url",
            "scheme_document",
            "scheme_document_url",
            "contact_person",
            "contact_number",
            "status",
            "is_featured",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "slug",
            "created_at",
            "updated_at",
        ]

    # =========================
    # File URL Helpers
    # =========================
    def get_scheme_image_url(self, obj):
        request = self.context.get("request")

        if obj.scheme_image:
            try:
                url = obj.scheme_image.url
                return request.build_absolute_uri(url) if request else url
            except Exception:
                return None

        return None

    def get_scheme_document_url(self, obj):
        request = self.context.get("request")

        if obj.scheme_document:
            try:
                url = obj.scheme_document.url
                return request.build_absolute_uri(url) if request else url
            except Exception:
                return None

        return None

    # =========================
    # Basic Text Validators
    # =========================
    def validate_scheme_name(self, value):
        value = str(value).strip()

        if not value:
            raise serializers.ValidationError("Scheme name is required.")

        return value

    def validate_scheme_code(self, value):
        value = str(value).strip().upper()

        if not value:
            raise serializers.ValidationError("Scheme code is required.")

        instance = getattr(self, "instance", None)

        if instance and instance.scheme_code != value:
            raise serializers.ValidationError(
                "Scheme code cannot be changed once created."
            )

        qs = GovernmentScheme.objects.filter(scheme_code=value)

        if instance:
            qs = qs.exclude(pk=instance.pk)

        if qs.exists():
            raise serializers.ValidationError("This scheme code already exists.")

        return value

    def validate_short_description(self, value):
        if value is not None:
            return str(value).strip()
        return value

    def validate_description(self, value):
        value = str(value).strip()

        if not value:
            raise serializers.ValidationError("Description is required.")

        return value

    def validate_benefits(self, value):
        value = str(value).strip()

        if not value:
            raise serializers.ValidationError("Benefits are required.")

        return value

    def validate_eligibility(self, value):
        value = str(value).strip()

        if not value:
            raise serializers.ValidationError("Eligibility is required.")

        return value

    def validate_required_documents(self, value):
        if value is not None:
            return str(value).strip()
        return value

    def validate_state(self, value):
        if value is not None:
            return str(value).strip()
        return value

    def validate_country(self, value):
        if value:
            return str(value).strip()
        return "India"

    def validate_contact_person(self, value):
        if value is not None:
            return str(value).strip()
        return value

    def validate_contact_number(self, value):
        if value is not None:
            value = str(value).strip()

            if value and not value.replace("+", "").replace("-", "").replace(" ", "").isdigit():
                raise serializers.ValidationError(
                    "Contact number must contain only digits, spaces, +, or -."
                )

            if value and len(value.replace("+", "").replace("-", "").replace(" ", "")) < 10:
                raise serializers.ValidationError(
                    "Contact number must be at least 10 digits."
                )

        return value

    # =========================
    # File Validators
    # =========================
    def validate_scheme_image(self, value):
        if value:
            max_size = 2 * 1024 * 1024  # 2 MB

            if value.size > max_size:
                raise serializers.ValidationError(
                    "Scheme image size must not exceed 2 MB."
                )

            allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/webp"]

            if hasattr(value, "content_type") and value.content_type not in allowed_types:
                raise serializers.ValidationError(
                    "Only JPG, JPEG, PNG, and WEBP images are allowed."
                )

        return value

    def validate_scheme_document(self, value):
        if value:
            max_size = 5 * 1024 * 1024  # 5 MB

            if value.size > max_size:
                raise serializers.ValidationError(
                    "Scheme document size must not exceed 5 MB."
                )

            allowed_types = [
                "application/pdf",
                "application/msword",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ]

            if hasattr(value, "content_type") and value.content_type not in allowed_types:
                raise serializers.ValidationError(
                    "Only PDF, DOC, and DOCX documents are allowed."
                )

        return value

    # =========================
    # Object Level Validation
    # =========================
    def validate(self, attrs):
        instance = getattr(self, "instance", None)

        category = attrs.get("category", getattr(instance, "category", None))
        state = attrs.get("state", getattr(instance, "state", None))
        start_date = attrs.get("start_date", getattr(instance, "start_date", None))
        end_date = attrs.get("end_date", getattr(instance, "end_date", None))
        official_link = attrs.get("official_link", getattr(instance, "official_link", None))
        apply_link = attrs.get("apply_link", getattr(instance, "apply_link", None))

        if category == GovernmentScheme.CategoryChoices.STATE and not state:
            raise serializers.ValidationError({
                "state": "State is required for state government schemes."
            })

        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError({
                "end_date": "End date cannot be earlier than start date."
            })

        if official_link and not str(official_link).startswith(("http://", "https://")):
            raise serializers.ValidationError({
                "official_link": "Official link must start with http:// or https://."
            })

        if apply_link and not str(apply_link).startswith(("http://", "https://")):
            raise serializers.ValidationError({
                "apply_link": "Apply link must start with http:// or https://."
            })

        return attrs

    # =========================
    # Create / Update
    # =========================
    def create(self, validated_data):
        if validated_data.get("scheme_code"):
            validated_data["scheme_code"] = validated_data["scheme_code"].strip().upper()

        if not validated_data.get("country"):
            validated_data["country"] = "India"

        return GovernmentScheme.objects.create(**validated_data)

    def update(self, instance, validated_data):
        # Do not allow scheme_code update
        validated_data.pop("scheme_code", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance