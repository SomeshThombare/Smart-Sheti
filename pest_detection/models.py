# pest_detection/models.py

from django.conf import settings
from django.db import models


class PestPrediction(models.Model):
    STATUS_SUCCESS = "SUCCESS"
    STATUS_FAILED = "FAILED"

    SEVERITY_HIGH = "HIGH"
    SEVERITY_MEDIUM = "MEDIUM"
    SEVERITY_LOW = "LOW"
    SEVERITY_UNCLEAR = "UNCLEAR"

    STATUS_CHOICES = [
        (STATUS_SUCCESS, "Success"),
        (STATUS_FAILED, "Failed"),
    ]

    SEVERITY_CHOICES = [
        (SEVERITY_HIGH, "High"),
        (SEVERITY_MEDIUM, "Medium"),
        (SEVERITY_LOW, "Low"),
        (SEVERITY_UNCLEAR, "Unclear"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="pest_predictions",
    )

    image = models.ImageField(
        upload_to="pest_images/",
    )

    pest_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    confidence = models.FloatField(
        default=0,
    )

    solution = models.TextField(
        blank=True,
        default="",
    )

    class_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    predicted_index = models.IntegerField(
        null=True,
        blank=True,
    )

    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        blank=True,
        default=SEVERITY_UNCLEAR,
    )

    treatment_priority = models.CharField(
        max_length=100,
        blank=True,
        default="Upload Clear Image Again",
    )

    top_predictions = models.JSONField(
        default=list,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_SUCCESS,
    )

    error_message = models.TextField(
        blank=True,
        default="",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Pest Prediction"
        verbose_name_plural = "Pest Predictions"

        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["pest_name"]),
            models.Index(fields=["confidence"]),
            models.Index(fields=["severity"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["user", "status"]),
        ]

    def __str__(self):
        return f"{self.pest_name or 'Unknown Pest'} - {self.confidence}%"

    @property
    def is_success(self):
        return self.status == self.STATUS_SUCCESS

    @property
    def is_failed(self):
        return self.status == self.STATUS_FAILED

    def calculate_severity(self):
        confidence = float(self.confidence or 0)

        if confidence >= 90:
            return self.SEVERITY_HIGH

        if confidence >= 70:
            return self.SEVERITY_MEDIUM

        if confidence >= 60:
            return self.SEVERITY_LOW

        return self.SEVERITY_UNCLEAR

    def calculate_treatment_priority(self):
        confidence = float(self.confidence or 0)

        if confidence >= 90:
            return "Immediate Action Required"

        if confidence >= 70:
            return "Treat Within 3 Days"

        if confidence >= 60:
            return "Monitor Closely"

        return "Upload Clear Image Again"

    def save(self, *args, **kwargs):
        if not self.severity:
            self.severity = self.calculate_severity()

        if not self.treatment_priority:
            self.treatment_priority = self.calculate_treatment_priority()

        super().save(*args, **kwargs)