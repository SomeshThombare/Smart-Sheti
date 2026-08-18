# pest_detection/urls.py

from django.urls import path

from .views import (
    FarmerPestDashboardAPIView,
    FarmerPestDetectionAPIView,
    FarmerPestHistoryAPIView,
    AdminPestDashboardAPIView,
    AdminPestPredictionAPIView,
    AdminPestPredictionExportCSVAPIView,
)

app_name = "pest_detection"

urlpatterns = [
    # =========================
    # FARMER SIDE URLS
    # =========================

    path(
        "farmer/pest-dashboard/",
        FarmerPestDashboardAPIView.as_view(),
        name="farmer_pest_dashboard",
    ),

    path(
        "farmer/pest-detection/",
        FarmerPestDetectionAPIView.as_view(),
        name="farmer_pest_detection",
    ),

    path(
        "farmer/pest-history/",
        FarmerPestHistoryAPIView.as_view(),
        name="farmer_pest_history",
    ),


    # =========================
    # ADMIN SIDE URLS
    # =========================

    path(
        "admin/pest-dashboard/",
        AdminPestDashboardAPIView.as_view(),
        name="admin_pest_dashboard",
    ),

    path(
        "admin/pest-predictions/",
        AdminPestPredictionAPIView.as_view(),
        name="admin_pest_predictions",
    ),

    path(
        "admin/pest-predictions/<int:prediction_id>/",
        AdminPestPredictionAPIView.as_view(),
        name="admin_pest_prediction_detail",
    ),

    path(
        "admin/pest-predictions/export-csv/",
        AdminPestPredictionExportCSVAPIView.as_view(),
        name="admin_pest_predictions_export_csv",
    ),
]