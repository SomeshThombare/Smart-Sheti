import json
import logging

from django.db.models import Q
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser

from .models import DiseasePrediction
from .forms import DiseaseUploadForm, PredictionSearchForm
from .predict import predict_disease


logger = logging.getLogger(__name__)

ROLE_ADMIN = "admin"
ROLE_FARMER = "farmer"


class BaseDiseaseAPIView(APIView):
    """
    Base Disease Detection API View

    Supports:
    - JSON + HTML response
    - Admin/Farmer role checking
    - Common response format
    - Logging
    - Form validation helpers
    - Optimized query helpers
    """

    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    permission_classes = [IsAuthenticated]

    template_list = None
    template_form = None
    template_detail = None

    # --------------------------------------------------
    # Logging Helpers
    # --------------------------------------------------
    def log_json_response(self, level, payload):
        try:
            pretty_json = json.dumps(payload, indent=4, ensure_ascii=False, default=str)
        except Exception:
            pretty_json = str(payload)

        if level == "info":
            logger.info("\n%s", pretty_json)
        elif level == "warning":
            logger.warning("\n%s", pretty_json)
        elif level == "error":
            logger.error("\n%s", pretty_json)
        else:
            logger.debug("\n%s", pretty_json)

    # --------------------------------------------------
    # Response Helpers
    # --------------------------------------------------
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

    # --------------------------------------------------
    # Common Utility Methods
    # --------------------------------------------------
    def is_html_request(self, request):
        return getattr(request.accepted_renderer, "format", None) == "html"

    def is_admin(self, request):
        user = request.user

        return (
            user.is_authenticated
            and (
                user.is_staff
                or user.is_superuser
                or getattr(user, "user_type", None) == ROLE_ADMIN
            )
        )

    def is_farmer(self, request):
        user = request.user

        if not user.is_authenticated:
            return False

        if hasattr(user, "user_type"):
            return user.user_type == ROLE_FARMER

        return not user.is_staff and not user.is_superuser

    def get_queryset(self):
        return DiseasePrediction.objects.all().order_by("-created_at")

    def get_farmer_queryset(self, request):
        return DiseasePrediction.objects.filter(
            user=request.user
        ).order_by("-created_at")

    def get_list_queryset(self):
        return DiseasePrediction.objects.select_related("user").only(
            "id",
            "user",
            "image",
            "crop_name",
            "disease_name",
            "confidence",
            "treatment",
            "suggestion",
            "class_name",
            "predicted_index",
            "status",
            "error_message",
            "created_at",
        ).order_by("-created_at")

    def get_object(self, prediction_id):
        return get_object_or_404(DiseasePrediction, id=prediction_id)

    def serialize_prediction(self, prediction):
        return {
            "id": prediction.id,
            "user": str(prediction.user) if prediction.user else "",
            "image": prediction.image.url if prediction.image else "",
            "crop_name": prediction.crop_name,
            "disease_name": prediction.disease_name,
            "confidence": prediction.confidence,
            "treatment": prediction.treatment,
            "suggestion": prediction.suggestion,
            "class_name": prediction.class_name,
            "predicted_index": prediction.predicted_index,
            "status": prediction.status,
            "error_message": prediction.error_message,
            "created_at": prediction.created_at,
        }

    def serialize_predictions(self, queryset):
        return [self.serialize_prediction(item) for item in queryset]

    def normalize_form_errors(self, form):
        try:
            return {
                field: [str(error) for error in errors]
                for field, errors in form.errors.items()
            }
        except Exception:
            return {"detail": ["Validation failed."]}

    # --------------------------------------------------
    # HTML Context Helpers
    # --------------------------------------------------
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

    def permission_denied_response(self, request, message="Permission denied."):
        context = self.base_context(
            request,
            message=message,
            errors={"detail": [message]},
            success=False,
        )

        if self.is_html_request(request):
            return Response(
                context,
                template_name=self.template_list or self.template_form or self.template_detail,
                status=status.HTTP_403_FORBIDDEN,
            )

        return self.error_response(
            message=message,
            errors={"detail": [message]},
            http_status=status.HTTP_403_FORBIDDEN,
        )

    def render_html_form_response(
        self,
        request,
        form,
        result=None,
        prediction_obj=None,
        message="",
        errors=None,
        success=False,
        http_status=status.HTTP_200_OK,
    ):
        return Response(
            self.base_context(
                request,
                form=form,
                result=result,
                prediction_obj=prediction_obj,
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
        predictions=None,
        form=None,
        message="",
        errors=None,
        success=False,
        http_status=status.HTTP_200_OK,
    ):
        return Response(
            self.base_context(
                request,
                predictions=predictions or [],
                form=form,
                message=message,
                errors=errors or {},
                success=success,
            ),
            template_name=self.template_list,
            status=http_status,
        )

    def render_html_detail_response(
        self,
        request,
        prediction=None,
        message="",
        errors=None,
        success=False,
        http_status=status.HTTP_200_OK,
    ):
        return Response(
            self.base_context(
                request,
                prediction=prediction,
                message=message,
                errors=errors or {},
                success=success,
            ),
            template_name=self.template_detail,
            status=http_status,
        )


class FarmerDiseaseDetectionAPIView(BaseDiseaseAPIView):
    """
    Farmer Disease Detection View

    GET  /disease/farmer/disease-detection/  -> upload page
    POST /disease/farmer/disease-detection/  -> upload image + detect disease

    Farmer can:
    - Upload image
    - See disease result
    - See treatment
    - See suggestion
    """

    template_form = "disease_detection/farmer_detect.html"

    def get(self, request, format=None):
        if not self.is_farmer(request):
            return self.permission_denied_response(
                request,
                "Only farmer can access disease detection page."
            )

        form = DiseaseUploadForm()

        if self.is_html_request(request):
            return self.render_html_form_response(
                request=request,
                form=form,
                result=None,
                prediction_obj=None,
                message="Disease detection page loaded successfully.",
                success=True,
                http_status=status.HTTP_200_OK,
            )

        return self.success_response(
            message="Disease detection page loaded successfully.",
            data={},
            http_status=status.HTTP_200_OK,
        )

    def post(self, request, format=None):
        if not self.is_farmer(request):
            return self.permission_denied_response(
                request,
                "Only farmer can upload crop images."
            )

        try:
            form = DiseaseUploadForm(request.POST, request.FILES)

            if not form.is_valid():
                errors = self.normalize_form_errors(form)

                if self.is_html_request(request):
                    return self.render_html_form_response(
                        request=request,
                        form=form,
                        result=None,
                        prediction_obj=None,
                        message="Image upload validation failed.",
                        errors=errors,
                        success=False,
                        http_status=status.HTTP_400_BAD_REQUEST,
                    )

                return self.error_response(
                    message="Image upload validation failed.",
                    errors=errors,
                    http_status=status.HTTP_400_BAD_REQUEST,
                )

            uploaded_image = form.cleaned_data["image"]

            prediction_obj = DiseasePrediction.objects.create(
                user=request.user,
                image=uploaded_image,
                crop_name="Processing",
                disease_name="Processing",
                confidence=0,
                treatment="Processing",
                suggestion="Processing",
                status="SUCCESS",
            )

            try:
                result = predict_disease(prediction_obj.image.path)

                prediction_obj.crop_name = result["crop_name"]
                prediction_obj.disease_name = result["disease_name"]
                prediction_obj.confidence = result["confidence"]
                prediction_obj.treatment = result["treatment"]
                prediction_obj.suggestion = result["suggestion"]
                prediction_obj.class_name = result.get("class_name", "")
                prediction_obj.predicted_index = result.get("predicted_index")
                prediction_obj.status = "SUCCESS"
                prediction_obj.error_message = ""
                prediction_obj.save()

                result["success"] = True

                response_data = {
                    "prediction": self.serialize_prediction(prediction_obj),
                    "result": result,
                }

                if self.is_html_request(request):
                    return self.render_html_form_response(
                        request=request,
                        form=DiseaseUploadForm(),
                        result=result,
                        prediction_obj=prediction_obj,
                        message="Disease detection completed successfully.",
                        success=True,
                        http_status=status.HTTP_200_OK,
                    )

                return self.success_response(
                    message="Disease detection completed successfully.",
                    data=response_data,
                    http_status=status.HTTP_201_CREATED,
                )

            except Exception as e:
                logger.exception("Disease prediction failed")

                prediction_obj.crop_name = "Unknown"
                prediction_obj.disease_name = "Prediction Failed"
                prediction_obj.confidence = 0
                prediction_obj.treatment = "No treatment available."
                prediction_obj.suggestion = "Please upload a clear crop leaf image and try again."
                prediction_obj.status = "FAILED"
                prediction_obj.error_message = str(e)
                prediction_obj.save()

                result = {
                    "success": False,
                    "crop_name": "Unknown",
                    "disease_name": "Prediction Failed",
                    "confidence": 0,
                    "treatment": "No treatment available.",
                    "suggestion": "Please upload a clear crop leaf image and try again.",
                    "error": str(e),

                    # old frontend support
                    "treatment_marathi": "No treatment available.",
                    "suggestion_marathi": "Please upload a clear crop leaf image and try again.",
                }

                if self.is_html_request(request):
                    return self.render_html_form_response(
                        request=request,
                        form=DiseaseUploadForm(),
                        result=result,
                        prediction_obj=prediction_obj,
                        message="Prediction failed.",
                        errors={"detail": [str(e)]},
                        success=False,
                        http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

                return self.error_response(
                    message="Prediction failed.",
                    errors={"detail": [str(e)]},
                    http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        except Exception as e:
            logger.exception("Error processing disease detection request")

            if self.is_html_request(request):
                return self.render_html_form_response(
                    request=request,
                    form=DiseaseUploadForm(),
                    result=None,
                    prediction_obj=None,
                    message="Error processing disease detection request.",
                    errors={"detail": [str(e)]},
                    success=False,
                    http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            return self.error_response(
                message="Error processing disease detection request.",
                errors={"detail": [str(e)]},
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class FarmerDiseaseHistoryAPIView(BaseDiseaseAPIView):
    """
    Farmer Disease History View

    GET /disease/farmer/disease-history/ -> farmer own history only
    """

    template_list = "disease_detection/farmer_history.html"

    def get(self, request, format=None):
        if not self.is_farmer(request):
            return self.permission_denied_response(
                request,
                "Only farmer can view farmer disease history."
            )

        try:
            predictions = self.get_farmer_queryset(request)
            predictions_data = self.serialize_predictions(predictions)

            if self.is_html_request(request):
                return self.render_html_list_response(
                    request=request,
                    predictions=predictions,
                    message="Farmer disease history retrieved successfully.",
                    success=True,
                    http_status=status.HTTP_200_OK,
                )

            return self.success_response(
                message="Farmer disease history retrieved successfully.",
                data=predictions_data,
                http_status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.exception("Error fetching farmer disease history")

            if self.is_html_request(request):
                return self.render_html_list_response(
                    request=request,
                    predictions=[],
                    message="Error fetching farmer disease history.",
                    errors={"detail": [str(e)]},
                    success=False,
                    http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            return self.error_response(
                message="Error fetching farmer disease history.",
                errors={"detail": [str(e)]},
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AdminDiseaseDashboardAPIView(BaseDiseaseAPIView):
    """
    Admin Disease Dashboard View

    GET /disease/admin/disease-dashboard/
    """

    template_list = "disease_detection/admin_dashboard.html"

    def get(self, request, format=None):
        if not self.is_admin(request):
            return self.permission_denied_response(
                request,
                "Only admin can access disease dashboard."
            )

        try:
            total_predictions = DiseasePrediction.objects.count()

            healthy_count = DiseasePrediction.objects.filter(
                disease_name__icontains="Healthy",
                status="SUCCESS"
            ).count()

            failed_count = DiseasePrediction.objects.filter(
                status="FAILED"
            ).count()

            disease_count = DiseasePrediction.objects.filter(
                status="SUCCESS"
            ).exclude(
                disease_name__icontains="Healthy"
            ).count()

            recent_predictions = DiseasePrediction.objects.select_related("user").order_by("-created_at")[:10]

            dashboard_data = {
                "total_predictions": total_predictions,
                "healthy_count": healthy_count,
                "disease_count": disease_count,
                "failed_count": failed_count,
                "recent_predictions": self.serialize_predictions(recent_predictions),
            }

            if self.is_html_request(request):
                return Response(
                    self.base_context(
                        request,
                        total_predictions=total_predictions,
                        healthy_count=healthy_count,
                        disease_count=disease_count,
                        failed_count=failed_count,
                        recent_predictions=recent_predictions,
                        message="Disease dashboard retrieved successfully.",
                        success=True,
                    ),
                    template_name=self.template_list,
                    status=status.HTTP_200_OK,
                )

            return self.success_response(
                message="Disease dashboard retrieved successfully.",
                data=dashboard_data,
                http_status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.exception("Error fetching disease dashboard")

            if self.is_html_request(request):
                return Response(
                    self.base_context(
                        request,
                        total_predictions=0,
                        healthy_count=0,
                        disease_count=0,
                        failed_count=0,
                        recent_predictions=[],
                        message="Error fetching disease dashboard.",
                        errors={"detail": [str(e)]},
                        success=False,
                    ),
                    template_name=self.template_list,
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            return self.error_response(
                message="Error fetching disease dashboard.",
                errors={"detail": [str(e)]},
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AdminDiseasePredictionAPIView(BaseDiseaseAPIView):
    """
    Admin Disease Prediction View

    GET /disease/admin/disease-predictions/                 -> list/search/filter
    GET /disease/admin/disease-predictions/<prediction_id>/  -> detail
    """

    template_list = "disease_detection/admin_prediction_list.html"
    template_detail = "disease_detection/admin_prediction_detail.html"

    def get(self, request, prediction_id=None, format=None):
        if not self.is_admin(request):
            return self.permission_denied_response(
                request,
                "Only admin can view disease prediction records."
            )

        try:
            if prediction_id:
                prediction = self.get_object(prediction_id)
                prediction_data = self.serialize_prediction(prediction)

                if self.is_html_request(request):
                    return self.render_html_detail_response(
                        request=request,
                        prediction=prediction,
                        message="Disease prediction detail retrieved successfully.",
                        success=True,
                        http_status=status.HTTP_200_OK,
                    )

                return self.success_response(
                    message="Disease prediction detail retrieved successfully.",
                    data=prediction_data,
                    http_status=status.HTTP_200_OK,
                )

            form = PredictionSearchForm(request.GET or None)
            predictions = self.get_list_queryset()

            if form.is_valid():
                search = form.cleaned_data.get("search")
                crop = form.cleaned_data.get("crop")
                status_filter = form.cleaned_data.get("status")

                if search:
                    predictions = predictions.filter(
                        Q(user__username__icontains=search)
                        | Q(user__email__icontains=search)
                        | Q(crop_name__icontains=search)
                        | Q(disease_name__icontains=search)
                        | Q(class_name__icontains=search)
                    )

                if crop:
                    predictions = predictions.filter(crop_name__icontains=crop)

                if status_filter:
                    predictions = predictions.filter(status=status_filter)

            predictions_data = self.serialize_predictions(predictions)

            if self.is_html_request(request):
                return self.render_html_list_response(
                    request=request,
                    predictions=predictions,
                    form=form,
                    message="Disease prediction list retrieved successfully.",
                    success=True,
                    http_status=status.HTTP_200_OK,
                )

            return self.success_response(
                message="Disease prediction list retrieved successfully.",
                data=predictions_data,
                http_status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.exception("Error fetching disease prediction data")

            if self.is_html_request(request):
                if prediction_id:
                    return self.render_html_detail_response(
                        request=request,
                        prediction=None,
                        message="Error fetching disease prediction detail.",
                        errors={"detail": [str(e)]},
                        success=False,
                        http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

                return self.render_html_list_response(
                    request=request,
                    predictions=[],
                    form=PredictionSearchForm(),
                    message="Error fetching disease prediction list.",
                    errors={"detail": [str(e)]},
                    success=False,
                    http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            return self.error_response(
                message="Error fetching disease prediction data.",
                errors={"detail": [str(e)]},
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )