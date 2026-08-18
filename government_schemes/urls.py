from django.urls import path

from . import views
from .views import (
    AdminGovernmentSchemeAPIView,
    FarmerGovernmentSchemeAPIView,
    AdminGovernmentSchemeFormPageView,
)

app_name = "government_scheme"

urlpatterns = [

    # ==================================================
    # ADMIN DASHBOARD
    # ==================================================

    path(
        "admin/schemes/dashboard/",
        views.admin_scheme_dashboard,
        name="admin-scheme-dashboard",
    ),


    path(
        "farmer/schemes/dashboard/",
        views.farmer_scheme_dashboard,
        name="farmer-scheme-dashboard",
    ),
    # ==================================================
    # ADMIN GOVERNMENT SCHEMES
    # ==================================================

    path(
        "admin/government-schemes/",
        AdminGovernmentSchemeAPIView.as_view(),
        name="admin_government_scheme_list",
    ),

    path(
        "admin/government-schemes/create/",
        AdminGovernmentSchemeFormPageView.as_view(),
        name="admin_government_scheme_create_form",
    ),

    path(
        "admin/government-schemes/<str:scheme_code>/",
        AdminGovernmentSchemeAPIView.as_view(),
        name="admin_government_scheme_detail",
    ),

    # ==================================================
    # FARMER GOVERNMENT SCHEMES
    # ==================================================

    path(
        "farmer/government-schemes/",
        FarmerGovernmentSchemeAPIView.as_view(),
        name="farmer_government_scheme_list",
    ),

    path(
        "farmer/government-schemes/<str:scheme_code>/",
        FarmerGovernmentSchemeAPIView.as_view(),
        name="farmer_government_scheme_detail",
    ),

]