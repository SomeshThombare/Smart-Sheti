import csv
import json
import logging

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Count

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser

from .recommendation import FertilizerRecommendation
from .models import FertilizerRecommendationHistory
from .forms import (
    FertilizerRecommendationInputForm,
    FertilizerRecommendationHistoryForm,
)
from .serializers import (
    FertilizerRecommendationInputSerializer,
    FertilizerRecommendationHistorySerializer,
    FertilizerRecommendationHistoryListSerializer,
    FertilizerDashboardStatsSerializer,
)

logger = logging.getLogger(__name__)

ROLE_ADMIN = "admin"
ROLE_FARMER = "farmer"


class BaseFertilizerRecommendationAPIView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    permission_classes = [IsAuthenticated]

    template_form = None
    template_result = None
    template_history = None
    template_dashboard = None

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

    def get_history_object(self, pk):
        return get_object_or_404(FertilizerRecommendationHistory, pk=pk)

    def get_admin_history_queryset(self):
        return (
            FertilizerRecommendationHistory.objects
            .select_related("user")
            .all()
            .order_by("-created_at")
        )

    def get_farmer_history_queryset(self, request):
        return (
            FertilizerRecommendationHistory.objects
            .select_related("user")
            .filter(user=request.user, user_type=ROLE_FARMER)
            .order_by("-created_at")
        )

    def serialize_history(self, history, request):
        return FertilizerRecommendationHistorySerializer(
            history,
            context={"request": request},
        ).data

    def serialize_history_list(self, queryset):
        return FertilizerRecommendationHistoryListSerializer(
            queryset,
            many=True,
        ).data

    def get_form_data(self, request):
        if request.FILES:
            return request.POST.copy()

        return request.data.copy() if hasattr(request.data, "copy") else dict(request.data)

    def build_input_form(self, request, data=None):
        if data is None:
            data = self.get_form_data(request)

        return FertilizerRecommendationInputForm(data=data or None)

    def build_history_form(self, request, instance=None, data=None):
        if data is None:
            data = self.get_form_data(request)

        return FertilizerRecommendationHistoryForm(
            data=data or None,
            instance=instance,
            request_user=request.user,
            request_user_type=self.get_user_role(request),
        )

    def normalize_form_errors(self, form):
        return {
            field: [str(error) for error in errors]
            for field, errors in form.errors.items()
        }

    def form_to_input_data(self, form):
        cleaned = form.cleaned_data

        return {
            "Crop": cleaned.get("crop_type"),
            "Soil_color": cleaned.get("soil_color"),
            "Nitrogen": cleaned.get("N"),
            "Phosphorus": cleaned.get("P"),
            "Potassium": cleaned.get("K"),
            "pH": cleaned.get("pH"),
            "Rainfall": cleaned.get("rainfall"),
            "Temperature": cleaned.get("temperature"),
        }

    def serializer_to_input_data(self, serializer):
        return serializer.validated_data

    def predict_fertilizer(self, input_data):
        recommendation = FertilizerRecommendation(
            crop_type=input_data.get("Crop"),
            soil_data={
                "soil_color": input_data.get("Soil_color"),
                "N": input_data.get("Nitrogen"),
                "P": input_data.get("Phosphorus"),
                "K": input_data.get("Potassium"),
                "pH": input_data.get("pH"),
                "rainfall": input_data.get("Rainfall"),
                "temperature": input_data.get("Temperature"),
            },
        )
        return recommendation.get_recommendation_result()

    def save_history(self, request, input_data, result, user_type):
        return FertilizerRecommendationHistory.objects.create(
            user=request.user,
            user_type=user_type,
            crop=input_data["Crop"],
            soil_color=input_data["Soil_color"],
            nitrogen=input_data["Nitrogen"],
            phosphorus=input_data["Phosphorus"],
            potassium=input_data["Potassium"],
            ph=input_data["pH"],
            rainfall=input_data["Rainfall"],
            temperature=input_data["Temperature"],
            recommendation_result=result,
        )

    def base_context(self, request, **extra):
        context = {
            "is_admin": self.is_admin(request),
            "is_farmer": self.is_farmer(request),
            "crops": FertilizerRecommendationHistory.CropChoices.values,
            "soil_colors": FertilizerRecommendationHistory.SoilColorChoices.values,
            "form": None,
            "history_form": None,
            "history": [],
            "dashboard": {},
            "message": "",
            "errors": {},
            "error": "",
            "success": False,
            "soil_data": {},
            "result": None,
            "crop": "",
        }
        context.update(extra)
        return context

    def render_html_form_response(
        self,
        request,
        form=None,
        input_data=None,
        message="",
        errors=None,
        error="",
        success=False,
        http_status=status.HTTP_200_OK,
    ):
        return Response(
            self.base_context(
                request,
                form=form or FertilizerRecommendationInputForm(),
                soil_data=input_data or {},
                message=message,
                errors=errors or {},
                error=error,
                success=success,
            ),
            template_name=self.template_form,
            status=http_status,
        )

    def render_html_result_response(self, request, input_data, result, message):
        return Response(
            self.base_context(
                request,
                crop=input_data.get("Crop"),
                soil_data=input_data,
                result=result,
                message=message,
                success=True,
            ),
            template_name=self.template_result,
            status=status.HTTP_200_OK,
        )

    def render_html_history_response(
        self,
        request,
        history=None,
        history_form=None,
        message="",
        errors=None,
        success=False,
        http_status=status.HTTP_200_OK,
    ):
        return Response(
            self.base_context(
                request,
                history=history or [],
                history_form=history_form,
                message=message,
                errors=errors or {},
                success=success,
            ),
            template_name=self.template_history,
            status=http_status,
        )

    def permission_denied_response(self, request, message="Permission denied."):
        if self.is_html_request(request):
            return Response(
                self.base_context(
                    request,
                    form=FertilizerRecommendationInputForm(),
                    message=message,
                    error=message,
                    errors={"detail": [message]},
                    success=False,
                ),
                template_name=self.template_form or self.template_history or self.template_dashboard,
                status=status.HTTP_403_FORBIDDEN,
            )

        return self.error_response(
            message=message,
            errors={"detail": [message]},
            http_status=status.HTTP_403_FORBIDDEN,
        )

    @transaction.atomic
    def handle_recommendation_post(self, request, user_type):
        if self.is_html_request(request):
            form = self.build_input_form(request)

            if not form.is_valid():
                return self.render_html_form_response(
                    request=request,
                    form=form,
                    input_data=request.data,
                    message=f"{user_type.title()} fertilizer recommendation validation failed.",
                    errors=self.normalize_form_errors(form),
                    error="Please check all fields properly.",
                    success=False,
                    http_status=status.HTTP_400_BAD_REQUEST,
                )

            input_data = self.form_to_input_data(form)

        else:
            serializer = FertilizerRecommendationInputSerializer(data=request.data)

            if not serializer.is_valid():
                return self.error_response(
                    f"{user_type.title()} fertilizer recommendation validation failed.",
                    serializer.errors,
                    status.HTTP_400_BAD_REQUEST,
                )

            input_data = self.serializer_to_input_data(serializer)

        try:
            result = self.predict_fertilizer(input_data)

            if result.get("status") == "error":
                error_message = result.get("message", "Fertilizer recommendation failed.")

                if self.is_html_request(request):
                    return self.render_html_form_response(
                        request=request,
                        form=self.build_input_form(request),
                        input_data=input_data,
                        message=f"{user_type.title()} fertilizer recommendation failed.",
                        errors={"detail": [error_message]},
                        error=error_message,
                        success=False,
                        http_status=status.HTTP_400_BAD_REQUEST,
                    )

                return self.error_response(
                    f"{user_type.title()} fertilizer recommendation failed.",
                    {"detail": [error_message]},
                    status.HTTP_400_BAD_REQUEST,
                )

            history = self.save_history(request, input_data, result, user_type)
            history_data = self.serialize_history(history, request)

            success_message = f"{user_type.title()} fertilizer recommendation generated successfully."

            if self.is_html_request(request):
                return self.render_html_result_response(
                    request=request,
                    input_data=input_data,
                    result=result,
                    message=success_message,
                )

            return self.success_response(
                success_message,
                {
                    "user_type": user_type,
                    "crop": input_data["Crop"],
                    "soil_data": input_data,
                    "result": result,
                    "history": history_data,
                },
                status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.exception("Error generating fertilizer recommendation")
            return self.error_response(
                "Error generating fertilizer recommendation.",
                {"detail": [str(e)]},
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AdminFertilizerRecommendationAPIView(BaseFertilizerRecommendationAPIView):
    template_form = "fertilizer/admin_fertilizer_form.html"
    template_result = "fertilizer/admin_fertilizer_result.html"

    def get(self, request, format=None):
        if not self.is_admin(request):
            return self.permission_denied_response(
                request,
                "Only admin can access admin fertilizer recommendation page.",
            )

        if self.is_html_request(request):
            return self.render_html_form_response(
                request=request,
                form=FertilizerRecommendationInputForm(),
                message="Admin fertilizer recommendation page loaded successfully.",
                success=True,
            )

        return self.success_response(
            "Admin fertilizer recommendation page loaded successfully.",
            {
                "role": ROLE_ADMIN,
                "crops": FertilizerRecommendationHistory.CropChoices.values,
                "soil_colors": FertilizerRecommendationHistory.SoilColorChoices.values,
            },
        )

    def post(self, request, format=None):
        if not self.is_admin(request):
            return self.permission_denied_response(
                request,
                "Only admin can generate fertilizer recommendation.",
            )

        return self.handle_recommendation_post(request, ROLE_ADMIN)


class FarmerFertilizerRecommendationAPIView(BaseFertilizerRecommendationAPIView):
    template_form = "fertilizer/farmer_fertilizer_form.html"
    template_result = "fertilizer/farmer_fertilizer_result.html"

    def get(self, request, format=None):
        if not self.is_farmer(request):
            return self.permission_denied_response(
                request,
                "Only farmer can access farmer fertilizer recommendation page.",
            )

        if self.is_html_request(request):
            return self.render_html_form_response(
                request=request,
                form=FertilizerRecommendationInputForm(),
                message="Farmer fertilizer recommendation page loaded successfully.",
                success=True,
            )

        return self.success_response(
            "Farmer fertilizer recommendation page loaded successfully.",
            {
                "role": ROLE_FARMER,
                "crops": FertilizerRecommendationHistory.CropChoices.values,
                "soil_colors": FertilizerRecommendationHistory.SoilColorChoices.values,
            },
        )

    def post(self, request, format=None):
        if not self.is_farmer(request):
            return self.permission_denied_response(
                request,
                "Only farmer can generate fertilizer recommendation.",
            )

        return self.handle_recommendation_post(request, ROLE_FARMER)


class AdminRecommendationHistoryAPIView(BaseFertilizerRecommendationAPIView):
    template_form = "fertilizer/admin_fertilizer_form.html"
    template_history = "fertilizer/admin_history.html"

    def get(self, request, format=None):
        if not self.is_admin(request):
            return self.permission_denied_response(
                request,
                "Only admin can view recommendation history.",
            )

        history = self.get_admin_history_queryset()
        history_data = self.serialize_history_list(history)

        if self.is_html_request(request):
            return self.render_html_history_response(
                request=request,
                history=history_data,
                history_form=FertilizerRecommendationHistoryForm(),
                message="Admin recommendation history loaded successfully.",
                success=True,
            )

        return self.success_response(
            "Admin recommendation history loaded successfully.",
            history_data,
        )

    @transaction.atomic
    def post(self, request, format=None):
        if not self.is_admin(request):
            return self.permission_denied_response(
                request,
                "Only admin can create recommendation history.",
            )

        if self.is_html_request(request):
            form = self.build_history_form(request)

            if not form.is_valid():
                return self.render_html_history_response(
                    request=request,
                    history=self.serialize_history_list(self.get_admin_history_queryset()),
                    history_form=form,
                    message="Recommendation history validation failed.",
                    errors=self.normalize_form_errors(form),
                    success=False,
                    http_status=status.HTTP_400_BAD_REQUEST,
                )

            form.save()

            return self.render_html_history_response(
                request=request,
                history=self.serialize_history_list(self.get_admin_history_queryset()),
                history_form=FertilizerRecommendationHistoryForm(),
                message="Recommendation history created successfully.",
                success=True,
                http_status=status.HTTP_201_CREATED,
            )

        serializer = FertilizerRecommendationHistorySerializer(
            data=request.data,
            context={"request": request},
        )

        if serializer.is_valid():
            serializer.save()
            return self.success_response(
                "Recommendation history created successfully.",
                serializer.data,
                status.HTTP_201_CREATED,
            )

        return self.error_response(
            "Recommendation history validation failed.",
            serializer.errors,
            status.HTTP_400_BAD_REQUEST,
        )


class AdminRecommendationHistoryDetailAPIView(BaseFertilizerRecommendationAPIView):
    template_form = "fertilizer/admin_fertilizer_form.html"
    template_history = "fertilizer/admin_history.html"

    def get(self, request, pk, format=None):
        if not self.is_admin(request):
            return self.permission_denied_response(
                request,
                "Only admin can view this history record.",
            )

        history = self.get_history_object(pk)

        return self.success_response(
            "Recommendation history retrieved successfully.",
            self.serialize_history(history, request),
        )

    @transaction.atomic
    def put(self, request, pk, format=None):
        return self._update(request, pk, partial=False)

    @transaction.atomic
    def patch(self, request, pk, format=None):
        return self._update(request, pk, partial=True)

    def _update(self, request, pk, partial=False):
        if not self.is_admin(request):
            return self.permission_denied_response(
                request,
                "Only admin can update recommendation history.",
            )

        history = self.get_history_object(pk)

        if self.is_html_request(request):
            form = self.build_history_form(request, instance=history)

            if partial:
                data = self.get_form_data(request)
                for field_name in form.fields:
                    if field_name not in data:
                        form.fields[field_name].required = False

            if not form.is_valid():
                return self.render_html_history_response(
                    request=request,
                    history=self.serialize_history_list(self.get_admin_history_queryset()),
                    history_form=form,
                    message="Recommendation history update validation failed.",
                    errors=self.normalize_form_errors(form),
                    success=False,
                    http_status=status.HTTP_400_BAD_REQUEST,
                )

            form.save()

            return self.render_html_history_response(
                request=request,
                history=self.serialize_history_list(self.get_admin_history_queryset()),
                history_form=FertilizerRecommendationHistoryForm(),
                message="Recommendation history updated successfully.",
                success=True,
            )

        serializer = FertilizerRecommendationHistorySerializer(
            history,
            data=request.data,
            partial=partial,
            context={"request": request},
        )

        if serializer.is_valid():
            serializer.save()
            return self.success_response(
                "Recommendation history updated successfully.",
                serializer.data,
            )

        return self.error_response(
            "Recommendation history update validation failed.",
            serializer.errors,
            status.HTTP_400_BAD_REQUEST,
        )

    @transaction.atomic
    def delete(self, request, pk, format=None):
        if not self.is_admin(request):
            return self.permission_denied_response(
                request,
                "Only admin can delete recommendation history.",
            )

        history = self.get_history_object(pk)
        history.delete()

        return self.success_response(
            "Recommendation history deleted successfully.",
            {},
            status.HTTP_200_OK,
        )


class FarmerRecommendationHistoryAPIView(BaseFertilizerRecommendationAPIView):
    template_form = "fertilizer/farmer_fertilizer_form.html"
    template_history = "fertilizer/farmer_history.html"

    def get(self, request, format=None):
        if not self.is_farmer(request):
            return self.permission_denied_response(
                request,
                "Only farmer can view own recommendation history.",
            )

        history_data = self.serialize_history_list(
            self.get_farmer_history_queryset(request)
        )

        if self.is_html_request(request):
            return self.render_html_history_response(
                request=request,
                history=history_data,
                message="Farmer recommendation history loaded successfully.",
                success=True,
            )

        return self.success_response(
            "Farmer recommendation history loaded successfully.",
            history_data,
        )


class FarmerRecommendationHistoryDetailAPIView(BaseFertilizerRecommendationAPIView):
    template_form = "fertilizer/farmer_fertilizer_form.html"
    template_history = "fertilizer/farmer_history.html"

    def get(self, request, pk, format=None):
        if not self.is_farmer(request):
            return self.permission_denied_response(
                request,
                "Only farmer can view own recommendation history detail.",
            )

        history = get_object_or_404(
            FertilizerRecommendationHistory,
            pk=pk,
            user=request.user,
            user_type=ROLE_FARMER,
        )

        return self.success_response(
            "Farmer recommendation history detail loaded successfully.",
            self.serialize_history(history, request),
        )


class FertilizerDashboardAPIView(BaseFertilizerRecommendationAPIView):
    template_form = "fertilizer/admin_fertilizer_form.html"
    template_dashboard = "fertilizer/admin_dashboard.html"

    def get(self, request, format=None):
        if not self.is_admin(request):
            return self.permission_denied_response(
                request,
                "Only admin can access fertilizer dashboard.",
            )

        total_recommendations = FertilizerRecommendationHistory.objects.count()

        total_farmer_recommendations = FertilizerRecommendationHistory.objects.filter(
            user_type=ROLE_FARMER
        ).count()

        total_admin_recommendations = FertilizerRecommendationHistory.objects.filter(
            user_type=ROLE_ADMIN
        ).count()

        total_unique_farmers = (
            FertilizerRecommendationHistory.objects
            .filter(user_type=ROLE_FARMER)
            .values("user")
            .distinct()
            .count()
        )

        crop_obj = (
            FertilizerRecommendationHistory.objects
            .values("crop")
            .annotate(total=Count("id"))
            .order_by("-total")
            .first()
        )

        soil_obj = (
            FertilizerRecommendationHistory.objects
            .values("soil_color")
            .annotate(total=Count("id"))
            .order_by("-total")
            .first()
        )

        data = {
            "total_recommendations": total_recommendations,
            "total_farmer_recommendations": total_farmer_recommendations,
            "total_admin_recommendations": total_admin_recommendations,
            "total_unique_farmers": total_unique_farmers,
            "most_used_crop": crop_obj["crop"] if crop_obj else "",
            "most_used_soil_color": soil_obj["soil_color"] if soil_obj else "",
        }

        serializer = FertilizerDashboardStatsSerializer(data)

        if self.is_html_request(request):
            return Response(
                self.base_context(
                    request,
                    dashboard=serializer.data,
                    message="Admin dashboard loaded successfully.",
                    success=True,
                ),
                template_name=self.template_dashboard,
                status=status.HTTP_200_OK,
            )

        return self.success_response(
            "Admin dashboard loaded successfully.",
            serializer.data,
        )


class FertilizerExportCSVAPIView(BaseFertilizerRecommendationAPIView):
    template_form = "fertilizer/admin_fertilizer_form.html"

    def get(self, request, format=None):
        if not self.is_admin(request):
            return self.permission_denied_response(
                request,
                "Only admin can export fertilizer recommendation history.",
            )

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            'attachment; filename="fertilizer_recommendation_history.csv"'
        )

        writer = csv.writer(response)

        writer.writerow([
            "ID",
            "Username",
            "User Type",
            "Crop",
            "Soil Color",
            "Nitrogen",
            "Phosphorus",
            "Potassium",
            "pH",
            "Rainfall",
            "Temperature",
            "Recommendation Result",
            "Created At",
            "Updated At",
        ])

        for item in self.get_admin_history_queryset():
            writer.writerow([
                item.id,
                item.user.username if item.user else "",
                item.user_type,
                item.crop,
                item.soil_color,
                item.nitrogen,
                item.phosphorus,
                item.potassium,
                item.ph,
                item.rainfall,
                item.temperature,
                json.dumps(item.recommendation_result, ensure_ascii=False),
                item.created_at,
                item.updated_at,
            ])

        return response


class AdminFertilizerFormPageView(AdminFertilizerRecommendationAPIView):
    pass


class FarmerFertilizerFormPageView(FarmerFertilizerRecommendationAPIView):
    pass