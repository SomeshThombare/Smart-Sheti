from django.urls import path
from .views import (
    AdminChatbotAPIView,
    FarmerChatbotAPIView,
    AdminChatbotPageView,
    AdminChatbotDashboardView,
    FarmerChatbotDashboardView,
    FarmerChatbotPageView,
)

urlpatterns = [
    path("admin/chat/", AdminChatbotAPIView.as_view(), name="admin_chatbot_api"),
    path("farmer/chat/", FarmerChatbotAPIView.as_view(), name="farmer_chatbot_api"),
    path("admin/chat/page/", AdminChatbotPageView.as_view(), name="admin_chatbot_page"),
    path("farmer/chat/page/", FarmerChatbotPageView.as_view(), name="farmer_chatbot_page"),

    path(
        "admin/chatbot/dashboard/",
        AdminChatbotDashboardView.as_view(),
        name="admin_chatbot_dashboard",
    ),

    path(
    "farmer/chatbot/dashboard/",
    FarmerChatbotDashboardView.as_view(),
    name="farmer_chatbot_dashboard",
),
]