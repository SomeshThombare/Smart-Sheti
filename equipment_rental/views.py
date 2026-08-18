import json
import logging
from django.conf import settings

from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone

from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from .forms import EquipmentBookingForm, EquipmentForm
from .models import Equipment, EquipmentBooking
from .serializers import (
    EquipmentBookingSerializer,
    EquipmentSerializer,
    RazorpayPaymentVerifySerializer,
)

from .services import (
    EquipmentBookingPaymentService,
    EquipmentBookingStatusService,
    EquipmentAvailabilityService,
    PendingBookingAutoCancelService,
)

from .permissions import ROLE_ADMIN, ROLE_FARMER

logger = logging.getLogger(__name__)


class RolePermissionMixin:
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


class BaseResponseMixin:
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

    def normalize_form_errors(self, form):
        try:
            return {
                field: [str(error) for error in errors]
                for field, errors in form.errors.items()
            }
        except Exception:
            return {"detail": ["Validation failed."]}

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
                template_name=self.template_list or self.template_form,
                status=status.HTTP_403_FORBIDDEN,
            )

        return self.error_response(
            message=message,
            errors={"detail": [message]},
            http_status=status.HTTP_403_FORBIDDEN,
        )


class BaseEquipmentAPIView(RolePermissionMixin, BaseResponseMixin, APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    permission_classes = [IsAuthenticated]

    template_list = None
    template_form = None

    def normalize_equipment_code(self, equipment_code):
        return str(equipment_code).strip().upper()

    def get_object(self, equipment_code):
        return get_object_or_404(
            Equipment,
            equipment_code=self.normalize_equipment_code(equipment_code),
        )

    def get_queryset(self):
        return Equipment.objects.all().order_by("-id")

    def get_active_queryset(self):
        return Equipment.objects.filter(
            is_active=True,
            approval_status=Equipment.EquipmentApprovalStatusChoices.APPROVED,
        ).exclude(
            equipment_status=Equipment.EquipmentStatusChoices.MAINTENANCE
        ).order_by("-id")

    def serialize_equipment(self, equipment, request):
        return EquipmentSerializer(equipment, context={"request": request}).data

    def serialize_equipments(self, queryset, request):
        return EquipmentSerializer(queryset, many=True, context={"request": request}).data

    def get_form_data(self, request):
        if request.FILES:
            data = request.POST.copy()
        else:
            data = request.data.copy() if hasattr(request.data, "copy") else dict(request.data)

        if data.get("equipment_code"):
            data["equipment_code"] = self.normalize_equipment_code(data.get("equipment_code"))

        return data

    def build_form(self, request, instance=None, data=None):
        if data is None:
            data = self.get_form_data(request)

        return EquipmentForm(
            data=data or None,
            files=request.FILES or None,
            instance=instance,
            user=request.user,
        )

    def render_html_form_response(
        self,
        request,
        form,
        equipment=None,
        message="",
        errors=None,
        success=False,
        http_status=status.HTTP_200_OK,
    ):
        return Response(
            self.base_context(
                request,
                form=form,
                equipment=equipment,
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
        equipments=None,
        message="",
        errors=None,
        success=False,
        http_status=status.HTTP_200_OK,
    ):
        return Response(
            self.base_context(
                request,
                equipments=equipments or [],
                message=message,
                errors=errors or {},
                success=success,
            ),
            template_name=self.template_list,
            status=http_status,
        )


class AdminEquipmentAPIView(BaseEquipmentAPIView):
    template_list = "equipment/admin_equipment_list.html"
    template_form = "equipment/admin_equipment_form.html"

    def get(self, request, equipment_code=None, format=None):
        if not self.is_admin(request):
            return self.permission_denied_response(
                request,
                "Only admin can access admin equipment pages.",
            )

        EquipmentBookingStatusService.auto_complete_expired_bookings(
            user=request.user
        )

        if equipment_code:
            equipment = self.get_object(equipment_code)

            if self.is_html_request(request):
                return self.render_html_form_response(
                    request=request,
                    form=EquipmentForm(instance=equipment, user=request.user),
                    equipment=equipment,
                    message="Equipment retrieved successfully.",
                    success=True,
                )

            return self.success_response(
                message="Equipment retrieved successfully.",
                data=self.serialize_equipment(equipment, request),
            )

        base_queryset = Equipment.objects.all()

        total_count = base_queryset.count()
        available_count = base_queryset.filter(
            equipment_status=Equipment.EquipmentStatusChoices.AVAILABLE
        ).count()
        rented_count = base_queryset.filter(
            equipment_status=Equipment.EquipmentStatusChoices.RENTED
        ).count()
        maintenance_count = base_queryset.filter(
            equipment_status=Equipment.EquipmentStatusChoices.MAINTENANCE
        ).count()

        queryset = self.get_queryset()

        search = request.GET.get("search", "").strip()
        status_filter = request.GET.get("status", "").strip()
        category_filter = request.GET.get("category", "").strip()

        category_options = (
            Equipment.objects
            .exclude(equipment_category__isnull=True)
            .exclude(equipment_category__exact="")
            .values_list("equipment_category", flat=True)
            .distinct()
            .order_by("equipment_category")
        )

        if search:
            queryset = queryset.filter(
                Q(equipment_code__icontains=search)
                | Q(equipment_name__icontains=search)
                | Q(equipment_category__icontains=search)
                | Q(equipment_brand__icontains=search)
                | Q(owner_name__icontains=search)
                | Q(equipment_identity_number__icontains=search)
                | Q(location_city__icontains=search)
            )

        if status_filter:
            queryset = queryset.filter(equipment_status=status_filter)

        if category_filter:
            queryset = queryset.filter(equipment_category=category_filter)

        if self.is_html_request(request):
            return Response(
                self.base_context(
                    request,
                    equipments=queryset,
                    category_options=category_options,
                    selected_search=search,
                    selected_status=status_filter,
                    selected_category=category_filter,
                    total_count=total_count,
                    available_count=available_count,
                    rented_count=rented_count,
                    maintenance_count=maintenance_count,
                    message="Equipment list retrieved successfully.",
                    success=True,
                ),
                template_name=self.template_list,
                status=status.HTTP_200_OK,
            )

        return self.success_response(
            message="Equipment list retrieved successfully.",
            data=self.serialize_equipments(queryset, request),
        )

    @transaction.atomic
    def post(self, request, equipment_code=None, format=None):
        if not self.is_admin(request):
            return self.permission_denied_response(
                request,
                "Only admin can create or update equipment.",
            )

        if request.POST.get("_method") == "DELETE" and equipment_code:
            return self.delete(request, equipment_code, format)

        if equipment_code:
            if self.is_html_request(request):
                messages.error(
                    request,
                    "Equipment update is disabled. You can only view equipment details.",
                )
                return redirect("equipment:admin-equipment-list")

            return self.error_response(
                "Equipment update is disabled.",
                {"detail": ["Admin can only view equipment details."]},
                status.HTTP_403_FORBIDDEN,
            )

        form = self.build_form(request)

        if not form.is_valid():
            errors = self.normalize_form_errors(form)

            if self.is_html_request(request):
                return self.render_html_form_response(
                    request=request,
                    form=form,
                    errors=errors,
                    message="Equipment validation failed.",
                    http_status=status.HTTP_400_BAD_REQUEST,
                )

            return self.error_response("Equipment validation failed.", errors)

        equipment = form.save()

        # Admin create equipment -> always available
        # Maintenance only admin can set during update.
        equipment.equipment_status = Equipment.EquipmentStatusChoices.AVAILABLE
        equipment.set_user_context(request.user)
        equipment.save(
            update_fields=[
                "equipment_status",
                "updated_by_user",
                "updated_at",
            ]
        )

        if self.is_html_request(request):
            return self.render_html_form_response(
                request=request,
                form=EquipmentForm(instance=equipment, user=request.user),
                equipment=equipment,
                message="Equipment created successfully.",
                success=True,
                http_status=status.HTTP_201_CREATED,
            )

        return self.success_response(
            message="Equipment created successfully.",
            data=self.serialize_equipment(equipment, request),
            http_status=status.HTTP_201_CREATED,
        )

    def put(self, request, equipment_code=None, format=None):
        return self.error_response(
            "Equipment update is disabled.",
            {"detail": ["Admin can only view equipment details."]},
            status.HTTP_403_FORBIDDEN,
        )

    def patch(self, request, equipment_code=None, format=None):
        return self.error_response(
            "Equipment update is disabled.",
            {"detail": ["Admin can only view equipment details."]},
            status.HTTP_403_FORBIDDEN,
        )

    def _update(self, request, equipment_code, partial=False):
        if not self.is_admin(request):
            return self.permission_denied_response(
                request,
                "Only admin can update equipment.",
            )

        equipment = self.get_object(equipment_code)
        old_status = equipment.equipment_status

        data = self.get_form_data(request)
        data["equipment_code"] = equipment.equipment_code

        if partial:
            form_fields = EquipmentForm(
                instance=equipment,
                user=request.user,
            ).fields

            for field_name in form_fields:
                if field_name not in data:
                    current_value = getattr(equipment, field_name, None)

                    if current_value is not None:
                        data[field_name] = current_value

        form = self.build_form(request, instance=equipment, data=data)

        if not form.is_valid():
            errors = self.normalize_form_errors(form)

            if self.is_html_request(request):
                return self.render_html_form_response(
                    request=request,
                    form=form,
                    equipment=equipment,
                    message="Equipment update validation failed.",
                    errors=errors,
                    http_status=status.HTTP_400_BAD_REQUEST,
                )

            return self.error_response(
                "Equipment update validation failed.",
                errors,
            )

        equipment = form.save()

        # If admin manually sets maintenance, keep maintenance.
        if equipment.equipment_status == Equipment.EquipmentStatusChoices.MAINTENANCE:
            equipment.set_user_context(request.user)
            equipment.save(
                update_fields=[
                    "equipment_status",
                    "updated_by_user",
                    "updated_at",
                ]
            )
        else:
            # If not maintenance, status should be calculated from paid confirmed bookings.
            EquipmentBookingStatusService.update_equipment_status(
                equipment=equipment,
                user=request.user,
            )

        if self.is_html_request(request):
            return self.render_html_form_response(
                request=request,
                form=EquipmentForm(instance=equipment, user=request.user),
                equipment=equipment,
                message="Equipment updated successfully.",
                success=True,
            )

        return self.success_response(
            message="Equipment updated successfully.",
            data=self.serialize_equipment(equipment, request),
        )

    @transaction.atomic
    def delete(self, request, equipment_code=None, format=None):
        if not self.is_admin(request):
            return self.permission_denied_response(
                request,
                "Only admin can delete equipment.",
            )

        if not equipment_code:
            return self.error_response(
                "Equipment code is required for delete.",
                {"equipment_code": ["Equipment code is required."]},
            )

        equipment = self.get_object(equipment_code)

        if equipment.equipment_bookings.exists():
            equipment.is_active = False
            equipment.set_user_context(request.user)
            equipment.save(
                update_fields=[
                    "is_active",
                    "updated_by_user",
                    "updated_at",
                ]
            )

            if self.is_html_request(request):
                queryset = self.get_queryset()

                return self.render_html_list_response(
                    request=request,
                    equipments=queryset,
                    message="Equipment has bookings, so it was deactivated instead of deleted.",
                    success=True,
                )

            return self.success_response(
                "Equipment has bookings, so it was deactivated instead of deleted."
            )

        equipment.delete()

        if self.is_html_request(request):
            queryset = self.get_queryset()

            return self.render_html_list_response(
                request=request,
                equipments=queryset,
                message="Equipment deleted successfully.",
                success=True,
            )

        return self.success_response("Equipment deleted successfully.")




class AdminEquipmentFormPageView(BaseEquipmentAPIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_list = "equipment/admin_equipment_list.html"
    template_form = "equipment/admin_equipment_form.html"

    def get(self, request, format=None):
        if not self.is_admin(request):
            return self.permission_denied_response(
                request,
                "Only admin can access equipment form page.",
            )

        return self.render_html_form_response(
            request=request,
            form=EquipmentForm(user=request.user),
            message="Equipment form loaded successfully.",
            success=True,
        )



class FarmerEquipmentAPIView(BaseEquipmentAPIView):
    template_list = "equipment/farmer_equipment_list.html"
    template_form = "equipment/farmer_equipment_detail.html"

    def get(self, request, equipment_code=None, format=None):
        if not self.is_farmer(request):
            return self.permission_denied_response(
                request,
                "Only farmer can access farmer equipment pages.",
            )

        EquipmentBookingStatusService.auto_complete_expired_bookings(
            user=request.user
        )

        if equipment_code:
            equipment = self.get_object(equipment_code)

            if (
                not equipment.is_active
                or equipment.approval_status != Equipment.EquipmentApprovalStatusChoices.APPROVED
            ):
                return self.error_response(
                    "Equipment not available.",
                    {"detail": ["Only approved and active equipment is visible to farmers."]},
                    status.HTTP_404_NOT_FOUND,
                )

            availability = EquipmentAvailabilityService.get_availability(equipment)

            if self.is_html_request(request):
                return Response(
                    self.base_context(
                        request,
                        equipment=equipment,
                        availability=availability,
                        message="Equipment retrieved successfully.",
                        success=True,
                    ),
                    template_name=self.template_form,
                    status=status.HTTP_200_OK,
                )

            data = self.serialize_equipment(equipment, request)
            data["availability"] = availability

            return self.success_response(
                "Equipment retrieved successfully.",
                data,
            )

        queryset = self.get_active_queryset()

        search = request.GET.get("search", "").strip()

        if search:
            queryset = queryset.filter(
                Q(equipment_name__icontains=search)
                | Q(equipment_code__icontains=search)
                | Q(equipment_category__icontains=search)
                | Q(equipment_brand__icontains=search)
                | Q(location_city__icontains=search)
            )

        equipment_items = []

        for equipment in queryset:
            availability = EquipmentAvailabilityService.get_availability(equipment)
            equipment.availability = availability
            equipment.availability_status = availability["status"]
            equipment.availability_label = availability["label"]
            equipment.availability_message = availability["message"]
            equipment.is_bookable_now = availability["is_bookable"]
            equipment_items.append(equipment)

        category_options = (
            queryset.exclude(equipment_category__isnull=True)
            .exclude(equipment_category__exact="")
            .values_list("equipment_category", flat=True)
            .distinct()
            .order_by("equipment_category")
        )

        total_count = len(equipment_items)
        available_count = sum(
            1 for item in equipment_items
            if item.availability_status == "available"
        )
        rented_count = sum(
            1 for item in equipment_items
            if item.availability_status == "rented"
        )
        maintenance_count = sum(
            1 for item in equipment_items
            if item.availability_status == "maintenance"
        )

        if self.is_html_request(request):
            return Response(
                self.base_context(
                    request,
                    equipments=equipment_items,
                    category_options=category_options,
                    total_count=total_count,
                    available_count=available_count,
                    rented_count=rented_count,
                    maintenance_count=maintenance_count,
                    message="Equipment list retrieved successfully.",
                    success=True,
                ),
                template_name=self.template_list,
                status=status.HTTP_200_OK,
            )

        serializer_data = []

        for equipment in equipment_items:
            data = self.serialize_equipment(equipment, request)
            data["availability"] = equipment.availability
            serializer_data.append(data)

        return self.success_response(
            "Equipment list retrieved successfully.",
            serializer_data,
        )



class BaseEquipmentBookingAPIView(RolePermissionMixin, BaseResponseMixin, APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    permission_classes = [IsAuthenticated]

    template_list = None
    template_form = None

    ACTIVE_BOOKING_STATUSES = [
        EquipmentBooking.BookingStatusChoices.PENDING,
        EquipmentBooking.BookingStatusChoices.CONFIRMED,
    ]

    HISTORY_BOOKING_STATUSES = [
        EquipmentBooking.BookingStatusChoices.CANCELLED,
        EquipmentBooking.BookingStatusChoices.COMPLETED,
    ]

    def normalize_booking_code(self, booking_code):
        return str(booking_code).strip().upper()

    def get_queryset(self):
        return (
            EquipmentBooking.objects
            .select_related("equipment", "farmer_user")
            .all()
            .order_by("-id")
        )

    def get_farmer_queryset(self, request):
        return (
            EquipmentBooking.objects
            .select_related("equipment", "farmer_user")
            .filter(farmer_user=request.user)
            .order_by("-id")
        )

    def get_object_for_request(self, request, booking_code):
        booking_code = self.normalize_booking_code(booking_code)

        queryset = EquipmentBooking.objects.select_related("equipment", "farmer_user")

        if self.is_admin(request):
            return get_object_or_404(queryset, booking_code=booking_code)

        if self.is_farmer(request):
            return get_object_or_404(
                queryset,
                booking_code=booking_code,
                farmer_user=request.user,
            )

        raise Http404("Booking not found.")

    def get_farmer_current_queryset(self, request):
        return (
            EquipmentBooking.objects
            .select_related("equipment", "farmer_user")
            .filter(
                farmer_user=request.user,
                booking_status__in=self.ACTIVE_BOOKING_STATUSES,
            )
            .order_by("-id")
        )

    def get_farmer_history_queryset(self, request):
        return (
            EquipmentBooking.objects
            .select_related("equipment", "farmer_user")
            .filter(
                farmer_user=request.user,
                booking_status__in=self.HISTORY_BOOKING_STATUSES,
            )
            .order_by("-id")
        )

    def get_equipment_queryset_for_user(self, request):
        return Equipment.objects.filter(
            is_active=True,
            approval_status=Equipment.EquipmentApprovalStatusChoices.APPROVED,
        ).exclude(
            equipment_status=Equipment.EquipmentStatusChoices.MAINTENANCE
        ).order_by("-id")

    def serialize_booking(self, booking, request):
        return EquipmentBookingSerializer(booking, context={"request": request}).data

    def serialize_bookings(self, queryset, request):
        return EquipmentBookingSerializer(queryset, many=True, context={"request": request}).data

    def get_form_data(self, request):
        data = request.data.copy() if hasattr(request.data, "copy") else dict(request.data)

        if data.get("customer_full_name"):
            data["customer_full_name"] = str(data.get("customer_full_name")).strip().title()

        if data.get("customer_phone_number"):
            data["customer_phone_number"] = str(data.get("customer_phone_number")).strip()

        if data.get("customer_email_address"):
            data["customer_email_address"] = str(data.get("customer_email_address")).strip().lower()

        return data

    def build_form(self, request, instance=None, data=None, initial=None):
        if data is None:
            data = self.get_form_data(request)

        form = EquipmentBookingForm(
            data=data or None,
            instance=instance,
            initial=initial or None,
            user=request.user,
        )
        form.fields["equipment"].queryset = self.get_equipment_queryset_for_user(request)
        return form

    def auto_complete_expired_bookings(self, request=None):
        """
        Common booking status sync.
        1) Confirmed + paid bookings whose end date is over become completed.
        2) Pending + unpaid bookings older than 15 minutes become cancelled.

        This method is called from booking list/detail/form/payment views.
        """
        user = None

        if (
            request
            and hasattr(request, "user")
            and request.user.is_authenticated
        ):
            user = request.user

        completed_result = EquipmentBookingStatusService.auto_complete_expired_bookings(
            user=user
        )

        cancelled_count = PendingBookingAutoCancelService.auto_cancel_pending_payment_bookings(
            user=user
        )

        return {
            "completed_result": completed_result,
            "cancelled_pending_bookings": cancelled_count,
        }

    def render_html_form_response(
        self,
        request,
        form,
        booking=None,
        equipment=None,
        selected_equipment=None,
        message="",
        errors=None,
        success=False,
        http_status=status.HTTP_200_OK,
    ):
        # Keep both names available in templates:
        # old templates may use selected_equipment, new templates use equipment.
        if equipment is None:
            equipment = selected_equipment

        if equipment is None and booking is not None:
            equipment = getattr(booking, "equipment", None)

        return Response(
            self.base_context(
                request,
                form=form,
                booking=booking,
                equipment=equipment,
                selected_equipment=equipment,
                today=timezone.localdate(),
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
        bookings=None,
        message="",
        errors=None,
        success=False,
        http_status=status.HTTP_200_OK,
    ):
        return Response(
            self.base_context(
                request,
                bookings=bookings or [],
                message=message,
                errors=errors or {},
                success=success,
            ),
            template_name=self.template_list,
            status=http_status,
        )


class AdminEquipmentBookingAPIView(BaseEquipmentBookingAPIView):
    template_list = "equipment_booking/admin_booking_list.html"
    template_form = "equipment_booking/admin_booking_form.html"

    def get(self, request, booking_code=None, format=None):
        if not self.is_admin(request):
            return self.permission_denied_response(
                request,
                "Only admin can access admin equipment booking pages.",
            )

        self.auto_complete_expired_bookings(request)

        if booking_code:
            booking = self.get_object_for_request(request, booking_code)

            if self.is_html_request(request):
                return self.render_html_form_response(
                    request=request,
                    form=self.build_form(request, instance=booking, data=None),
                    booking=booking,
                    message="Equipment booking retrieved successfully.",
                    success=True,
                )

            return self.success_response(
                "Equipment booking retrieved successfully.",
                self.serialize_booking(booking, request),
            )

        queryset = self.get_queryset()

        search = request.GET.get("search")
        if search:
            queryset = queryset.filter(
                Q(booking_code__icontains=search)
                | Q(customer_full_name__icontains=search)
                | Q(customer_phone_number__icontains=search)
                | Q(customer_email_address__icontains=search)
                | Q(equipment__equipment_code__icontains=search)
                | Q(equipment__equipment_name__icontains=search)
                | Q(payment_transaction_id__icontains=search)
                | Q(razorpay_order_id__icontains=search)
            )

        if self.is_html_request(request):
            return self.render_html_list_response(
                request=request,
                bookings=queryset,
                message="Equipment booking list retrieved successfully.",
                success=True,
            )

        return self.success_response(
            "Equipment booking list retrieved successfully.",
            self.serialize_bookings(queryset, request),
        )

    @transaction.atomic
    def post(self, request, booking_code=None, format=None):
        if not self.is_admin(request):
            return self.permission_denied_response(
                request,
                "Only admin can create or update equipment bookings.",
            )

        self.auto_complete_expired_bookings(request)

        if booking_code:
            if self.is_html_request(request):
                messages.error(
                    request,
                    "Booking update is disabled. You can only view booking details.",
                )
                return redirect("equipment:admin-booking-list")

            return self.error_response(
                "Booking update is disabled.",
                {"detail": ["Admin can only view booking details."]},
                status.HTTP_403_FORBIDDEN,
            )

        form = self.build_form(request)

        if not form.is_valid():
            errors = self.normalize_form_errors(form)

            if self.is_html_request(request):
                return self.render_html_form_response(
                    request=request,
                    form=form,
                    message="Equipment booking validation failed.",
                    errors=errors,
                    http_status=status.HTTP_400_BAD_REQUEST,
                )

            return self.error_response("Equipment booking validation failed.", errors)

        booking = form.save()
        EquipmentBookingStatusService.update_equipment_status(booking.equipment, request.user)

        if self.is_html_request(request):
            return self.render_html_form_response(
                request=request,
                form=self.build_form(request, instance=booking, data=None),
                booking=booking,
                message="Equipment booking created successfully.",
                success=True,
                http_status=status.HTTP_201_CREATED,
            )

        return self.success_response(
            "Equipment booking created successfully.",
            self.serialize_booking(booking, request),
            status.HTTP_201_CREATED,
        )

    def put(self, request, booking_code=None, format=None):
        return self.error_response(
            "Booking update is disabled.",
            {"detail": ["Admin can only view booking details."]},
            status.HTTP_403_FORBIDDEN,
        )

    def patch(self, request, booking_code=None, format=None):
        return self.error_response(
            "Booking update is disabled.",
            {"detail": ["Admin can only view booking details."]},
            status.HTTP_403_FORBIDDEN,
        )

    def _update(self, request, booking_code, partial=False):
        if not self.is_admin(request):
            return self.permission_denied_response(request, "Only admin can update equipment bookings.")

        booking = self.get_object_for_request(request, booking_code)
        data = self.get_form_data(request)
        form = self.build_form(request, instance=booking, data=data)

        if partial:
            for field_name in form.fields:
                if field_name not in data:
                    form.fields[field_name].required = False

        if not form.is_valid():
            errors = self.normalize_form_errors(form)

            if self.is_html_request(request):
                return self.render_html_form_response(
                    request=request,
                    form=form,
                    booking=booking,
                    equipment=booking.equipment,
                    errors=errors,
                    message="Equipment booking update validation failed.",
                    http_status=status.HTTP_400_BAD_REQUEST,
                )

            return self.error_response("Equipment booking update validation failed.", errors)

        booking = form.save()
        EquipmentBookingStatusService.update_equipment_status(booking.equipment, request.user)

        if self.is_html_request(request):
            return self.render_html_form_response(
                request=request,
                form=self.build_form(request, instance=booking, data=None),
                booking=booking,
                message="Equipment booking updated successfully.",
                success=True,
            )

        return self.success_response(
            "Equipment booking updated successfully.",
            self.serialize_booking(booking, request),
        )

    @transaction.atomic
    def delete(self, request, booking_code=None, format=None):
        if not self.is_admin(request):
            return self.permission_denied_response(
                request,
                "Only admin can delete equipment bookings.",
            )

        if not booking_code:
            return self.error_response(
                "Booking code is required for delete.",
                {"booking_code": ["Booking code is required."]},
            )

        booking = self.get_object_for_request(request, booking_code)
        equipment = booking.equipment
        booking.delete()

        if equipment:
            EquipmentBookingStatusService.update_equipment_status(equipment, request.user)

        return self.success_response("Equipment booking deleted successfully.")





class AdminEquipmentBookingFormPageView(BaseEquipmentBookingAPIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_list = "equipment_booking/admin_booking_list.html"
    template_form = "equipment_booking/admin_booking_form.html"

    def get(self, request, format=None):
        if not self.is_admin(request):
            return self.permission_denied_response(
                request,
                "Only admin can access booking form page.",
            )

        return self.render_html_form_response(
            request=request,
            form=self.build_form(request, data=None),
            message="Equipment booking form page loaded successfully.",
            success=True,
        )


class FarmerEquipmentBookingAPIView(BaseEquipmentBookingAPIView):
    template_list = "equipment_booking/farmer_booking_list.html"
    template_form = "equipment_booking/farmer_booking_form.html"
    template_detail = "equipment_booking/farmer_booking_detail.html"
    template_payment = "equipment_booking/farmer_payment.html"

    def can_farmer_edit_booking(self, booking):
        return (
            booking.booking_status == EquipmentBooking.BookingStatusChoices.PENDING
            and booking.payment_status == EquipmentBooking.PaymentStatusChoices.PENDING
        )

    def get_equipment_from_query(self, request):
        equipment_code = request.GET.get("equipment_code")

        if not equipment_code:
            return None

        return (
            Equipment.objects
            .filter(
                equipment_code=str(equipment_code).strip().upper(),
                is_active=True,
                approval_status=Equipment.EquipmentApprovalStatusChoices.APPROVED,
            )
            .exclude(
                equipment_status=Equipment.EquipmentStatusChoices.MAINTENANCE
            )
            .first()
        )

    def get_equipment_from_data(self, data):
        equipment_id = data.get("equipment")
        equipment_code = data.get("equipment_code")

        equipment = None

        if equipment_id:
            equipment = (
                Equipment.objects
                .filter(
                    pk=equipment_id,
                    is_active=True,
                    approval_status=Equipment.EquipmentApprovalStatusChoices.APPROVED,
                )
                .exclude(
                    equipment_status=Equipment.EquipmentStatusChoices.MAINTENANCE
                )
                .first()
            )

        if not equipment and equipment_code:
            equipment = (
                Equipment.objects
                .filter(
                    equipment_code=str(equipment_code).strip().upper(),
                    is_active=True,
                    approval_status=Equipment.EquipmentApprovalStatusChoices.APPROVED,
                )
                .exclude(
                    equipment_status=Equipment.EquipmentStatusChoices.MAINTENANCE
                )
                .first()
            )

        return equipment

    def render_booking_detail_page(self, request, booking, message="", success=True):
        return Response(
            self.base_context(
                request,
                booking=booking,
                equipment=booking.equipment,
                today=timezone.localdate(),
                message=message,
                success=success,
            ),
            template_name=self.template_detail,
            status=status.HTTP_200_OK,
        )

    def render_payment_page(self, request, booking, http_status=status.HTTP_200_OK):
        return Response(
            self.base_context(
                request,
                booking=booking,
                equipment=booking.equipment,
                today=timezone.localdate(),
                razorpay_key_id=settings.RAZORPAY_KEY_ID,
                message="Equipment booking created. Complete payment to confirm booking.",
                success=True,
            ),
            template_name=self.template_payment,
            status=http_status,
        )

    def get(self, request, booking_code=None, format=None):
        if not self.is_farmer(request):
            return self.permission_denied_response(
                request,
                "Only farmer can access farmer equipment booking pages.",
            )

        self.auto_complete_expired_bookings(request)

        if booking_code:
            booking = self.get_object_for_request(request, booking_code)

            if self.is_html_request(request):
                if self.can_farmer_edit_booking(booking):
                    return self.render_html_form_response(
                        request=request,
                        form=self.build_form(request, instance=booking, data=None),
                        booking=booking,
                        equipment=booking.equipment,
                        message="You can edit this pending booking.",
                        success=True,
                    )

                return self.render_booking_detail_page(
                    request=request,
                    booking=booking,
                    message="Booking details loaded successfully.",
                    success=True,
                )

            return self.success_response(
                "Equipment booking retrieved successfully.",
                self.serialize_booking(booking, request),
            )

        equipment = self.get_equipment_from_query(request)

        if request.GET.get("equipment_code") and not equipment:
            if self.is_html_request(request):
                messages.error(request, "Selected equipment not found or not available.")
                return redirect("equipment:farmer-equipment-list")

            return self.error_response(
                "Selected equipment not found or not available.",
                {"equipment_code": ["Invalid equipment code."]},
            )

        if self.is_html_request(request) and equipment:
            initial_data = {
                "equipment": equipment.pk,
                "equipment_code": equipment.equipment_code,
                "booking_created_date": timezone.localdate(),
            }

            form = self.build_form(request, data=None, initial=initial_data)

            return self.render_html_form_response(
                request=request,
                form=form,
                booking=None,
                equipment=equipment,
                message="Equipment booking form loaded successfully.",
                success=True,
            )

        queryset = self.get_farmer_current_queryset(request)

        if self.is_html_request(request):
            return Response(
                self.base_context(
                    request,
                    bookings=queryset,
                    total_count=queryset.count(),
                    confirmed_count=queryset.filter(
                        booking_status=EquipmentBooking.BookingStatusChoices.CONFIRMED
                    ).count(),
                    pending_count=queryset.filter(
                        booking_status=EquipmentBooking.BookingStatusChoices.PENDING
                    ).count(),
                    paid_count=queryset.filter(
                        payment_status=EquipmentBooking.PaymentStatusChoices.PAID
                    ).count(),
                    message="Current booking list retrieved successfully.",
                    success=True,
                ),
                template_name=self.template_list,
                status=status.HTTP_200_OK,
            )

        return self.success_response(
            "Current booking list retrieved successfully.",
            self.serialize_bookings(queryset, request),
        )

    def prepare_booking_data(self, request):
        data = self.get_form_data(request)

        if not data.get("booking_created_date"):
            data["booking_created_date"] = timezone.localdate()

        equipment_code = data.get("equipment_code")

        if equipment_code and not data.get("equipment"):
            equipment = self.get_equipment_from_data(data)

            if equipment:
                data["equipment"] = equipment.pk

        return data

    def keep_equipment_available_after_pending_booking(self, booking, user):
        equipment = booking.equipment

        if not equipment:
            return

        if equipment.equipment_status == Equipment.EquipmentStatusChoices.MAINTENANCE:
            return

        equipment.equipment_status = Equipment.EquipmentStatusChoices.AVAILABLE

        if user and getattr(user, "is_authenticated", False):
            equipment.set_user_context(user)

        equipment.save(
            update_fields=[
                "equipment_status",
                "updated_by_user",
                "updated_at",
            ]
        )

    @transaction.atomic
    def post(self, request, booking_code=None, format=None):
        if not self.is_farmer(request):
            return self.permission_denied_response(
                request,
                "Only farmer can create equipment bookings.",
            )

        self.auto_complete_expired_bookings(request)

        if booking_code:
            return self._update(request, booking_code, partial=False)

        data = self.prepare_booking_data(request)
        form = self.build_form(request, data=data)

        form.instance.farmer_user = request.user
        form.instance.set_user_context(request.user)

        if not form.is_valid():
            errors = self.normalize_form_errors(form)

            if self.is_html_request(request):
                return self.render_html_form_response(
                    request=request,
                    form=form,
                    equipment=self.get_equipment_from_data(data),
                    errors=errors,
                    message="Equipment booking validation failed.",
                    http_status=status.HTTP_400_BAD_REQUEST,
                )

            return self.error_response(
                "Equipment booking validation failed.",
                errors,
            )

        booking = form.save(commit=False)
        booking.farmer_user = request.user
        booking.payment_status = EquipmentBooking.PaymentStatusChoices.PENDING
        booking.booking_status = EquipmentBooking.BookingStatusChoices.PENDING
        booking.payment_paid_at = None
        booking.set_user_context(request.user)
        booking.save()

        self.keep_equipment_available_after_pending_booking(
            booking=booking,
            user=request.user,
        )

        booking.refresh_from_db()

        if self.is_html_request(request):
            return redirect(
                "equipment:farmer-payment-page",
                booking_code=booking.booking_code
            )

        return self.success_response(
            "Equipment booking created. Complete payment to confirm booking.",
            self.serialize_booking(booking, request),
            status.HTTP_201_CREATED,
        )

    @transaction.atomic
    def put(self, request, booking_code=None, format=None):
        if not booking_code:
            return self.error_response(
                "Booking code is required for update.",
                {"booking_code": ["Booking code is required."]},
            )

        return self._update(request, booking_code, partial=False)

    @transaction.atomic
    def patch(self, request, booking_code=None, format=None):
        if not booking_code:
            return self.error_response(
                "Booking code is required for update.",
                {"booking_code": ["Booking code is required."]},
            )

        return self._update(request, booking_code, partial=True)

    def _update(self, request, booking_code, partial=False):
        if not self.is_farmer(request):
            return self.permission_denied_response(
                request,
                "Only farmer can update equipment bookings.",
            )

        booking = self.get_object_for_request(request, booking_code)

        if not self.can_farmer_edit_booking(booking):
            return self.error_response(
                "This booking cannot be edited.",
                {"detail": ["Only pending unpaid bookings can be edited."]},
                status.HTTP_403_FORBIDDEN,
            )

        data = self.prepare_booking_data(request)
        form = self.build_form(request, instance=booking, data=data)

        form.instance.farmer_user = request.user
        form.instance.set_user_context(request.user)

        if partial:
            for field_name in form.fields:
                if field_name not in data:
                    form.fields[field_name].required = False

        if not form.is_valid():
            errors = self.normalize_form_errors(form)

            if self.is_html_request(request):
                return self.render_html_form_response(
                    request=request,
                    form=form,
                    booking=booking,
                    equipment=booking.equipment,
                    errors=errors,
                    message="Equipment booking update validation failed.",
                    http_status=status.HTTP_400_BAD_REQUEST,
                )

            return self.error_response(
                "Equipment booking update validation failed.",
                errors,
            )

        booking = form.save(commit=False)
        booking.farmer_user = request.user
        booking.payment_status = EquipmentBooking.PaymentStatusChoices.PENDING
        booking.booking_status = EquipmentBooking.BookingStatusChoices.PENDING
        booking.payment_paid_at = None
        booking.set_user_context(request.user)
        booking.save()

        self.keep_equipment_available_after_pending_booking(
            booking=booking,
            user=request.user,
        )

        booking.refresh_from_db()

        if self.is_html_request(request):
            return self.render_payment_page(
                request=request,
                booking=booking,
                http_status=status.HTTP_200_OK,
            )

        return self.success_response(
            "Equipment booking updated successfully. Complete payment to confirm booking.",
            self.serialize_booking(booking, request),
        )

    @transaction.atomic
    def delete(self, request, booking_code=None, format=None):
        if not self.is_farmer(request):
            return self.permission_denied_response(
                request,
                "Only farmer can delete equipment bookings.",
            )

        if not booking_code:
            return self.error_response(
                "Booking code is required for delete.",
                {"booking_code": ["Booking code is required."]},
            )

        booking = self.get_object_for_request(request, booking_code)

        if booking.is_paid:
            return self.error_response(
                "Paid booking cannot be deleted.",
                {"detail": ["Cancel it instead."]},
            )

        equipment = booking.equipment
        booking.delete()

        if equipment and equipment.equipment_status != Equipment.EquipmentStatusChoices.MAINTENANCE:
            EquipmentBookingStatusService.update_equipment_status(
                equipment=equipment,
                user=request.user,
            )

        return self.success_response(
            "Equipment booking deleted successfully."
        )


        
class FarmerEquipmentBookingFormPageView(BaseEquipmentBookingAPIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_list = "equipment_booking/farmer_booking_list.html"
    template_form = "equipment_booking/farmer_booking_form.html"

    def get(self, request, format=None):
        if not self.is_farmer(request):
            return self.permission_denied_response(
                request,
                "Only farmer can access booking form page.",
            )

        self.auto_complete_expired_bookings(request)

        equipment_queryset = self.get_equipment_queryset_for_user(request)
        equipment_code = request.GET.get("equipment_code", "").strip().upper()

        selected_equipment = None
        initial = {
            "booking_created_date": timezone.localdate(),
        }

        if equipment_code:
            selected_equipment = equipment_queryset.filter(
                equipment_code=equipment_code
            ).first()

            if not selected_equipment:
                messages.error(request, "Selected equipment not found or not available.")
                return redirect("equipment:farmer-equipment-list")

            initial["equipment"] = selected_equipment.pk
            initial["equipment_code"] = selected_equipment.equipment_code

        form = self.build_form(request, data=None, initial=initial)

        return self.render_html_form_response(
            request=request,
            form=form,
            equipment=selected_equipment,
            selected_equipment=selected_equipment,
            message="Equipment booking form page loaded successfully.",
            success=True,
        )


class FarmerEquipmentBookingHistoryAPIView(BaseEquipmentBookingAPIView):
    template_list = "equipment_booking/farmer_booking_history.html"

    def get(self, request, format=None):
        if not self.is_farmer(request):
            return self.permission_denied_response(
                request,
                "Only farmer can access booking history.",
            )

        self.auto_complete_expired_bookings(request)
        queryset = self.get_farmer_history_queryset(request)

        if self.is_html_request(request):
            return self.render_html_list_response(
                request=request,
                bookings=queryset,
                message="Booking history loaded successfully.",
                success=True,
            )

        return self.success_response(
            "Booking history loaded successfully.",
            self.serialize_bookings(queryset, request),
        )


class FarmerPaymentPageAPIView(BaseEquipmentBookingAPIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_form = "equipment_booking/farmer_payment.html"
    template_detail = "equipment_booking/farmer_booking_detail.html"

    def get(self, request, booking_code=None, format=None):
        if not self.is_farmer(request):
            return self.permission_denied_response(
                request,
                "Only farmer can access payment page.",
            )

        self.auto_complete_expired_bookings(request)

        booking = self.get_object_for_request(request, booking_code)

        if booking.booking_status == EquipmentBooking.BookingStatusChoices.CANCELLED:
            return Response(
                self.base_context(
                    request,
                    booking=booking,
                    equipment=booking.equipment,
                    message="This booking was cancelled because payment was not completed within 15 minutes.",
                    success=False,
                ),
                template_name=self.template_detail,
                status=status.HTTP_200_OK,
            )

        if booking.payment_status == EquipmentBooking.PaymentStatusChoices.PAID:
            return Response(
                self.base_context(
                    request,
                    booking=booking,
                    equipment=booking.equipment,
                    message="Payment is already completed for this booking.",
                    success=True,
                ),
                template_name=self.template_detail,
                status=status.HTTP_200_OK,
            )

        return Response(
            self.base_context(
                request,
                booking=booking,
                equipment=booking.equipment,
                today=timezone.localdate(),
                razorpay_key_id=settings.RAZORPAY_KEY_ID,
                message="Payment page loaded successfully.",
                success=True,
            ),
            template_name=self.template_form,
            status=status.HTTP_200_OK,
        )


class FarmerBookingCreateRazorpayOrderAPIView(BaseEquipmentBookingAPIView):
    @transaction.atomic
    def post(self, request, booking_code=None, format=None):
        if not self.is_farmer(request):
            return self.permission_denied_response(
                request,
                "Only farmer can create payment order.",
            )

        self.auto_complete_expired_bookings(request)

        try:
            data = EquipmentBookingPaymentService.create_payment_order(
                booking_code=booking_code,
                user=request.user,
            )

            return self.success_response(
                "Razorpay order created successfully.",
                data,
            )

        except Exception as exc:
            logger.exception("Error creating Razorpay order")
            return self.error_response(
                "Error creating Razorpay order.",
                {"detail": [str(exc)]},
                status.HTTP_400_BAD_REQUEST,
            )


class FarmerBookingVerifyPaymentAPIView(BaseEquipmentBookingAPIView):
    @transaction.atomic
    def post(self, request, booking_code=None, format=None):
        if not self.is_farmer(request):
            return self.permission_denied_response(
                request,
                "Only farmer can verify payment.",
            )

        self.auto_complete_expired_bookings(request)

        serializer = RazorpayPaymentVerifySerializer(data=request.data)

        if not serializer.is_valid():
            return self.error_response(
                "Payment verification validation failed.",
                serializer.errors,
            )

        try:
            booking = EquipmentBookingPaymentService.verify_payment(
                booking_code=booking_code,
                user=request.user,
                razorpay_order_id=serializer.validated_data["razorpay_order_id"],
                razorpay_payment_id=serializer.validated_data["razorpay_payment_id"],
                razorpay_signature=serializer.validated_data["razorpay_signature"],
                payment_method=serializer.validated_data.get("payment_method", "upi"),
            )

            return self.success_response(
                "Payment verified and booking confirmed successfully.",
                self.serialize_booking(booking, request),
            )

        except Exception as exc:
            logger.exception("Error verifying Razorpay payment")
            return self.error_response(
                "Payment verification failed.",
                {"detail": [str(exc)]},
                status.HTTP_400_BAD_REQUEST,
            )


class FarmerBookingCancelAPIView(BaseEquipmentBookingAPIView):
    @transaction.atomic
    def post(self, request, booking_code=None, format=None):
        if not self.is_farmer(request):
            return self.permission_denied_response(
                request,
                "Only farmer can cancel booking.",
            )

        self.auto_complete_expired_bookings(request)

        booking = self.get_object_for_request(request, booking_code)

        try:
            booking = EquipmentBookingStatusService.cancel_booking(
                booking=booking,
                user=request.user,
            )

            if self.is_html_request(request):
                messages.success(request, "Booking cancelled successfully.")
                return redirect("equipment:farmer-booking-list")

            return self.success_response(
                "Booking cancelled successfully.",
                self.serialize_booking(booking, request),
            )

        except Exception as exc:
            logger.exception("Booking cancellation failed.")

            if self.is_html_request(request):
                messages.error(request, f"Booking cancellation failed: {exc}")
                return redirect("equipment:farmer-booking-detail", booking_code=booking.booking_code)

            return self.error_response(
                "Booking cancellation failed.",
                {"detail": [str(exc)]},
            )


from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import EquipmentBooking


@login_required
def farmer_dashboard_page(request):
    bookings = EquipmentBooking.objects.filter(
        farmer_user=request.user
    ).select_related("equipment")

    context = {
        "total_bookings": bookings.count(),

        "active_bookings": bookings.filter(
            booking_status__in=["pending", "confirmed"]
        ).count(),

        "completed_bookings": bookings.filter(
            booking_status="completed"
        ).count(),

        "cancelled_bookings": bookings.filter(
            booking_status="cancelled"
        ).count(),

        "recent_bookings": bookings.order_by("-created_at")[:5],
    }

    return render(request, "equipment/farmer_dashboard.html", context)


from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Equipment, EquipmentBooking


@login_required
def admin_dashboard_page(request):
    equipments = Equipment.objects.all()
    bookings = EquipmentBooking.objects.select_related("equipment", "farmer_user").all()

    context = {
        "total_equipment": equipments.count(),
        "available_equipment": equipments.filter(equipment_status="available").count(),
        "rented_equipment": equipments.filter(equipment_status="rented").count(),
        "maintenance_equipment": equipments.filter(equipment_status="maintenance").count(),

        "total_bookings": bookings.count(),
        "pending_bookings": bookings.filter(booking_status="pending").count(),
        "confirmed_bookings": bookings.filter(booking_status="confirmed").count(),
        "completed_bookings": bookings.filter(booking_status="completed").count(),
        "cancelled_bookings": bookings.filter(booking_status="cancelled").count(),

        "recent_bookings": bookings.order_by("-created_at")[:5],
    }

    return render(request, "equipment/admin_dashboard.html", context)