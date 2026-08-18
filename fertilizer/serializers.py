from rest_framework import serializers

from .models import FertilizerRecommendationHistory


# ======================================================
# 1. INPUT SERIALIZER
# Used for admin/farmer recommendation input API
# ======================================================
class FertilizerRecommendationInputSerializer(serializers.Serializer):
    crop_type = serializers.ChoiceField(
        choices=FertilizerRecommendationHistory.CropChoices.choices
    )

    soil_color = serializers.ChoiceField(
        choices=FertilizerRecommendationHistory.SoilColorChoices.choices
    )

    N = serializers.FloatField(min_value=0, default=80)
    P = serializers.FloatField(min_value=0, default=50)
    K = serializers.FloatField(min_value=0, default=100)

    pH = serializers.FloatField(
        min_value=0,
        max_value=14,
        default=6.5
    )

    rainfall = serializers.FloatField(min_value=0, default=1000)

    temperature = serializers.FloatField(
        min_value=-50,
        max_value=100,
        default=25
    )

    # =========================
    # Field Validators
    # =========================
    def validate_crop_type(self, value):
        value = str(value).strip().title()

        if not value:
            raise serializers.ValidationError("Crop is required.")

        if value not in FertilizerRecommendationHistory.CropChoices.values:
            raise serializers.ValidationError("Invalid crop selected.")

        return value

    def validate_soil_color(self, value):
        value = str(value).strip().title()

        if not value:
            raise serializers.ValidationError("Soil color is required.")

        if value not in FertilizerRecommendationHistory.SoilColorChoices.values:
            raise serializers.ValidationError("Invalid soil color selected.")

        return value

    def validate_N(self, value):
        return self._validate_positive_number(value, "Nitrogen")

    def validate_P(self, value):
        return self._validate_positive_number(value, "Phosphorus")

    def validate_K(self, value):
        return self._validate_positive_number(value, "Potassium")

    def validate_pH(self, value):
        if value is None:
            raise serializers.ValidationError("pH value is required.")

        value = float(value)

        if value < 0 or value > 14:
            raise serializers.ValidationError("pH must be between 0 and 14.")

        return value

    def validate_rainfall(self, value):
        return self._validate_positive_number(value, "Rainfall")

    def validate_temperature(self, value):
        if value is None:
            raise serializers.ValidationError("Temperature value is required.")

        value = float(value)

        if value < -50 or value > 100:
            raise serializers.ValidationError(
                "Temperature must be between -50 and 100."
            )

        return value

    def _validate_positive_number(self, value, field_label):
        if value is None:
            raise serializers.ValidationError(
                f"{field_label} value is required."
            )

        value = float(value)

        if value < 0:
            raise serializers.ValidationError(
                f"{field_label} cannot be negative."
            )

        return value

    # =========================
    # Object Level Validation
    # =========================
    def validate(self, attrs):
        attrs["Crop"] = attrs.get("crop_type")
        attrs["Soil_color"] = attrs.get("soil_color")
        attrs["Nitrogen"] = attrs.get("N")
        attrs["Phosphorus"] = attrs.get("P")
        attrs["Potassium"] = attrs.get("K")
        attrs["Rainfall"] = attrs.get("rainfall")
        attrs["Temperature"] = attrs.get("temperature")

        return attrs


# ======================================================
# 2. HISTORY SERIALIZER
# Used for create/update/edit history
# ======================================================
class FertilizerRecommendationHistorySerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        source="user.username",
        read_only=True
    )

    user_full_name = serializers.SerializerMethodField(read_only=True)

    user_type_display = serializers.CharField(
        source="get_user_type_display",
        read_only=True
    )

    crop_display = serializers.CharField(
        source="get_crop_display",
        read_only=True
    )

    soil_color_display = serializers.CharField(
        source="get_soil_color_display",
        read_only=True
    )

    created_at = serializers.ReadOnlyField()
    updated_at = serializers.ReadOnlyField()

    class Meta:
        model = FertilizerRecommendationHistory

        fields = [
            "id",
            "user",
            "username",
            "user_full_name",
            "user_type",
            "user_type_display",
            "crop",
            "crop_display",
            "soil_color",
            "soil_color_display",
            "nitrogen",
            "phosphorus",
            "potassium",
            "ph",
            "rainfall",
            "temperature",
            "recommendation_result",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "username",
            "user_full_name",
            "user_type_display",
            "crop_display",
            "soil_color_display",
            "created_at",
            "updated_at",
        ]

    # =========================
    # Display Helpers
    # =========================
    def get_user_full_name(self, obj):
        if obj.user:
            full_name = obj.user.get_full_name()
            return full_name if full_name else obj.user.username

        return ""

    # =========================
    # Basic Text Validators
    # =========================
    def validate_user_type(self, value):
        value = str(value).strip().lower()

        if not value:
            raise serializers.ValidationError("User type is required.")

        if value not in FertilizerRecommendationHistory.UserTypeChoices.values:
            raise serializers.ValidationError("Invalid user type selected.")

        return value

    def validate_crop(self, value):
        value = str(value).strip().title()

        if not value:
            raise serializers.ValidationError("Crop is required.")

        if value not in FertilizerRecommendationHistory.CropChoices.values:
            raise serializers.ValidationError("Invalid crop selected.")

        return value

    def validate_soil_color(self, value):
        value = str(value).strip().title()

        if not value:
            raise serializers.ValidationError("Soil color is required.")

        if value not in FertilizerRecommendationHistory.SoilColorChoices.values:
            raise serializers.ValidationError("Invalid soil color selected.")

        return value

    # =========================
    # Number Validators
    # =========================
    def validate_nitrogen(self, value):
        return self._validate_positive_number(value, "Nitrogen")

    def validate_phosphorus(self, value):
        return self._validate_positive_number(value, "Phosphorus")

    def validate_potassium(self, value):
        return self._validate_positive_number(value, "Potassium")

    def validate_ph(self, value):
        if value is None:
            raise serializers.ValidationError("pH value is required.")

        value = float(value)

        if value < 0 or value > 14:
            raise serializers.ValidationError("pH must be between 0 and 14.")

        return value

    def validate_rainfall(self, value):
        return self._validate_positive_number(value, "Rainfall")

    def validate_temperature(self, value):
        if value is None:
            raise serializers.ValidationError("Temperature value is required.")

        value = float(value)

        if value < -50 or value > 100:
            raise serializers.ValidationError(
                "Temperature must be between -50 and 100."
            )

        return value

    def _validate_positive_number(self, value, field_label):
        if value is None:
            raise serializers.ValidationError(
                f"{field_label} value is required."
            )

        value = float(value)

        if value < 0:
            raise serializers.ValidationError(
                f"{field_label} cannot be negative."
            )

        return value

    # =========================
    # JSON Validator
    # =========================
    def validate_recommendation_result(self, value):
        if value in [None, ""]:
            raise serializers.ValidationError(
                "Recommendation result is required."
            )

        if not isinstance(value, dict):
            raise serializers.ValidationError(
                "Recommendation result must be a valid JSON object."
            )

        return value

    # =========================
    # Object Level Validation
    # =========================
    def validate(self, attrs):
        request = self.context.get("request")
        instance = getattr(self, "instance", None)

        selected_user = attrs.get(
            "user",
            getattr(instance, "user", None)
        )

        selected_user_type = attrs.get(
            "user_type",
            getattr(instance, "user_type", None)
        )

        if request and request.user and request.user.is_authenticated:
            current_user = request.user
            current_user_type = getattr(current_user, "user_type", None)

            is_admin = (
                current_user_type == "admin"
                or current_user.is_staff
                or current_user.is_superuser
            )

            is_farmer = current_user_type == "farmer"

            if is_farmer:
                attrs["user"] = current_user
                attrs["user_type"] = "farmer"

            if not is_admin:
                if selected_user and selected_user != current_user:
                    raise serializers.ValidationError({
                        "user": "You cannot create recommendation history for another user."
                    })

                if selected_user_type == "admin":
                    raise serializers.ValidationError({
                        "user_type": "Only admin can create admin recommendation history."
                    })

        return attrs

    # =========================
    # Create / Update
    # =========================
    def create(self, validated_data):
        if validated_data.get("user_type"):
            validated_data["user_type"] = str(
                validated_data["user_type"]
            ).strip().lower()

        if validated_data.get("crop"):
            validated_data["crop"] = str(
                validated_data["crop"]
            ).strip().title()

        if validated_data.get("soil_color"):
            validated_data["soil_color"] = str(
                validated_data["soil_color"]
            ).strip().title()

        return FertilizerRecommendationHistory.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            if attr == "user_type" and value:
                value = str(value).strip().lower()

            if attr in ["crop", "soil_color"] and value:
                value = str(value).strip().title()

            setattr(instance, attr, value)

        instance.save()
        return instance


# ======================================================
# 3. HISTORY LIST SERIALIZER
# Used for table/list response
# ======================================================
class FertilizerRecommendationHistoryListSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        source="user.username",
        read_only=True
    )

    user_full_name = serializers.SerializerMethodField(read_only=True)

    user_type_display = serializers.CharField(
        source="get_user_type_display",
        read_only=True
    )

    crop_display = serializers.CharField(
        source="get_crop_display",
        read_only=True
    )

    soil_color_display = serializers.CharField(
        source="get_soil_color_display",
        read_only=True
    )

    class Meta:
        model = FertilizerRecommendationHistory

        fields = [
            "id",
            "username",
            "user_full_name",
            "user_type",
            "user_type_display",
            "crop",
            "crop_display",
            "soil_color",
            "soil_color_display",
            "nitrogen",
            "phosphorus",
            "potassium",
            "ph",
            "rainfall",
            "temperature",
            "recommendation_result",
            "created_at",
            "updated_at",
        ]

        read_only_fields = fields

    def get_user_full_name(self, obj):
        if obj.user:
            full_name = obj.user.get_full_name()
            return full_name if full_name else obj.user.username

        return ""


# ======================================================
# 4. DASHBOARD SERIALIZER
# Used for admin dashboard statistics
# ======================================================
class FertilizerDashboardStatsSerializer(serializers.Serializer):
    total_recommendations = serializers.IntegerField()
    total_farmer_recommendations = serializers.IntegerField()
    total_admin_recommendations = serializers.IntegerField()
    total_unique_farmers = serializers.IntegerField()
    most_used_crop = serializers.CharField(allow_blank=True)
    most_used_soil_color = serializers.CharField(allow_blank=True)