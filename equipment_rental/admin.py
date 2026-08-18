from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html

from .models import Equipment, EquipmentBooking


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = [
        "equipment_code",
        "equipment_name",
        "equipment_category",
        "equipment_brand",
        "owner_name",
        "rental_price_per_day",
        "equipment_status_badge",
        "approval_status_badge",
        "is_active",
        "equipment_image_preview",
        "created_at",
    ]

    list_filter = [
        "equipment_category",
        "equipment_status",
        "approval_status",
        "is_active",
        "location_city",
        "created_at",
    ]

    search_fields = [
        "equipment_code",
        "equipment_name",
        "equipment_brand",
        "owner_name",
        "equipment_identity_number",
        "location_city",
    ]

    readonly_fields = [
        "equipment_slug",
        "approved_by_user",
        "approved_at",
        "created_by_user",
        "updated_by_user",
        "created_at",
        "updated_at",
        "equipment_image_preview",
    ]

    list_per_page = 25
    ordering = ["-created_at"]
    date_hierarchy = "created_at"

    fieldsets = (
        ("Equipment Information", {
            "fields": (
                "equipment_name",
                "equipment_code",
                "equipment_slug",
                "equipment_category",
                "equipment_brand",
                "equipment_identity_number",
                "owner_name",
                "equipment_description",
            )
        }),
        ("Rental Information", {
            "fields": (
                "rental_price_per_day",
                "location_city",
                "equipment_image",
                "equipment_image_preview",
            )
        }),
        ("Status Information", {
            "fields": (
                "equipment_status",
                "approval_status",
                "approved_by_user",
                "approved_at",
                "is_active",
            )
        }),
        ("Tracking Information", {
            "classes": ("collapse",),
            "fields": (
                "created_by_user",
                "updated_by_user",
                "created_at",
                "updated_at",
            )
        }),
    )

    actions = [
        "approve_selected_equipment",
        "reject_selected_equipment",
        "mark_as_available",
        "mark_as_rented",
        "mark_as_maintenance",
        "activate_equipment",
        "deactivate_equipment",
    ]

    def save_model(self, request, obj, form, change):
        obj.set_user_context(request.user)

        if obj.approval_status == Equipment.EquipmentApprovalStatusChoices.APPROVED:
            obj.approved_by_user = request.user.username.strip().title()
            obj.approved_at = timezone.now()

        super().save_model(request, obj, form, change)

    def equipment_status_badge(self, obj):
        colors = {
            Equipment.EquipmentStatusChoices.AVAILABLE: "#198754",
            Equipment.EquipmentStatusChoices.RENTED: "#dc3545",
            Equipment.EquipmentStatusChoices.MAINTENANCE: "#ffc107",
        }

        return format_html(
            '<span style="padding:4px 10px;border-radius:12px;color:white;background:{};">{}</span>',
            colors.get(obj.equipment_status, "#6c757d"),
            obj.get_equipment_status_display(),
        )

    equipment_status_badge.short_description = "Equipment Status"

    def approval_status_badge(self, obj):
        colors = {
            Equipment.EquipmentApprovalStatusChoices.APPROVED: "#198754",
            Equipment.EquipmentApprovalStatusChoices.REJECTED: "#dc3545",
        }

        return format_html(
            '<span style="padding:4px 10px;border-radius:12px;color:white;background:{};">{}</span>',
            colors.get(obj.approval_status, "#6c757d"),
            obj.get_approval_status_display(),
        )

    approval_status_badge.short_description = "Approval Status"

    def equipment_image_preview(self, obj):
        if obj.equipment_image:
            return format_html(
                '<img src="{}" width="80" height="80" style="border-radius:8px;object-fit:cover;" />',
                obj.equipment_image.url,
            )

        return "-"

    equipment_image_preview.short_description = "Image Preview"

    @admin.action(description="Approve selected equipment")
    def approve_selected_equipment(self, request, queryset):
        count = 0

        for equipment in queryset:
            equipment.approve_equipment(request.user)
            equipment.save()
            count += 1

        self.message_user(request, f"{count} equipment approved successfully.")

    @admin.action(description="Reject selected equipment")
    def reject_selected_equipment(self, request, queryset):
        count = 0

        for equipment in queryset:
            equipment.reject_equipment(request.user)
            equipment.save()
            count += 1

        self.message_user(request, f"{count} equipment rejected successfully.")

    @admin.action(description="Mark selected equipment as available")
    def mark_as_available(self, request, queryset):
        count = queryset.update(
            equipment_status=Equipment.EquipmentStatusChoices.AVAILABLE,
        )
        self.message_user(request, f"{count} equipment marked as available.")

    @admin.action(description="Mark selected equipment as rented")
    def mark_as_rented(self, request, queryset):
        count = queryset.update(
            equipment_status=Equipment.EquipmentStatusChoices.RENTED,
        )
        self.message_user(request, f"{count} equipment marked as rented.")

    @admin.action(description="Mark selected equipment as maintenance")
    def mark_as_maintenance(self, request, queryset):
        count = queryset.update(
            equipment_status=Equipment.EquipmentStatusChoices.MAINTENANCE,
        )
        self.message_user(request, f"{count} equipment marked as maintenance.")

    @admin.action(description="Activate selected equipment")
    def activate_equipment(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f"{count} equipment activated successfully.")

    @admin.action(description="Deactivate selected equipment")
    def deactivate_equipment(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"{count} equipment deactivated successfully.")


@admin.register(EquipmentBooking)
class EquipmentBookingAdmin(admin.ModelAdmin):
    list_display = [
        "booking_code",
        "customer_full_name",
        "customer_phone_number",
        "equipment",
        "booking_start_date",
        "booking_end_date",
        "booking_total_days",
        "booking_total_amount",
        "payment_status_badge",
        "booking_status_badge",
        "payment_method",
        "payment_paid_at",
        "created_at",
    ]

    list_filter = [
        "payment_status",
        "payment_method",
        "booking_status",
        "booking_created_date",
        "booking_start_date",
        "booking_end_date",
        "payment_paid_at",
        "created_at",
    ]

    search_fields = [
        "booking_code",
        "customer_full_name",
        "customer_phone_number",
        "customer_email_address",
        "razorpay_order_id",
        "payment_transaction_id",
        "equipment__equipment_code",
        "equipment__equipment_name",
        "farmer_user__username",
        "farmer_user__email",
    ]

    readonly_fields = [
        "booking_slug",
        "booking_total_days",
        "booking_rental_price_per_day",
        "booking_total_amount",
        "razorpay_order_id",
        "payment_transaction_id",
        "razorpay_signature",
        "payment_paid_at",
        "created_by_user",
        "updated_by_user",
        "created_at",
        "updated_at",
    ]

    autocomplete_fields = [
        "equipment",
        "farmer_user",
    ]

    list_per_page = 25
    ordering = ["-created_at"]
    date_hierarchy = "created_at"

    fieldsets = (
        ("Booking Information", {
            "fields": (
                "booking_code",
                "booking_slug",
                "farmer_user",
                "equipment",
            )
        }),
        ("Customer Information", {
            "fields": (
                "customer_full_name",
                "customer_phone_number",
                "customer_email_address",
                "customer_full_address",
            )
        }),
        ("Booking Dates", {
            "fields": (
                "booking_created_date",
                "booking_start_date",
                "booking_end_date",
                "booking_total_days",
            )
        }),
        ("Rental Amount", {
            "fields": (
                "booking_rental_price_per_day",
                "booking_total_amount",
            )
        }),
        ("Payment Information", {
            "fields": (
                "payment_status",
                "payment_method",
                "razorpay_order_id",
                "payment_transaction_id",
                "razorpay_signature",
                "payment_failure_reason",
                "payment_paid_at",
            )
        }),
        ("Booking Status", {
            "fields": (
                "booking_status",
                "booking_notes",
            )
        }),
        ("Tracking Information", {
            "classes": ("collapse",),
            "fields": (
                "created_by_user",
                "updated_by_user",
                "created_at",
                "updated_at",
            )
        }),
    )

    actions = [
        "mark_booking_pending",
        "mark_booking_confirmed",
        "mark_booking_cancelled",
        "mark_booking_completed",
        "mark_payment_pending",
        "mark_payment_paid",
        "mark_payment_failed",
        "mark_payment_refunded",
    ]

    def save_model(self, request, obj, form, change):
        obj.set_user_context(request.user)

        if obj.payment_status == EquipmentBooking.PaymentStatusChoices.PAID and not obj.payment_paid_at:
            obj.payment_paid_at = timezone.now()

        super().save_model(request, obj, form, change)

    def payment_status_badge(self, obj):
        colors = {
            EquipmentBooking.PaymentStatusChoices.PENDING: "#ffc107",
            EquipmentBooking.PaymentStatusChoices.PAID: "#198754",
            EquipmentBooking.PaymentStatusChoices.FAILED: "#dc3545",
            EquipmentBooking.PaymentStatusChoices.REFUNDED: "#0dcaf0",
        }

        return format_html(
            '<span style="padding:4px 10px;border-radius:12px;color:white;background:{};">{}</span>',
            colors.get(obj.payment_status, "#6c757d"),
            obj.get_payment_status_display(),
        )

    payment_status_badge.short_description = "Payment Status"

    def booking_status_badge(self, obj):
        colors = {
            EquipmentBooking.BookingStatusChoices.PENDING: "#ffc107",
            EquipmentBooking.BookingStatusChoices.CONFIRMED: "#198754",
            EquipmentBooking.BookingStatusChoices.CANCELLED: "#dc3545",
            EquipmentBooking.BookingStatusChoices.COMPLETED: "#0d6efd",
        }

        return format_html(
            '<span style="padding:4px 10px;border-radius:12px;color:white;background:{};">{}</span>',
            colors.get(obj.booking_status, "#6c757d"),
            obj.get_booking_status_display(),
        )

    booking_status_badge.short_description = "Booking Status"

    @admin.action(description="Mark booking pending")
    def mark_booking_pending(self, request, queryset):
        count = queryset.update(
            booking_status=EquipmentBooking.BookingStatusChoices.PENDING,
        )
        self.message_user(request, f"{count} bookings marked as pending.")

    @admin.action(description="Mark booking confirmed")
    def mark_booking_confirmed(self, request, queryset):
        count = queryset.update(
            booking_status=EquipmentBooking.BookingStatusChoices.CONFIRMED,
        )
        self.message_user(request, f"{count} bookings confirmed successfully.")

    @admin.action(description="Mark booking cancelled")
    def mark_booking_cancelled(self, request, queryset):
        count = queryset.update(
            booking_status=EquipmentBooking.BookingStatusChoices.CANCELLED,
        )
        self.message_user(request, f"{count} bookings cancelled successfully.")

    @admin.action(description="Mark booking completed")
    def mark_booking_completed(self, request, queryset):
        count = queryset.update(
            booking_status=EquipmentBooking.BookingStatusChoices.COMPLETED,
        )
        self.message_user(request, f"{count} bookings completed successfully.")

    @admin.action(description="Mark payment pending")
    def mark_payment_pending(self, request, queryset):
        count = queryset.update(
            payment_status=EquipmentBooking.PaymentStatusChoices.PENDING,
            payment_paid_at=None,
        )
        self.message_user(request, f"{count} payments marked as pending.")

    @admin.action(description="Mark payment paid")
    def mark_payment_paid(self, request, queryset):
        count = queryset.update(
            payment_status=EquipmentBooking.PaymentStatusChoices.PAID,
            payment_paid_at=timezone.now(),
        )
        self.message_user(request, f"{count} payments marked as paid.")

    @admin.action(description="Mark payment failed")
    def mark_payment_failed(self, request, queryset):
        count = queryset.update(
            payment_status=EquipmentBooking.PaymentStatusChoices.FAILED,
        )
        self.message_user(request, f"{count} payments marked as failed.")

    @admin.action(description="Mark payment refunded")
    def mark_payment_refunded(self, request, queryset):
        count = queryset.update(
            payment_status=EquipmentBooking.PaymentStatusChoices.REFUNDED,
        )
        self.message_user(request, f"{count} payments marked as refunded.")