from rest_framework import serializers

from .models import CropPredictionHistory


# ======================================================
# 1. INPUT SERIALIZER
# Used for admin/farmer crop prediction input API
# ======================================================
class CropRecommendationInputSerializer(serializers.Serializer):
    nitrogen = serializers.FloatField(
        min_value=0,
        default=80,
    )

    phosphorus = serializers.FloatField(
        min_value=0,
        default=50,
    )

    potassium = serializers.FloatField(
        min_value=0,
        default=50,
    )

    temperature = serializers.FloatField(
        min_value=-50,
        max_value=100,
        default=25,
    )

    humidity = serializers.FloatField(
        min_value=0,
        max_value=100,
        default=60,
    )

    ph = serializers.FloatField(
        min_value=0,
        max_value=14,
        default=6.5,
    )

    rainfall = serializers.FloatField(
        min_value=0,
        default=100,
    )

    # =========================
    # Field Validators
    # =========================
    def validate_nitrogen(self, value):
        return self._validate_positive_number(value, "Nitrogen")

    def validate_phosphorus(self, value):
        return self._validate_positive_number(value, "Phosphorus")

    def validate_potassium(self, value):
        return self._validate_positive_number(value, "Potassium")

    def validate_temperature(self, value):
        if value is None:
            raise serializers.ValidationError("Temperature value is required.")

        value = float(value)

        if value < -50 or value > 100:
            raise serializers.ValidationError(
                "Temperature must be between -50 and 100."
            )

        return value

    def validate_humidity(self, value):
        if value is None:
            raise serializers.ValidationError("Humidity value is required.")

        value = float(value)

        if value < 0 or value > 100:
            raise serializers.ValidationError(
                "Humidity must be between 0 and 100."
            )

        return value

    def validate_ph(self, value):
        if value is None:
            raise serializers.ValidationError("pH value is required.")

        value = float(value)

        if value < 0 or value > 14:
            raise serializers.ValidationError("pH must be between 0 and 14.")

        return value

    def validate_rainfall(self, value):
        return self._validate_positive_number(value, "Rainfall")

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
        attrs["Nitrogen"] = attrs.get("nitrogen")
        attrs["Phosphorus"] = attrs.get("phosphorus")
        attrs["Potassium"] = attrs.get("potassium")
        attrs["Temperature"] = attrs.get("temperature")
        attrs["Humidity"] = attrs.get("humidity")
        attrs["Ph"] = attrs.get("ph")
        attrs["Rainfall"] = attrs.get("rainfall")

        return attrs


# ======================================================
# 2. HISTORY SERIALIZER
# Used for create/update/edit crop prediction history
# ======================================================
class CropPredictionHistorySerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        source="user.username",
        read_only=True,
    )

    user_full_name = serializers.SerializerMethodField(read_only=True)

    predicted_crop_display = serializers.SerializerMethodField(read_only=True)

    created_at = serializers.ReadOnlyField()
    updated_at = serializers.ReadOnlyField()

    class Meta:
        model = CropPredictionHistory

        fields = [
            "id",
            "user",
            "username",
            "user_full_name",
            "nitrogen",
            "phosphorus",
            "potassium",
            "temperature",
            "humidity",
            "ph",
            "rainfall",
            "predicted_crop",
            "predicted_crop_display",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "username",
            "user_full_name",
            "predicted_crop_display",
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

    def get_predicted_crop_display(self, obj):
        if obj.predicted_crop:
            return str(obj.predicted_crop).title()

        return ""

    # =========================
    # Number Validators
    # =========================
    def validate_nitrogen(self, value):
        return self._validate_positive_number(value, "Nitrogen")

    def validate_phosphorus(self, value):
        return self._validate_positive_number(value, "Phosphorus")

    def validate_potassium(self, value):
        return self._validate_positive_number(value, "Potassium")

    def validate_temperature(self, value):
        if value is None:
            raise serializers.ValidationError("Temperature value is required.")

        value = float(value)

        if value < -50 or value > 100:
            raise serializers.ValidationError(
                "Temperature must be between -50 and 100."
            )

        return value

    def validate_humidity(self, value):
        if value is None:
            raise serializers.ValidationError("Humidity value is required.")

        value = float(value)

        if value < 0 or value > 100:
            raise serializers.ValidationError(
                "Humidity must be between 0 and 100."
            )

        return value

    def validate_ph(self, value):
        if value is None:
            raise serializers.ValidationError("pH value is required.")

        value = float(value)

        if value < 0 or value > 14:
            raise serializers.ValidationError("pH must be between 0 and 14.")

        return value

    def validate_rainfall(self, value):
        return self._validate_positive_number(value, "Rainfall")

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
    # Text Validator
    # =========================
    def validate_predicted_crop(self, value):
        if value:
            value = str(value).strip().title()

        if not value:
            raise serializers.ValidationError("Predicted crop is required.")

        return value

    # =========================
    # Object Level Validation
    # =========================
    def validate(self, attrs):
        request = self.context.get("request")
        instance = getattr(self, "instance", None)

        selected_user = attrs.get(
            "user",
            getattr(instance, "user", None),
        )

        if request and request.user and request.user.is_authenticated:
            current_user = request.user
            current_user_type = getattr(current_user, "user_type", None)

            is_admin = (
                current_user_type == "admin"
                or current_user.is_staff
                or current_user.is_superuser
            )

            if not is_admin:
                attrs["user"] = current_user

                if selected_user and selected_user != current_user:
                    raise serializers.ValidationError({
                        "user": "You cannot create crop prediction history for another user."
                    })

        return attrs

    # =========================
    # Create / Update
    # =========================
    def create(self, validated_data):
        if validated_data.get("predicted_crop"):
            validated_data["predicted_crop"] = str(
                validated_data["predicted_crop"]
            ).strip().title()

        return CropPredictionHistory.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            if attr == "predicted_crop" and value:
                value = str(value).strip().title()

            setattr(instance, attr, value)

        instance.save()
        return instance


# ======================================================
# 3. HISTORY LIST SERIALIZER
# Used for table/list response
# ======================================================
class CropPredictionHistoryListSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        source="user.username",
        read_only=True,
    )

    user_full_name = serializers.SerializerMethodField(read_only=True)

    predicted_crop_display = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CropPredictionHistory

        fields = [
            "id",
            "username",
            "user_full_name",
            "nitrogen",
            "phosphorus",
            "potassium",
            "temperature",
            "humidity",
            "ph",
            "rainfall",
            "predicted_crop",
            "predicted_crop_display",
            "created_at",
            "updated_at",
        ]

        read_only_fields = fields

    def get_user_full_name(self, obj):
        if obj.user:
            full_name = obj.user.get_full_name()
            return full_name if full_name else obj.user.username

        return ""

    def get_predicted_crop_display(self, obj):
        if obj.predicted_crop:
            return str(obj.predicted_crop).title()

        return ""


# ======================================================
# 4. DASHBOARD SERIALIZER
# Used for admin dashboard statistics
# ======================================================
class CropDashboardStatsSerializer(serializers.Serializer):
    total_predictions = serializers.IntegerField()
    total_unique_users = serializers.IntegerField()
    most_predicted_crop = serializers.CharField(allow_blank=True)
    average_nitrogen = serializers.FloatField()
    average_phosphorus = serializers.FloatField()
    average_potassium = serializers.FloatField()
    average_temperature = serializers.FloatField()
    average_humidity = serializers.FloatField()
    average_ph = serializers.FloatField()
    average_rainfall = serializers.FloatField()