import json
import base64
import logging

from django.utils import timezone
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser

from .chatbot import get_ai_response, DEFAULT_SYSTEM_PROMPT
from .models import ChatbotConversation

logger = logging.getLogger(__name__)

ROLE_ADMIN = "admin"
ROLE_FARMER = "farmer"


ADMIN_FEATURES = """
Admin side features:
1. Farmer management
2. Crop management
3. Fertilizer management
4. Government scheme management
5. Equipment rental management
6. Disease detection reports
7. Weather insights
8. Marketplace/order reports
9. Dashboard analytics
10. Complaint/support handling
11. Import/export guidance
12. Admin report explanation
13. Farmer query analysis
14. Crop recommendation report explanation
15. Disease image/PDF report understanding
""".strip()


FARMER_FEATURES = """
Farmer/User side features:
1. Crop suggestion
2. Fertilizer suggestion
3. Soil guidance
4. Weather-based farming advice
5. Crop disease help
6. Pest control guidance
7. Irrigation guidance
8. Government scheme information
9. Equipment rental help
10. Marketplace help
11. Marathi farming support
12. Step-by-step practical farming advice
13. Crop growth stage guidance
14. Organic farming tips
15. Image/PDF based farming help
""".strip()


class BaseChatbotAPIView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    permission_classes = [IsAuthenticated]

    template_chat = None
    user_type = None

    # =====================================================
    # RESPONSE HELPERS
    # =====================================================
    def log_json_response(self, level, payload):
        try:
            pretty_json = json.dumps(payload, indent=4, ensure_ascii=False, default=str)
        except Exception:
            pretty_json = str(payload)

        log_method = getattr(logger, level, logger.debug)
        log_method("\n%s", pretty_json)

    def success_response(self, message, data=None, http_status=status.HTTP_200_OK):
        payload = {
            "status": "success",
            "message": message,
            "data": data if data is not None else {},
        }
        self.log_json_response("info", payload)
        return Response(payload, status=http_status)

    def error_response(self, message, errors=None, http_status=status.HTTP_400_BAD_REQUEST):
        payload = {
            "status": "error",
            "message": message,
            "errors": errors if errors is not None else {},
        }
        self.log_json_response("error", payload)
        return Response(payload, status=http_status)

    def is_html_request(self, request):
        return getattr(request.accepted_renderer, "format", None) == "html"

    # =====================================================
    # ROLE HELPERS
    # =====================================================
    def get_user_role(self, request):
        return (
            getattr(request.user, "role", None)
            or getattr(request.user, "user_type", None)
            or ""
        ).lower()

    def is_admin(self, request):
        return (
            request.user.is_authenticated
            and (
                request.user.is_superuser
                or request.user.is_staff
                or self.get_user_role(request) == ROLE_ADMIN
            )
        )

    def is_farmer(self, request):
        return (
            request.user.is_authenticated
            and self.get_user_role(request) == ROLE_FARMER
        )

    def has_permission_for_chatbot(self, request):
        if self.user_type == ROLE_ADMIN:
            return self.is_admin(request)

        if self.user_type == ROLE_FARMER:
            return self.is_farmer(request)

        return False

    # =====================================================
    # INPUT HELPERS
    # =====================================================
    def normalize_text_value(self, value):
        return str(value).strip() if value is not None else ""

    def decode_base64_value(self, value, field_name):
        if not value:
            return None

        try:
            if isinstance(value, str) and "," in value:
                value = value.split(",", 1)[1]

            return base64.b64decode(value)

        except Exception:
            raise ValueError(f"{field_name} contains invalid base64 data.")

    def read_uploaded_file(self, uploaded_file):
        if not uploaded_file:
            return None
        return uploaded_file.read()

    def get_input_data(self, request):
        data = request.data.copy() if hasattr(request.data, "copy") else dict(request.data)

        user_message = self.normalize_text_value(data.get("message", ""))

        image_file = request.FILES.get("image_file")
        pdf_file = request.FILES.get("pdf_file")

        image_b64 = data.get("image")
        pdf_b64 = data.get("pdf")

        image_mime = self.normalize_text_value(data.get("image_mime", "image/jpeg"))

        image_data = None
        pdf_data = None

        if image_file:
            image_data = self.read_uploaded_file(image_file)
            image_mime = image_file.content_type or "image/jpeg"
        elif image_b64:
            image_data = self.decode_base64_value(image_b64, "image")

        if pdf_file:
            pdf_data = self.read_uploaded_file(pdf_file)
        elif pdf_b64:
            pdf_data = self.decode_base64_value(pdf_b64, "pdf")

        return {
            "message": user_message,
            "image": image_data,
            "image_mime": image_mime,
            "pdf": pdf_data,
        }

    def validate_input_data(self, input_data):
        errors = {}

        if not input_data["message"] and not input_data["image"] and not input_data["pdf"]:
            errors["detail"] = ["At least one input is required: message, image, or pdf."]

        if input_data["image"] and not input_data["image_mime"]:
            errors["image_mime"] = ["Image MIME type is required when image is provided."]

        return errors

    # =====================================================
    # PROMPT + AI RESPONSE
    # =====================================================
    def get_system_prompt(self, request):
        return DEFAULT_SYSTEM_PROMPT

    def generate_chatbot_response(self, request, input_data):
        return get_ai_response(
            user_message=input_data.get("message"),
            image_data=input_data.get("image"),
            image_mime=input_data.get("image_mime"),
            pdf_data=input_data.get("pdf"),
            system_prompt=self.get_system_prompt(request),
        )

    # =====================================================
    # CHAT HISTORY
    # =====================================================
    def save_chat_history(
        self,
        request,
        input_data,
        bot_response="",
        chat_status="success",
        error_message="",
    ):
        try:
            return ChatbotConversation.objects.create(
                user=request.user,
                user_type=self.user_type,
                message=input_data.get("message", ""),
                bot_response=bot_response or "",
                has_image=bool(input_data.get("image")),
                has_pdf=bool(input_data.get("pdf")),
                status=chat_status,
                error_message=error_message or "",
            )
        except Exception:
            logger.exception("Failed to save chatbot conversation history.")
            return None

    # =====================================================
    # HTML CONTEXT
    # =====================================================
    def base_context(self, request, **extra):
        context = {
            "is_admin": self.is_admin(request),
            "is_farmer": self.is_farmer(request),
            "message": "",
            "errors": {},
            "error": "",
            "success": False,
            "user_message": "",
            "bot_response": "",
            "image_uploaded": False,
            "pdf_uploaded": False,
            "admin_features": ADMIN_FEATURES,
            "farmer_features": FARMER_FEATURES,
        }
        context.update(extra)
        return context

    def render_html_chat_response(
        self,
        request,
        user_message="",
        bot_response="",
        message="",
        errors=None,
        error="",
        success=False,
        image_uploaded=False,
        pdf_uploaded=False,
        http_status=status.HTTP_200_OK,
    ):
        return Response(
            self.base_context(
                request,
                user_message=user_message,
                bot_response=bot_response,
                message=message,
                errors=errors or {},
                error=error,
                success=success,
                image_uploaded=image_uploaded,
                pdf_uploaded=pdf_uploaded,
            ),
            template_name=self.template_chat,
            status=http_status,
        )

    # =====================================================
    # PERMISSION
    # =====================================================
    def permission_denied_response(self, request, message="Permission denied."):
        if self.is_html_request(request):
            return self.render_html_chat_response(
                request=request,
                message=message,
                errors={"detail": [message]},
                error=message,
                success=False,
                http_status=status.HTTP_403_FORBIDDEN,
            )

        return self.error_response(
            message=message,
            errors={"detail": [message]},
            http_status=status.HTTP_403_FORBIDDEN,
        )

    # =====================================================
    # GET / POST
    # =====================================================
    def get_chatbot_page(self, request):
        if not self.has_permission_for_chatbot(request):
            return self.permission_denied_response(
                request,
                f"Only {self.user_type} can access this chatbot page.",
            )

        if self.is_html_request(request):
            return self.render_html_chat_response(
                request=request,
                message=f"{self.user_type.title()} chatbot page loaded successfully.",
                success=True,
            )

        features = ADMIN_FEATURES if self.user_type == ROLE_ADMIN else FARMER_FEATURES

        return self.success_response(
            message=f"{self.user_type.title()} chatbot page loaded successfully.",
            data={
                "user_type": self.user_type,
                "features": features,
            },
        )

    def post_chatbot_message(self, request):
        if not self.has_permission_for_chatbot(request):
            return self.permission_denied_response(
                request,
                f"Only {self.user_type} can use this chatbot.",
            )

        input_data = {
            "message": "",
            "image": None,
            "image_mime": "image/jpeg",
            "pdf": None,
        }

        try:
            input_data = self.get_input_data(request)
            errors = self.validate_input_data(input_data)

            if errors:
                if self.is_html_request(request):
                    return self.render_html_chat_response(
                        request=request,
                        user_message=input_data.get("message", ""),
                        message=f"{self.user_type.title()} chatbot validation failed.",
                        errors=errors,
                        error="Please check the input properly.",
                        success=False,
                        image_uploaded=bool(input_data.get("image")),
                        pdf_uploaded=bool(input_data.get("pdf")),
                        http_status=status.HTTP_400_BAD_REQUEST,
                    )

                return self.error_response(
                    message=f"{self.user_type.title()} chatbot validation failed.",
                    errors=errors,
                    http_status=status.HTTP_400_BAD_REQUEST,
                )

            bot_response = self.generate_chatbot_response(request, input_data)

            if not bot_response:
                bot_response = "⚠️ Sorry, I could not generate a response."

            self.save_chat_history(
                request=request,
                input_data=input_data,
                bot_response=bot_response,
                chat_status="success",
            )

            if self.is_html_request(request):
                return self.render_html_chat_response(
                    request=request,
                    user_message=input_data.get("message", ""),
                    bot_response=bot_response,
                    message=f"{self.user_type.title()} chatbot response generated successfully.",
                    success=True,
                    image_uploaded=bool(input_data.get("image")),
                    pdf_uploaded=bool(input_data.get("pdf")),
                    http_status=status.HTTP_200_OK,
                )

            features = ADMIN_FEATURES if self.user_type == ROLE_ADMIN else FARMER_FEATURES

            return self.success_response(
                message=f"{self.user_type.title()} chatbot response generated successfully.",
                data={
                    "user_type": self.user_type,
                    "features": features,
                    "user_message": input_data.get("message", ""),
                    "bot_response": bot_response,
                    "image_uploaded": bool(input_data.get("image")),
                    "pdf_uploaded": bool(input_data.get("pdf")),
                },
            )

        except ValueError as exc:
            error_text = str(exc)

            self.save_chat_history(
                request=request,
                input_data=input_data,
                chat_status="failed",
                error_message=error_text,
            )

            if self.is_html_request(request):
                return self.render_html_chat_response(
                    request=request,
                    message="Invalid input value.",
                    errors={"detail": [error_text]},
                    error=error_text,
                    success=False,
                    http_status=status.HTTP_400_BAD_REQUEST,
                )

            return self.error_response(
                message="Invalid input value.",
                errors={"detail": [error_text]},
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as exc:
            logger.exception("Error generating chatbot response")
            error_text = str(exc)

            self.save_chat_history(
                request=request,
                input_data=input_data,
                chat_status="failed",
                error_message=error_text,
            )

            if self.is_html_request(request):
                return self.render_html_chat_response(
                    request=request,
                    message="Error generating chatbot response.",
                    errors={"detail": [error_text]},
                    error=error_text,
                    success=False,
                    http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            return self.error_response(
                message="Error generating chatbot response.",
                errors={"detail": [error_text]},
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AdminChatbotAPIView(BaseChatbotAPIView):
    template_chat = "chatbot/admin_chat.html"
    user_type = ROLE_ADMIN

    def get_system_prompt(self, request):
        return f"""
{DEFAULT_SYSTEM_PROMPT}

ADMIN MODE:
You are also Smart Sheti Admin AI Assistant.

{ADMIN_FEATURES}

Admin rules:
- Help admin understand dashboard reports, farmer records, crop reports, fertilizer reports, disease reports, PDF reports and image reports.
- Help admin manage crops, fertilizers, schemes, equipment, marketplace, complaints and reports.
- If admin asks crop disease information, always follow full disease format.
- Never give only disease names.
- Always include Disease Name, Scientific Name, Severity, Symptoms, Cause, Control/Management, Recommended Treatment, Prevention and Safety Precautions.
- Disease category accuracy is mandatory.
- Do not mix viral diseases inside bacterial diseases.
- Do not mix nutrient deficiencies inside fungal/bacterial/viral diseases.
- Give professional, clear and structured answers.
""".strip()

    def get(self, request, format=None):
        return self.get_chatbot_page(request)

    def post(self, request, format=None):
        return self.post_chatbot_message(request)


class FarmerChatbotAPIView(BaseChatbotAPIView):
    template_chat = "chatbot/farmer_chat.html"
    user_type = ROLE_FARMER

    def get_system_prompt(self, request):
        return f"""
{DEFAULT_SYSTEM_PROMPT}

FARMER MODE:
You are also Smart Sheti Farmer/User AI Assistant.

{FARMER_FEATURES}

Farmer rules:
- Give simple, practical and step-by-step farming help.
- If farmer asks crop disease information, always follow full disease format.
- Never give only disease names.
- Always include Disease Name, Scientific Name, Severity, Symptoms, Cause, Control/Management, Recommended Treatment, Prevention and Safety Precautions.
- Disease category accuracy is mandatory.
- Do not mix viral diseases inside bacterial diseases.
- Do not mix nutrient deficiencies inside fungal/bacterial/viral diseases.
- If user asks in Marathi, reply fully in Marathi.
- Avoid long technical answers unless farmer asks.
""".strip()

    def get(self, request, format=None):
        return self.get_chatbot_page(request)

    def post(self, request, format=None):
        return self.post_chatbot_message(request)


class AdminChatbotPageView(AdminChatbotAPIView):
    renderer_classes = [TemplateHTMLRenderer]

    def get(self, request, format=None):
        return self.get_chatbot_page(request)


class FarmerChatbotPageView(FarmerChatbotAPIView):
    renderer_classes = [TemplateHTMLRenderer]

    def get(self, request, format=None):
        return self.get_chatbot_page(request)


class AdminChatbotDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "chatbot/admin_chatbot_dashboard.html"

    def test_func(self):
        user = self.request.user

        return (
            user.is_authenticated
            and (
                user.is_superuser
                or user.is_staff
                or getattr(user, "role", "").lower() == ROLE_ADMIN
                or getattr(user, "user_type", "").lower() == ROLE_ADMIN
            )
        )

    def handle_no_permission(self):
        from django.shortcuts import redirect
        return redirect("accounts:login")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        today = timezone.localdate()
        all_chats = ChatbotConversation.objects.all()

        context["total_chats"] = all_chats.count()
        context["today_chats"] = all_chats.filter(created_at__date=today).count()
        context["image_chats"] = all_chats.filter(has_image=True).count()
        context["pdf_chats"] = all_chats.filter(has_pdf=True).count()
        context["success_chats"] = all_chats.filter(status="success").count()
        context["failed_chats"] = all_chats.filter(status="failed").count()

        context["admin_chats"] = all_chats.filter(user_type=ROLE_ADMIN).count()
        context["farmer_chats"] = all_chats.filter(user_type=ROLE_FARMER).count()

        context["recent_chats"] = all_chats.select_related("user").order_by("-created_at")[:20]

        context["page_title"] = "Admin Chatbot Dashboard"
        context["today"] = today

        return context
    


class FarmerChatbotDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "chatbot/farmer_chatbot_dashboard.html"

    def test_func(self):
        user = self.request.user

        return (
            user.is_authenticated
            and (
                getattr(user, "role", "").lower() == ROLE_FARMER
                or getattr(user, "user_type", "").lower() == ROLE_FARMER
            )
        )

    def handle_no_permission(self):
        from django.shortcuts import redirect
        return redirect("accounts:login")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        today = timezone.localdate()

        my_chats = ChatbotConversation.objects.filter(
            user=self.request.user,
            user_type=ROLE_FARMER,
        )

        context["total_chats"] = my_chats.count()
        context["today_chats"] = my_chats.filter(created_at__date=today).count()
        context["image_chats"] = my_chats.filter(has_image=True).count()
        context["pdf_chats"] = my_chats.filter(has_pdf=True).count()
        context["success_chats"] = my_chats.filter(status="success").count()
        context["failed_chats"] = my_chats.filter(status="failed").count()

        context["recent_chats"] = my_chats.order_by("-created_at")[:20]

        context["page_title"] = "Farmer Chatbot Dashboard"
        context["today"] = today

        return context