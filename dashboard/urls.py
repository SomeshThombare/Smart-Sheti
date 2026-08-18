from django.urls import path
from .views import index, admin_dashboard, farmer_dashboard, dashboard_redirect

urlpatterns = [
    path("", index, name="index"),
    path("dashboard/", dashboard_redirect, name="dashboard-redirect"),
    path("admin-dashboard/", admin_dashboard, name="admin-dashboard"),
    path("farmer-dashboard/", farmer_dashboard, name="farmer-dashboard"),
]