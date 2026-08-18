import logging
from datetime import timedelta

import razorpay
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import Equipment, EquipmentBooking


logger = logging.getLogger(__name__)


class EquipmentAvailabilityService:
    @staticmethod
    def get_current_paid_booking(equipment):
        today = timezone.localdate()

        return (
            EquipmentBooking.objects
            .filter(
                equipment=equipment,
                booking_status=EquipmentBooking.BookingStatusChoices.CONFIRMED,
                payment_status=EquipmentBooking.PaymentStatusChoices.PAID,
                booking_start_date__lte=today,
                booking_end_date__gte=today,
            )
            .order_by("booking_end_date")
            .first()
        )

    @staticmethod
    def get_next_paid_booking(equipment):
        today = timezone.localdate()

        return (
            EquipmentBooking.objects
            .filter(
                equipment=equipment,
                booking_status=EquipmentBooking.BookingStatusChoices.CONFIRMED,
                payment_status=EquipmentBooking.PaymentStatusChoices.PAID,
                booking_start_date__gt=today,
            )
            .order_by("booking_start_date")
            .first()
        )

    @staticmethod
    def get_availability(equipment):
        if equipment.equipment_status == Equipment.EquipmentStatusChoices.MAINTENANCE:
            return {
                "status": "maintenance",
                "label": "Maintenance",
                "is_bookable": False,
                "message": "Equipment is under maintenance.",
                "next_available_date": None,
                "current_booking": None,
                "next_booking": None,
            }

        current_booking = EquipmentAvailabilityService.get_current_paid_booking(equipment)

        if current_booking:
            next_available_date = current_booking.booking_end_date + timedelta(days=1)

            return {
                "status": "rented",
                "label": "Rented",
                "is_bookable": False,
                "message": f"Booked till {current_booking.booking_end_date}. Available from {next_available_date}.",
                "next_available_date": next_available_date,
                "current_booking": current_booking,
                "next_booking": None,
            }

        next_booking = EquipmentAvailabilityService.get_next_paid_booking(equipment)

        if next_booking:
            return {
                "status": "available",
                "label": "Available Now",
                "is_bookable": True,
                "message": f"Available now. Next booking from {next_booking.booking_start_date} to {next_booking.booking_end_date}.",
                "next_available_date": None,
                "current_booking": None,
                "next_booking": next_booking,
            }

        return {
            "status": "available",
            "label": "Available",
            "is_bookable": True,
            "message": "Equipment is available for booking.",
            "next_available_date": None,
            "current_booking": None,
            "next_booking": None,
        }

    @staticmethod
    @transaction.atomic
    def sync_equipment_status(equipment, user=None):
        if not equipment:
            return None

        availability = EquipmentAvailabilityService.get_availability(equipment)

        if availability["status"] == "maintenance":
            return equipment

        if availability["status"] == "rented":
            equipment.equipment_status = Equipment.EquipmentStatusChoices.RENTED
        else:
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

        return equipment


class PendingBookingAutoCancelService:
    EXPIRY_MINUTES = 15

    @staticmethod
    @transaction.atomic
    def auto_cancel_pending_payment_bookings(user=None):
        expiry_time = timezone.now() - timedelta(
            minutes=PendingBookingAutoCancelService.EXPIRY_MINUTES
        )

        expired_bookings = (
            EquipmentBooking.objects
            .select_for_update()
            .select_related("equipment")
            .filter(
                booking_status=EquipmentBooking.BookingStatusChoices.PENDING,
                payment_status=EquipmentBooking.PaymentStatusChoices.PENDING,
                created_at__lte=expiry_time,
            )
        )

        cancelled_count = 0

        for booking in expired_bookings:
            equipment = booking.equipment

            auto_cancel_message = (
                "Auto cancelled because payment was not completed within 15 minutes."
            )

            if auto_cancel_message not in (booking.booking_notes or ""):
                booking.booking_notes = (
                    f"{booking.booking_notes or ''}\n{auto_cancel_message}"
                ).strip()

            booking.booking_status = EquipmentBooking.BookingStatusChoices.CANCELLED

            if user and getattr(user, "is_authenticated", False):
                booking.set_user_context(user)

            booking.save(
                update_fields=[
                    "booking_status",
                    "booking_notes",
                    "updated_by_user",
                    "updated_at",
                ]
            )

            EquipmentAvailabilityService.sync_equipment_status(
                equipment=equipment,
                user=user,
            )

            cancelled_count += 1

        return cancelled_count


class RazorpayService:
    @staticmethod
    def get_client():
        return razorpay.Client(
            auth=(
                settings.RAZORPAY_KEY_ID,
                settings.RAZORPAY_KEY_SECRET,
            )
        )

    @staticmethod
    def create_order(booking):
        if booking.payment_status == EquipmentBooking.PaymentStatusChoices.PAID:
            raise ValueError("This booking is already paid.")

        if booking.booking_status in [
            EquipmentBooking.BookingStatusChoices.CANCELLED,
            EquipmentBooking.BookingStatusChoices.COMPLETED,
        ]:
            raise ValueError("Cancelled or completed booking cannot be paid.")

        amount = booking.amount_in_paise

        if amount <= 0:
            raise ValueError("Invalid payment amount.")

        client = RazorpayService.get_client()

        razorpay_order = client.order.create(
            {
                "amount": amount,
                "currency": getattr(settings, "RAZORPAY_CURRENCY", "INR"),
                "payment_capture": 1,
                "notes": {
                    "booking_code": booking.booking_code,
                    "equipment_code": booking.equipment.equipment_code,
                    "farmer_id": booking.farmer_user_id,
                    "customer_name": booking.customer_full_name,
                },
            }
        )

        booking.razorpay_order_id = razorpay_order["id"]
        booking.payment_status = EquipmentBooking.PaymentStatusChoices.PENDING
        booking.save(
            update_fields=[
                "razorpay_order_id",
                "payment_status",
                "updated_at",
            ]
        )

        return {
            "booking_code": booking.booking_code,
            "razorpay_key_id": settings.RAZORPAY_KEY_ID,
            "razorpay_order_id": razorpay_order["id"],
            "amount": amount,
            "currency": getattr(settings, "RAZORPAY_CURRENCY", "INR"),
            "customer_name": booking.customer_full_name,
            "customer_email": booking.customer_email_address,
            "customer_phone": booking.customer_phone_number,
        }

    @staticmethod
    def verify_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature):
        client = RazorpayService.get_client()

        client.utility.verify_payment_signature(
            {
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature,
            }
        )

        return True


class EquipmentBookingPaymentService:
    @staticmethod
    @transaction.atomic
    def create_payment_order(booking_code, user):
        PendingBookingAutoCancelService.auto_cancel_pending_payment_bookings(user=user)

        booking = (
            EquipmentBooking.objects
            .select_for_update()
            .select_related("equipment", "farmer_user")
            .get(
                booking_code=str(booking_code).strip().upper(),
                farmer_user=user,
            )
        )

        if booking.booking_status == EquipmentBooking.BookingStatusChoices.CANCELLED:
            raise ValueError("Booking cancelled because payment was not completed within 15 minutes.")

        if booking.payment_status == EquipmentBooking.PaymentStatusChoices.PAID:
            raise ValueError("This booking is already paid.")

        if (
            booking.razorpay_order_id
            and booking.payment_status == EquipmentBooking.PaymentStatusChoices.PENDING
        ):
            return {
                "booking_code": booking.booking_code,
                "razorpay_key_id": settings.RAZORPAY_KEY_ID,
                "razorpay_order_id": booking.razorpay_order_id,
                "amount": booking.amount_in_paise,
                "currency": getattr(settings, "RAZORPAY_CURRENCY", "INR"),
                "customer_name": booking.customer_full_name,
                "customer_email": booking.customer_email_address,
                "customer_phone": booking.customer_phone_number,
            }

        return RazorpayService.create_order(booking)

    @staticmethod
    @transaction.atomic
    def verify_payment(
        booking_code,
        user,
        razorpay_order_id,
        razorpay_payment_id,
        razorpay_signature,
        payment_method="upi",
    ):
        PendingBookingAutoCancelService.auto_cancel_pending_payment_bookings(user=user)

        booking = (
            EquipmentBooking.objects
            .select_for_update()
            .select_related("equipment", "farmer_user")
            .get(
                booking_code=str(booking_code).strip().upper(),
                farmer_user=user,
            )
        )

        if booking.booking_status == EquipmentBooking.BookingStatusChoices.CANCELLED:
            raise ValueError("Booking cancelled because payment was not completed within 15 minutes.")

        if booking.payment_status == EquipmentBooking.PaymentStatusChoices.PAID:
            return booking

        if booking.booking_status == EquipmentBooking.BookingStatusChoices.COMPLETED:
            raise ValueError("Completed booking cannot be paid.")

        if booking.razorpay_order_id != razorpay_order_id:
            booking.mark_payment_failed(
                reason="Razorpay order id does not match booking.",
                user=user,
            )
            booking.save()

            EquipmentAvailabilityService.sync_equipment_status(
                equipment=booking.equipment,
                user=user,
            )

            raise ValueError("Invalid Razorpay order id.")

        try:
            RazorpayService.verify_signature(
                razorpay_order_id=razorpay_order_id,
                razorpay_payment_id=razorpay_payment_id,
                razorpay_signature=razorpay_signature,
            )
        except Exception as exc:
            logger.exception("Razorpay signature verification failed")

            booking.mark_payment_failed(
                reason="Invalid Razorpay payment signature.",
                user=user,
            )
            booking.save()

            EquipmentAvailabilityService.sync_equipment_status(
                equipment=booking.equipment,
                user=user,
            )

            raise ValueError("Invalid Razorpay payment signature.") from exc

        booking.mark_payment_paid(
            razorpay_order_id=razorpay_order_id,
            razorpay_payment_id=razorpay_payment_id,
            razorpay_signature=razorpay_signature,
            payment_method=payment_method,
            user=user,
        )
        booking.save()

        EquipmentAvailabilityService.sync_equipment_status(
            equipment=booking.equipment,
            user=user,
        )

        return booking

    @staticmethod
    @transaction.atomic
    def mark_payment_failed(booking_code, user, reason="Payment failed."):
        booking = (
            EquipmentBooking.objects
            .select_for_update()
            .select_related("equipment", "farmer_user")
            .get(
                booking_code=str(booking_code).strip().upper(),
                farmer_user=user,
            )
        )

        booking.mark_payment_failed(reason=reason, user=user)
        booking.save()

        EquipmentAvailabilityService.sync_equipment_status(
            equipment=booking.equipment,
            user=user,
        )

        return booking


class EquipmentBookingStatusService:
    @staticmethod
    @transaction.atomic
    def update_equipment_status(equipment, user=None):
        return EquipmentAvailabilityService.sync_equipment_status(
            equipment=equipment,
            user=user,
        )

    @staticmethod
    @transaction.atomic
    def auto_complete_expired_bookings(user=None):
        today = timezone.localdate()

        expired_bookings = (
            EquipmentBooking.objects
            .select_for_update()
            .select_related("equipment")
            .filter(
                booking_status=EquipmentBooking.BookingStatusChoices.CONFIRMED,
                payment_status=EquipmentBooking.PaymentStatusChoices.PAID,
                booking_end_date__lt=today,
            )
        )

        completed_count = 0

        for booking in expired_bookings:
            booking.booking_status = EquipmentBooking.BookingStatusChoices.COMPLETED

            if user and getattr(user, "is_authenticated", False):
                booking.set_user_context(user)

            booking.save()
            completed_count += 1

            EquipmentAvailabilityService.sync_equipment_status(
                equipment=booking.equipment,
                user=user,
            )

        auto_cancelled_count = (
            PendingBookingAutoCancelService.auto_cancel_pending_payment_bookings(
                user=user
            )
        )

        return {
            "completed_count": completed_count,
            "auto_cancelled_count": auto_cancelled_count,
        }

    @staticmethod
    @transaction.atomic
    def cancel_booking(booking, user=None):
        if booking.booking_status == EquipmentBooking.BookingStatusChoices.COMPLETED:
            raise ValueError("Completed booking cannot be cancelled.")

        booking.booking_status = EquipmentBooking.BookingStatusChoices.CANCELLED

        if user and getattr(user, "is_authenticated", False):
            booking.set_user_context(user)

        booking.save()

        EquipmentAvailabilityService.sync_equipment_status(
            equipment=booking.equipment,
            user=user,
        )

        return booking

    @staticmethod
    @transaction.atomic
    def complete_booking(booking, user=None):
        booking.booking_status = EquipmentBooking.BookingStatusChoices.COMPLETED

        if user and getattr(user, "is_authenticated", False):
            booking.set_user_context(user)

        booking.save()

        EquipmentAvailabilityService.sync_equipment_status(
            equipment=booking.equipment,
            user=user,
        )

        return booking

    @staticmethod
    @transaction.atomic
    def confirm_booking(booking, user=None):
        booking.booking_status = EquipmentBooking.BookingStatusChoices.CONFIRMED

        if user and getattr(user, "is_authenticated", False):
            booking.set_user_context(user)

        booking.save()

        EquipmentAvailabilityService.sync_equipment_status(
            equipment=booking.equipment,
            user=user,
        )

        return booking