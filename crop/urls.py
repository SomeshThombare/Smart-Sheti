from django.urls import path

from .views import (
    FarmerCropRecommendationAPIView,
    FarmerCropHistoryAPIView,
    FarmerCropHistoryDetailAPIView,
    AdminCropDashboardAPIView,
    AdminCropRecordsAPIView,
    AdminCropExportCSVAPIView,
)


urlpatterns = [
    path(
        "farmer/recommend/",
        FarmerCropRecommendationAPIView.as_view(),
        name="farmer_crop_recommendation"
    ),

    path(
        "farmer/history/",
        FarmerCropHistoryAPIView.as_view(),
        name="farmer_crop_history"
    ),

    path(
        "farmer/result/<int:pk>/",
        FarmerCropHistoryDetailAPIView.as_view(),
        name="farmer_crop_result"
    ),

    path(
        "admin/dashboard/",
        AdminCropDashboardAPIView.as_view(),
        name="admin_crop_dashboard"
    ),

    path(
        "admin/records/",
        AdminCropRecordsAPIView.as_view(),
        name="admin_crop_records"
    ),

    path(
        "admin/export-csv/",
        AdminCropExportCSVAPIView.as_view(),
        name="admin_crop_export_csv"
    ),
]