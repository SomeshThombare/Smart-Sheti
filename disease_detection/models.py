from django.db import models
from django.conf import settings


class DiseasePrediction(models.Model):

    STATUS_CHOICES = (
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
    )

    # 🔐 User (Farmer)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # 📷 Uploaded Image
    image = models.ImageField(upload_to="disease_images/")

    # 🌱 Prediction Data
    crop_name = models.CharField(max_length=100, default="", blank=True)
    disease_name = models.CharField(max_length=150, default="", blank=True)
    confidence = models.FloatField(default=0)

    # 💊 AI Output
    treatment = models.TextField(default="", blank=True)
    suggestion = models.TextField(default="", blank=True)

    # 🔍 Model Info
    class_name = models.CharField(max_length=150, null=True, blank=True)
    predicted_index = models.IntegerField(null=True, blank=True)

    # ⚠️ Status Tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="SUCCESS"
    )

    error_message = models.TextField(null=True, blank=True)

    # ⏱️ Timestamp
    created_at = models.DateTimeField(auto_now_add=True)

    # 📊 Default Order
    class Meta:
        ordering = ["-created_at"]

    # 🧾 String Display
    def __str__(self):
        return f"{self.user} | {self.crop_name} | {self.disease_name} | {self.status}"