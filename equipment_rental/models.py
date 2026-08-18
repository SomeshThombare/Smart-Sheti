from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

from .constants import (
    EQUIPMENT_STATUS_AVAILABLE,
    EQUIPMENT_STATUS_RENTED,
    EQUIPMENT_STATUS_MAINTENANCE,
    EQUIPMENT_CATEGORY_CHOICES,
    ENGINE_BASED_CATEGORIES,
    APPROVAL_STATUS_APPROVED,
    APPROVAL_STATUS_REJECTED,
    PAYMENT_STATUS_PENDING,
    PAYMENT_STATUS_PAID,
    PAYMENT_STATUS_FAILED,
    PAYMENT_STATUS_REFUNDED,
    PAYMENT_METHOD_UPI,
    PAYMENT_METHOD_CHOICES,
    BOOKING_STATUS_PENDING,
    BOOKING_STATUS_CONFIRMED,
    BOOKING_STATUS_CANCELLED,
    BOOKING_STATUS_COMPLETED,
)

from .validators import (
    validate_image_size,
    validate_image_extension,
    validate_positive_amount,
    validate_minimum_rental_price,
    validate_razorpay_order_id,
    validate_razorpay_payment_id,
)

from .utils import (
    generate_equipment_code,
    generate_booking_code,
    generate_unique_slug,
    calculate_booking_total_days,
    calculate_booking_total_amount,
    convert_rupees_to_paise,
    get_user_full_name,
    get_user_email,
    safe_strip,
    safe_upper,
    safe_title,
    safe_lower,
)


class TimeStampedUserTrackingModel(models.Model):
    created_by_user = models.CharField(max_length=100, blank=True, null=True)
    updated_by_user = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    _current_user = None

    class Meta:
        abstract = True

    def set_user_context(self, user):
        self._current_user = user
        if user and getattr(user, "is_authenticated", False):
            username = safe_title(getattr(user, "username", None) or str(user))
            if username:
                if not self.pk and not self.created_by_user:
                    self.created_by_user = username
                self.updated_by_user = username

    def normalize_user_tracking_fields(self):
        self.created_by_user = safe_title(self.created_by_user)
        self.updated_by_user = safe_title(self.updated_by_user)


class Equipment(TimeStampedUserTrackingModel):

    class EquipmentStatusChoices(models.TextChoices):
        AVAILABLE = EQUIPMENT_STATUS_AVAILABLE, "Available"
        RENTED = EQUIPMENT_STATUS_RENTED, "Rented"
        MAINTENANCE = EQUIPMENT_STATUS_MAINTENANCE, "Maintenance"

    class EquipmentApprovalStatusChoices(models.TextChoices):
        APPROVED = APPROVAL_STATUS_APPROVED, "Approved"
        REJECTED = APPROVAL_STATUS_REJECTED, "Rejected"

    equipment_name_validator = RegexValidator(
        regex=r"^[A-Za-z0-9\s\-\&\(\)\/\.]+$",
        message="Equipment name can contain letters, numbers, spaces, hyphen, &, (), / and dot only.",
    )

    equipment_code_validator = RegexValidator(
        regex=r"^[A-Z0-9_-]+$",
        message="Equipment code must contain only uppercase letters, numbers, underscore, or hyphen.",
    )

    identity_number_validator = RegexValidator(
        regex=r"^[A-Za-z0-9\-/]+$",
        message="Identity number can contain letters, numbers, hyphen and slash only.",
    )

    owner_name_validator = RegexValidator(
        regex=r"^[A-Za-z0-9\s\-\&\(\)\/\.]+$",
        message="Owner name can contain letters, numbers, spaces, hyphen, &, (), / and dot only.",
    )

    equipment_name = models.CharField(max_length=150, validators=[equipment_name_validator])

    equipment_code = models.CharField(
        max_length=30,
        unique=True,
        blank=True,
        validators=[equipment_code_validator],
    )

    equipment_slug = models.SlugField(max_length=180, unique=True, blank=True)

    equipment_category = models.CharField(max_length=50, choices=EQUIPMENT_CATEGORY_CHOICES)

    equipment_brand = models.CharField(max_length=100, blank=True, null=True)

    owner_name = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        validators=[owner_name_validator],
    )

    equipment_identity_number = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True,
        validators=[identity_number_validator],
        help_text="Enter engine number, vehicle number, chassis number, or serial number.",
    )

    equipment_description = models.TextField(blank=True, null=True)

    rental_price_per_day = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[validate_positive_amount, validate_minimum_rental_price],
    )

    location_city = models.CharField(max_length=100, blank=True, null=True)

    equipment_image = models.ImageField(
        upload_to="equipment/images/",
        blank=True,
        null=True,
        validators=[validate_image_extension, validate_image_size],
    )

    equipment_status = models.CharField(
        max_length=20,
        choices=EquipmentStatusChoices.choices,
        default=EquipmentStatusChoices.AVAILABLE,
        db_index=True,
    )

    approval_status = models.CharField(
        max_length=20,
        choices=EquipmentApprovalStatusChoices.choices,
        default=EquipmentApprovalStatusChoices.APPROVED,
        db_index=True,
    )

    approved_by_user = models.CharField(max_length=100, blank=True, null=True)
    approved_at = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Equipment"
        verbose_name_plural = "Equipment"
        indexes = [
            models.Index(fields=["equipment_code"]),
            models.Index(fields=["equipment_slug"]),
            models.Index(fields=["equipment_category"]),
            models.Index(fields=["equipment_brand"]),
            models.Index(fields=["owner_name"]),
            models.Index(fields=["equipment_identity_number"]),
            models.Index(fields=["equipment_status"]),
            models.Index(fields=["approval_status"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["location_city"]),
            models.Index(fields=["is_active", "approval_status", "equipment_status"]),
            models.Index(fields=["created_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(rental_price_per_day__gte=0),
                name="equipment_rental_price_per_day_gte_zero",
            )
        ]

    def __str__(self):
        return f"{self.equipment_name} ({self.equipment_code})"

    def get_identity_field_label(self):
        if self.equipment_category in ENGINE_BASED_CATEGORIES:
            return "Engine / Vehicle / Chassis Number"
        return "Serial Number"

    def approve_equipment(self, user=None):
        self.approval_status = self.EquipmentApprovalStatusChoices.APPROVED
        self.approved_at = timezone.now()
        if user and getattr(user, "is_authenticated", False):
            self.approved_by_user = get_user_full_name(user)
            self.set_user_context(user)

    def reject_equipment(self, user=None):
        self.approval_status = self.EquipmentApprovalStatusChoices.REJECTED
        self.approved_at = timezone.now()
        if user and getattr(user, "is_authenticated", False):
            self.approved_by_user = get_user_full_name(user)
            self.set_user_context(user)

    def clean(self):
        self._normalize_fields()
        errors = {}

        if not self.equipment_name:
            errors["equipment_name"] = "Equipment name is required."

        if not self.equipment_category:
            errors["equipment_category"] = "Equipment category is required."

        if not self.equipment_identity_number:
            if self.equipment_category in ENGINE_BASED_CATEGORIES:
                errors["equipment_identity_number"] = "Engine / Vehicle / Chassis number is required."
            else:
                errors["equipment_identity_number"] = "Serial number is required."

        if self.pk:
            old_obj = Equipment.objects.filter(pk=self.pk).only("equipment_code").first()
            if old_obj and old_obj.equipment_code != self.equipment_code:
                errors["equipment_code"] = "Equipment code cannot be changed once created."

        if self.equipment_identity_number:
            duplicate_qs = Equipment.objects.filter(
                equipment_identity_number__iexact=self.equipment_identity_number,
            ).exclude(pk=self.pk)

            if duplicate_qs.exists():
                errors["equipment_identity_number"] = (
                    "Equipment identity number already exists. Duplicate machine data is not allowed."
                )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self._normalize_fields()

        if not self.equipment_code:
            self.equipment_code = generate_equipment_code()

        if not self.equipment_slug:
            self.equipment_slug = generate_unique_slug(
                model_class=Equipment,
                value=self.equipment_name or self.equipment_code or "equipment",
                slug_field="equipment_slug",
                instance_id=self.pk,
            )

        self.full_clean()
        super().save(*args, **kwargs)

    def _normalize_fields(self):
        self.equipment_name = safe_title(self.equipment_name)
        self.equipment_code = safe_upper(self.equipment_code)
        self.equipment_brand = safe_title(self.equipment_brand)
        self.owner_name = safe_title(self.owner_name)
        self.equipment_identity_number = safe_upper(self.equipment_identity_number)
        self.equipment_description = safe_strip(self.equipment_description)
        self.location_city = safe_title(self.location_city)
        self.approved_by_user = safe_title(self.approved_by_user)
        self.normalize_user_tracking_fields()


class EquipmentBooking(TimeStampedUserTrackingModel):

    class BookingStatusChoices(models.TextChoices):
        PENDING = BOOKING_STATUS_PENDING, "Pending"
        CONFIRMED = BOOKING_STATUS_CONFIRMED, "Confirmed"
        CANCELLED = BOOKING_STATUS_CANCELLED, "Cancelled"
        COMPLETED = BOOKING_STATUS_COMPLETED, "Completed"

    class PaymentStatusChoices(models.TextChoices):
        PENDING = PAYMENT_STATUS_PENDING, "Pending"
        PAID = PAYMENT_STATUS_PAID, "Paid"
        FAILED = PAYMENT_STATUS_FAILED, "Failed"
        REFUNDED = PAYMENT_STATUS_REFUNDED, "Refunded"

    booking_code_validator = RegexValidator(
        regex=r"^[A-Z0-9_-]+$",
        message="Booking code must contain only uppercase letters, numbers, underscore, or hyphen.",
    )

    customer_name_validator = RegexValidator(
        regex=r"^[A-Za-z\s]+$",
        message="Customer full name can contain letters and spaces only.",
    )

    phone_validator = RegexValidator(
        regex=r"^[0-9+\- ]{8,15}$",
        message="Enter a valid contact number.",
    )

    booking_code = models.CharField(
        max_length=30,
        unique=True,
        blank=True,
        validators=[booking_code_validator],
    )

    booking_slug = models.SlugField(max_length=180, unique=True, blank=True)

    farmer_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="equipment_bookings",
        db_index=True,
    )

    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.PROTECT,
        related_name="equipment_bookings",
        db_index=True,
    )

    customer_full_name = models.CharField(
        max_length=150,
        validators=[customer_name_validator],
        blank=True,
    )

    customer_phone_number = models.CharField(max_length=15, validators=[phone_validator])
    customer_email_address = models.EmailField(blank=True, null=True)
    customer_full_address = models.TextField(blank=True, null=True)

    booking_created_date = models.DateField(default=timezone.localdate)
    booking_start_date = models.DateField()
    booking_end_date = models.DateField()

    booking_total_days = models.PositiveIntegerField(default=0)

    booking_rental_price_per_day = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[validate_positive_amount],
    )

    booking_total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[validate_positive_amount],
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatusChoices.choices,
        default=PaymentStatusChoices.PENDING,
        db_index=True,
    )

    payment_method = models.CharField(
        max_length=30,
        choices=PAYMENT_METHOD_CHOICES,
        blank=True,
        null=True,
        db_index=True,
    )

    razorpay_order_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        validators=[validate_razorpay_order_id],
        db_index=True,
    )

    payment_transaction_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        validators=[validate_razorpay_payment_id],
        db_index=True,
        help_text="Razorpay payment id.",
    )

    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    payment_failure_reason = models.TextField(blank=True, null=True)
    payment_paid_at = models.DateTimeField(blank=True, null=True, db_index=True)

    booking_status = models.CharField(
        max_length=20,
        choices=BookingStatusChoices.choices,
        default=BookingStatusChoices.PENDING,
        db_index=True,
    )

    booking_notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Equipment Booking"
        verbose_name_plural = "Equipment Bookings"
        indexes = [
            models.Index(fields=["booking_code"]),
            models.Index(fields=["booking_slug"]),
            models.Index(fields=["farmer_user", "booking_status"]),
            models.Index(fields=["equipment", "booking_status"]),
            models.Index(fields=["equipment", "booking_start_date", "booking_end_date"]),
            models.Index(fields=["payment_status", "booking_status"]),
            models.Index(fields=["booking_start_date", "booking_end_date"]),
            models.Index(fields=["payment_paid_at"]),
            models.Index(fields=["created_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(booking_total_days__gte=0),
                name="booking_total_days_gte_zero",
            ),
            models.CheckConstraint(
                condition=models.Q(booking_rental_price_per_day__gte=0),
                name="booking_rental_price_per_day_gte_zero",
            ),
            models.CheckConstraint(
                condition=models.Q(booking_total_amount__gte=0),
                name="booking_total_amount_gte_zero",
            ),
            models.CheckConstraint(
                condition=models.Q(booking_end_date__gte=models.F("booking_start_date")),
                name="booking_end_date_gte_booking_start_date",
            ),
            models.UniqueConstraint(
                fields=["razorpay_order_id"],
                condition=models.Q(razorpay_order_id__isnull=False),
                name="unique_non_null_razorpay_order_id",
            ),
            models.UniqueConstraint(
                fields=["payment_transaction_id"],
                condition=models.Q(payment_transaction_id__isnull=False),
                name="unique_non_null_payment_transaction_id",
            ),
        ]

    def __str__(self):
        return f"{self.booking_code} - {self.customer_full_name}"

    @property
    def amount_in_paise(self):
        return convert_rupees_to_paise(self.booking_total_amount)

    @property
    def is_paid(self):
        return self.payment_status == self.PaymentStatusChoices.PAID

    @property
    def is_active_booking(self):
        return self.booking_status in [
            self.BookingStatusChoices.PENDING,
            self.BookingStatusChoices.CONFIRMED,
        ]

    def can_edit(self):
        return (
            self.payment_status != self.PaymentStatusChoices.PAID
            and self.booking_status not in [
                self.BookingStatusChoices.CANCELLED,
                self.BookingStatusChoices.COMPLETED,
            ]
        )

    def can_cancel(self):
        return self.booking_status != self.BookingStatusChoices.COMPLETED

    def mark_payment_paid(
        self,
        razorpay_order_id,
        razorpay_payment_id,
        razorpay_signature,
        payment_method=PAYMENT_METHOD_UPI,
        user=None,
    ):
        self.razorpay_order_id = razorpay_order_id
        self.payment_transaction_id = razorpay_payment_id
        self.razorpay_signature = razorpay_signature
        self.payment_method = payment_method
        self.payment_status = self.PaymentStatusChoices.PAID
        self.booking_status = self.BookingStatusChoices.CONFIRMED
        self.payment_paid_at = timezone.now()

        if user:
            self.set_user_context(user)

    def mark_payment_failed(self, reason="", user=None):
        self.payment_status = self.PaymentStatusChoices.FAILED
        self.payment_failure_reason = reason or "Payment failed."
        self.booking_status = self.BookingStatusChoices.PENDING

        if user:
            self.set_user_context(user)

    def clean(self):
        self._normalize_fields()
        errors = {}

        current_user_authenticated = bool(
            self._current_user and getattr(self._current_user, "is_authenticated", False)
        )

        if not self.farmer_user_id and not current_user_authenticated:
            errors["farmer_user"] = "Farmer user is required."

        if not self.equipment_id:
            errors["equipment"] = "Equipment is required."

        if not self.customer_full_name:
            errors["customer_full_name"] = "Customer full name is required."

        if not self.customer_phone_number:
            errors["customer_phone_number"] = "Customer phone number is required."

        if not self.booking_start_date:
            errors["booking_start_date"] = "Booking start date is required."

        if not self.booking_end_date:
            errors["booking_end_date"] = "Booking end date is required."

        if self.booking_start_date and self.booking_end_date:
            if self.booking_end_date < self.booking_start_date:
                errors["booking_end_date"] = "Booking end date cannot be earlier than booking start date."

        if self.equipment_id:
            if not self.equipment.is_active:
                errors["equipment"] = "Inactive equipment cannot be booked."

            elif self.equipment.equipment_status == Equipment.EquipmentStatusChoices.MAINTENANCE:
                errors["equipment"] = "Equipment under maintenance cannot be booked."

            elif self.equipment.approval_status != Equipment.EquipmentApprovalStatusChoices.APPROVED:
                errors["equipment"] = "Only approved equipment can be booked."

        if self.payment_status == self.PaymentStatusChoices.PAID:
            if not self.razorpay_order_id:
                errors["razorpay_order_id"] = "Razorpay order id is required."

            if not self.payment_transaction_id:
                errors["payment_transaction_id"] = "Razorpay payment id is required."

            if not self.razorpay_signature:
                errors["razorpay_signature"] = "Razorpay signature is required."

            if not self.payment_paid_at:
                self.payment_paid_at = timezone.now()

        if self.payment_status == self.PaymentStatusChoices.FAILED:
            if not self.payment_failure_reason:
                errors["payment_failure_reason"] = "Payment failure reason is required."

        if self.pk:
            old_obj = EquipmentBooking.objects.filter(pk=self.pk).only("booking_code").first()
            if old_obj and old_obj.booking_code != self.booking_code:
                errors["booking_code"] = "Booking code cannot be changed once created."

        if self.equipment_id and self.booking_start_date and self.booking_end_date:
            overlapping_qs = EquipmentBooking.objects.filter(
                equipment_id=self.equipment_id,
                booking_status__in=[
                    self.BookingStatusChoices.PENDING,
                    self.BookingStatusChoices.CONFIRMED,
                ],
                booking_start_date__lte=self.booking_end_date,
                booking_end_date__gte=self.booking_start_date,
            ).exclude(pk=self.pk)

            if overlapping_qs.exists():
                latest_booking = overlapping_qs.order_by("-booking_end_date").first()
                next_available_date = latest_booking.booking_end_date + timedelta(days=1)

                errors["equipment"] = (
                    f"This equipment is already booked for the selected dates. "
                    f"You can book it from {next_available_date}."
                )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self._normalize_fields()

        if self._current_user and getattr(self._current_user, "is_authenticated", False):
            if not self.farmer_user_id:
                self.farmer_user = self._current_user

            if not self.customer_full_name:
                self.customer_full_name = get_user_full_name(self._current_user)

            if not self.customer_email_address:
                self.customer_email_address = get_user_email(self._current_user)

        if not self.booking_code:
            self.booking_code = generate_booking_code()

        if self.booking_start_date and self.booking_end_date:
            self.booking_total_days = calculate_booking_total_days(
                self.booking_start_date,
                self.booking_end_date,
            )
        else:
            self.booking_total_days = 0

        if self.equipment_id and (
            self.booking_rental_price_per_day is None
            or self.booking_rental_price_per_day == Decimal("0.00")
        ):
            self.booking_rental_price_per_day = (
                self.equipment.rental_price_per_day or Decimal("0.00")
            )

        self.booking_total_amount = calculate_booking_total_amount(
            self.booking_total_days,
            self.booking_rental_price_per_day,
        )

        if self.payment_status != self.PaymentStatusChoices.PAID:
            self.payment_paid_at = None

        if not self.booking_slug:
            self.booking_slug = generate_unique_slug(
                model_class=EquipmentBooking,
                value=self.booking_code or self.customer_full_name or "booking",
                slug_field="booking_slug",
                instance_id=self.pk,
            )

        self.full_clean()
        super().save(*args, **kwargs)

    def _normalize_fields(self):
        self.booking_code = safe_upper(self.booking_code)
        self.customer_full_name = safe_title(self.customer_full_name)
        self.customer_phone_number = safe_strip(self.customer_phone_number)
        self.customer_email_address = safe_lower(self.customer_email_address)
        self.customer_full_address = safe_strip(self.customer_full_address)
        self.razorpay_order_id = safe_strip(self.razorpay_order_id)
        self.payment_transaction_id = safe_strip(self.payment_transaction_id)
        self.razorpay_signature = safe_strip(self.razorpay_signature)
        self.payment_method = safe_lower(self.payment_method)
        self.payment_failure_reason = safe_strip(self.payment_failure_reason)
        self.booking_notes = safe_strip(self.booking_notes)
        self.normalize_user_tracking_fields()


        