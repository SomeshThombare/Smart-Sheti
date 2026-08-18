from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class CropPredictionHistory(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="crop_predictions",
        null=True,
        blank=True,
    )

    nitrogen = models.FloatField()

    phosphorus = models.FloatField()

    potassium = models.FloatField()

    temperature = models.FloatField()

    humidity = models.FloatField()

    ph = models.FloatField(
        verbose_name="pH"
    )

    rainfall = models.FloatField()

    predicted_crop = models.CharField(
        max_length=100,
        db_index=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "-created_at"
        ]

        verbose_name = (
            "Crop Prediction History"
        )

        verbose_name_plural = (
            "Crop Prediction Histories"
        )

        indexes = [
            models.Index(fields=["user"]),

            models.Index(
                fields=["predicted_crop"]
            ),

            models.Index(
                fields=["created_at"]
            ),

            models.Index(
                fields=["updated_at"]
            ),

            models.Index(
                fields=["user", "created_at"]
            ),

            models.Index(
                fields=[
                    "predicted_crop",
                    "created_at",
                ]
            ),
        ]

        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    nitrogen__gte=0
                ),
                name=(
                    "crop_history_nitrogen_gte_0"
                ),
            ),

            models.CheckConstraint(
                condition=models.Q(
                    phosphorus__gte=0
                ),
                name=(
                    "crop_history_phosphorus_gte_0"
                ),
            ),

            models.CheckConstraint(
                condition=models.Q(
                    potassium__gte=0
                ),
                name=(
                    "crop_history_potassium_gte_0"
                ),
            ),

            models.CheckConstraint(
                condition=(
                    models.Q(
                        temperature__gte=-50
                    )
                    &
                    models.Q(
                        temperature__lte=100
                    )
                ),
                name=(
                    "crop_history_temperature_valid_range"
                ),
            ),

            models.CheckConstraint(
                condition=(
                    models.Q(
                        humidity__gte=0
                    )
                    &
                    models.Q(
                        humidity__lte=100
                    )
                ),
                name=(
                    "crop_history_humidity_between_0_100"
                ),
            ),

            models.CheckConstraint(
                condition=(
                    models.Q(ph__gte=0)
                    &
                    models.Q(ph__lte=14)
                ),
                name=(
                    "crop_history_ph_between_0_14"
                ),
            ),

            models.CheckConstraint(
                condition=models.Q(
                    rainfall__gte=0
                ),
                name=(
                    "crop_history_rainfall_gte_0"
                ),
            ),
        ]

    def __str__(self):
        return (
            f"{self.predicted_crop} - "
            f"{self.user} - "
            f"{self.created_at}"
        )

    # ==================================================
    # VALIDATION
    # ==================================================
    def clean(self):
        self._normalize_fields()

        errors = {}

        if self.nitrogen is None:
            errors["nitrogen"] = (
                "Nitrogen value is required."
            )

        elif self.nitrogen < 0:
            errors["nitrogen"] = (
                "Nitrogen cannot be negative."
            )

        if self.phosphorus is None:
            errors["phosphorus"] = (
                "Phosphorus value is required."
            )

        elif self.phosphorus < 0:
            errors["phosphorus"] = (
                "Phosphorus cannot be negative."
            )

        if self.potassium is None:
            errors["potassium"] = (
                "Potassium value is required."
            )

        elif self.potassium < 0:
            errors["potassium"] = (
                "Potassium cannot be negative."
            )

        if self.temperature is None:
            errors["temperature"] = (
                "Temperature value is required."
            )

        elif (
            self.temperature < -50
            or self.temperature > 100
        ):
            errors["temperature"] = (
                "Temperature must be between -50 and 100."
            )

        if self.humidity is None:
            errors["humidity"] = (
                "Humidity value is required."
            )

        elif (
            self.humidity < 0
            or self.humidity > 100
        ):
            errors["humidity"] = (
                "Humidity must be between 0 and 100."
            )

        if self.ph is None:
            errors["ph"] = (
                "pH value is required."
            )

        elif self.ph < 0 or self.ph > 14:
            errors["ph"] = (
                "pH must be between 0 and 14."
            )

        if self.rainfall is None:
            errors["rainfall"] = (
                "Rainfall value is required."
            )

        elif self.rainfall < 0:
            errors["rainfall"] = (
                "Rainfall cannot be negative."
            )

        if not self.predicted_crop:
            errors["predicted_crop"] = (
                "Predicted crop is required."
            )

        if errors:
            raise ValidationError(errors)

    # ==================================================
    # SAVE
    # ==================================================
    def save(self, *args, **kwargs):
        self._normalize_fields()

        self.full_clean()

        super().save(*args, **kwargs)

    # ==================================================
    # NORMALIZATION
    # ==================================================
    def _normalize_fields(self):
        if self.predicted_crop:
            self.predicted_crop = str(
                self.predicted_crop
            ).strip().title()

        self.nitrogen = self._to_float(
            self.nitrogen
        )

        self.phosphorus = self._to_float(
            self.phosphorus
        )

        self.potassium = self._to_float(
            self.potassium
        )

        self.temperature = self._to_float(
            self.temperature
        )

        self.humidity = self._to_float(
            self.humidity
        )

        self.ph = self._to_float(
            self.ph
        )

        self.rainfall = self._to_float(
            self.rainfall
        )

    # ==================================================
    # FLOAT CONVERTER
    # ==================================================
    def _to_float(self, value):
        if value in [None, ""]:
            return None

        try:
            return float(value)

        except (
            TypeError,
            ValueError,
        ):
            return value