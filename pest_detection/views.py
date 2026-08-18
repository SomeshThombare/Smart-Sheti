# pest_detection/views.py

import csv
import json
import logging
from datetime import datetime

from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from .ai_model.predict_pest import predict_pest
from .ai_model.solution import get_pest_solution
from .forms import PestPredictionSearchForm, PestUploadForm
from .models import PestPrediction


logger = logging.getLogger(__name__)

ROLE_ADMIN = "admin"
ROLE_FARMER = "farmer"

STATUS_SUCCESS = "SUCCESS"
STATUS_FAILED = "FAILED"


class BasePestAPIView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    permission_classes = [IsAuthenticated]

    template_list = None
    template_form = None
    template_detail = None

    def log_json_response(self, level, payload):
        try:
            pretty_json = json.dumps(payload, indent=4, ensure_ascii=False, default=str)
        except Exception:
            pretty_json = str(payload)

        if level == "error":
            logger.error("\n%s", pretty_json)
        elif level == "warning":
            logger.warning("\n%s", pretty_json)
        else:
            logger.info("\n%s", pretty_json)

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

    def model_has_field(self, field_name):
        try:
            PestPrediction._meta.get_field(field_name)
            return True
        except Exception:
            return False

    def set_optional_field(self, obj, field_name, value):
        if self.model_has_field(field_name):
            setattr(obj, field_name, value)

    def safe_int(self, value, default=None):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def safe_float(self, value, default=None):
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def get_all_queryset(self):
        return PestPrediction.objects.select_related("user").order_by("-created_at")

    def get_farmer_queryset(self, request):
        return PestPrediction.objects.filter(user=request.user).order_by("-created_at")

    def get_object(self, prediction_id):
        return get_object_or_404(PestPrediction, id=prediction_id)

    def calculate_success_rate(self, total_count, success_count):
        if total_count <= 0:
            return 0
        return round((success_count / total_count) * 100, 2)

    def get_severity(self, confidence):
        confidence = self.safe_float(confidence, 0)

        if confidence >= 90:
            return "HIGH"

        if confidence >= 70:
            return "MEDIUM"

        if confidence >= 60:
            return "LOW"

        return "UNCLEAR"

    def get_treatment_priority(self, confidence):
        confidence = self.safe_float(confidence, 0)

        if confidence >= 90:
            return "Immediate Action Required"

        if confidence >= 70:
            return "Treat Within 3 Days"

        if confidence >= 60:
            return "Monitor Closely"

        return "Upload Clear Image Again"

    def normalize_prediction_status(self, result):
        result_status = str(result.get("status", "")).lower()
        success_value = result.get("success")

        if success_value is True or result_status == "success":
            return STATUS_SUCCESS

        return STATUS_FAILED

    def build_prediction_result(self, result):
        pest_name = result.get("pest_name") or "Unknown"
        confidence = result.get("confidence") or 0
        class_name = result.get("class_name") or pest_name
        predicted_index = self.safe_int(result.get("predicted_index"), default=None)
        top_predictions = result.get("top_predictions", [])

        prediction_status = self.normalize_prediction_status(result)
        message = result.get("message") or ""

        if prediction_status == STATUS_SUCCESS:
            solution = get_pest_solution(pest_name)
            error_message = ""
            success = True
        else:
            solution = (
                result.get("solution")
                or message
                or "No solution available. Please upload a clear pest image and try again."
            )
            error_message = message
            success = False

        severity = self.get_severity(confidence)
        treatment_priority = self.get_treatment_priority(confidence)

        clean_result = {
            "success": success,
            "status": result.get("status", prediction_status.lower()),
            "pest_name": pest_name,
            "confidence": confidence,
            "class_name": class_name,
            "predicted_index": predicted_index,
            "solution": solution,
            "message": message,
            "top_predictions": top_predictions,
            "severity": severity,
            "treatment_priority": treatment_priority,
        }

        return {
            "pest_name": pest_name,
            "confidence": confidence,
            "class_name": class_name,
            "predicted_index": predicted_index,
            "solution": solution,
            "status": prediction_status,
            "error_message": error_message,
            "top_predictions": top_predictions,
            "severity": severity,
            "treatment_priority": treatment_priority,
            "result": clean_result,
            "success": success,
        }

    def serialize_prediction(self, prediction):
        data = {
            "id": prediction.id,
            "user": str(prediction.user) if prediction.user else "",
            "image": prediction.image.url if prediction.image else "",
            "pest_name": prediction.pest_name,
            "confidence": prediction.confidence,
            "solution": prediction.solution,
            "class_name": prediction.class_name,
            "predicted_index": prediction.predicted_index,
            "status": prediction.status,
            "error_message": prediction.error_message,
            "created_at": prediction.created_at,
        }

        for optional_field in [
            "top_predictions",
            "severity",
            "treatment_priority",
            "district",
            "city",
            "state",
        ]:
            if self.model_has_field(optional_field):
                data[optional_field] = getattr(prediction, optional_field, None)

        return data

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

    def apply_prediction_filters(self, request, queryset):
        search = request.GET.get("search", "").strip()
        status_filter = request.GET.get("status", "").strip()
        pest_name = request.GET.get("pest_name", "").strip()
        date_from = request.GET.get("date_from", "").strip()
        date_to = request.GET.get("date_to", "").strip()
        min_confidence = request.GET.get("min_confidence", "").strip()
        max_confidence = request.GET.get("max_confidence", "").strip()

        if search:
            queryset = queryset.filter(
                Q(user__username__icontains=search)
                | Q(user__email__icontains=search)
                | Q(user__first_name__icontains=search)
                | Q(user__last_name__icontains=search)
                | Q(pest_name__icontains=search)
                | Q(class_name__icontains=search)
            )

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        if pest_name:
            queryset = queryset.filter(pest_name__icontains=pest_name)

        if date_from:
            try:
                parsed_date_from = datetime.strptime(date_from, "%Y-%m-%d").date()
                queryset = queryset.filter(created_at__date__gte=parsed_date_from)
            except ValueError:
                pass

        if date_to:
            try:
                parsed_date_to = datetime.strptime(date_to, "%Y-%m-%d").date()
                queryset = queryset.filter(created_at__date__lte=parsed_date_to)
            except ValueError:
                pass

        min_conf = self.safe_float(min_confidence)
        if min_conf is not None:
            queryset = queryset.filter(confidence__gte=min_conf)

        max_conf = self.safe_float(max_confidence)
        if max_conf is not None:
            queryset = queryset.filter(confidence__lte=max_conf)

        return queryset

    def apply_sorting(self, request, queryset):
        sort = request.GET.get("sort", "-created_at")

        allowed_sort_fields = {
            "date": "created_at",
            "-date": "-created_at",
            "confidence": "confidence",
            "-confidence": "-confidence",
            "pest_name": "pest_name",
            "-pest_name": "-pest_name",
            "status": "status",
            "-status": "-status",
        }

        return queryset.order_by(allowed_sort_fields.get(sort, "-created_at"))

    def paginate_queryset(self, request, queryset, per_page=10):
        page_size = self.safe_int(request.GET.get("page_size"), default=per_page)

        if page_size is None or page_size <= 0:
            page_size = per_page

        if page_size > 100:
            page_size = 100

        paginator = Paginator(queryset, page_size)
        page_number = request.GET.get("page")
        return paginator.get_page(page_number)

    def get_top_pests(self, queryset, limit=5):
        return (
            queryset.exclude(pest_name__isnull=True)
            .exclude(pest_name__exact="")
            .values("pest_name")
            .annotate(total=Count("id"))
            .order_by("-total")[:limit]
        )

    def get_top_farmers(self, queryset, limit=10):
        return (
            queryset.exclude(user__isnull=True)
            .values(
                "user__id",
                "user__username",
                "user__first_name",
                "user__last_name",
                "user__email",
            )
            .annotate(total=Count("id"))
            .order_by("-total")[:limit]
        )

    def get_monthly_trend(self, queryset):
        return (
            queryset.annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(total=Count("id"))
            .order_by("month")
        )

    def get_district_report(self, queryset):
        if not self.model_has_field("district"):
            return []

        return (
            queryset.exclude(district__isnull=True)
            .exclude(district__exact="")
            .values("district")
            .annotate(total=Count("id"))
            .order_by("-total")
        )

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
        if self.is_html_request(request):
            return Response(
                self.base_context(
                    request,
                    message=message,
                    errors={"detail": [message]},
                    success=False,
                ),
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
        page_obj=None,
        paginator=None,
        message="",
        errors=None,
        success=False,
        http_status=status.HTTP_200_OK,
        **extra,
    ):
        return Response(
            self.base_context(
                request,
                predictions=predictions or [],
                form=form,
                page_obj=page_obj,
                paginator=paginator,
                message=message,
                errors=errors or {},
                success=success,
                **extra,
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


class FarmerPestDashboardAPIView(BasePestAPIView):
    template_list = "pest_detection/farmer_dashboard.html"

    def get(self, request, format=None):
        if not self.is_farmer(request):
            return self.permission_denied_response(
                request,
                "Only farmer can access pest dashboard."
            )

        try:
            farmer_predictions = self.get_farmer_queryset(request)

            total_predictions = farmer_predictions.count()
            success_count = farmer_predictions.filter(status=STATUS_SUCCESS).count()
            failed_count = farmer_predictions.filter(status=STATUS_FAILED).count()
            today_predictions = farmer_predictions.filter(
                created_at__date=timezone.localdate()
            ).count()
            monthly_predictions = farmer_predictions.filter(
                created_at__year=timezone.now().year,
                created_at__month=timezone.now().month,
            ).count()

            success_rate = self.calculate_success_rate(total_predictions, success_count)
            recent_predictions = farmer_predictions[:10]
            last_prediction = farmer_predictions.first()
            last_success_prediction = farmer_predictions.filter(status=STATUS_SUCCESS).first()
            most_detected_pest = self.get_top_pests(farmer_predictions, limit=1)
            top_pests = self.get_top_pests(farmer_predictions, limit=5)
            monthly_trend = self.get_monthly_trend(farmer_predictions)

            most_detected_pest = most_detected_pest[0] if most_detected_pest else None

            dashboard_data = {
                "total_predictions": total_predictions,
                "success_count": success_count,
                "failed_count": failed_count,
                "today_predictions": today_predictions,
                "monthly_predictions": monthly_predictions,
                "success_rate": success_rate,
                "last_prediction": self.serialize_prediction(last_prediction)
                if last_prediction else None,
                "last_success_prediction": self.serialize_prediction(last_success_prediction)
                if last_success_prediction else None,
                "most_detected_pest": most_detected_pest,
                "top_pests": list(top_pests),
                "monthly_trend": list(monthly_trend),
                "recent_predictions": self.serialize_predictions(recent_predictions),
            }

            if self.is_html_request(request):
                return Response(
                    self.base_context(
                        request,
                        total_predictions=total_predictions,
                        success_count=success_count,
                        failed_count=failed_count,
                        today_predictions=today_predictions,
                        monthly_predictions=monthly_predictions,
                        success_rate=success_rate,
                        recent_predictions=recent_predictions,
                        last_prediction=last_prediction,
                        last_success_prediction=last_success_prediction,
                        most_detected_pest=most_detected_pest,
                        top_pests=top_pests,
                        monthly_trend=monthly_trend,
                        message="Farmer pest dashboard retrieved successfully.",
                        success=True,
                    ),
                    template_name=self.template_list,
                    status=status.HTTP_200_OK,
                )

            return self.success_response(
                message="Farmer pest dashboard retrieved successfully.",
                data=dashboard_data,
                http_status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.exception("Error fetching farmer pest dashboard")

            if self.is_html_request(request):
                return Response(
                    self.base_context(
                        request,
                        total_predictions=0,
                        success_count=0,
                        failed_count=0,
                        today_predictions=0,
                        monthly_predictions=0,
                        success_rate=0,
                        recent_predictions=[],
                        last_prediction=None,
                        last_success_prediction=None,
                        most_detected_pest=None,
                        top_pests=[],
                        monthly_trend=[],
                        message="Error fetching farmer pest dashboard.",
                        errors={"detail": [str(e)]},
                        success=False,
                    ),
                    template_name=self.template_list,
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            return self.error_response(
                message="Error fetching farmer pest dashboard.",
                errors={"detail": [str(e)]},
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class FarmerPestDetectionAPIView(BasePestAPIView):
    template_form = "pest_detection/farmer_detect.html"

    def get(self, request, format=None):
        if not self.is_farmer(request):
            return self.permission_denied_response(
                request,
                "Only farmer can access pest detection page."
            )

        form = PestUploadForm()

        if self.is_html_request(request):
            return self.render_html_form_response(
                request=request,
                form=form,
                result=None,
                prediction_obj=None,
                message="Pest detection page loaded successfully.",
                success=True,
                http_status=status.HTTP_200_OK,
            )

        return self.success_response(
            message="Pest detection page loaded successfully.",
            data={},
            http_status=status.HTTP_200_OK,
        )

    def post(self, request, format=None):
        if not self.is_farmer(request):
            return self.permission_denied_response(
                request,
                "Only farmer can upload pest images."
            )

        try:
            form = PestUploadForm(request.POST, request.FILES)

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

            prediction_obj = PestPrediction.objects.create(
                user=request.user,
                image=uploaded_image,
                pest_name="Processing",
                confidence=0,
                solution="Processing",
                class_name="Processing",
                predicted_index=None,
                status=STATUS_SUCCESS,
                error_message="",
            )

            try:
                raw_result = predict_pest(prediction_obj.image.path)
                prepared = self.build_prediction_result(raw_result)

                prediction_obj.pest_name = prepared["pest_name"]
                prediction_obj.confidence = prepared["confidence"]
                prediction_obj.solution = prepared["solution"]
                prediction_obj.class_name = prepared["class_name"]
                prediction_obj.predicted_index = prepared["predicted_index"]
                prediction_obj.status = prepared["status"]
                prediction_obj.error_message = prepared["error_message"]

                self.set_optional_field(
                    prediction_obj,
                    "top_predictions",
                    prepared["top_predictions"],
                )
                self.set_optional_field(
                    prediction_obj,
                    "severity",
                    prepared["severity"],
                )
                self.set_optional_field(
                    prediction_obj,
                    "treatment_priority",
                    prepared["treatment_priority"],
                )

                prediction_obj.save()

                response_data = {
                    "prediction": self.serialize_prediction(prediction_obj),
                    "result": prepared["result"],
                }

                if self.is_html_request(request):
                    return self.render_html_form_response(
                        request=request,
                        form=PestUploadForm(),
                        result=prepared["result"],
                        prediction_obj=prediction_obj,
                        message=prepared["result"].get("message")
                        or "Pest detection completed successfully.",
                        success=prepared["success"],
                        http_status=status.HTTP_200_OK,
                    )

                if prepared["success"]:
                    return self.success_response(
                        message="Pest detection completed successfully.",
                        data=response_data,
                        http_status=status.HTTP_201_CREATED,
                    )

                return self.error_response(
                    message=prepared["result"].get("message") or "Pest detection failed.",
                    errors={"detail": [prepared["error_message"]]},
                    http_status=status.HTTP_400_BAD_REQUEST,
                )

            except Exception as e:
                logger.exception("Pest prediction failed")

                prediction_obj.pest_name = "Prediction Failed"
                prediction_obj.confidence = 0
                prediction_obj.solution = (
                    "No solution available. Please upload a clear pest image and try again."
                )
                prediction_obj.class_name = "Prediction Failed"
                prediction_obj.predicted_index = None
                prediction_obj.status = STATUS_FAILED
                prediction_obj.error_message = str(e)

                self.set_optional_field(prediction_obj, "severity", "UNCLEAR")
                self.set_optional_field(
                    prediction_obj,
                    "treatment_priority",
                    "Upload Clear Image Again",
                )
                self.set_optional_field(prediction_obj, "top_predictions", [])

                prediction_obj.save()

                result = {
                    "success": False,
                    "status": "error",
                    "pest_name": "Prediction Failed",
                    "confidence": 0,
                    "class_name": "Prediction Failed",
                    "predicted_index": None,
                    "solution": prediction_obj.solution,
                    "message": str(e),
                    "error": str(e),
                    "top_predictions": [],
                    "severity": "UNCLEAR",
                    "treatment_priority": "Upload Clear Image Again",
                }

                if self.is_html_request(request):
                    return self.render_html_form_response(
                        request=request,
                        form=PestUploadForm(),
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
            logger.exception("Error processing pest detection request")

            if self.is_html_request(request):
                return self.render_html_form_response(
                    request=request,
                    form=PestUploadForm(),
                    result=None,
                    prediction_obj=None,
                    message="Error processing pest detection request.",
                    errors={"detail": [str(e)]},
                    success=False,
                    http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            return self.error_response(
                message="Error processing pest detection request.",
                errors={"detail": [str(e)]},
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class FarmerPestHistoryAPIView(BasePestAPIView):
    template_list = "pest_detection/farmer_history.html"

    def get(self, request, format=None):
        if not self.is_farmer(request):
            return self.permission_denied_response(
                request,
                "Only farmer can view farmer pest history."
            )

        try:
            predictions = self.get_farmer_queryset(request)
            predictions = self.apply_prediction_filters(request, predictions)
            predictions = self.apply_sorting(request, predictions)

            page_obj = self.paginate_queryset(request, predictions, per_page=10)

            if self.is_html_request(request):
                return self.render_html_list_response(
                    request=request,
                    predictions=page_obj,
                    page_obj=page_obj,
                    paginator=page_obj.paginator,
                    message="Farmer pest history retrieved successfully.",
                    success=True,
                    http_status=status.HTTP_200_OK,
                )

            return self.success_response(
                message="Farmer pest history retrieved successfully.",
                data={
                    "count": page_obj.paginator.count,
                    "page": page_obj.number,
                    "total_pages": page_obj.paginator.num_pages,
                    "results": self.serialize_predictions(page_obj.object_list),
                },
                http_status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.exception("Error fetching farmer pest history")

            if self.is_html_request(request):
                return self.render_html_list_response(
                    request=request,
                    predictions=[],
                    message="Error fetching farmer pest history.",
                    errors={"detail": [str(e)]},
                    success=False,
                    http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            return self.error_response(
                message="Error fetching farmer pest history.",
                errors={"detail": [str(e)]},
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AdminPestDashboardAPIView(BasePestAPIView):
    template_list = "pest_detection/admin_dashboard.html"

    def get(self, request, format=None):
        if not self.is_admin(request):
            return self.permission_denied_response(
                request,
                "Only admin can access pest dashboard."
            )

        try:
            all_predictions = self.get_all_queryset()

            total_predictions = all_predictions.count()
            success_count = all_predictions.filter(status=STATUS_SUCCESS).count()
            failed_count = all_predictions.filter(status=STATUS_FAILED).count()
            today_predictions = all_predictions.filter(
                created_at__date=timezone.localdate()
            ).count()
            monthly_predictions = all_predictions.filter(
                created_at__year=timezone.now().year,
                created_at__month=timezone.now().month,
            ).count()

            success_rate = self.calculate_success_rate(total_predictions, success_count)
            recent_predictions = all_predictions[:10]

            top_pests = self.get_top_pests(all_predictions, limit=5)
            top_farmers = self.get_top_farmers(all_predictions, limit=10)
            monthly_trend = self.get_monthly_trend(all_predictions)
            district_report = self.get_district_report(all_predictions)

            most_detected_pest = top_pests[0] if top_pests else None

            dashboard_data = {
                "total_predictions": total_predictions,
                "success_count": success_count,
                "failed_count": failed_count,
                "today_predictions": today_predictions,
                "monthly_predictions": monthly_predictions,
                "success_rate": success_rate,
                "most_detected_pest": most_detected_pest,
                "top_pests": list(top_pests),
                "top_farmers": list(top_farmers),
                "monthly_trend": list(monthly_trend),
                "district_report": list(district_report),
                "recent_predictions": self.serialize_predictions(recent_predictions),
            }

            if self.is_html_request(request):
                return Response(
                    self.base_context(
                        request,
                        total_predictions=total_predictions,
                        success_count=success_count,
                        failed_count=failed_count,
                        today_predictions=today_predictions,
                        monthly_predictions=monthly_predictions,
                        success_rate=success_rate,
                        most_detected_pest=most_detected_pest,
                        top_pests=top_pests,
                        top_farmers=top_farmers,
                        monthly_trend=monthly_trend,
                        district_report=district_report,
                        recent_predictions=recent_predictions,
                        message="Pest dashboard retrieved successfully.",
                        success=True,
                    ),
                    template_name=self.template_list,
                    status=status.HTTP_200_OK,
                )

            return self.success_response(
                message="Pest dashboard retrieved successfully.",
                data=dashboard_data,
                http_status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.exception("Error fetching pest dashboard")

            if self.is_html_request(request):
                return Response(
                    self.base_context(
                        request,
                        total_predictions=0,
                        success_count=0,
                        failed_count=0,
                        today_predictions=0,
                        monthly_predictions=0,
                        success_rate=0,
                        most_detected_pest=None,
                        top_pests=[],
                        top_farmers=[],
                        monthly_trend=[],
                        district_report=[],
                        recent_predictions=[],
                        message="Error fetching pest dashboard.",
                        errors={"detail": [str(e)]},
                        success=False,
                    ),
                    template_name=self.template_list,
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            return self.error_response(
                message="Error fetching pest dashboard.",
                errors={"detail": [str(e)]},
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AdminPestPredictionAPIView(BasePestAPIView):
    template_list = "pest_detection/admin_prediction_list.html"
    template_detail = "pest_detection/admin_prediction_detail.html"

    def get(self, request, prediction_id=None, format=None):
        if not self.is_admin(request):
            return self.permission_denied_response(
                request,
                "Only admin can view pest prediction records."
            )

        try:
            if prediction_id:
                prediction = self.get_object(prediction_id)
                prediction_data = self.serialize_prediction(prediction)

                if self.is_html_request(request):
                    return self.render_html_detail_response(
                        request=request,
                        prediction=prediction,
                        message="Pest prediction detail retrieved successfully.",
                        success=True,
                        http_status=status.HTTP_200_OK,
                    )

                return self.success_response(
                    message="Pest prediction detail retrieved successfully.",
                    data=prediction_data,
                    http_status=status.HTTP_200_OK,
                )

            form = PestPredictionSearchForm(request.GET or None)
            predictions = self.get_all_queryset()
            predictions = self.apply_prediction_filters(request, predictions)
            predictions = self.apply_sorting(request, predictions)

            page_obj = self.paginate_queryset(request, predictions, per_page=10)

            if self.is_html_request(request):
                return self.render_html_list_response(
                    request=request,
                    predictions=page_obj,
                    form=form,
                    page_obj=page_obj,
                    paginator=page_obj.paginator,
                    message="Pest prediction list retrieved successfully.",
                    success=True,
                    http_status=status.HTTP_200_OK,
                )

            return self.success_response(
                message="Pest prediction list retrieved successfully.",
                data={
                    "count": page_obj.paginator.count,
                    "page": page_obj.number,
                    "total_pages": page_obj.paginator.num_pages,
                    "results": self.serialize_predictions(page_obj.object_list),
                },
                http_status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.exception("Error fetching pest prediction data")

            if self.is_html_request(request):
                if prediction_id:
                    return self.render_html_detail_response(
                        request=request,
                        prediction=None,
                        message="Error fetching pest prediction detail.",
                        errors={"detail": [str(e)]},
                        success=False,
                        http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

                return self.render_html_list_response(
                    request=request,
                    predictions=[],
                    form=PestPredictionSearchForm(),
                    message="Error fetching pest prediction list.",
                    errors={"detail": [str(e)]},
                    success=False,
                    http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            return self.error_response(
                message="Error fetching pest prediction data.",
                errors={"detail": [str(e)]},
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AdminPestPredictionExportCSVAPIView(BasePestAPIView):
    def get(self, request, format=None):
        if not self.is_admin(request):
            return self.permission_denied_response(
                request,
                "Only admin can export pest prediction records."
            )

        predictions = self.get_all_queryset()
        predictions = self.apply_prediction_filters(request, predictions)
        predictions = self.apply_sorting(request, predictions)

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="pest_predictions.csv"'

        writer = csv.writer(response)
        writer.writerow([
            "SR No",
            "Prediction ID",
            "Farmer",
            "Email",
            "Pest Name",
            "Confidence",
            "Class Name",
            "Predicted Index",
            "Status",
            "Created Date",
        ])

        for index, prediction in enumerate(predictions, start=1):
            user = prediction.user
            writer.writerow([
                index,
                prediction.id,
                user.get_full_name() if user else "",
                user.email if user else "",
                prediction.pest_name,
                prediction.confidence,
                prediction.class_name,
                prediction.predicted_index,
                prediction.status,
                prediction.created_at.strftime("%d-%m-%Y %I:%M %p")
                if prediction.created_at else "",
            ])

        return response