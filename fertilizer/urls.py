from django.urls import path

from .views import (
    AdminFertilizerRecommendationAPIView,
    FarmerFertilizerRecommendationAPIView,
    AdminFertilizerFormPageView,
    FarmerFertilizerFormPageView,
    AdminRecommendationHistoryAPIView,
    AdminRecommendationHistoryDetailAPIView,
    FarmerRecommendationHistoryAPIView,
    FarmerRecommendationHistoryDetailAPIView,
    FertilizerDashboardAPIView,
    FertilizerExportCSVAPIView,
)

app_name = "fertilizer"

urlpatterns = [
    path("admin/", AdminFertilizerRecommendationAPIView.as_view(), name="admin_fertilizer"),
    path("farmer/", FarmerFertilizerRecommendationAPIView.as_view(), name="farmer_fertilizer"),

    path("admin/form/", AdminFertilizerFormPageView.as_view(), name="admin_fertilizer_form"),
    path("farmer/form/", FarmerFertilizerFormPageView.as_view(), name="farmer_fertilizer_form"),

    path("admin/history/", AdminRecommendationHistoryAPIView.as_view(), name="admin_history"),
    path("admin/history/<int:pk>/", AdminRecommendationHistoryDetailAPIView.as_view(), name="admin_history_detail"),

    path("farmer/history/", FarmerRecommendationHistoryAPIView.as_view(), name="farmer_history"),
    path("farmer/history/<int:pk>/", FarmerRecommendationHistoryDetailAPIView.as_view(), name="farmer_history_detail"),

    path("admin/dashboard/", FertilizerDashboardAPIView.as_view(), name="admin_dashboard"),
    path("admin/export/csv/", FertilizerExportCSVAPIView.as_view(), name="export_csv"),
]