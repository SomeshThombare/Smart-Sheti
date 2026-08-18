from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError


class FertilizerRecommendationHistory(models.Model):
    class UserTypeChoices(models.TextChoices):
        ADMIN = "admin", "Admin"
        FARMER = "farmer", "Farmer"

    class CropChoices(models.TextChoices):
        COTTON = "Cotton", "Cotton"
        GINGER = "Ginger", "Ginger"
        GRAM = "Gram", "Gram"
        GRAPES = "Grapes", "Grapes"
        GROUNDNUT = "Groundnut", "Groundnut"
        JOWAR = "Jowar", "Jowar"
        MAIZE = "Maize", "Maize"
        MASOOR = "Masoor", "Masoor"
        MOONG = "Moong", "Moong"
        RICE = "Rice", "Rice"
        SOYBEAN = "Soybean", "Soybean"
        SUGARCANE = "Sugarcane", "Sugarcane"
        TUR = "Tur", "Tur"
        TURMERIC = "Turmeric", "Turmeric"
        URAD = "Urad", "Urad"
        WHEAT = "Wheat", "Wheat"

    class SoilColorChoices(models.TextChoices):
        BLACK = "Black", "Black"
        DARK_BROWN = "Dark Brown", "Dark Brown"
        LIGHT_BROWN = "Light Brown", "Light Brown"
        MEDIUM_BROWN = "Medium Brown", "Medium Brown"
        RED = "Red", "Red"
        REDDISH_BROWN = "Reddish Brown", "Reddish Brown"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="fertilizer_recommendations",
    )

    user_type = models.CharField(
        max_length=20,
        choices=UserTypeChoices.choices,
        db_index=True,
    )

    crop = models.CharField(
        max_length=100,
        choices=CropChoices.choices,
        db_index=True,
    )

    soil_color = models.CharField(
        max_length=100,
        choices=SoilColorChoices.choices,
        db_index=True,
    )

    nitrogen = models.FloatField()
    phosphorus = models.FloatField()
    potassium = models.FloatField()

    ph = models.FloatField(
        verbose_name="pH",
    )

    rainfall = models.FloatField()
    temperature = models.FloatField()

    recommendation_result = models.JSONField()

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Fertilizer Recommendation History"
        verbose_name_plural = "Fertilizer Recommendation Histories"

        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["user_type"]),
            models.Index(fields=["crop"]),
            models.Index(fields=["soil_color"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["updated_at"]),
            models.Index(fields=["user_type", "crop"]),
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["crop", "soil_color"]),
        ]

        constraints = [
            models.CheckConstraint(
                condition=models.Q(nitrogen__gte=0),
                name="fertilizer_history_nitrogen_gte_0",
            ),
            models.CheckConstraint(
                condition=models.Q(phosphorus__gte=0),
                name="fertilizer_history_phosphorus_gte_0",
            ),
            models.CheckConstraint(
                condition=models.Q(potassium__gte=0),
                name="fertilizer_history_potassium_gte_0",
            ),
            models.CheckConstraint(
                condition=models.Q(ph__gte=0) & models.Q(ph__lte=14),
                name="fertilizer_history_ph_between_0_14",
            ),
            models.CheckConstraint(
                condition=models.Q(rainfall__gte=0),
                name="fertilizer_history_rainfall_gte_0",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(temperature__gte=-50)
                    & models.Q(temperature__lte=100)
                ),
                name="fertilizer_history_temperature_valid_range",
            ),
        ]

    def __str__(self):
        return f"{self.user} - {self.crop} - {self.soil_color} - {self.created_at}"

    # =========================
    # Validation
    # =========================
    def clean(self):
        self._normalize_fields()

        errors = {}

        if not self.user:
            errors["user"] = "User is required."

        if not self.user_type:
            errors["user_type"] = "User type is required."
        elif self.user_type not in self.UserTypeChoices.values:
            errors["user_type"] = "Invalid user type."

        if not self.crop:
            errors["crop"] = "Crop is required."
        elif self.crop not in self.CropChoices.values:
            errors["crop"] = "Invalid crop selected."

        if not self.soil_color:
            errors["soil_color"] = "Soil color is required."
        elif self.soil_color not in self.SoilColorChoices.values:
            errors["soil_color"] = "Invalid soil color selected."

        if self.nitrogen is None:
            errors["nitrogen"] = "Nitrogen value is required."
        elif self.nitrogen < 0:
            errors["nitrogen"] = "Nitrogen cannot be negative."

        if self.phosphorus is None:
            errors["phosphorus"] = "Phosphorus value is required."
        elif self.phosphorus < 0:
            errors["phosphorus"] = "Phosphorus cannot be negative."

        if self.potassium is None:
            errors["potassium"] = "Potassium value is required."
        elif self.potassium < 0:
            errors["potassium"] = "Potassium cannot be negative."

        if self.ph is None:
            errors["ph"] = "pH value is required."
        elif self.ph < 0 or self.ph > 14:
            errors["ph"] = "pH must be between 0 and 14."

        if self.rainfall is None:
            errors["rainfall"] = "Rainfall value is required."
        elif self.rainfall < 0:
            errors["rainfall"] = "Rainfall cannot be negative."

        if self.temperature is None:
            errors["temperature"] = "Temperature value is required."
        elif self.temperature < -50 or self.temperature > 100:
            errors["temperature"] = "Temperature must be between -50 and 100."

        if self.recommendation_result in [None, ""]:
            errors["recommendation_result"] = "Recommendation result is required."
        elif not isinstance(self.recommendation_result, dict):
            errors["recommendation_result"] = "Recommendation result must be valid JSON object."

        if errors:
            raise ValidationError(errors)

    # =========================
    # Save
    # =========================
    def save(self, *args, **kwargs):
        self._normalize_fields()
        self.full_clean()
        super().save(*args, **kwargs)

    # =========================
    # Normalization
    # =========================
    def _normalize_fields(self):
        if self.user_type:
            self.user_type = str(self.user_type).strip().lower()

        if self.crop:
            self.crop = str(self.crop).strip().title()

        if self.soil_color:
            self.soil_color = str(self.soil_color).strip().title()

        self.nitrogen = self._to_float(self.nitrogen)
        self.phosphorus = self._to_float(self.phosphorus)
        self.potassium = self._to_float(self.potassium)
        self.ph = self._to_float(self.ph)
        self.rainfall = self._to_float(self.rainfall)
        self.temperature = self._to_float(self.temperature)

    def _to_float(self, value):
        if value in [None, ""]:
            return None

        try:
            return float(value)
        except (TypeError, ValueError):
            return value