import json
import logging
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from .forms import GovernmentSchemeForm
from .models import GovernmentScheme
from .serializers import GovernmentSchemeSerializer


logger = logging.getLogger(__name__)

ROLE_ADMIN = "admin"
ROLE_FARMER = "farmer"


class BaseGovernmentSchemeAPIView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    permission_classes = [IsAuthenticated]

    template_list = None
    template_form = None

    def is_html_request(self, request):
        return getattr(request.accepted_renderer, "format", None) == "html"

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

    def error_response(
        self,
        message,
        errors=None,
        http_status=status.HTTP_400_BAD_REQUEST,
    ):
        payload = {
            "status": "error",
            "message": message,
            "errors": errors if errors is not None else {},
        }
        self.log_json_response("error", payload)
        return Response(payload, status=http_status)

    def normalize_scheme_code(self, scheme_code):
        return str(scheme_code or "").strip().upper()

    def get_object(self, scheme_code):
        return get_object_or_404(
            GovernmentScheme,
            scheme_code=self.normalize_scheme_code(scheme_code),
        )

    def get_list_queryset(self):
        return GovernmentScheme.objects.all().order_by("-created_at", "-id")

    def get_active_list_queryset(self):
        return GovernmentScheme.objects.filter(
            status=GovernmentScheme.StatusChoices.ACTIVE
        ).order_by("-is_featured", "-created_at", "-id")

    def serialize_scheme(self, scheme, request):
        return GovernmentSchemeSerializer(
            scheme,
            context={"request": request},
        ).data

    def serialize_schemes(self, queryset, request):
        return GovernmentSchemeSerializer(
            queryset,
            many=True,
            context={"request": request},
        ).data

    def get_form_data(self, request):
        if request.FILES:
            data = request.POST.copy()
        else:
            data = request.data.copy() if hasattr(request.data, "copy") else dict(request.data)

        if data.get("scheme_code"):
            data["scheme_code"] = self.normalize_scheme_code(data.get("scheme_code"))

        return data

    def build_form(self, request, instance=None, data=None):
        return GovernmentSchemeForm(
            data=data if data is not None else self.get_form_data(request),
            files=request.FILES or None,
            instance=instance,
        )

    def normalize_form_errors(self, form):
        return {
            field: [str(error) for error in errors]
            for field, errors in form.errors.items()
        }

    def save_form_optimized(self, form, is_create=False):
        if is_create:
            return form.save()

        if not form.has_changed() and not form.files:
            return form.instance

        instance = form.save(commit=False)
        changed_fields = list(form.changed_data)

        for file_field in form.files.keys():
            if file_field not in changed_fields:
                changed_fields.append(file_field)

        if changed_fields:
            instance.save(update_fields=changed_fields)
        else:
            instance.save()

        if hasattr(form, "save_m2m"):
            form.save_m2m()

        return instance

    def base_context(self, request, **extra):
        context = {
            "is_admin": self.is_admin(request),
            "is_farmer": self.is_farmer(request),
            "message": "",
            "errors": {},
            "success": False,
        }
        context.update(extra)
        return context

    def render_html_form_response(
        self,
        request,
        form,
        scheme=None,
        message="",
        errors=None,
        success=False,
        http_status=status.HTTP_200_OK,
    ):
        return Response(
            self.base_context(
                request,
                form=form,
                scheme=scheme,
                message=message,
                errors=errors or {},
                success=success,
            ),
            template_name=self.template_form,
            status=http_status,
        )

    def render_html_list_response(
        self,
        request,
        schemes=None,
        message="",
        errors=None,
        success=False,
        http_status=status.HTTP_200_OK,
    ):
        return Response(
            self.base_context(
                request,
                schemes=schemes or [],
                message=message,
                errors=errors or {},
                success=success,
            ),
            template_name=self.template_list,
            status=http_status,
        )

    def permission_denied_response(self, request, message="Permission denied."):
        if self.is_html_request(request):
            return Response(
                self.base_context(
                    request,
                    message=message,
                    errors={"detail": [message]},
                    success=False,
                ),
                template_name=self.template_list or self.template_form,
                status=status.HTTP_403_FORBIDDEN,
            )

        return self.error_response(
            message=message,
            errors={"detail": [message]},
            http_status=status.HTTP_403_FORBIDDEN,
        )


class AdminGovernmentSchemeAPIView(BaseGovernmentSchemeAPIView):
    template_list = "government_schemes/admin_scheme_list.html"
    template_form = "government_schemes/admin_scheme_form.html"

    def get(self, request, scheme_code=None, format=None):
        if not self.is_admin(request):
            return self.permission_denied_response(
                request,
                "Only admin can access government schemes.",
            )

        try:
            if scheme_code:
                scheme = self.get_object(scheme_code)

                if self.is_html_request(request):
                    return self.render_html_form_response(
                        request=request,
                        form=GovernmentSchemeForm(instance=scheme),
                        scheme=scheme,
                        message="Government scheme loaded successfully.",
                        success=True,
                    )

                return self.success_response(
                    "Government scheme retrieved successfully.",
                    self.serialize_scheme(scheme, request),
                )

            schemes = self.get_list_queryset()

            if self.is_html_request(request):
                return self.render_html_list_response(
                    request=request,
                    schemes=schemes,
                    message="Government scheme list loaded successfully.",
                    success=True,
                )

            return self.success_response(
                "Government scheme list retrieved successfully.",
                self.serialize_schemes(schemes, request),
            )

        except Exception as error:
            logger.exception("Error fetching government schemes")
            return self.error_response(
                "Error fetching government scheme data.",
                {"detail": [str(error)]},
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @transaction.atomic
    def post(self, request, scheme_code=None, format=None):
        if not self.is_admin(request):
            return self.permission_denied_response(
                request,
                "Only admin can create/update government schemes.",
            )

        method = str(request.POST.get("_method", "")).upper()

        if method == "PUT" and scheme_code:
            return self._update(request, scheme_code, partial=False)

        if method == "DELETE" and scheme_code:
            return self.delete(request, scheme_code)

        if scheme_code:
            return self._update(request, scheme_code, partial=False)

        try:
            form = self.build_form(request)

            if not form.is_valid():
                errors = self.normalize_form_errors(form)

                if self.is_html_request(request):
                    return self.render_html_form_response(
                        request=request,
                        form=form,
                        message="Government scheme validation failed.",
                        errors=errors,
                        success=False,
                        http_status=status.HTTP_400_BAD_REQUEST,
                    )

                return self.error_response(
                    "Government scheme validation failed.",
                    errors,
                    status.HTTP_400_BAD_REQUEST,
                )

            scheme = self.save_form_optimized(form, is_create=True)

            if self.is_html_request(request):
                return redirect("government_scheme:admin_government_scheme_list")

            return self.success_response(
                "Government scheme created successfully.",
                self.serialize_scheme(scheme, request),
                status.HTTP_201_CREATED,
            )

        except Exception as error:
            logger.exception("Error creating government scheme")
            return self.error_response(
                "Error creating government scheme.",
                {"detail": [str(error)]},
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @transaction.atomic
    def put(self, request, scheme_code=None, format=None):
        if not self.is_admin(request):
            return self.permission_denied_response(
                request,
                "Only admin can update government schemes.",
            )

        if not scheme_code:
            return self.error_response(
                "Scheme code is required for update.",
                {"scheme_code": ["Scheme code is required for update."]},
            )

        return self._update(request, scheme_code, partial=False)

    @transaction.atomic
    def patch(self, request, scheme_code=None, format=None):
        if not self.is_admin(request):
            return self.permission_denied_response(
                request,
                "Only admin can update government schemes.",
            )

        if not scheme_code:
            return self.error_response(
                "Scheme code is required for update.",
                {"scheme_code": ["Scheme code is required for update."]},
            )

        return self._update(request, scheme_code, partial=True)

    def _update(self, request, scheme_code, partial=False):
        try:
            scheme = self.get_object(scheme_code)
            data = self.get_form_data(request)

            data["scheme_code"] = scheme.scheme_code

            form = self.build_form(request, instance=scheme, data=data)

            if partial:
                for field_name in form.fields:
                    if field_name not in data and field_name not in request.FILES:
                        form.fields[field_name].required = False

            if not form.is_valid():
                errors = self.normalize_form_errors(form)

                if self.is_html_request(request):
                    return self.render_html_form_response(
                        request=request,
                        form=form,
                        scheme=scheme,
                        message="Government scheme update validation failed.",
                        errors=errors,
                        success=False,
                        http_status=status.HTTP_400_BAD_REQUEST,
                    )

                return self.error_response(
                    "Government scheme update validation failed.",
                    errors,
                    status.HTTP_400_BAD_REQUEST,
                )

            updated_scheme = self.save_form_optimized(form, is_create=False)

            if self.is_html_request(request):
                return redirect("government_scheme:admin_government_scheme_list")

            return self.success_response(
                "Government scheme updated successfully.",
                self.serialize_scheme(updated_scheme, request),
            )

        except Exception as error:
            logger.exception("Error updating government scheme")
            return self.error_response(
                "Error updating government scheme.",
                {"detail": [str(error)]},
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @transaction.atomic
    def delete(self, request, scheme_code=None, format=None):
        if not self.is_admin(request):
            return self.permission_denied_response(
                request,
                "Only admin can delete government schemes.",
            )

        if not scheme_code:
            return self.error_response(
                "Scheme code is required for delete.",
                {"scheme_code": ["Scheme code is required for delete."]},
            )

        try:
            scheme = self.get_object(scheme_code)
            scheme.delete()

            return self.success_response(
                "Government scheme deleted successfully.",
                {},
            )

        except Exception as error:
            logger.exception("Error deleting government scheme")
            return self.error_response(
                "Error deleting government scheme.",
                {"detail": [str(error)]},
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AdminGovernmentSchemeFormPageView(BaseGovernmentSchemeAPIView):
    renderer_classes = [TemplateHTMLRenderer]
    permission_classes = [IsAuthenticated]

    template_list = "government_schemes/admin_scheme_list.html"
    template_form = "government_schemes/admin_scheme_form.html"

    def get(self, request, format=None):
        if not self.is_admin(request):
            return self.permission_denied_response(
                request,
                "Only admin can access scheme form page.",
            )

        return self.render_html_form_response(
            request=request,
            form=GovernmentSchemeForm(),
            scheme=None,
            message="Government scheme form page loaded successfully.",
            success=True,
        )


class FarmerGovernmentSchemeAPIView(BaseGovernmentSchemeAPIView):
    template_list = "government_schemes/farmer_scheme_list.html"
    template_form = "government_schemes/farmer_scheme_detail.html"

    def get(self, request, scheme_code=None, format=None):
        if not self.is_farmer(request):
            return self.permission_denied_response(
                request,
                "Only farmer can access government schemes.",
            )

        try:
            if scheme_code:
                scheme = self.get_object(scheme_code)

                if scheme.status != GovernmentScheme.StatusChoices.ACTIVE:
                    return self.error_response(
                        "Government scheme not available.",
                        {"detail": ["Only active schemes are visible to farmers."]},
                        status.HTTP_404_NOT_FOUND,
                    )

                if self.is_html_request(request):
                    return Response(
                        self.base_context(
                            request,
                            scheme=scheme,
                            message="Government scheme loaded successfully.",
                            success=True,
                        ),
                        template_name=self.template_form,
                        status=status.HTTP_200_OK,
                    )

                return self.success_response(
                    "Government scheme retrieved successfully.",
                    self.serialize_scheme(scheme, request),
                )

            schemes = self.get_active_list_queryset()

            if self.is_html_request(request):
                return self.render_html_list_response(
                    request=request,
                    schemes=schemes,
                    message="Government scheme list loaded successfully.",
                    success=True,
                )

            return self.success_response(
                "Government scheme list retrieved successfully.",
                self.serialize_schemes(schemes, request),
            )

        except Exception as error:
            logger.exception("Error fetching farmer government schemes")
            return self.error_response(
                "Error fetching government scheme data.",
                {"detail": [str(error)]},
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@login_required
def admin_scheme_dashboard(request):
    today = timezone.localdate()
    closing_date = today + timedelta(days=15)

    schemes = GovernmentScheme.objects.all()

    total_schemes = schemes.count()

    active_schemes = schemes.filter(
        status=GovernmentScheme.StatusChoices.ACTIVE
    ).count()

    expired_schemes = schemes.filter(
        end_date__lt=today
    ).count()

    closing_soon_schemes = schemes.filter(
        status=GovernmentScheme.StatusChoices.ACTIVE,
        end_date__gte=today,
        end_date__lte=closing_date,
    ).count()

    recent_schemes = schemes.order_by("-created_at", "-id")[:5]

    context = {
        "total_schemes": total_schemes,
        "active_schemes": active_schemes,
        "expired_schemes": expired_schemes,
        "closing_soon_schemes": closing_soon_schemes,
        "recent_schemes": recent_schemes,
        "message": "",
        "errors": {},
        "success": True,
    }

    return render(
        request,
        "government_schemes/admin_scheme_dashboard.html",
        context,
    )



@login_required
def farmer_scheme_dashboard(request):
    today = timezone.localdate()
    closing_date = today + timedelta(days=15)

    schemes = GovernmentScheme.objects.filter(
        status=GovernmentScheme.StatusChoices.ACTIVE
    )

    context = {
        "total_schemes": schemes.count(),
        "featured_schemes": schemes.filter(is_featured=True).count(),
        "closing_soon_schemes": schemes.filter(
            end_date__gte=today,
            end_date__lte=closing_date,
        ).count(),
        "new_schemes": schemes.order_by("-created_at")[:6],
        "recent_schemes": schemes.order_by("-created_at", "-id")[:5],
    }

    return render(
        request,
        "government_schemes/farmer_scheme_dashboard.html",
        context,
    )