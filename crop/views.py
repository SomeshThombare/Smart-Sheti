import csv
import logging

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.db.models import Count
from django.db import transaction

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser

from .forms import CropRecommendationForm
from .models import CropPredictionHistory
from .ml_model import predict_crop, get_model_accuracy


logger = logging.getLogger(__name__)

ROLE_ADMIN = "admin"
ROLE_FARMER = "farmer"


def get_crop_management_analysis(nitrogen, phosphorus, potassium, temperature, humidity, ph, rainfall):
    return {
        "nitrogen_status": "Low Nitrogen" if nitrogen < 40 else "Medium Nitrogen" if nitrogen <= 90 else "High Nitrogen",
        "phosphorus_status": "Low Phosphorus" if phosphorus < 30 else "Medium Phosphorus" if phosphorus <= 70 else "High Phosphorus",
        "potassium_status": "Low Potassium" if potassium < 30 else "Medium Potassium" if potassium <= 80 else "High Potassium",
        "ph_status": "Acidic Soil" if ph < 6 else "Neutral Soil" if ph <= 7.5 else "Alkaline Soil",
        "rainfall_status": "Low Rainfall" if rainfall < 60 else "Medium Rainfall" if rainfall <= 150 else "High Rainfall",
        "temperature_status": "Low Temperature" if temperature < 20 else "Suitable Temperature" if temperature <= 35 else "High Temperature",
        "humidity_status": "Low Humidity" if humidity < 40 else "Medium Humidity" if humidity <= 80 else "High Humidity",
    }


class BaseCropAPIView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    permission_classes = [IsAuthenticated]

    template_form = None
    template_result = None
    template_history = None
    template_dashboard = None
    template_records = None

    def get_user_role(self, request):
        role = (
            getattr(request.user, "role", None)
            or getattr(request.user, "user_type", None)
            or ""
        )
        return str(role).strip().lower()

    def is_admin(self, request):
        if not request.user.is_authenticated:
            return False

        role = self.get_user_role(request)

        return (
            request.user.is_superuser
            or request.user.is_staff
            or role == ROLE_ADMIN
        )

    def is_farmer(self, request):
        if not request.user.is_authenticated:
            return False

        role = self.get_user_role(request)

        return (
            request.user.is_superuser
            or request.user.is_staff
            or role == ROLE_FARMER
            or role == "farmers"
            or role == "user"
            or role == ""
        )

    def is_html_request(self, request):
        return getattr(request.accepted_renderer, "format", None) == "html"

    def success_response(self, message, data=None, http_status=status.HTTP_200_OK):
        return Response({
            "status": "success",
            "message": message,
            "data": data if data is not None else {},
        }, status=http_status)

    def error_response(self, message, errors=None, http_status=status.HTTP_400_BAD_REQUEST):
        return Response({
            "status": "error",
            "message": message,
            "errors": errors if errors is not None else {},
        }, status=http_status)

    def permission_denied_response(self, request, message):
        if self.is_html_request(request):
            return Response(
                {
                    "form": CropRecommendationForm(),
                    "message": "",
                    "error": message,
                    "success": False,
                },
                template_name=self.template_form or self.template_history or self.template_dashboard,
                status=status.HTTP_200_OK,
            )

        return self.error_response(
            message,
            {"detail": [message]},
            status.HTTP_403_FORBIDDEN,
        )

    def normalize_form_errors(self, form):
        return {
            field: [str(error) for error in errors]
            for field, errors in form.errors.items()
        }

    def get_farmer_queryset(self, request):
        return (
            CropPredictionHistory.objects
            .select_related("user")
            .filter(user=request.user)
            .order_by("-created_at")
        )

    def get_admin_queryset(self):
        return (
            CropPredictionHistory.objects
            .select_related("user")
            .all()
            .order_by("-created_at")
        )

    def serialize_history(self, item):
        analysis = get_crop_management_analysis(
            item.nitrogen,
            item.phosphorus,
            item.potassium,
            item.temperature,
            item.humidity,
            item.ph,
            item.rainfall,
        )

        return {
            "id": item.id,
            "farmer_name": item.user.username if item.user else "Unknown",
            "nitrogen": item.nitrogen,
            "phosphorus": item.phosphorus,
            "potassium": item.potassium,
            "temperature": item.temperature,
            "humidity": item.humidity,
            "ph": item.ph,
            "rainfall": item.rainfall,
            "predicted_crop": item.predicted_crop,
            "crop_management_analysis": analysis,
            "created_at": item.created_at,
        }

    def serialize_history_list(self, queryset):
        return [self.serialize_history(item) for item in queryset]

    @transaction.atomic
    def handle_crop_prediction(self, request):
        form = CropRecommendationForm(request.POST or request.data)

        if not form.is_valid():
            logger.warning("Crop form validation errors: %s", form.errors)

            if self.is_html_request(request):
                return Response(
                    {
                        "form": form,
                        "errors": self.normalize_form_errors(form),
                        "error": "Please enter valid crop recommendation values.",
                        "message": "",
                        "success": False,
                    },
                    template_name=self.template_form,
                    status=status.HTTP_200_OK,
                )

            return self.error_response(
                "Crop recommendation validation failed.",
                self.normalize_form_errors(form),
                status.HTTP_400_BAD_REQUEST,
            )

        nitrogen = form.cleaned_data["nitrogen"]
        phosphorus = form.cleaned_data["phosphorus"]
        potassium = form.cleaned_data["potassium"]
        temperature = form.cleaned_data["temperature"]
        humidity = form.cleaned_data["humidity"]
        ph = form.cleaned_data["ph"]
        rainfall = form.cleaned_data["rainfall"]

        try:
            predicted_crop = predict_crop(
                nitrogen,
                phosphorus,
                potassium,
                temperature,
                humidity,
                ph,
                rainfall,
            )

            crop_management_analysis = get_crop_management_analysis(
                nitrogen,
                phosphorus,
                potassium,
                temperature,
                humidity,
                ph,
                rainfall,
            )

            history = CropPredictionHistory.objects.create(
                user=request.user,
                nitrogen=nitrogen,
                phosphorus=phosphorus,
                potassium=potassium,
                temperature=temperature,
                humidity=humidity,
                ph=ph,
                rainfall=rainfall,
                predicted_crop=predicted_crop,
            )

            data = self.serialize_history(history)

            if self.is_html_request(request):
                return Response(
                    {
                        "history": history,
                        "crop_management_analysis": crop_management_analysis,
                        "message": "Crop recommended successfully.",
                        "error": "",
                        "success": True,
                    },
                    template_name=self.template_result,
                    status=status.HTTP_200_OK,
                )

            return self.success_response(
                "Crop recommended successfully.",
                data,
                status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.exception("Crop prediction error")

            if self.is_html_request(request):
                return Response(
                    {
                        "form": CropRecommendationForm(),
                        "error": "Crop prediction failed. Please try again.",
                        "message": "",
                        "success": False,
                    },
                    template_name=self.template_form,
                    status=status.HTTP_200_OK,
                )

            return self.error_response(
                "Crop prediction failed.",
                {"detail": [str(e)]},
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class FarmerCropRecommendationAPIView(BaseCropAPIView):
    template_form = "crop/farmer_crop_form.html"
    template_result = "crop/farmer_crop_result.html"

    def get(self, request, format=None):
        if not self.is_farmer(request):
            return self.permission_denied_response(
                request,
                "Only farmer can access crop recommendation page."
            )

        if self.is_html_request(request):
            return Response(
                {
                    "form": CropRecommendationForm(),
                    "message": "",
                    "error": "",
                    "success": True,
                },
                template_name=self.template_form,
                status=status.HTTP_200_OK,
            )

        return self.success_response(
            "Farmer crop recommendation page loaded successfully.",
            {"role": ROLE_FARMER},
        )

    def post(self, request, format=None):
        if not self.is_farmer(request):
            return self.permission_denied_response(
                request,
                "Only farmer can generate crop recommendation."
            )

        return self.handle_crop_prediction(request)


class FarmerCropHistoryAPIView(BaseCropAPIView):
    template_history = "crop/farmer_crop_history.html"

    def get(self, request, format=None):
        if not self.is_farmer(request):
            return self.permission_denied_response(
                request,
                "Only farmer can view own crop history."
            )

        histories = self.get_farmer_queryset(request)

        if self.is_html_request(request):
            return Response(
                {
                    "histories": histories,
                    "message": "Farmer crop history loaded successfully.",
                    "success": True,
                },
                template_name=self.template_history,
                status=status.HTTP_200_OK,
            )

        return self.success_response(
            "Farmer crop history loaded successfully.",
            self.serialize_history_list(histories),
        )


class FarmerCropHistoryDetailAPIView(BaseCropAPIView):
    template_result = "crop/farmer_crop_result.html"

    def get(self, request, pk, format=None):
        if not self.is_farmer(request):
            return self.permission_denied_response(
                request,
                "Only farmer can view own crop result."
            )

        history = get_object_or_404(
            CropPredictionHistory,
            pk=pk,
            user=request.user,
        )

        crop_management_analysis = get_crop_management_analysis(
            history.nitrogen,
            history.phosphorus,
            history.potassium,
            history.temperature,
            history.humidity,
            history.ph,
            history.rainfall,
        )

        if self.is_html_request(request):
            return Response(
                {
                    "history": history,
                    "crop_management_analysis": crop_management_analysis,
                    "message": "Crop result loaded successfully.",
                    "success": True,
                },
                template_name=self.template_result,
                status=status.HTTP_200_OK,
            )

        return self.success_response(
            "Crop result loaded successfully.",
            self.serialize_history(history),
        )


class AdminCropDashboardAPIView(BaseCropAPIView):
    template_dashboard = "crop/admin_crop_dashboard.html"

    def get(self, request, format=None):
        if not self.is_admin(request):
            return self.permission_denied_response(
                request,
                "Only admin can access crop dashboard."
            )

        histories = self.get_admin_queryset()

        total_predictions = histories.count()
        total_farmers = histories.values("user").distinct().count()

        most_recommended = (
            histories
            .values("predicted_crop")
            .annotate(total=Count("predicted_crop"))
            .order_by("-total")
            .first()
        )

        crop_stats = (
            histories
            .values("predicted_crop")
            .annotate(total=Count("predicted_crop"))
            .order_by("-total")
        )

        recent_predictions = histories[:10]

        dashboard = {
            "total_predictions": total_predictions,
            "total_farmers": total_farmers,
            "most_recommended_crop": most_recommended["predicted_crop"] if most_recommended else "",
            "most_recommended_count": most_recommended["total"] if most_recommended else 0,
            "model_accuracy": get_model_accuracy(),
        }

        if self.is_html_request(request):
            return Response(
                {
                    "dashboard": dashboard,
                    "crop_stats": crop_stats,
                    "recent_predictions": recent_predictions,
                    "message": "Admin crop dashboard loaded successfully.",
                    "success": True,
                },
                template_name=self.template_dashboard,
                status=status.HTTP_200_OK,
            )

        return self.success_response(
            "Admin crop dashboard loaded successfully.",
            {
                "dashboard": dashboard,
                "crop_stats": list(crop_stats),
                "recent_predictions": self.serialize_history_list(recent_predictions),
            },
        )


class AdminCropRecordsAPIView(BaseCropAPIView):
    template_records = "crop/admin_crop_records.html"

    def get(self, request, format=None):
        if not self.is_admin(request):
            return self.permission_denied_response(
                request,
                "Only admin can view all crop records."
            )

        records = self.get_admin_queryset()

        crop = request.GET.get("crop")
        farmer = request.GET.get("farmer")

        if crop:
            records = records.filter(predicted_crop__icontains=crop)

        if farmer:
            records = records.filter(user__username__icontains=farmer)

        if self.is_html_request(request):
            return Response(
                {
                    "records": records,
                    "crop": crop,
                    "farmer": farmer,
                    "message": "Admin crop records loaded successfully.",
                    "success": True,
                },
                template_name=self.template_records,
                status=status.HTTP_200_OK,
            )

        return self.success_response(
            "Admin crop records loaded successfully.",
            self.serialize_history_list(records),
        )


class AdminCropExportCSVAPIView(BaseCropAPIView):
    def get(self, request, format=None):
        if not self.is_admin(request):
            return self.permission_denied_response(
                request,
                "Only admin can export crop records."
            )

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="crop_prediction_records.csv"'

        writer = csv.writer(response)

        writer.writerow([
            "ID",
            "Farmer Name",
            "N",
            "P",
            "K",
            "Temperature",
            "Humidity",
            "pH",
            "Rainfall",
            "Predicted Crop",
            "Nitrogen Status",
            "Phosphorus Status",
            "Potassium Status",
            "pH Status",
            "Rainfall Status",
            "Temperature Status",
            "Humidity Status",
            "Date",
        ])

        for item in self.get_admin_queryset():
            analysis = get_crop_management_analysis(
                item.nitrogen,
                item.phosphorus,
                item.potassium,
                item.temperature,
                item.humidity,
                item.ph,
                item.rainfall,
            )

            writer.writerow([
                item.id,
                item.user.username if item.user else "Unknown",
                item.nitrogen,
                item.phosphorus,
                item.potassium,
                item.temperature,
                item.humidity,
                item.ph,
                item.rainfall,
                item.predicted_crop,
                analysis["nitrogen_status"],
                analysis["phosphorus_status"],
                analysis["potassium_status"],
                analysis["ph_status"],
                analysis["rainfall_status"],
                analysis["temperature_status"],
                analysis["humidity_status"],
                item.created_at,
            ])

        return response