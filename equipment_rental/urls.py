from django.urls import path

from .views import (
    AdminEquipmentAPIView,
    AdminEquipmentFormPageView,
    FarmerEquipmentAPIView,

    AdminEquipmentBookingAPIView,
    AdminEquipmentBookingFormPageView,
    FarmerEquipmentBookingAPIView,
    FarmerEquipmentBookingFormPageView,
    FarmerEquipmentBookingHistoryAPIView,

    FarmerPaymentPageAPIView,
    FarmerBookingCreateRazorpayOrderAPIView,
    FarmerBookingVerifyPaymentAPIView,
    FarmerBookingCancelAPIView,
    admin_dashboard_page,
    farmer_dashboard_page,
)

app_name = "equipment"

urlpatterns = [

    path(
        "admin/equipments/",
        AdminEquipmentAPIView.as_view(),
        name="admin-equipment-list"
    ),

    path(
        "admin/equipments/form/",
        AdminEquipmentFormPageView.as_view(),
        name="admin-equipment-form-page"
    ),

    path(
        "admin/equipments/<str:equipment_code>/",
        AdminEquipmentAPIView.as_view(),
        name="admin-equipment-detail"
    ),

    path(
        "farmer/equipments/",
        FarmerEquipmentAPIView.as_view(),
        name="farmer-equipment-list"
    ),

    path(
        "farmer/equipments/<str:equipment_code>/",
        FarmerEquipmentAPIView.as_view(),
        name="farmer-equipment-detail"
    ),

    path(
        "admin/bookings/",
        AdminEquipmentBookingAPIView.as_view(),
        name="admin-booking-list"
    ),

    path(
        "admin/bookings/form/",
        AdminEquipmentBookingFormPageView.as_view(),
        name="admin-booking-form-page"
    ),

    path(
        "admin/bookings/<str:booking_code>/",
        AdminEquipmentBookingAPIView.as_view(),
        name="admin-booking-detail"
    ),

    path(
        "farmer/bookings/",
        FarmerEquipmentBookingAPIView.as_view(),
        name="farmer-booking-list"
    ),

    path(
        "farmer/bookings/form/",
        FarmerEquipmentBookingFormPageView.as_view(),
        name="farmer-booking-form-page"
    ),

    path(
        "farmer/bookings/history/",
        FarmerEquipmentBookingHistoryAPIView.as_view(),
        name="farmer-booking-history"
    ),

    path(
        "farmer/bookings/<str:booking_code>/",
        FarmerEquipmentBookingAPIView.as_view(),
        name="farmer-booking-detail"
    ),

    path(
        "farmer/bookings/<str:booking_code>/payment/",
        FarmerPaymentPageAPIView.as_view(),
        name="farmer-payment-page"
    ),

    path(
        "farmer/bookings/<str:booking_code>/create-order/",
        FarmerBookingCreateRazorpayOrderAPIView.as_view(),
        name="farmer-create-razorpay-order"
    ),

    path(
        "farmer/bookings/<str:booking_code>/verify-payment/",
        FarmerBookingVerifyPaymentAPIView.as_view(),
        name="farmer-verify-payment"
    ),

    path(
        "farmer/bookings/<str:booking_code>/cancel/",
        FarmerBookingCancelAPIView.as_view(),
        name="farmer-booking-cancel"
    ),

    path(
        "farmer/dashboard/",
        farmer_dashboard_page,
        name="farmer-dashboard-page"
    ),

    path(
    "admin/dashboard/",
    admin_dashboard_page,
    name="admin-dashboard-page"
    ),  
]