from django.urls import path

from .views import (
    FarmerDiseaseDetectionAPIView,
    FarmerDiseaseHistoryAPIView,
    AdminDiseaseDashboardAPIView,
    AdminDiseasePredictionAPIView,
)

app_name = "disease_detection"

urlpatterns = [
    # ==========================================================
    # DISEASE DETECTION - FARMER
    # ==========================================================
    path(
        "farmer/disease-detection/",
        FarmerDiseaseDetectionAPIView.as_view(),
        name="farmer-disease-detection",
    ),
    path(
        "farmer/disease-history/",
        FarmerDiseaseHistoryAPIView.as_view(),
        name="farmer-disease-history",
    ),

    # ==========================================================
    # DISEASE DETECTION - ADMIN
    # ==========================================================
    path(
        "admin/disease-dashboard/",
        AdminDiseaseDashboardAPIView.as_view(),
        name="admin-disease-dashboard",
    ),
    path(
        "admin/disease-predictions/",
        AdminDiseasePredictionAPIView.as_view(),
        name="admin-disease-prediction-list",
    ),
    path(
        "admin/disease-predictions/<int:prediction_id>/",
        AdminDiseasePredictionAPIView.as_view(),
        name="admin-disease-prediction-detail",
    ),
]