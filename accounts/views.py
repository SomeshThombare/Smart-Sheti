# ============================================================
#                       STANDARD LIBRARY
# ============================================================
import json
import logging
from datetime import timedelta

# ============================================================
#                       DJANGO IMPORTS
# ============================================================
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.shortcuts import redirect
from django.utils import translation, timezone

# ============================================================
#                       DRF IMPORTS
# ============================================================
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.renderers import (
    JSONRenderer,
    TemplateHTMLRenderer,
    BrowsableAPIRenderer,
)
from rest_framework.response import Response
from rest_framework.views import APIView

# ============================================================
#                       JWT
# ============================================================
from rest_framework_simplejwt.tokens import RefreshToken

# ============================================================
#                       LOCAL IMPORTS
# ============================================================
from .forms import (
    AdminRegistrationForm,
    FarmerRegistrationForm,
    SendOTPForm,
    UserLoginForm,
    VerifyOTPForm,
    CurrentProfileUpdateForm,
)

from .models import (
    CustomUser,
    OTPVerification,
    AdminProfile,
)

from .serializers import (
    AdminFullProfileSerializer,
    AdminRegistrationSerializer,
    FarmerFullProfileSerializer,
    FarmerRegistrationSerializer,
    LoginSerializer,
    SendOTPSerializer,
    VerifyOTPSerializer,
)

from .utils import create_otp_record, verify_otp

# ============================================================
#                       LOGGER
# ============================================================
logger = logging.getLogger(__name__)


ROLE_ADMIN = "admin"
ROLE_FARMER = "farmer"


# ============================================================
#            OTP AUTHENTICATION BASE VIEW
# ============================================================

class BaseAuthAPIView(APIView):
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    permission_classes = [AllowAny]

    # --------------------------------------------------------
    # Check request type: HTML or API
    # --------------------------------------------------------
    def is_html_request(self, request):
        """
        API URLs must always return JSON.
        Web URLs can return HTML.
        """

        if request.path.startswith("/accounts/api/"):
            return False

        accept_header = request.META.get("HTTP_ACCEPT", "")

        return (
            "text/html" in accept_header
            and "application/json" not in accept_header
        )

    # --------------------------------------------------------
    # Get request data safely
    # --------------------------------------------------------
    def get_request_data(self, request):
        return request.data if request.data else request.POST

    # --------------------------------------------------------
    # Render HTML form response
    # --------------------------------------------------------
    def render_html_form_response(
        self,
        request,
        form=None,
        data=None,
        message="",
        errors=None,
        success=False,
        http_status=status.HTTP_200_OK,
    ):
        return Response(
            {
                "form": form,
                "data": data or {},
                "message": message,
                "errors": errors or {},
                "success": success,
            },
            template_name=self.template_form,
            status=http_status,
        )

    # --------------------------------------------------------
    # User profile response data
    # --------------------------------------------------------
    def get_user_profile_data(self, user):
        if not user:
            return {}

        return {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "country_code": user.country_code,
            "mobile_number": user.mobile_number,
            "language_preference": user.language_preference,
            "role": user.role,
            "is_active": user.is_active,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
            "date_joined": user.date_joined,
        }

    # --------------------------------------------------------
    # Log JSON response
    # --------------------------------------------------------
    def log_json_response(self, level, payload):
        try:
            pretty_json = json.dumps(
                payload,
                indent=4,
                ensure_ascii=False,
                default=str,
            )
        except Exception:
            pretty_json = str(payload)

        log_method = getattr(logger, level, logger.info)
        log_method("\n%s", pretty_json)

    # --------------------------------------------------------
    # Success response
    # --------------------------------------------------------
    def success_response(
        self,
        message="Request completed successfully.",
        data=None,
        http_status=status.HTTP_200_OK,
    ):
        payload = {
            "status": "success",
            "success": True,
            "message": message,
            "data": data if data is not None else {},
        }

        self.log_json_response("info", payload)
        return Response(payload, status=http_status)

    # --------------------------------------------------------
    # Error response
    # --------------------------------------------------------
    def error_response(
        self,
        message="Request failed.",
        errors=None,
        http_status=status.HTTP_400_BAD_REQUEST,
    ):
        payload = {
            "status": "error",
            "success": False,
            "message": message,
            "errors": errors if errors is not None else {},
        }

        log_level = "warning" if http_status < 500 else "error"
        self.log_json_response(log_level, payload)
        return Response(payload, status=http_status)

    # --------------------------------------------------------
    # Format Django form errors
    # --------------------------------------------------------
    def format_form_errors(self, form):
        return {
            field: [str(error) for error in field_errors]
            for field, field_errors in form.errors.items()
        }

    # --------------------------------------------------------
    # Format serializer errors
    # --------------------------------------------------------
    def format_serializer_errors(self, serializer):
        errors = {}

        for field, field_errors in serializer.errors.items():
            if isinstance(field_errors, list):
                errors[field] = [str(error) for error in field_errors]
            else:
                errors[field] = [str(field_errors)]

        return errors

    # --------------------------------------------------------
    # Validate OTP sending result
    # --------------------------------------------------------
    def validate_otp_send_result(self, result):
        if not isinstance(result, dict):
            return False, "Invalid OTP service response.", {
                "detail": ["Invalid OTP service response."]
            }

        sms_result = result.get("sms_result", {})
        email_result = result.get("email_result", {})

        sms_ok = sms_result.get("success", True)
        email_ok = email_result.get("success", True)

        if not sms_ok:
            message = sms_result.get(
                "message",
                "Failed to send OTP on mobile number.",
            )
            return False, message, {
                "mobile_number": [message]
            }

        if not email_ok:
            message = email_result.get(
                "message",
                "Failed to send OTP on email address.",
            )
            return False, message, {
                "email": [message]
            }

        return True, "OTP sent successfully on email and mobile number.", {}
    
# ============================================================
#                   SEND OTP WEB VIEW
# ============================================================

class SendOTPWebView(BaseAuthAPIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_form = "accounts/auth/send_otp.html"

    def get_context(
        self,
        form=None,
        message="",
        errors=None,
        success=False,
        data=None,
    ):
        return {
            "form": form or SendOTPForm(),
            "message": message,
            "errors": errors or {},
            "success": success,
            "data": data or {},
        }

    def html_response(self, context, http_status=status.HTTP_200_OK):
        return Response(
            context,
            template_name=self.template_form,
            status=http_status,
        )

    def get(self, request, format=None):
        context = self.get_context(
            message="Enter email and mobile number to receive OTP.",
            success=False,
        )
        return self.html_response(context)

    def post(self, request, format=None):
        form = SendOTPForm(request.POST)

        if not form.is_valid():
            errors = self.format_form_errors(form)

            context = self.get_context(
                form=form,
                message="Please correct the highlighted errors.",
                errors=errors,
                success=False,
            )

            return self.html_response(
                context,
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        email = form.cleaned_data.get("email")
        mobile_number = form.cleaned_data.get("mobile_number")

        try:
            result = create_otp_record(email, mobile_number)

        except Exception:
            logger.exception("Something went wrong while sending OTP.")

            context = self.get_context(
                form=form,
                message="Something went wrong while sending OTP.",
                errors={"server": ["Internal server error."]},
                success=False,
            )

            return self.html_response(
                context,
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        ok, message_text, errors = self.validate_otp_send_result(result)

        if not ok:
            context = self.get_context(
                form=form,
                message=message_text,
                errors=errors,
                success=False,
            )

            return self.html_response(
                context,
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        response_data = {
            "email": email,
            "mobile_number": mobile_number,
        }

        self.log_json_response(
            "info",
            {
                "status": "success",
                "success": True,
                "message": message_text,
                "data": response_data,
            },
        )

        context = self.get_context(
            form=SendOTPForm(),
            message=message_text,
            errors={},
            success=True,
            data=response_data,
        )

        return self.html_response(context)

# ============================================================
#                   SEND OTP API VIEW
# ============================================================

class SendOTPAPIView(BaseAuthAPIView):
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]

    def get(self, request, format=None):
        return self.success_response(
            message="Send OTP API is ready.",
            data={
                "required_fields": ["email", "mobile_number"],
                "method": "POST",
                "content_type": "application/json",
            },
            http_status=status.HTTP_200_OK,
        )

    def post(self, request, format=None):
        serializer = SendOTPSerializer(data=request.data)

        if not serializer.is_valid():
            return self.error_response(
                message="Please provide valid email and mobile number.",
                errors=self.format_serializer_errors(serializer),
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        email = serializer.validated_data.get("email")
        mobile_number = serializer.validated_data.get("mobile_number")

        try:
            result = create_otp_record(email, mobile_number)

        except Exception:
            logger.exception("Something went wrong while sending OTP.")

            return self.error_response(
                message="Something went wrong while sending OTP.",
                errors={"server": ["Internal server error."]},
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        ok, message_text, errors = self.validate_otp_send_result(result)

        if not ok:
            return self.error_response(
                message=message_text,
                errors=errors,
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        return self.success_response(
            message=message_text,
            data={
                "email": email,
                "mobile_number": mobile_number,
            },
            http_status=status.HTTP_200_OK,
        )
       
import json

from django.shortcuts import redirect
from django.contrib import messages
from django.db import transaction
from rest_framework import status
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response


# ============================================================
#                 VERIFY OTP WEB VIEW
# ============================================================

class VerifyOTPWebView(BaseAuthAPIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_form = "accounts/auth/verify_otp.html"

    def get_context(self, form=None, message="", errors=None, success=False, data=None):
        return {
            "form": form or VerifyOTPForm(),
            "message": message,
            "errors": errors or {},
            "success": success,
            "data": data or {},
        }

    def html_response(self, context, http_status=status.HTTP_200_OK):
        return Response(
            context,
            template_name=self.template_form,
            status=http_status,
        )

    def print_post_data_in_cmd(self, request):
        print("\n" + "=" * 70)
        print("POST DATA RECEIVED IN VERIFY OTP WEB VIEW")
        print("=" * 70)

        try:
            print("\nREQUEST.POST:")
            print(json.dumps(request.POST.dict(), indent=4))
        except Exception as exc:
            print("REQUEST.POST print error:", exc)

        try:
            print("\nREQUEST.DATA:")
            print(json.dumps(request.data, indent=4, default=str))
        except Exception as exc:
            print("REQUEST.DATA print error:", exc)

        try:
            raw_body = request.body.decode("utf-8")
            print("\nRAW BODY:")
            print(raw_body if raw_body else "No raw body")
        except Exception as exc:
            print("RAW BODY print error:", exc)

        print("=" * 70 + "\n")

    def get_initial_data(self, request):
        for session_key in [
            "pending_farmer_registration",
            "pending_admin_registration",
            "pending_password_reset",
            "pending_profile_update",
        ]:
            pending_data = request.session.get(session_key)

            if pending_data:
                return {
                    "email": pending_data.get("new_email") or pending_data.get("email", ""),
                    "mobile_number": pending_data.get("new_mobile_number") or pending_data.get("mobile_number", ""),
                }

        return {}

    def get(self, request, format=None):
        form = VerifyOTPForm(initial=self.get_initial_data(request))

        return self.html_response(
            self.get_context(
                form=form,
                message="Please enter the OTP sent to your email and mobile number.",
                success=False,
            )
        )

    def complete_pending_registration(
        self,
        request,
        session_key,
        form_class,
        success_message,
        input_data,
    ):
        pending_data = request.session.get(session_key)

        if not pending_data:
            return None

        pending_data = pending_data.copy()

        pending_data.pop("registration_state", None)
        pending_data.pop("role", None)
        pending_data.pop("is_active", None)

        print("\n" + "=" * 70)
        print("PENDING REGISTRATION SESSION DATA")
        print("=" * 70)
        print("SESSION KEY:", session_key)
        print(json.dumps(pending_data, indent=4, default=str))
        print("=" * 70 + "\n")

        register_form = form_class(pending_data)

        if session_key == "pending_admin_registration":
            register_form.instance.role = CustomUser.RoleChoices.ADMIN

        elif session_key == "pending_farmer_registration":
            register_form.instance.role = CustomUser.RoleChoices.FARMER

        if not register_form.is_valid():
            request.session.pop(session_key, None)
            request.session.modified = True

            return self.html_response(
                self.get_context(
                    form=VerifyOTPForm(input_data),
                    message="Pending registration data is invalid. Please register again.",
                    errors=self.format_form_errors(register_form),
                    success=False,
                ),
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                user = register_form.save(commit=True)

                if session_key == "pending_admin_registration":
                    user.role = CustomUser.RoleChoices.ADMIN
                    user.is_staff = True
                    user.is_superuser = False
                    role_name = "Admin"

                elif session_key == "pending_farmer_registration":
                    user.role = CustomUser.RoleChoices.FARMER
                    user.is_staff = False
                    user.is_superuser = False
                    role_name = "Farmer"

                else:
                    role_name = "User"

                user.is_active = True
                user.save(
                    update_fields=[
                        "role",
                        "is_staff",
                        "is_superuser",
                        "is_active",
                    ]
                )

            request.session.pop(session_key, None)
            request.session.modified = True

        except Exception:
            logger.exception("Registration completion failed after OTP verification.")

            return self.html_response(
                self.get_context(
                    form=VerifyOTPForm(input_data),
                    message="OTP verified, but registration could not be completed.",
                    errors={"server": ["Registration completion failed."]},
                    success=False,
                ),
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        messages.success(
            request,
            f"{role_name} registration completed successfully. Please login."
        )

        return redirect("login")

    def complete_profile_update(self, request, input_data):
        pending_profile_update = request.session.get("pending_profile_update")

        if not pending_profile_update:
            return None

        if not request.user.is_authenticated:
            return self.html_response(
                self.get_context(
                    form=VerifyOTPForm(input_data),
                    message="Login required to update profile.",
                    errors={"auth": ["Please login again."]},
                    success=False,
                ),
                http_status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            user = request.user

            if user.id != pending_profile_update.get("user_id"):
                return self.html_response(
                    self.get_context(
                        form=VerifyOTPForm(input_data),
                        message="Invalid profile update session.",
                        errors={"session": ["Invalid profile update session."]},
                        success=False,
                    ),
                    http_status=status.HTTP_400_BAD_REQUEST,
                )

            update_data = pending_profile_update.get("update_data", {})

            with transaction.atomic():
                for field, value in update_data.items():
                    setattr(user, field, value)

                user.full_clean()
                user.save()

            request.session.pop("pending_profile_update", None)
            request.session.modified = True

        except Exception as exc:
            logger.exception("Profile update failed after OTP verification.")

            return self.html_response(
                self.get_context(
                    form=VerifyOTPForm(input_data),
                    message="Profile update failed after OTP verification.",
                    errors={"detail": [str(exc)]},
                    success=False,
                ),
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        return self.html_response(
            self.get_context(
                form=VerifyOTPForm(),
                message="OTP verified. Profile updated successfully.",
                errors={},
                success=True,
                data=self.get_user_profile_data(user),
            ),
            http_status=status.HTTP_200_OK,
        )

    def post(self, request, format=None):
        self.print_post_data_in_cmd(request)

        form = VerifyOTPForm(request.POST)

        if not form.is_valid():
            return self.html_response(
                self.get_context(
                    form=form,
                    message="Please enter valid OTP verification details.",
                    errors=self.format_form_errors(form),
                    success=False,
                ),
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        email = form.cleaned_data["email"]
        mobile_number = form.cleaned_data["mobile_number"]
        email_otp = form.cleaned_data["email_otp"]
        mobile_otp = form.cleaned_data["mobile_otp"]

        try:
            verified, message_text = verify_otp(
                email=email,
                mobile_number=mobile_number,
                email_otp=email_otp,
                mobile_otp=mobile_otp,
            )

        except Exception:
            logger.exception("Something went wrong while verifying OTP.")

            return self.html_response(
                self.get_context(
                    form=form,
                    message="Something went wrong while verifying OTP.",
                    errors={"server": ["Internal server error. Please try again later."]},
                    success=False,
                ),
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if not verified:
            return self.html_response(
                self.get_context(
                    form=form,
                    message=message_text or "Invalid OTP. Please try again.",
                    errors={"otp": [message_text or "Invalid or expired OTP."]},
                    success=False,
                ),
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        response = self.complete_pending_registration(
            request=request,
            session_key="pending_farmer_registration",
            form_class=FarmerRegistrationForm,
            success_message="Farmer registration completed successfully.",
            input_data=request.POST,
        )
        if response is not None:
            return response

        response = self.complete_pending_registration(
            request=request,
            session_key="pending_admin_registration",
            form_class=AdminRegistrationForm,
            success_message="Admin registration completed successfully.",
            input_data=request.POST,
        )
        if response is not None:
            return response

        response = self.complete_profile_update(
            request=request,
            input_data=request.POST,
        )
        if response is not None:
            return response

        pending_reset = request.session.get("pending_password_reset")

        if pending_reset:
            request.session["password_reset_verified"] = True
            request.session.modified = True

            return self.html_response(
                self.get_context(
                    form=VerifyOTPForm(),
                    message="OTP verified successfully. You can now reset your password.",
                    errors={},
                    success=True,
                    data={"password_reset_verified": True},
                ),
                http_status=status.HTTP_200_OK,
            )

        return self.html_response(
            self.get_context(
                form=VerifyOTPForm(),
                message=message_text or "Email OTP and mobile OTP verified successfully.",
                errors={},
                success=True,
                data={
                    "email": email,
                    "mobile_number": mobile_number,
                    "verified": True,
                },
            ),
            http_status=status.HTTP_200_OK,
        )
        
# ============================================================
#                 VERIFY OTP API VIEW
# ============================================================

class VerifyOTPAPIView(BaseAuthAPIView):
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]

    # ============================================================
    # GET
    # ============================================================
    def get(self, request, format=None):
        return self.success_response(
            message="Verify OTP API is ready.",
            data={
                "method": "POST",
                "required_fields": [
                    "email",
                    "mobile_number",
                    "email_otp",
                    "mobile_otp",
                ],
                "sample_request": {
                    "email": "user@example.com",
                    "mobile_number": "9876543210",
                    "email_otp": "123456",
                    "mobile_otp": "123456",
                },
            },
            http_status=status.HTTP_200_OK,
        )

    # ============================================================
    # GET INITIAL SESSION DATA
    # ============================================================
    def get_initial_data(self, request):
        for session_key in [
            "pending_farmer_registration",
            "pending_admin_registration",
            "pending_password_reset",
            "pending_profile_update",
        ]:
            pending_data = request.session.get(session_key)

            if pending_data:
                return {
                    "email": pending_data.get("new_email")
                    or pending_data.get("email", ""),
                    "mobile_number": pending_data.get("new_mobile_number")
                    or pending_data.get("mobile_number", ""),
                }

        return {}

    # ============================================================
    # COMPLETE FARMER / ADMIN REGISTRATION
    # ============================================================
    def complete_pending_registration(
        self,
        request,
        session_key,
        form_class,
        success_message,
    ):
        pending_data = request.session.get(session_key)

        if not pending_data:
            return None

        pending_data = pending_data.copy()

        pending_data.pop("registration_state", None)
        pending_data.pop("role", None)
        pending_data.pop("is_active", None)

        register_form = form_class(pending_data)

        if session_key == "pending_admin_registration":
            register_form.instance.role = CustomUser.RoleChoices.ADMIN

        elif session_key == "pending_farmer_registration":
            register_form.instance.role = CustomUser.RoleChoices.FARMER

        if not register_form.is_valid():
            return self.error_response(
                message="Pending registration data is invalid. Please register again.",
                errors=self.format_form_errors(register_form),
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                user = register_form.save(commit=True)

                if session_key == "pending_admin_registration":
                    user.role = CustomUser.RoleChoices.ADMIN
                    user.is_staff = True
                    user.is_superuser = False

                elif session_key == "pending_farmer_registration":
                    user.role = CustomUser.RoleChoices.FARMER
                    user.is_staff = False
                    user.is_superuser = False

                user.is_active = True
                user.save(
                    update_fields=[
                        "role",
                        "is_staff",
                        "is_superuser",
                        "is_active",
                    ]
                )

            request.session.pop(session_key, None)
            request.session.modified = True

        except Exception:
            logger.exception("Registration completion failed after OTP verification.")

            return self.error_response(
                message="OTP verified, but registration could not be completed.",
                errors={"server": ["Registration completion failed."]},
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return self.success_response(
            message=success_message,
            data={
                "registration_state": "APPROVED",
                "registration_completed": True,
                "user": self.get_user_profile_data(user),
            },
            http_status=status.HTTP_201_CREATED,
        )

    # ============================================================
    # PROFILE UPDATE AFTER OTP
    # ============================================================
    def complete_profile_update(self, request):
        pending_profile_update = request.session.get("pending_profile_update")

        if not pending_profile_update:
            return None

        if not request.user.is_authenticated:
            return self.error_response(
                message="Login required to update profile.",
                errors={"auth": ["Please login again."]},
                http_status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            user = request.user

            if user.id != pending_profile_update.get("user_id"):
                return self.error_response(
                    message="Invalid profile update session.",
                    errors={"session": ["Invalid profile update session."]},
                    http_status=status.HTTP_400_BAD_REQUEST,
                )

            update_data = pending_profile_update.get("update_data", {})

            with transaction.atomic():
                for field, value in update_data.items():
                    setattr(user, field, value)

                user.full_clean()
                user.save()

            request.session.pop("pending_profile_update", None)
            request.session.modified = True

        except Exception as exc:
            logger.exception("Profile update failed after OTP verification.")

            return self.error_response(
                message="Profile update failed after OTP verification.",
                errors={"detail": [str(exc)]},
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        return self.success_response(
            message="OTP verified. Profile updated successfully.",
            data=self.get_user_profile_data(user),
            http_status=status.HTTP_200_OK,
        )

    # ============================================================
    # PASSWORD RESET AFTER OTP
    # ============================================================
    def complete_password_reset_verification(self, request):
        pending_reset = request.session.get("pending_password_reset")

        if not pending_reset:
            return None

        request.session["password_reset_verified"] = True
        request.session.modified = True

        return self.success_response(
            message="OTP verified successfully. You can now reset your password.",
            data={
                "password_reset_verified": True,
            },
            http_status=status.HTTP_200_OK,
        )

    # ============================================================
    # POST
    # ============================================================
    def post(self, request, format=None):
        serializer = VerifyOTPSerializer(data=request.data)

        if not serializer.is_valid():
            return self.error_response(
                message="Please enter valid OTP verification details.",
                errors=serializer.errors,
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        email = serializer.validated_data["email"]
        mobile_number = serializer.validated_data["mobile_number"]
        email_otp = serializer.validated_data["email_otp"]
        mobile_otp = serializer.validated_data["mobile_otp"]

        try:
            verified, message_text = verify_otp(
                email=email,
                mobile_number=mobile_number,
                email_otp=email_otp,
                mobile_otp=mobile_otp,
            )

        except Exception:
            logger.exception("Something went wrong while verifying OTP.")

            return self.error_response(
                message="Something went wrong while verifying OTP.",
                errors={"server": ["Internal server error. Please try again later."]},
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if not verified:
            return self.error_response(
                message=message_text or "Invalid OTP. Please try again.",
                errors={"otp": [message_text or "Invalid or expired OTP."]},
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        response = self.complete_pending_registration(
            request=request,
            session_key="pending_farmer_registration",
            form_class=FarmerRegistrationForm,
            success_message="Farmer registration completed successfully.",
        )
        if response is not None:
            return response

        response = self.complete_pending_registration(
            request=request,
            session_key="pending_admin_registration",
            form_class=AdminRegistrationForm,
            success_message="Admin registration completed successfully.",
        )
        if response is not None:
            return response

        response = self.complete_profile_update(request)
        if response is not None:
            return response

        response = self.complete_password_reset_verification(request)
        if response is not None:
            return response

        return self.success_response(
            message=message_text or "Email OTP and mobile OTP verified successfully.",
            data={
                "email": email,
                "mobile_number": mobile_number,
                "verified": True,
            },
            http_status=status.HTTP_200_OK,
        )

    # ============================================================
    # FARMER REGISTRATION
    # ============================================================
    def complete_farmer_registration(self, request):
        pending = request.session.get("pending_farmer_registration")
        if not pending:
            return None

        form = FarmerRegistrationForm(pending)

        if not form.is_valid():
            return self.error_response(
                message="Invalid data.",
                errors=form.errors,
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                user = form.save()

                user.role = CustomUser.RoleChoices.FARMER
                user.is_active = True
                user.save()

            request.session.pop("pending_farmer_registration", None)
            request.session.modified = True

        except Exception as exc:
            return self.error_response(
                message="Farmer registration failed.",
                errors={"server": [str(exc)]},
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return self.success_response(
            message="Farmer registration completed.",
            data=self.get_user_profile_data(user),
            http_status=status.HTTP_201_CREATED,
        )

    # ============================================================
    # PASSWORD RESET
    # ============================================================
    def complete_password_reset_verification(self, request):
        pending = request.session.get("pending_password_reset")

        if not pending:
            return None

        pending["otp_verified"] = True
        request.session.modified = True

        return self.success_response(
            message="OTP verified. You can reset password.",
            data={"next": "/accounts/api/v1/reset-password/"},
            http_status=status.HTTP_200_OK,
        )

    # ============================================================
    # POST VERIFY OTP
    # ============================================================
    def post(self, request, format=None):
        serializer = VerifyOTPSerializer(
            data=request.data,
            context={
                "pending_profile_update": request.session.get("pending_profile_update")
            },
        )

        if not serializer.is_valid():
            return self.error_response(
                message="Please enter valid OTP details.",
                errors=self.format_serializer_errors(serializer),
                http_status=status.HTTP_400_BAD_REQUEST,
            )


        # ============================================================
        # CHECK IF PROFILE UPDATE FLOW
        # ============================================================
        pending_profile = request.session.get("pending_profile_update")

        if pending_profile:
            email_changed = pending_profile.get("email_changed", False)
            mobile_changed = pending_profile.get("mobile_changed", False)

            email = pending_profile.get("new_email") if email_changed else None
            mobile_number = pending_profile.get("new_mobile_number") if mobile_changed else None

            email_otp = serializer.validated_data.get("email_otp")
            mobile_otp = serializer.validated_data.get("mobile_otp")

            if email_changed and not email_otp:
                return self.error_response(
                    message="Email OTP required.",
                    errors={"email_otp": ["Required"]},
                    http_status=status.HTTP_400_BAD_REQUEST,
                )

            if mobile_changed and not mobile_otp:
                return self.error_response(
                    message="Mobile OTP required.",
                    errors={"mobile_otp": ["Required"]},
                    http_status=status.HTTP_400_BAD_REQUEST,
                )

        else:
            email = serializer.validated_data.get("email")
            mobile_number = serializer.validated_data.get("mobile_number")
            email_otp = serializer.validated_data.get("email_otp")
            mobile_otp = serializer.validated_data.get("mobile_otp")

        # ============================================================
        # VERIFY OTP
        # ============================================================
        try:
            verified, message = verify_otp(
                email=email,
                mobile_number=mobile_number,
                email_otp=email_otp,
                mobile_otp=mobile_otp,
            )
        except Exception:
            return self.error_response(
                message="OTP verification error.",
                errors={"server": ["Try again"]},
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if not verified:
            return self.error_response(
                message="Invalid OTP",
                errors={"otp": ["Invalid or expired"]},
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        # ============================================================
        # EXECUTE FLOW
        # ============================================================
        for func in [
            self.complete_profile_update,
            self.complete_farmer_registration,
            self.complete_admin_registration,
            self.complete_password_reset_verification,
        ]:
            response = func(request)
            if response is not None:
                return response

        return self.success_response(
            message="OTP verified successfully.",
            data={"verified": True},
            http_status=status.HTTP_200_OK,
        )
        
import json
import logging

logger = logging.getLogger(__name__)


# ============================================================
#                 ADMIN REGISTRATION WEB VIEW
# ============================================================

class AdminRegistrationWebView(BaseAuthAPIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_form = "accounts/admin/admin_register.html"

    def get_context(self, form=None, message="", errors=None, success=False, data=None):
        return {
            "form": form or AdminRegistrationForm(),
            "message": message,
            "errors": errors or {},
            "success": success,
            "data": data or {},
        }

    def get(self, request, format=None):
        logger.info("Admin Registration Page Opened")

        return Response(
            self.get_context(message="Fill admin registration form."),
            template_name=self.template_form,
            status=status.HTTP_200_OK,
        )

    def post(self, request, format=None):

        # ============================================================
        # 🔥 LOG REQUEST DATA (SAFE JSON)
        # ============================================================

        try:
            data = request.POST.dict()

            safe_data = data.copy()
            safe_data.pop("password1", None)
            safe_data.pop("password2", None)

            logger.info("=" * 70)
            logger.info("ADMIN REGISTRATION WEB VIEW POST DATA")
            logger.info(json.dumps(safe_data, indent=4))
            logger.info("=" * 70)

        except Exception:
            logger.exception("Failed to log request data")

        # ============================================================
        # FORM VALIDATION
        # ============================================================

        form = AdminRegistrationForm(request.POST)

        form.instance.role = CustomUser.RoleChoices.ADMIN

        if not form.is_valid():
            logger.warning("Admin registration form validation failed")
            logger.warning(self.format_form_errors(form))

            return Response(
                self.get_context(
                    form=form,
                    message="Admin registration failed.",
                    errors=self.format_form_errors(form),
                    success=False,
                ),
                template_name=self.template_form,
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ============================================================
        # SAVE PENDING DATA IN SESSION
        # ============================================================

        pending_data = form.cleaned_data.copy()
        pending_data["registration_state"] = "DRAFT"

        request.session["pending_admin_registration"] = pending_data
        request.session.modified = True

        logger.info("Admin registration data stored in session")

        email = pending_data.get("email")
        mobile_number = pending_data.get("mobile_number")

        # ============================================================
        # OTP CREATION
        # ============================================================

        try:
            logger.info(f"Sending OTP to Email: {email}, Mobile: {mobile_number}")

            result = create_otp_record(email, mobile_number)

        except Exception:
            logger.exception("OTP sending failed for admin registration.")

            return Response(
                self.get_context(
                    form=form,
                    message="OTP sending failed.",
                    errors={"otp": ["Unable to send OTP. Please try again."]},
                    success=False,
                ),
                template_name=self.template_form,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # ============================================================
        # OTP RESULT VALIDATION
        # ============================================================

        ok, message_text, errors = self.validate_otp_send_result(result)

        if not ok:
            logger.warning("OTP validation failed")
            logger.warning(errors)

            return Response(
                self.get_context(
                    form=form,
                    message=message_text,
                    errors=errors,
                    success=False,
                ),
                template_name=self.template_form,
                status=status.HTTP_400_BAD_REQUEST,
            )

        logger.info("OTP sent successfully. Redirecting to verify OTP page.")

        # ============================================================
        # REDIRECT TO OTP PAGE
        # ============================================================

        return redirect("verify_otp")
    

# ============================================================
#                 ADMIN REGISTRATION API VIEW
# ============================================================

class AdminRegistrationAPIView(BaseAuthAPIView):
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]

    def get(self, request, format=None):
        return self.success_response(
            message="Admin Registration API is ready.",
            data={
                "method": "POST",
                "content_type": "application/json",
                "required_fields": [
                    "first_name",
                    "last_name",
                    "username",
                    "email",
                    "country_code",
                    "mobile_number",
                    "language_preference",
                    "admin_secret_code",
                    "password1",
                    "password2",
                ],
                "sample_request": {
                    "first_name": "Shubham",
                    "last_name": "Patil",
                    "username": "shubhamadmin",
                    "email": "admin@example.com",
                    "country_code": "+91",
                    "mobile_number": "9890682025",
                    "language_preference": "en",
                    "admin_secret_code": "YOUR_ADMIN_SECRET_CODE",
                    "password1": "Admin@123",
                    "password2": "Admin@123"
                },
                "next_step": "Verify OTP using /accounts/api/verify-otp/",
            },
            http_status=status.HTTP_200_OK,
        )

    def post(self, request, format=None):
        form = AdminRegistrationForm(request.data)

        # ✅ FIX: role required before form validation
        form.instance.role = CustomUser.RoleChoices.ADMIN

        if not form.is_valid():
            return self.error_response(
                message="Admin registration failed.",
                errors=self.format_form_errors(form),
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        pending_data = form.cleaned_data.copy()
        pending_data["registration_state"] = "DRAFT"

        request.session["pending_admin_registration"] = pending_data
        request.session.modified = True

        email = pending_data.get("email")
        mobile_number = pending_data.get("mobile_number")

        try:
            result = create_otp_record(email, mobile_number)

        except Exception:
            logger.exception("OTP sending failed for admin registration.")

            return self.error_response(
                message="OTP sending failed.",
                errors={
                    "otp": ["Unable to send OTP. Please try again."]
                },
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        ok, message_text, errors = self.validate_otp_send_result(result)

        if not ok:
            return self.error_response(
                message=message_text,
                errors=errors,
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        return self.success_response(
            message="Admin registration saved as draft. OTP sent successfully.",
            data={
                "registration_state": "DRAFT",
                "email": email,
                "mobile_number": mobile_number,
                "otp_sent": True,
                "next": "/accounts/api/verify-otp/",
            },
            http_status=status.HTTP_200_OK,
        )


# ============================================================
#                 ADMIN LIST / DETAIL / UPDATE WEB + API VIEW
# ============================================================

class AdminListDetailView(BaseAuthAPIView):
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]


    template_list = "accounts/admin_list.html"
    template_detail = "accounts/admin_detail.html"

    allowed_update_fields = [
        "username",
        "first_name",
        "last_name",
        "email",
        "country_code",
        "mobile_number",
        "language_preference",
    ]

    def get_admin_queryset(self):
        return CustomUser.objects.filter(
            role=CustomUser.RoleChoices.ADMIN
        ).order_by("-id")

    def serialize_admin(self, admin):
        return {
            "id": admin.id,
            "username": admin.username,
            "first_name": admin.first_name,
            "last_name": admin.last_name,
            "email": admin.email,
            "country_code": admin.country_code,
            "mobile_number": admin.mobile_number,
            "language_preference": admin.language_preference,
            "role": admin.role,
            "is_active": admin.is_active,
            "date_joined": admin.date_joined,
        }

    def wants_html(self, request):
        return (
            request.path.startswith("/accounts/web/")
            or self.is_html_request(request)
        )

    # ============================================================
    #                 GET ALL ADMINS / GET ADMIN
    # ============================================================

    def get(self, request, username=None, format=None):
        if username:
            try:
                admin = self.get_admin_queryset().get(username=username)
            except CustomUser.DoesNotExist:
                context = {
                    "success": False,
                    "message": "Admin not found.",
                    "errors": {"username": ["Invalid admin username."]},
                    "admin": None,
                }

                if self.wants_html(request):
                    return Response(
                        context,
                        template_name=self.template_detail,
                        status=status.HTTP_404_NOT_FOUND,
                    )

                return self.error_response(
                    message="Admin not found.",
                    errors=context["errors"],
                    http_status=status.HTTP_404_NOT_FOUND,
                )

            admin_data = self.serialize_admin(admin)

            if self.wants_html(request):
                return Response(
                    {
                        "success": True,
                        "message": "Admin fetched successfully.",
                        "admin": admin_data,
                    },
                    template_name=self.template_detail,
                    status=status.HTTP_200_OK,
                )

            return self.success_response(
                message="Admin fetched successfully.",
                data=admin_data,
                http_status=status.HTTP_200_OK,
            )

        admins_data = [
            self.serialize_admin(admin)
            for admin in self.get_admin_queryset()
        ]

        if self.wants_html(request):
            return Response(
                {
                    "success": True,
                    "message": "All admins fetched successfully.",
                    "admins": admins_data,
                },
                template_name=self.template_list,
                status=status.HTTP_200_OK,
            )

        return self.success_response(
            message="All admins fetched successfully.",
            data=admins_data,
            http_status=status.HTTP_200_OK,
        )

    # ============================================================
    #                 UPDATE ADMIN API VIEW
    # ============================================================

    def put(self, request, username=None, format=None):
        return self.update_admin(request, username)

    def patch(self, request, username=None, format=None):
        return self.update_admin(request, username)

    # ============================================================
    #                 UPDATE ADMIN WEB VIEW
    # ============================================================

    def post(self, request, username=None, format=None):
        if username and self.wants_html(request):
            return self.update_admin(request, username)

        return self.error_response(
            message="Invalid request.",
            errors={"detail": ["POST is only allowed for web update form."]},
            http_status=status.HTTP_400_BAD_REQUEST,
        )

    # ============================================================
    #                 UPDATE ADMIN COMMON LOGIC
    # ============================================================

    def update_admin(self, request, username):
        if not username:
            return self.error_response(
                message="Username is required.",
                errors={"username": ["Username is required."]},
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            admin = self.get_admin_queryset().get(username=username)
        except CustomUser.DoesNotExist:
            return self.error_response(
                message="Admin not found.",
                errors={"username": ["Invalid username."]},
                http_status=status.HTTP_404_NOT_FOUND,
            )

        input_data = request.data if request.data else request.POST

        errors = {}
        update_data = {}

        for field in self.allowed_update_fields:
            if field in input_data:
                value = input_data.get(field)

                if value in [None, ""]:
                    errors[field] = [f"{field} is required."]
                else:
                    update_data[field] = value

        if not update_data:
            errors["allowed_fields"] = self.allowed_update_fields

        if errors:
            if self.wants_html(request):
                return Response(
                    {
                        "success": False,
                        "message": "Admin update failed.",
                        "errors": errors,
                        "admin": self.serialize_admin(admin),
                    },
                    template_name=self.template_detail,
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return self.error_response(
                message="Admin update failed.",
                errors=errors,
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        old_email = admin.email
        old_mobile_number = admin.mobile_number

        new_email = update_data.get("email", old_email)
        new_mobile_number = update_data.get("mobile_number", old_mobile_number)

        email_changed = new_email != old_email
        mobile_changed = new_mobile_number != old_mobile_number

        # OTP required only when email or mobile changed
        if email_changed or mobile_changed:
            request.session["pending_admin_update"] = {
                "username": username,
                "update_data": update_data,
                "old_email": old_email,
                "old_mobile_number": old_mobile_number,
                "new_email": new_email,
                "new_mobile_number": new_mobile_number,
            }
            request.session.modified = True

            try:
                result = create_otp_record(new_email, new_mobile_number)

            except Exception:
                logger.exception("OTP sending failed for admin update.")

                if self.wants_html(request):
                    return Response(
                        {
                            "success": False,
                            "message": "OTP sending failed.",
                            "errors": {
                                "otp": ["Unable to send OTP. Please try again."]
                            },
                            "admin": self.serialize_admin(admin),
                        },
                        template_name=self.template_detail,
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

                return self.error_response(
                    message="OTP sending failed.",
                    errors={"otp": ["Unable to send OTP. Please try again."]},
                    http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            ok, message_text, otp_errors = self.validate_otp_send_result(result)

            if not ok:
                if self.wants_html(request):
                    return Response(
                        {
                            "success": False,
                            "message": message_text,
                            "errors": otp_errors,
                            "admin": self.serialize_admin(admin),
                        },
                        template_name=self.template_detail,
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                return self.error_response(
                    message=message_text,
                    errors=otp_errors,
                    http_status=status.HTTP_400_BAD_REQUEST,
                )

            if self.wants_html(request):
                return Response(
                    {
                        "success": True,
                        "message": "Email or mobile number changed. OTP verification required.",
                        "otp_required": True,
                        "email_changed": email_changed,
                        "mobile_changed": mobile_changed,
                        "email": new_email,
                        "mobile_number": new_mobile_number,
                        "next": "/accounts/verify-otp/",
                        "admin": self.serialize_admin(admin),
                    },
                    template_name=self.template_detail,
                    status=status.HTTP_200_OK,
                )

            return self.success_response(
                message="Email or mobile number changed. OTP verification required.",
                data={
                    "otp_required": True,
                    "email_changed": email_changed,
                    "mobile_changed": mobile_changed,
                    "email": new_email,
                    "mobile_number": new_mobile_number,
                    "next": "/accounts/api/verify-otp/",
                },
                http_status=status.HTTP_200_OK,
            )

        # Normal update without OTP
        for field, value in update_data.items():
            setattr(admin, field, value)

        try:
            admin.full_clean()
            admin.save()

        except Exception as exc:
            errors = {"detail": [str(exc)]}

            if self.wants_html(request):
                return Response(
                    {
                        "success": False,
                        "message": "Validation failed.",
                        "errors": errors,
                        "admin": self.serialize_admin(admin),
                    },
                    template_name=self.template_detail,
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return self.error_response(
                message="Validation failed.",
                errors=errors,
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        admin_data = self.serialize_admin(admin)

        if self.wants_html(request):
            return Response(
                {
                    "success": True,
                    "message": "Admin updated successfully.",
                    "admin": admin_data,
                },
                template_name=self.template_detail,
                status=status.HTTP_200_OK,
            )

        return self.success_response(
            message="Admin updated successfully.",
            data=admin_data,
            http_status=status.HTTP_200_OK,
        )
        
            # ============================================================
    #                 DELETE ADMIN API + WEB VIEW
    # ============================================================

    def delete(self, request, username=None, format=None):
        if username:
            return self.delete_admin_by_username(request, username)

        return self.delete_current_admin_account(request)

    # ============================================================
    #                 DELETE ADMIN BY USERNAME
    #                 LOGIN NOT REQUIRED
    # ============================================================

    def delete_admin_by_username(self, request, username):
        try:
            admin = self.get_admin_queryset().get(username=username)

        except CustomUser.DoesNotExist:
            return self.error_response(
                message="Admin not found.",
                errors={"username": ["Invalid admin username."]},
                http_status=status.HTTP_404_NOT_FOUND,
            )

        deleted_admin_data = self.serialize_admin(admin)

        try:
            admin.delete()

        except Exception as exc:
            return self.error_response(
                message="Admin delete failed.",
                errors={"detail": [str(exc)]},
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        return self.success_response(
            message="Admin account deleted successfully.",
            data={
                "deleted_admin": deleted_admin_data,
                "current_account_deleted": False,
                "login_required": False,
            },
            http_status=status.HTTP_200_OK,
        )

    # ============================================================
    #                 DELETE CURRENT LOGIN ADMIN ACCOUNT
    #                 LOGIN REQUIRED
    # ============================================================

    def delete_current_admin_account(self, request):
        if not request.user.is_authenticated:
            return self.error_response(
                message="Login required.",
                errors={"auth": ["Please login first."]},
                http_status=status.HTTP_401_UNAUTHORIZED,
            )

        user = request.user

        if user.role != CustomUser.RoleChoices.ADMIN:
            return self.error_response(
                message="Only admin account can be deleted here.",
                errors={"role": ["Logged-in user is not admin."]},
                http_status=status.HTTP_403_FORBIDDEN,
            )

        deleted_admin_data = self.serialize_admin(user)

        try:
            user.delete()
            logout(request)

        except Exception as exc:
            return self.error_response(
                message="Current account delete failed.",
                errors={"detail": [str(exc)]},
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        return self.success_response(
            message="Current admin account deleted successfully. Please login again.",
            data={
                "deleted_admin": deleted_admin_data,
                "current_account_deleted": True,
                "login_required": True,
                "redirect_url": "/accounts/login/",
            },
            http_status=status.HTTP_200_OK,
        )
# ============================================================
#              CURRENT PROFILE UPDATE BASE MIXIN
# ============================================================

class CurrentProfileUpdateMixin:
    allowed_update_fields = [
        "username",
        "first_name",
        "last_name",
        "email",
        "country_code",
        "mobile_number",
        "language_preference",
    ]

    otp_required_fields = ["email", "mobile_number"]

    def normalize_value(self, value):
        if value is None:
            return ""
        return str(value).strip()

    def update_current_user_profile(self, request, update_data):
        user = CustomUser.objects.get(id=request.user.id)
        errors = {}

        clean_update_data = {
            field: value
            for field, value in update_data.items()
            if field in self.allowed_update_fields
        }

        if not clean_update_data:
            return False, {
                "message": "No valid fields provided.",
                "errors": {"allowed_fields": self.allowed_update_fields},
                "status": status.HTTP_400_BAD_REQUEST,
            }

        for field, value in clean_update_data.items():
            if value in [None, ""]:
                errors[field] = [f"{field} is required."]

        if errors:
            return False, {
                "message": "Profile update failed.",
                "errors": errors,
                "status": status.HTTP_400_BAD_REQUEST,
            }

        old_email = self.normalize_value(user.email)
        old_mobile_number = self.normalize_value(user.mobile_number)

        new_email = self.normalize_value(
            clean_update_data.get("email", old_email)
        )
        new_mobile_number = self.normalize_value(
            clean_update_data.get("mobile_number", old_mobile_number)
        )

        email_changed = (
            "email" in clean_update_data
            and new_email != old_email
        )

        mobile_changed = (
            "mobile_number" in clean_update_data
            and new_mobile_number != old_mobile_number
        )

        # ========================================================
        # EMAIL / MOBILE CHANGE असेल तर OTP REQUIRED
        # ========================================================
        if email_changed or mobile_changed:
            request.session["pending_profile_update"] = {
                "user_id": user.id,
                "update_data": clean_update_data,
                "old_email": old_email,
                "old_mobile_number": old_mobile_number,
                "new_email": new_email,
                "new_mobile_number": new_mobile_number,
                "email_changed": email_changed,
                "mobile_changed": mobile_changed,
            }
            request.session.modified = True

            try:
                result = create_otp_record(
                    email=new_email if email_changed else None,
                    mobile_number=new_mobile_number if mobile_changed else None,
                )

            except Exception:
                logger.exception("OTP sending failed for profile update.")

                return False, {
                    "message": "OTP sending failed.",
                    "errors": {
                        "otp": ["Unable to send OTP. Please try again."]
                    },
                    "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                }

            ok, message_text, otp_errors = self.validate_otp_send_result(result)

            if not ok:
                return False, {
                    "message": message_text,
                    "errors": otp_errors,
                    "status": status.HTTP_400_BAD_REQUEST,
                }

            if email_changed and mobile_changed:
                message = "Email and mobile number changed. Email OTP and SMS OTP verification required."
            elif email_changed:
                message = "Email changed. Email OTP verification required."
            else:
                message = "Mobile number changed. SMS OTP verification required."

            return True, {
                "message": message,
                "data": {
                    "otp_required": True,
                    "email_changed": email_changed,
                    "mobile_changed": mobile_changed,
                    "email": new_email,
                    "mobile_number": new_mobile_number,
                    "next": "/accounts/verify-otp/",
                },
                "status": status.HTTP_200_OK,
            }

        # ========================================================
        # EMAIL / MOBILE CHANGE नाही तर ONLY OTHER FIELDS UPDATE
        # ========================================================
        safe_direct_update_data = {
            field: value
            for field, value in clean_update_data.items()
            if field not in self.otp_required_fields
        }

        if not safe_direct_update_data:
            return False, {
                "message": "No profile changes found.",
                "errors": {
                    "profile": ["No profile changes found."]
                },
                "status": status.HTTP_400_BAD_REQUEST,
            }

        try:
            with transaction.atomic():
                for field, value in safe_direct_update_data.items():
                    setattr(user, field, value)

                user.full_clean()
                user.save()

        except Exception as exc:
            logger.exception("Profile update failed.")

            return False, {
                "message": "Validation failed.",
                "errors": {"detail": [str(exc)]},
                "status": status.HTTP_400_BAD_REQUEST,
            }

        return True, {
            "message": "Profile updated successfully.",
            "data": self.get_user_profile_data(user),
            "status": status.HTTP_200_OK,
        }

    # ========================================================
    # APPLY PROFILE UPDATE AFTER OTP VERIFY
    # ========================================================
    def complete_pending_profile_update(self, request):
        pending_data = request.session.get("pending_profile_update")

        if not pending_data:
            return None

        if not request.user.is_authenticated:
            return {
                "success": False,
                "message": "Login required to update profile.",
                "errors": {"auth": ["Please login again."]},
            }

        try:
            user = CustomUser.objects.get(id=pending_data["user_id"])

            if request.user.id != user.id:
                return {
                    "success": False,
                    "message": "Invalid profile update session.",
                    "errors": {
                        "session": ["Invalid profile update session."]
                    },
                }

            update_data = pending_data.get("update_data", {})

            clean_update_data = {
                field: value
                for field, value in update_data.items()
                if field in self.allowed_update_fields
            }

            with transaction.atomic():
                for field, value in clean_update_data.items():
                    setattr(user, field, value)

                user.full_clean()
                user.save()

            request.session.pop("pending_profile_update", None)
            request.session.modified = True

            return {
                "success": True,
                "message": "OTP verified. Profile updated successfully.",
                "data": self.get_user_profile_data(user),
            }

        except Exception as exc:
            logger.exception("Profile update after OTP verification failed.")

            return {
                "success": False,
                "message": "Profile update failed after OTP verification.",
                "errors": {"detail": [str(exc)]},
            }


# ============================================================
#              CURRENT PROFILE UPDATE API VIEW
# ============================================================

class CurrentProfileUpdateAPIView(
    CurrentProfileUpdateMixin,
    BaseAuthAPIView,
):
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        return self.success_response(
            message="Current profile update API is ready.",
            data={
                "method": ["PUT", "PATCH"],
                "login_required": True,
                "allowed_fields": self.allowed_update_fields,
                "otp_required_for": self.otp_required_fields,
                "current_profile": self.get_user_profile_data(request.user),
            },
            http_status=status.HTTP_200_OK,
        )

    def put(self, request, format=None):
        return self.update_profile(request)

    def patch(self, request, format=None):
        return self.update_profile(request)

    def update_profile(self, request):
        success, result = self.update_current_user_profile(
            request=request,
            update_data=request.data,
        )

        if success:
            return self.success_response(
                message=result["message"],
                data=result.get("data", {}),
                http_status=result["status"],
            )

        return self.error_response(
            message=result["message"],
            errors=result.get("errors", {}),
            http_status=result["status"],
        )


# ============================================================
#              CURRENT PROFILE UPDATE WEB VIEW
# ============================================================

class CurrentProfileUpdateWebView(
    LoginRequiredMixin,
    CurrentProfileUpdateMixin,
    BaseAuthAPIView,
):
    renderer_classes = [TemplateHTMLRenderer]
    permission_classes = [IsAuthenticated]
    template_name = "accounts/auth/current_profile_update.html"
    login_url = "/accounts/login/"

    def get_context(
        self,
        request,
        form=None,
        message="",
        errors=None,
        success=False,
        otp_required=False,
    ):
        return {
            "form": form or CurrentProfileUpdateForm(instance=request.user),
            "message": message,
            "errors": errors or {},
            "success": success,
            "otp_required": otp_required,
        }

    def get(self, request, format=None):
        return Response(
            self.get_context(request=request),
            template_name=self.template_name,
            status=status.HTTP_200_OK,
        )

    def post(self, request, format=None):
        form = CurrentProfileUpdateForm(
            data=request.POST,
            instance=request.user,
        )

        if not form.is_valid():
            return Response(
                self.get_context(
                    request=request,
                    form=form,
                    message="Profile update failed.",
                    errors=form.errors,
                    success=False,
                ),
                template_name=self.template_name,
                status=status.HTTP_400_BAD_REQUEST,
            )

        success, result = self.update_current_user_profile(
            request=request,
            update_data=form.cleaned_data,
        )

        if success:
            otp_required = result.get("data", {}).get("otp_required", False)

            if otp_required:
                return Response(
                    self.get_context(
                        request=request,
                        form=form,
                        message=result["message"],
                        success=True,
                        otp_required=True,
                    ),
                    template_name=self.template_name,
                    status=result["status"],
                )

            return Response(
                self.get_context(
                    request=request,
                    form=CurrentProfileUpdateForm(instance=request.user),
                    message=result["message"],
                    success=True,
                ),
                template_name=self.template_name,
                status=result["status"],
            )

        return Response(
            self.get_context(
                request=request,
                form=form,
                message=result["message"],
                errors=result.get("errors", {}),
                success=False,
            ),
            template_name=self.template_name,
            status=result["status"],
        )
        
        
        
# ============================================================
#                 FARMER REGISTRATION WEB VIEW
# ============================================================

class FarmerRegistrationWebView(BaseAuthAPIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_form = "accounts/farmer/farmer_register.html"

    def get_context(self, form=None, message="", errors=None, success=False, data=None):
        return {
            "form": form or FarmerRegistrationForm(),
            "message": message,
            "errors": errors or {},
            "success": success,
            "data": data or {},
        }

    def get(self, request, format=None):
        return Response(
            self.get_context(message="Fill farmer registration form."),
            template_name=self.template_form,
            status=status.HTTP_200_OK,
        )

    def post(self, request, format=None):
        form = FarmerRegistrationForm(request.POST)

        # ✅ FIX: role required before form validation
        form.instance.role = CustomUser.RoleChoices.FARMER

        if not form.is_valid():
            return Response(
                self.get_context(
                    form=form,
                    message="Farmer registration failed.",
                    errors=self.format_form_errors(form),
                    success=False,
                ),
                template_name=self.template_form,
                status=status.HTTP_400_BAD_REQUEST,
            )

        pending_data = form.cleaned_data.copy()
        pending_data["registration_state"] = "DRAFT"

        request.session["pending_farmer_registration"] = pending_data
        request.session.modified = True

        email = pending_data.get("email")
        mobile_number = pending_data.get("mobile_number")

        try:
            result = create_otp_record(email, mobile_number)

        except Exception:
            logger.exception("OTP sending failed for farmer registration.")

            return Response(
                self.get_context(
                    form=form,
                    message="OTP sending failed.",
                    errors={
                        "otp": ["Unable to send OTP. Please try again."]
                    },
                    success=False,
                ),
                template_name=self.template_form,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        ok, message_text, errors = self.validate_otp_send_result(result)

        if not ok:
            return Response(
                self.get_context(
                    form=form,
                    message=message_text,
                    errors=errors,
                    success=False,
                ),
                template_name=self.template_form,
                status=status.HTTP_400_BAD_REQUEST,
            )

        return redirect("verify_otp")


# ============================================================
#                 FARMER REGISTRATION API VIEW
# ============================================================

class FarmerRegistrationAPIView(BaseAuthAPIView):
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]

    def get(self, request, format=None):
        return self.success_response(
            message="Farmer Registration API is ready.",
            data={
                "method": "POST",
                "content_type": "application/json",
                "required_fields": [
                    "first_name",
                    "last_name",
                    "username",
                    "email",
                    "country_code",
                    "mobile_number",
                    "language_preference",
                    "password1",
                    "password2",
                ],
                "sample_request": {
                    "first_name": "Shubham",
                    "last_name": "Patil",
                    "username": "shubhamfarmer",
                    "email": "farmer@example.com",
                    "country_code": "+91",
                    "mobile_number": "9890682025",
                    "language_preference": "en",
                    "password1": "Farmer@123",
                    "password2": "Farmer@123",
                },
                "next_step": "Verify OTP using /accounts/api/verify-otp/",
            },
            http_status=status.HTTP_200_OK,
        )

    def post(self, request, format=None):
        form = FarmerRegistrationForm(request.data)

        # ✅ FIX: role required before form validation
        form.instance.role = CustomUser.RoleChoices.FARMER

        if not form.is_valid():
            return self.error_response(
                message="Farmer registration failed.",
                errors=self.format_form_errors(form),
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        pending_data = form.cleaned_data.copy()
        pending_data["registration_state"] = "DRAFT"

        request.session["pending_farmer_registration"] = pending_data
        request.session.modified = True

        email = pending_data.get("email")
        mobile_number = pending_data.get("mobile_number")

        try:
            result = create_otp_record(email, mobile_number)

        except Exception:
            logger.exception("OTP sending failed for farmer registration.")

            return self.error_response(
                message="OTP sending failed.",
                errors={
                    "otp": ["Unable to send OTP. Please try again."]
                },
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        ok, message_text, errors = self.validate_otp_send_result(result)

        if not ok:
            return self.error_response(
                message=message_text,
                errors=errors,
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        return self.success_response(
            message="Farmer registration saved as draft. OTP sent successfully.",
            data={
                "registration_state": "DRAFT",
                "email": email,
                "mobile_number": mobile_number,
                "otp_sent": True,
                "next": "/accounts/api/verify-otp/",
            },
            http_status=status.HTTP_200_OK,
        )
    
    
# ============================================================
#              FARMER LIST / DETAIL / UPDATE WEB + API VIEW
# ============================================================

class FarmerListDetailView(BaseAuthAPIView):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer, BrowsableAPIRenderer]

    template_list = "accounts/farmer_list.html"
    template_detail = "accounts/admin/farmer_detail.html"

    allowed_update_fields = [
        "username",
        "first_name",
        "last_name",
        "email",
        "country_code",
        "mobile_number",
        "language_preference",
        "gender",
        "village",
        "taluka",
        "district",
        "state",
        "pincode",
        "full_address",
    ]

    def get_farmer_queryset(self):
        return CustomUser.objects.filter(
            role=CustomUser.RoleChoices.FARMER
        ).select_related("farmer_profile").order_by("-id")

    def serialize_farmer(self, farmer):
        profile = getattr(farmer, "farmer_profile", None)

        return {
            "id": farmer.id,
            "username": farmer.username,
            "first_name": farmer.first_name,
            "last_name": farmer.last_name,
            "full_name": f"{farmer.first_name or ''} {farmer.last_name or ''}".strip(),

            "email": farmer.email,
            "country_code": farmer.country_code,
            "mobile_number": farmer.mobile_number,
            "language_preference": farmer.language_preference,

            "gender": getattr(profile, "gender", None),
            "village": getattr(profile, "village", None),
            "taluka": getattr(profile, "taluka", None),
            "district": getattr(profile, "district", None),
            "state": getattr(profile, "state", None),
            "pincode": getattr(profile, "pincode", None),
            "full_address": getattr(profile, "full_address", None),

            "role": farmer.role,
            "is_active": farmer.is_active,
            "date_joined": farmer.date_joined,
        }

    def wants_html(self, request):
        return (
            request.path.startswith("/accounts/web/")
            or self.is_html_request(request)
        )

    def get(self, request, username=None, format=None):
        if username:
            try:
                farmer = self.get_farmer_queryset().get(username=username)

            except CustomUser.DoesNotExist:
                context = {
                    "success": False,
                    "message": "Farmer not found.",
                    "errors": {
                        "username": ["Invalid farmer username."]
                    },
                    "farmer": None,
                }

                if self.wants_html(request):
                    return Response(
                        context,
                        template_name=self.template_detail,
                        status=status.HTTP_404_NOT_FOUND,
                    )

                return self.error_response(
                    message="Farmer not found.",
                    errors=context["errors"],
                    http_status=status.HTTP_404_NOT_FOUND,
                )

            farmer_data = self.serialize_farmer(farmer)

            if self.wants_html(request):
                return Response(
                    {
                        "success": True,
                        "message": "Farmer fetched successfully.",
                        "farmer": farmer_data,
                    },
                    template_name=self.template_detail,
                    status=status.HTTP_200_OK,
                )

            return self.success_response(
                message="Farmer fetched successfully.",
                data=farmer_data,
                http_status=status.HTTP_200_OK,
            )

        farmers_data = [
            self.serialize_farmer(farmer)
            for farmer in self.get_farmer_queryset()
        ]

        if self.wants_html(request):
            return Response(
                {
                    "success": True,
                    "message": "All farmers fetched successfully.",
                    "farmers": farmers_data,
                },
                template_name=self.template_list,
                status=status.HTTP_200_OK,
            )

        return self.success_response(
            message="All farmers fetched successfully.",
            data=farmers_data,
            http_status=status.HTTP_200_OK,
        )

    # ============================================================
    #                 UPDATE FARMER API VIEW
    # ============================================================

    def put(self, request, username=None, format=None):
        return self.update_farmer(request, username)

    def patch(self, request, username=None, format=None):
        return self.update_farmer(request, username)

    # ============================================================
    #                 UPDATE FARMER WEB VIEW
    # ============================================================

    def post(self, request, username=None, format=None):
        if username and self.wants_html(request):
            return self.update_farmer(request, username)

        return self.error_response(
            message="Invalid request.",
            errors={"detail": ["POST is only allowed for web update form."]},
            http_status=status.HTTP_400_BAD_REQUEST,
        )

    # ============================================================
    #                 UPDATE FARMER COMMON LOGIC
    # ============================================================

    def update_farmer(self, request, username):
        if not username:
            return self.error_response(
                message="Username is required.",
                errors={"username": ["Username is required."]},
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            farmer = self.get_farmer_queryset().get(username=username)
        except CustomUser.DoesNotExist:
            return self.error_response(
                message="Farmer not found.",
                errors={"username": ["Invalid username."]},
                http_status=status.HTTP_404_NOT_FOUND,
            )

        input_data = request.data if request.data else request.POST

        errors = {}
        update_data = {}

        for field in self.allowed_update_fields:
            if field in input_data:
                value = input_data.get(field)

                if value in [None, ""]:
                    errors[field] = [f"{field} is required."]
                else:
                    update_data[field] = value

        if not update_data:
            errors["allowed_fields"] = self.allowed_update_fields

        if errors:
            if self.wants_html(request):
                return Response(
                    {
                        "success": False,
                        "message": "Farmer update failed.",
                        "errors": errors,
                        "farmer": self.serialize_farmer(farmer),
                    },
                    template_name=self.template_detail,
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return self.error_response(
                message="Farmer update failed.",
                errors=errors,
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        old_email = farmer.email
        old_mobile_number = farmer.mobile_number

        new_email = update_data.get("email", old_email)
        new_mobile_number = update_data.get("mobile_number", old_mobile_number)

        email_changed = new_email != old_email
        mobile_changed = new_mobile_number != old_mobile_number

        if email_changed or mobile_changed:
            request.session["pending_farmer_update"] = {
                "username": username,
                "update_data": update_data,
                "old_email": old_email,
                "old_mobile_number": old_mobile_number,
                "new_email": new_email,
                "new_mobile_number": new_mobile_number,
            }
            request.session.modified = True

            try:
                result = create_otp_record(new_email, new_mobile_number)

            except Exception:
                logger.exception("OTP sending failed for farmer update.")

                if self.wants_html(request):
                    return Response(
                        {
                            "success": False,
                            "message": "OTP sending failed.",
                            "errors": {
                                "otp": ["Unable to send OTP. Please try again."]
                            },
                            "farmer": self.serialize_farmer(farmer),
                        },
                        template_name=self.template_detail,
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

                return self.error_response(
                    message="OTP sending failed.",
                    errors={"otp": ["Unable to send OTP. Please try again."]},
                    http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            ok, message_text, otp_errors = self.validate_otp_send_result(result)

            if not ok:
                if self.wants_html(request):
                    return Response(
                        {
                            "success": False,
                            "message": message_text,
                            "errors": otp_errors,
                            "farmer": self.serialize_farmer(farmer),
                        },
                        template_name=self.template_detail,
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                return self.error_response(
                    message=message_text,
                    errors=otp_errors,
                    http_status=status.HTTP_400_BAD_REQUEST,
                )

            if self.wants_html(request):
                return Response(
                    {
                        "success": True,
                        "message": "Email or mobile number changed. OTP verification required.",
                        "otp_required": True,
                        "email_changed": email_changed,
                        "mobile_changed": mobile_changed,
                        "email": new_email,
                        "mobile_number": new_mobile_number,
                        "next": "/accounts/verify-otp/",
                        "farmer": self.serialize_farmer(farmer),
                    },
                    template_name=self.template_detail,
                    status=status.HTTP_200_OK,
                )

            return self.success_response(
                message="Email or mobile number changed. OTP verification required.",
                data={
                    "otp_required": True,
                    "email_changed": email_changed,
                    "mobile_changed": mobile_changed,
                    "email": new_email,
                    "mobile_number": new_mobile_number,
                    "next": "/accounts/api/v1/verify-otp/",
                },
                http_status=status.HTTP_200_OK,
            )

        for field, value in update_data.items():
            setattr(farmer, field, value)

        try:
            farmer.full_clean()
            farmer.save()

        except Exception as exc:
            errors = {"detail": [str(exc)]}

            if self.wants_html(request):
                return Response(
                    {
                        "success": False,
                        "message": "Validation failed.",
                        "errors": errors,
                        "farmer": self.serialize_farmer(farmer),
                    },
                    template_name=self.template_detail,
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return self.error_response(
                message="Validation failed.",
                errors=errors,
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        farmer_data = self.serialize_farmer(farmer)

        if self.wants_html(request):
            return Response(
                {
                    "success": True,
                    "message": "Farmer updated successfully.",
                    "farmer": farmer_data,
                },
                template_name=self.template_detail,
                status=status.HTTP_200_OK,
            )

        return self.success_response(
            message="Farmer updated successfully.",
            data=farmer_data,
            http_status=status.HTTP_200_OK,
        )

    # ============================================================
    #                 DELETE FARMER API + WEB VIEW
    # ============================================================

    def delete(self, request, username=None, format=None):
        if username:
            return self.delete_farmer_by_username(request, username)

        return self.delete_current_farmer_account(request)

    # ============================================================
    #                 DELETE FARMER BY USERNAME
    # ============================================================

    def delete_farmer_by_username(self, request, username):
        try:
            farmer = self.get_farmer_queryset().get(username=username)

        except CustomUser.DoesNotExist:
            return self.error_response(
                message="Farmer not found.",
                errors={"username": ["Invalid farmer username."]},
                http_status=status.HTTP_404_NOT_FOUND,
            )

        deleted_farmer_data = self.serialize_farmer(farmer)

        try:
            farmer.delete()

        except Exception as exc:
            return self.error_response(
                message="Farmer delete failed.",
                errors={"detail": [str(exc)]},
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        return self.success_response(
            message="Farmer account deleted successfully.",
            data={
                "deleted_farmer": deleted_farmer_data,
                "current_account_deleted": False,
                "login_required": False,
            },
            http_status=status.HTTP_200_OK,
        )

    # ============================================================
    #                 DELETE CURRENT LOGIN FARMER ACCOUNT
    # ============================================================

    def delete_current_farmer_account(self, request):
        if not request.user.is_authenticated:
            return self.error_response(
                message="Login required.",
                errors={"auth": ["Please login first."]},
                http_status=status.HTTP_401_UNAUTHORIZED,
            )

        user = request.user

        if user.role != CustomUser.RoleChoices.FARMER:
            return self.error_response(
                message="Only farmer account can be deleted here.",
                errors={"role": ["Logged-in user is not farmer."]},
                http_status=status.HTTP_403_FORBIDDEN,
            )

        deleted_farmer_data = self.serialize_farmer(user)

        try:
            user.delete()
            logout(request)

        except Exception as exc:
            return self.error_response(
                message="Current account delete failed.",
                errors={"detail": [str(exc)]},
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        return self.success_response(
            message="Current farmer account deleted successfully. Please login again.",
            data={
                "deleted_farmer": deleted_farmer_data,
                "current_account_deleted": True,
                "login_required": True,
                "redirect_url": "/accounts/login/",
            },
            http_status=status.HTTP_200_OK,
        )
    
   

# ============================================================
#              CURRENT FARMER PROFILE UPDATE BASE MIXIN
# ============================================================

class CurrentFarmerProfileUpdateMixin:
    allowed_update_fields = [
        "username",
        "first_name",
        "last_name",
        "email",
        "country_code",
        "mobile_number",
        "language_preference",
        "gender",
        "village",
        "taluka",
        "district",
        "state",
        "pincode",
        "full_address",
    ]

    def update_current_farmer_profile(self, request, update_data):
        user = request.user
        errors = {}

        if user.role != CustomUser.RoleChoices.FARMER:
            return False, {
                "message": "Only farmer profile can be updated here.",
                "errors": {"role": ["Logged-in user is not farmer."]},
                "status": status.HTTP_403_FORBIDDEN,
            }

        for field, value in update_data.items():
            if field not in self.allowed_update_fields:
                continue

            if value in [None, ""]:
                errors[field] = [f"{field} is required."]

        if errors:
            return False, {
                "message": "Farmer profile update failed.",
                "errors": errors,
                "status": status.HTTP_400_BAD_REQUEST,
            }

        clean_update_data = {
            field: value
            for field, value in update_data.items()
            if field in self.allowed_update_fields
        }

        if not clean_update_data:
            return False, {
                "message": "No valid fields provided.",
                "errors": {"allowed_fields": self.allowed_update_fields},
                "status": status.HTTP_400_BAD_REQUEST,
            }

        old_email = user.email
        old_mobile_number = user.mobile_number

        new_email = clean_update_data.get("email", old_email)
        new_mobile_number = clean_update_data.get(
            "mobile_number",
            old_mobile_number,
        )

        email_changed = new_email != old_email
        mobile_changed = new_mobile_number != old_mobile_number

        if email_changed or mobile_changed:
            request.session["pending_farmer_profile_update"] = {
                "user_id": user.id,
                "update_data": clean_update_data,
                "old_email": old_email,
                "old_mobile_number": old_mobile_number,
                "new_email": new_email,
                "new_mobile_number": new_mobile_number,
            }
            request.session.modified = True

            try:
                result = create_otp_record(new_email, new_mobile_number)

            except Exception:
                logger.exception("OTP sending failed for farmer profile update.")

                return False, {
                    "message": "OTP sending failed.",
                    "errors": {
                        "otp": ["Unable to send OTP. Please try again."]
                    },
                    "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                }

            ok, message_text, otp_errors = self.validate_otp_send_result(result)

            if not ok:
                return False, {
                    "message": message_text,
                    "errors": otp_errors,
                    "status": status.HTTP_400_BAD_REQUEST,
                }

            return True, {
                "message": "Email or mobile number changed. OTP verification required.",
                "data": {
                    "otp_required": True,
                    "email_changed": email_changed,
                    "mobile_changed": mobile_changed,
                    "email": new_email,
                    "mobile_number": new_mobile_number,
                    "next": "/accounts/api/v1/verify-otp/",
                },
                "status": status.HTTP_200_OK,
            }

        try:
            with transaction.atomic():
                for field, value in clean_update_data.items():
                    setattr(user, field, value)

                user.full_clean()
                user.save()

        except Exception as exc:
            return False, {
                "message": "Validation failed.",
                "errors": {"detail": [str(exc)]},
                "status": status.HTTP_400_BAD_REQUEST,
            }

        return True, {
            "message": "Farmer profile updated successfully.",
            "data": self.get_user_profile_data(user),
            "status": status.HTTP_200_OK,
        }


# ============================================================
#              CURRENT FARMER PROFILE UPDATE API VIEW
# ============================================================

class CurrentFarmerProfileUpdateAPIView(
    CurrentFarmerProfileUpdateMixin,
    BaseAuthAPIView,
):
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        return self.success_response(
            message="Current farmer profile update API is ready.",
            data={
                "method": ["PUT", "PATCH"],
                "login_required": True,
                "allowed_fields": self.allowed_update_fields,
                "current_profile": self.get_user_profile_data(request.user),
            },
            http_status=status.HTTP_200_OK,
        )

    def put(self, request, format=None):
        return self.update_profile(request)

    def patch(self, request, format=None):
        return self.update_profile(request)

    def update_profile(self, request):
        success, result = self.update_current_farmer_profile(
            request=request,
            update_data=request.data,
        )

        if success:
            return self.success_response(
                message=result["message"],
                data=result.get("data", {}),
                http_status=result["status"],
            )

        return self.error_response(
            message=result["message"],
            errors=result.get("errors", {}),
            http_status=result["status"],
        )


# ============================================================
#              CURRENT FARMER PROFILE UPDATE WEB VIEW
# ============================================================

class CurrentFarmerProfileUpdateWebView(
    LoginRequiredMixin,
    CurrentFarmerProfileUpdateMixin,
    BaseAuthAPIView,
):
    renderer_classes = [TemplateHTMLRenderer]
    permission_classes = [IsAuthenticated]
    template_name = "accounts/auth/current_farmer_profile_update.html"
    login_url = "/accounts/login/"

    def get_context(
        self,
        request,
        form=None,
        message="",
        errors=None,
        success=False,
        otp_required=False,
    ):
        return {
            "form": form or CurrentProfileUpdateForm(instance=request.user),
            "message": message,
            "errors": errors or {},
            "success": success,
            "otp_required": otp_required,
        }

    def get(self, request, format=None):
        context = self.get_context(request)
        return Response(context, template_name=self.template_name)

    def post(self, request, format=None):
        form = CurrentProfileUpdateForm(
            data=request.POST,
            instance=request.user,
        )

        if not form.is_valid():
            context = self.get_context(
                request=request,
                form=form,
                message="Farmer profile update failed.",
                errors=form.errors,
                success=False,
            )
            return Response(
                context,
                template_name=self.template_name,
                status=status.HTTP_400_BAD_REQUEST,
            )

        success, result = self.update_current_farmer_profile(
            request=request,
            update_data=form.cleaned_data,
        )

        if success:
            otp_required = result.get("data", {}).get("otp_required", False)

            if otp_required:
                context = self.get_context(
                    request=request,
                    form=form,
                    message=result["message"],
                    success=True,
                    otp_required=True,
                )
                return Response(
                    context,
                    template_name=self.template_name,
                    status=result["status"],
                )

            context = self.get_context(
                request=request,
                form=CurrentProfileUpdateForm(instance=request.user),
                message=result["message"],
                success=True,
            )
            return Response(
                context,
                template_name=self.template_name,
                status=result["status"],
            )

        context = self.get_context(
            request=request,
            form=form,
            message=result["message"],
            errors=result.get("errors", {}),
            success=False,
        )

        return Response(
            context,
            template_name=self.template_name,
            status=result["status"],
        )
   
   
# ============================================================
#          SEARCH FARMER + ACTIVE / INACTIVE
# ============================================================
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.views.decorators.http import require_POST

User = get_user_model()


def farmer_detail_web(request, username):
    farmer = get_object_or_404(
        User.objects.select_related('farmer_profile'),
        username=username
    )

    return render(request, 'accounts/admin/farmer_detail.html', {
        'farmer': farmer
    })


def admin_search_farmers(request):
    search = request.GET.get('search', '').strip()

    farmers = User.objects.filter(role='farmer').select_related('farmer_profile').order_by('id')

    if search:
        farmers = farmers.filter(
            Q(username__icontains=search)
            | Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(email__icontains=search)
            | Q(country_code__icontains=search)
            | Q(mobile_number__icontains=search)
            | Q(farmer_profile__village__icontains=search)
            | Q(farmer_profile__district__icontains=search)
        ).distinct()

    paginator = Paginator(farmers, 10)
    page_number = request.GET.get('page')
    farmers_page = paginator.get_page(page_number)

    return render(request, 'accounts/admin/farmer_management.html', {
        'farmers': farmers_page,
        'search': search
    })


@require_POST
def admin_toggle_farmer_status(request, farmer_id):
    farmer = get_object_or_404(User, id=farmer_id, role='farmer')

    farmer.is_active = not farmer.is_active
    farmer.save()

    if farmer.is_active:
        messages.success(request, 'Farmer activated successfully.')
    else:
        messages.success(request, 'Farmer deactivated successfully.')

    return redirect('admin_search_farmers')

   
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt


# ============================================================
#                 ROLE WISE DASHBOARD MIXIN
# ============================================================

class RoleDashboardMixin:
    def get_redirect_url(self, user):
        role = str(getattr(user, "role", "")).strip().lower()

        # Admin Redirect
        if user.is_superuser or user.is_staff or role == "admin":
            return "/accounts/admin/dashboard/"

        # Farmer Redirect
        if role == "farmer":
            return "/accounts/farmer/dashboard/"

        # Default Redirect
        return "/accounts/login/"
    
# ============================================================
#                 LOGIN API + WEB VIEW
# ============================================================

@method_decorator(csrf_exempt, name="dispatch")
class LoginAPIView(RoleDashboardMixin, BaseAuthAPIView):
    renderer_classes = [
        TemplateHTMLRenderer,
        JSONRenderer,
        BrowsableAPIRenderer,
    ]
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    permission_classes = [AllowAny]
    authentication_classes = []
    template_form = "accounts/auth/login.html"

    def get_renderers(self):
        if self.request.path.startswith("/accounts/api/"):
            return [JSONRenderer(), BrowsableAPIRenderer()]

        return [TemplateHTMLRenderer(), JSONRenderer(), BrowsableAPIRenderer()]

    def get(self, request, format=None):
        if request.user.is_authenticated:
            redirect_url = self.get_redirect_url(request.user)

            if self.is_html_request(request):
                return redirect(redirect_url)

            return self.success_response(
                message="User already logged in.",
                data={
                    "role": request.user.role,
                    "redirect_url": redirect_url,
                    "user": self.get_user_profile_data(request.user),
                },
                http_status=status.HTTP_200_OK,
            )

        if self.is_html_request(request):
            return Response(
                {
                    "form": UserLoginForm(),
                    "message": "Login page loaded successfully.",
                    "success": True,
                },
                template_name=self.template_form,
                status=status.HTTP_200_OK,
            )

        return self.success_response(
            message="Login endpoint ready.",
            data={
                "method": "POST",
                "login_with": "username / email / mobile_number",
                "required_fields": ["username", "password"],
            },
            http_status=status.HTTP_200_OK,
        )

    def post(self, request, format=None):
        input_data = self.get_request_data(request)

        if self.is_html_request(request):
            form = UserLoginForm(request, data=input_data)

            if not form.is_valid():
                return Response(
                    {
                        "form": form,
                        "message": "Invalid login credentials.",
                        "errors": form.errors,
                        "success": False,
                    },
                    template_name=self.template_form,
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user = form.get_user()

            if not user.is_active:
                return Response(
                    {
                        "form": form,
                        "message": "Your account is inactive. Please verify OTP first.",
                        "errors": {
                            "detail": [
                                "Your account is inactive. Please verify OTP first."
                            ]
                        },
                        "success": False,
                    },
                    template_name=self.template_form,
                    status=status.HTTP_403_FORBIDDEN,
                )

            login(request, user)

            language_code = user.language_preference or settings.LANGUAGE_CODE
            translation.activate(language_code)

            response = redirect(self.get_redirect_url(user))
            response.set_cookie(settings.LANGUAGE_COOKIE_NAME, language_code)

            messages.success(request, f"{user.role.title()} login successful.")
            return response

        serializer = LoginSerializer(data=input_data)

        if not serializer.is_valid():
            return self.error_response(
                message="Invalid login credentials.",
                errors=serializer.errors,
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.validated_data["user"]

        if not user.is_active:
            return self.error_response(
                message="User account is inactive.",
                errors={"detail": ["Please verify OTP first."]},
                http_status=status.HTTP_403_FORBIDDEN,
            )

        refresh = RefreshToken.for_user(user)
        token, _ = Token.objects.get_or_create(user=user)

        return self.success_response(
            message=f"{user.role.title()} login successful.",
            data={
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "token": token.key,
                "role": user.role,
                "redirect_url": self.get_redirect_url(user),
                "user": self.get_user_profile_data(user),
            },
            http_status=status.HTTP_200_OK,
        )


# ============================================================
#                 ADMIN DASHBOARD WEB VIEW
# ============================================================

class AdminDashboardView(LoginRequiredMixin, BaseAuthAPIView):
    renderer_classes = [TemplateHTMLRenderer]
    permission_classes = [IsAuthenticated]
    template_name = "accounts/admin/admin_dashboard.html"
    login_url = "/auth/accounts/login/"

    def is_admin_user(self, user):
        if not user or not user.is_authenticated:
            return False

        role = str(getattr(user, "role", "")).strip().lower()

        return (
            user.is_superuser
            or user.is_staff
            or role == "admin"
        )

    def get(self, request, format=None):
        if not self.is_admin_user(request.user):
            messages.error(request, "Only admin can access this dashboard.")
            return redirect("/accounts/login/")

        return Response(
            {
                "success": True,
                "message": "Welcome to Admin Dashboard.",
                "user": self.get_user_profile_data(request.user),
            },
            template_name=self.template_name,
            status=status.HTTP_200_OK,
        )


# ============================================================
#                 FARMER DASHBOARD WEB VIEW
# ============================================================

class FarmerDashboardView(LoginRequiredMixin, BaseAuthAPIView):
    renderer_classes = [TemplateHTMLRenderer]
    permission_classes = [IsAuthenticated]
    template_name = "accounts/farmer/farmer_dashboard.html"
    login_url = "/accounts/auth/login/"

    def get(self, request, format=None):
        role = str(getattr(request.user, "role", "")).strip().lower()

        if role != "farmer":
            messages.error(request, "Only farmer can access this dashboard.")
            return redirect("/accounts/login/")

        return Response(
            {
                "success": True,
                "message": "Welcome to Farmer Dashboard.",
                "user": self.get_user_profile_data(request.user),
            },
            template_name=self.template_name,
            status=status.HTTP_200_OK,
        )


# ============================================================
#                 ADMIN DASHBOARD API VIEW
# ============================================================

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer, TemplateHTMLRenderer
from rest_framework.response import Response

from .models import CustomUser


class AdminDashboardAPIView(BaseAuthAPIView):
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer, TemplateHTMLRenderer]
    permission_classes = [IsAuthenticated]

    template_name = "admin_dashboard.html"

    def is_html_request(self, request):
        return getattr(request.accepted_renderer, "format", None) == "html"

    def is_admin_user(self, user):
        if not user or not user.is_authenticated:
            return False

        role = getattr(user, "role", None)

        return (
            user.is_superuser
            or user.is_staff
            or role == CustomUser.RoleChoices.ADMIN
            or str(role).strip().lower() == "admin"
        )

    def get(self, request, format=None):
        if not self.is_admin_user(request.user):

            if self.is_html_request(request):
                return Response(
                    {
                        "message": "Only admin can access admin dashboard.",
                        "errors": {
                            "role": ["Only admin can access this dashboard."]
                        },
                        "success": False,
                    },
                    template_name=self.template_name,
                    status=status.HTTP_403_FORBIDDEN,
                )

            return self.error_response(
                message="Permission denied.",
                errors={
                    "role": ["Only admin can access this dashboard."]
                },
                http_status=status.HTTP_403_FORBIDDEN,
            )

        data = {
            "dashboard": "admin",
            "user": self.get_user_profile_data(request.user),
        }

        if self.is_html_request(request):
            return Response(
                {
                    "message": "Admin dashboard fetched successfully.",
                    "data": data,
                    "user_data": data["user"],
                    "success": True,
                },
                template_name=self.template_name,
                status=status.HTTP_200_OK,
            )

        return self.success_response(
            message="Admin dashboard fetched successfully.",
            data=data,
            http_status=status.HTTP_200_OK,
        )


# ============================================================
#                 FARMER DASHBOARD API VIEW
# ============================================================

class FarmerDashboardAPIView(BaseAuthAPIView):
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        if getattr(request.user, "role", None) != CustomUser.RoleChoices.FARMER:
            return self.error_response(
                message="Permission denied.",
                errors={"role": ["Only farmer can access this dashboard."]},
                http_status=status.HTTP_403_FORBIDDEN,
            )

        return self.success_response(
            message="Farmer dashboard fetched successfully.",
            data={
                "dashboard": "farmer",
                "user": self.get_user_profile_data(request.user),
            },
            http_status=status.HTTP_200_OK,
        )
        
# ============================================================
#                     LOGOUT API + WEB VIEW
# ============================================================

class LogoutAPIView(BaseAuthAPIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]
    template_form = "accounts/auth/login.html"

    def get(self, request, format=None):
        return self.logout_user(request)

    def post(self, request, format=None):
        return self.logout_user(request)

    def logout_user(self, request):
        try:
            input_data = self.get_request_data(request)
            refresh_token = input_data.get("refresh")

            if refresh_token:
                try:
                    RefreshToken(refresh_token).blacklist()
                except Exception:
                    logger.warning("Refresh token blacklist failed or invalid token.")

            # Get user role BEFORE logout/session flush
            role = getattr(request.user, "role", None)

            if not role:
                role = request.session.get("user_type", "")

            # Clear old messages like "Farmer login successful."
            storage = messages.get_messages(request)
            list(storage)

            # Logout user
            logout(request)
            request.session.flush()

            # Role-wise logout message
            if role == "admin":
                logout_message = "Admin logout successful."
            elif role == "farmer":
                logout_message = "Farmer logout successful."
            else:
                logout_message = "Logout successful."

            if self.is_html_request(request):
                messages.success(request, logout_message)
                return redirect("login")

            return self.success_response(
                message=logout_message,
                data={
                    "role": role,
                    "redirect_url": "/accounts/login/",
                },
                http_status=status.HTTP_200_OK,
            )

        except Exception as exc:
            logger.exception("Error during logout")

            if self.is_html_request(request):
                messages.error(request, "Error during logout.")
                return redirect("login")

            return self.error_response(
                message="Error during logout.",
                errors={"detail": [str(exc)]},
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    
    
# ============================================================
#                     CHANGE PASSWORD API + WEB VIEW
# ============================================================

class ChangePasswordAPIView(BaseAuthAPIView):
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]

    permission_classes = [IsAuthenticated]
    template_form = "accounts/auth/change_password.html"

    def get(self, request, format=None):
        if self.is_html_request(request):
            return Response(
                {
                    "message": "Change password page loaded successfully.",
                    "success": True,
                    "errors": {},
                },
                template_name=self.template_form,
                status=status.HTTP_200_OK,
            )

        return self.success_response(
            message="Change password endpoint ready.",
            data={
                "method": "POST",
                "login_required": True,
                "required_fields": [
                    "old_password",
                    "new_password",
                    "confirm_password",
                ],
                "sample_request": {
                    "old_password": "Old@12345",
                    "new_password": "New@12345",
                    "confirm_password": "New@12345",
                },
            },
            http_status=status.HTTP_200_OK,
        )

    def post(self, request, format=None):
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")

        errors = {}

        if not old_password:
            errors["old_password"] = ["Old password is required."]

        if not new_password:
            errors["new_password"] = ["New password is required."]

        if not confirm_password:
            errors["confirm_password"] = ["Confirm password is required."]

        if errors:
            return self.password_response(
                request=request,
                message="All password fields are required.",
                errors=errors,
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        if not request.user.check_password(old_password):
            return self.password_response(
                request=request,
                message="Old password is incorrect.",
                errors={"old_password": ["Old password is incorrect."]},
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        if old_password == new_password:
            return self.password_response(
                request=request,
                message="New password must be different from old password.",
                errors={
                    "new_password": [
                        "New password must be different from old password."
                    ]
                },
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        if new_password != confirm_password:
            return self.password_response(
                request=request,
                message="New password and confirm password do not match.",
                errors={
                    "confirm_password": [
                        "New password and confirm password do not match."
                    ]
                },
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_password(new_password, user=request.user)

        except ValidationError as exc:
            return self.password_response(
                request=request,
                message="Password does not meet validation requirements.",
                errors={"new_password": list(exc.messages)},
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            request.user.set_password(new_password)
            request.user.save(update_fields=["password"])

            update_session_auth_hash(request, request.user)

        except Exception as exc:
            logger.exception("Error changing password.")

            return self.password_response(
                request=request,
                message="Error changing password.",
                errors={"detail": [str(exc)]},
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if self.is_html_request(request):
            messages.success(request, "Password changed successfully.")

        return self.password_response(
            request=request,
            message="Password changed successfully.",
            errors={},
            success=True,
            http_status=status.HTTP_200_OK,
        )

    def password_response(
        self,
        request,
        message,
        errors=None,
        success=False,
        http_status=status.HTTP_200_OK,
    ):
        errors = errors or {}

        if self.is_html_request(request):
            return Response(
                {
                    "message": message,
                    "errors": errors,
                    "success": success,
                },
                template_name=self.template_form,
                status=http_status,
            )

        if success:
            return self.success_response(
                message=message,
                data={},
                http_status=http_status,
            )

        return self.error_response(
            message=message,
            errors=errors,
            http_status=http_status,
        )
    
    


# ============================================================
#                     FORGOT PASSWORD API + WEB VIEW
# ============================================================

class ForgotPasswordAPIView(BaseAuthAPIView):
    renderer_classes = [
        JSONRenderer,
        TemplateHTMLRenderer,
    ]

    permission_classes = [AllowAny]
    template_form = "accounts/auth/forgot_password.html"

    def get(self, request, format=None):
        context = {
            "message": "Forgot password page loaded successfully.",
            "success": True,
            "errors": {},
            "data": {
                "steps": [
                    "Enter username, email, or phone number",
                    "Choose Email OTP or SMS OTP",
                    "Verify OTP",
                    "Set new password",
                    "Login with new password",
                ]
            },
        }

        if self.is_html_request(request):
            return Response(
                context,
                template_name=self.template_form,
                status=status.HTTP_200_OK,
            )

        return self.success_response(
            message="Forgot password endpoint ready.",
            data={
                "method": "POST",
                "required_fields": ["identifier", "otp_method"],
                "identifier_options": ["username", "email", "mobile_number"],
                "otp_method_options": ["email", "sms"],
                "sample_request": {
                    "identifier": "user@example.com",
                    "otp_method": "email",
                },
                "next_step": "/accounts/api/v1/verify-forgot-password-otp/",
            },
            http_status=status.HTTP_200_OK,
        )

    def post(self, request, format=None):
        input_data = self.get_request_data(request)

        identifier = input_data.get("identifier", "").strip()
        otp_method = input_data.get("otp_method", "").strip().lower()

        errors = {}

        if not identifier:
            errors["identifier"] = [
                "Username, email, or phone number is required."
            ]

        if not otp_method:
            errors["otp_method"] = [
                "Please choose Email OTP or SMS OTP."
            ]

        if otp_method and otp_method not in ["email", "sms"]:
            errors["otp_method"] = [
                "Invalid OTP method. Choose either email or sms."
            ]

        if errors:
            return self.forgot_password_response(
                request=request,
                message="Please enter valid details.",
                errors=errors,
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        # ------------------------------------------------------------
        # Detect identifier type
        # ------------------------------------------------------------
        identifier_type = "username"

        if "@" in identifier:
            identifier_type = "email"
        elif identifier.isdigit():
            identifier_type = "mobile"

        # ------------------------------------------------------------
        # If identifier is email, force email OTP
        # If identifier is mobile, force SMS OTP
        # If identifier is username, allow selected otp_method
        # ------------------------------------------------------------
        if identifier_type == "email":
            otp_method = "email"

        elif identifier_type == "mobile":
            otp_method = "sms"

        else:
            if otp_method not in ["email", "sms"]:
                return self.forgot_password_response(
                    request=request,
                    message="Please choose Email OTP or SMS OTP.",
                    errors={
                        "otp_method": ["Choose either email or sms."]
                    },
                    http_status=status.HTTP_400_BAD_REQUEST,
                )

        try:
            user = CustomUser.objects.get(
                Q(username__iexact=identifier)
                | Q(email__iexact=identifier)
                | Q(mobile_number=identifier)
            )

        except CustomUser.DoesNotExist:
            return self.forgot_password_response(
                request=request,
                message="User not found.",
                errors={
                    "detail": [
                        "No active user found with this username, email, or phone number."
                    ]
                },
                http_status=status.HTTP_404_NOT_FOUND,
            )

        except CustomUser.MultipleObjectsReturned:
            return self.forgot_password_response(
                request=request,
                message="Multiple users found.",
                errors={
                    "detail": [
                        "Please use your email address instead of phone number."
                    ]
                },
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        if not user.is_active:
            return self.forgot_password_response(
                request=request,
                message="User account is inactive.",
                errors={
                    "detail": [
                        "Please verify your account before resetting password."
                    ]
                },
                http_status=status.HTTP_403_FORBIDDEN,
            )

        if otp_method == "email" and not user.email:
            return self.forgot_password_response(
                request=request,
                message="Email not available.",
                errors={
                    "email": ["This user does not have an email address."]
                },
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        if otp_method == "sms" and not user.mobile_number:
            return self.forgot_password_response(
                request=request,
                message="Mobile number not available.",
                errors={
                    "mobile_number": [
                        "This user does not have a mobile number."
                    ]
                },
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        request.session["pending_password_reset"] = {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "mobile_number": user.mobile_number,
            "identifier_type": identifier_type,
            "otp_method": otp_method,
            "otp_verified": False,
        }
        request.session.modified = True

        # ------------------------------------------------------------
        # Send OTP based on final otp_method
        # ------------------------------------------------------------
        try:
            if otp_method == "email":
                result = create_otp_record(
                    email=user.email,
                    send_to="email",
                    purpose="forgot_password",
                )

            else:
                result = create_otp_record(
                    mobile_number=user.mobile_number,
                    send_to="sms",
                    purpose="forgot_password",
                )

        except Exception:
            logger.exception("OTP sending failed for forgot password.")

            return self.forgot_password_response(
                request=request,
                message="OTP sending failed.",
                errors={
                    "otp": ["Unable to send OTP. Please try again."]
                },
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        ok, message_text, otp_errors = self.validate_otp_send_result(result)

        if not ok:
            return self.forgot_password_response(
                request=request,
                message=message_text,
                errors=otp_errors,
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        return self.forgot_password_response(
            request=request,
            message="OTP sent successfully. Please verify OTP.",
            data={
                "username": user.username,
                "identifier_type": identifier_type,
                "email": user.email if otp_method == "email" else None,
                "mobile_number": user.mobile_number if otp_method == "sms" else None,
                "otp_method": otp_method,
                "otp_sent": True,
                "next": "/accounts/api/v1/verify-forgot-password-otp/",
            },
            success=True,
            http_status=status.HTTP_200_OK,
        )

    def forgot_password_response(
        self,
        request,
        message,
        errors=None,
        data=None,
        success=False,
        http_status=status.HTTP_200_OK,
    ):
        errors = errors or {}
        data = data or {}

        if self.is_html_request(request):
            return Response(
                {
                    "message": message,
                    "errors": errors,
                    "success": success,
                    "data": data,
                },
                template_name=self.template_form,
                status=http_status,
            )

        if success:
            return self.success_response(
                message=message,
                data=data,
                http_status=http_status,
            )

        return self.error_response(
            message=message,
            errors=errors,
            http_status=http_status,
        )

# ============================================================
#              VERIFY FORGOT PASSWORD OTP API + WEB VIEW
# ============================================================

class VerifyForgotPasswordOTPAPIView(BaseAuthAPIView):
    renderer_classes = [
        JSONRenderer,
        TemplateHTMLRenderer,
    ]

    permission_classes = [AllowAny]
    template_form = "accounts/auth/verify_forgot_password_otp.html"

    def get(self, request, format=None):
        if self.is_html_request(request):
            return Response(
                {
                    "message": "Verify OTP page loaded successfully.",
                    "success": True,
                    "errors": {},
                },
                template_name=self.template_form,
                status=status.HTTP_200_OK,
            )

        return self.success_response(
            message="Verify forgot password OTP endpoint ready.",
            data={
                "method": "POST",
                "required_fields": ["otp"],
                "sample_request": {
                    "otp": "123456"
                },
                "next_step": "/accounts/api/v1/reset-password/",
            },
            http_status=status.HTTP_200_OK,
        )

    def post(self, request, format=None):
        input_data = self.get_request_data(request)
        otp = input_data.get("otp", "").strip()

        pending_password_reset = request.session.get("pending_password_reset")

        if not pending_password_reset:
            return self.verify_otp_response(
                request=request,
                message="Password reset session not found.",
                errors={
                    "session": [
                        "Please start forgot password process first."
                    ]
                },
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        if not otp:
            return self.verify_otp_response(
                request=request,
                message="OTP is required.",
                errors={
                    "otp": ["Please enter OTP."]
                },
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        email = pending_password_reset.get("email")
        mobile_number = pending_password_reset.get("mobile_number")
        otp_method = pending_password_reset.get("otp_method")

        try:
            if otp_method == "email":
                otp_record = OTPVerification.objects.filter(
                    email=email,
                    email_otp=otp,
                    purpose="forgot_password",
                    is_email_verified=False,
                ).latest("created_at")

            else:
                otp_record = OTPVerification.objects.filter(
                    mobile_number=mobile_number,
                    mobile_otp=otp,
                    purpose="forgot_password",
                    is_mobile_verified=False,
                ).latest("created_at")

        except OTPVerification.DoesNotExist:
            return self.verify_otp_response(
                request=request,
                message="Invalid OTP.",
                errors={
                    "otp": ["Invalid or expired OTP."]
                },
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        if hasattr(otp_record, "is_expired") and otp_record.is_expired():
            return self.verify_otp_response(
                request=request,
                message="OTP expired.",
                errors={
                    "otp": ["OTP has expired. Please request a new OTP."]
                },
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        if otp_method == "email":
            otp_record.is_email_verified = True
        else:
            otp_record.is_mobile_verified = True

        otp_record.is_verified = True
        otp_record.save(
            update_fields=[
                "is_email_verified",
                "is_mobile_verified",
                "is_verified",
            ]
        )

        pending_password_reset["otp_verified"] = True
        request.session["pending_password_reset"] = pending_password_reset
        request.session.modified = True

        return self.verify_otp_response(
            request=request,
            message="OTP verified successfully. Please set new password.",
            data={
                "otp_verified": True,
                "otp_method": otp_method,
                "next": "/accounts/api/v1/reset-password/",
            },
            success=True,
            http_status=status.HTTP_200_OK,
        )

    def verify_otp_response(
        self,
        request,
        message,
        errors=None,
        data=None,
        success=False,
        http_status=status.HTTP_200_OK,
    ):
        errors = errors or {}
        data = data or {}

        if self.is_html_request(request):
            return Response(
                {
                    "message": message,
                    "errors": errors,
                    "success": success,
                    "data": data,
                },
                template_name=self.template_form,
                status=http_status,
            )

        if success:
            return self.success_response(
                message=message,
                data=data,
                http_status=http_status,
            )

        return self.error_response(
            message=message,
            errors=errors,
            http_status=http_status,
        )
# ============================================================
#                     RESET PASSWORD API + WEB VIEW
# ============================================================

class ResetPasswordAPIView(BaseAuthAPIView):
    renderer_classes = [
        JSONRenderer,
        TemplateHTMLRenderer,
    ]

    permission_classes = [AllowAny]
    template_form = "accounts/auth/reset_password.html"

    def get(self, request, format=None):
        if self.is_html_request(request):
            return Response(
                {
                    "message": "",
                    "success": False,
                    "errors": {},
                    "data": {},
                },
                template_name=self.template_form,
                status=status.HTTP_200_OK,
            )

        return self.success_response(
            message="Reset password endpoint ready.",
            data={
                "method": "POST",
                "required_fields": [
                    "new_password",
                    "confirm_password",
                ],
                "sample_request": {
                    "new_password": "StrongPass@123",
                    "confirm_password": "StrongPass@123",
                },
                "next_step": "/accounts/login/",
            },
            http_status=status.HTTP_200_OK,
        )

    def post(self, request, format=None):
        input_data = self.get_request_data(request)

        new_password = input_data.get("new_password", "").strip()
        confirm_password = input_data.get("confirm_password", "").strip()

        pending_password_reset = request.session.get("pending_password_reset")

        if not pending_password_reset:
            return self.reset_password_response(
                request=request,
                message="Password reset session not found.",
                errors={
                    "session": [
                        "Please start forgot password process first."
                    ]
                },
                success=False,
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        if not pending_password_reset.get("otp_verified"):
            return self.reset_password_response(
                request=request,
                message="OTP verification required.",
                errors={
                    "otp": [
                        "Please verify OTP before resetting password."
                    ]
                },
                success=False,
                http_status=status.HTTP_403_FORBIDDEN,
            )

        errors = {}

        if not new_password:
            errors["new_password"] = ["New password is required."]

        if not confirm_password:
            errors["confirm_password"] = ["Confirm password is required."]

        if new_password and confirm_password and new_password != confirm_password:
            errors["confirm_password"] = [
                "New password and confirm password do not match."
            ]

        if errors:
            return self.reset_password_response(
                request=request,
                message="Password reset failed.",
                errors=errors,
                success=False,
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = CustomUser.objects.get(
                id=pending_password_reset["user_id"]
            )

        except CustomUser.DoesNotExist:
            return self.reset_password_response(
                request=request,
                message="User not found.",
                errors={
                    "user": ["Invalid password reset user."]
                },
                success=False,
                http_status=status.HTTP_404_NOT_FOUND,
            )

        try:
            validate_password(new_password, user=user)

        except ValidationError as exc:
            return self.reset_password_response(
                request=request,
                message="Password does not meet validation requirements.",
                errors={
                    "new_password": list(exc.messages)
                },
                success=False,
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        # ============================================================
        #                     SAVE NEW PASSWORD
        # ============================================================

        user.set_password(new_password)
        user.save(update_fields=["password"])

        # Clear reset session
        request.session.pop("pending_password_reset", None)
        request.session.modified = True

        # ============================================================
        #             SUCCESS RESPONSE + LOGIN REDIRECT DATA
        # ============================================================

        return self.reset_password_response(
            request=request,
            message="Password changed successfully. Please login again.",
            errors={},
            data={
                "redirect_url": "/accounts/login/",
            },
            success=True,
            http_status=status.HTTP_200_OK,
        )

    def reset_password_response(
        self,
        request,
        message,
        errors=None,
        data=None,
        success=False,
        http_status=status.HTTP_200_OK,
    ):
        errors = errors or {}
        data = data or {}

        if self.is_html_request(request):
            return Response(
                {
                    "message": message,
                    "success": success,
                    "errors": errors,
                    "data": data,
                },
                template_name=self.template_form,
                status=http_status,
            )

        if success:
            return self.success_response(
                message=message,
                data=data,
                http_status=http_status,
            )

        return self.error_response(
            message=message,
            errors=errors,
            http_status=http_status,
        )
