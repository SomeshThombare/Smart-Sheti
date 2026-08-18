from django.urls import path
from . import views

urlpatterns = [

    # ============================================================
    # WEB URLS
    # ============================================================

    # AUTH WEB
    path("login/", views.LoginAPIView.as_view(), name="login"),
    path("logout/", views.LogoutAPIView.as_view(), name="logout"),

    # OTP WEB
    path("web/send-otp/", views.SendOTPWebView.as_view(), name="send_otp_web"),
    path("verify-otp/", views.VerifyOTPWebView.as_view(), name="verify_otp"),

    # FORGOT PASSWORD WEB
    path("forgot-password/", views.ForgotPasswordAPIView.as_view(), name="forgot_password"),
    path("verify-forgot-password-otp/", views.VerifyForgotPasswordOTPAPIView.as_view(), name="verify_forgot_password_otp"),
    path("reset-password/", views.ResetPasswordAPIView.as_view(), name="reset_password"),

    # REGISTRATION WEB
    path("admin/register/", views.AdminRegistrationWebView.as_view(), name="admin_register"),
    path("web/farmer-register/", views.FarmerRegistrationWebView.as_view(), name="farmer_register_web"),

    # DASHBOARD WEB
    path("admin/dashboard/", views.AdminDashboardView.as_view(), name="admin_dashboard"),
    path("farmer/dashboard/", views.FarmerDashboardView.as_view(), name="farmer_dashboard"),
    
    

    # PROFILE WEB
    path("profile/update/", views.CurrentProfileUpdateWebView.as_view(), name="current_profile_update_web"),
    path("farmer/profile/update/", views.CurrentFarmerProfileUpdateWebView.as_view(), name="current_farmer_profile_update_web"),

    # PASSWORD WEB
    path("change-password/", views.ChangePasswordAPIView.as_view(), name="change_password"),

    # ADMIN WEB
    path("web/admins/", views.AdminListDetailView.as_view(), name="admin_list_web"),
    path("web/admins/<str:username>/", views.AdminListDetailView.as_view(), name="admin_detail_web"),

    # ============================================================
    #                       FARMER WEB
    # ============================================================

    path(
        "web/farmers/",
        views.FarmerListDetailView.as_view(),
        name="farmer_list_web"
    ),

    path(
        "web/farmers/<str:username>/",
        views.FarmerListDetailView.as_view(),
        name="farmer_detail_web"
    ),


    # ============================================================
    #               ADMIN SIDE FARMER MANAGEMENT
    # ============================================================

    path(
        "admin-side/farmers/search/",
        views.admin_search_farmers,
        name="admin_search_farmers"
    ),

    path(
        "admin-side/farmers/status/<int:user_id>/",
        views.admin_toggle_farmer_status,
        name="admin_toggle_farmer_status"
    ),


    # ============================================================
    # API URLS
    # ============================================================

    # AUTH API
    path("api/v1/login/", views.LoginAPIView.as_view(), name="login_api"),
    path("api/v1/logout/", views.LogoutAPIView.as_view(), name="logout_api"),

    # OTP API
    path("api/v1/send-otp/", views.SendOTPAPIView.as_view(), name="send_otp_api"),
    path("api/v1/verify-otp/", views.VerifyOTPAPIView.as_view(), name="verify_otp_api"),

    # FORGOT PASSWORD API
    path("api/v1/forgot-password/", views.ForgotPasswordAPIView.as_view(), name="forgot_password_api"),
    path("api/v1/verify-forgot-password-otp/", views.VerifyForgotPasswordOTPAPIView.as_view(), name="verify_forgot_password_otp_api"),
    path("api/v1/reset-password/", views.ResetPasswordAPIView.as_view(), name="reset_password_api"),

    # REGISTRATION API
    path("api/v1/admin/register/", views.AdminRegistrationAPIView.as_view(), name="admin_register_api"),
    path("api/v1/farmer-register/", views.FarmerRegistrationAPIView.as_view(), name="farmer_register_api"),

    # DASHBOARD API
    path("api/v1/admin/dashboard/", views.AdminDashboardAPIView.as_view(), name="admin_dashboard_api"),
    path("api/v1/farmer/dashboard/", views.FarmerDashboardAPIView.as_view(), name="farmer_dashboard_api"),

    # PROFILE API
    path("api/v1/profile/update/", views.CurrentProfileUpdateAPIView.as_view(), name="current_profile_update_api"),
    path("api/v1/farmer/profile/update/", views.CurrentFarmerProfileUpdateAPIView.as_view(), name="current_farmer_profile_update_api"),

    # PASSWORD API
    path("api/v1/change-password/", views.ChangePasswordAPIView.as_view(), name="change_password_api"),

    # ADMIN API
    path("api/v1/admins/", views.AdminListDetailView.as_view(), name="admin_list_api"),
    path("api/v1/admins/<str:username>/", views.AdminListDetailView.as_view(), name="admin_detail_api"),
    path("api/v1/admins/me/delete/", views.AdminListDetailView.as_view(), name="admin_delete_current_api"),
    path("api/v1/admins/<str:username>/delete/", views.AdminListDetailView.as_view(), name="admin_delete_by_username_api"),

    # FARMER API
    path("api/v1/farmers/", views.FarmerListDetailView.as_view(), name="farmer_list_api"),
    path("api/v1/farmers/<str:username>/", views.FarmerListDetailView.as_view(), name="farmer_detail_api"),
    path("api/v1/farmers/me/delete/", views.FarmerListDetailView.as_view(), name="farmer_delete_current_api"),
    path("api/v1/farmers/<str:username>/delete/", views.FarmerListDetailView.as_view(), name="farmer_delete_by_username_api"),
]