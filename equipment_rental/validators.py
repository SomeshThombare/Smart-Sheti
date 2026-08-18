import os
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _


ALLOWED_IMAGE_EXTENSIONS = [
    "jpg",
    "jpeg",
    "png",
    "webp",
]

MAX_IMAGE_SIZE_MB = 5
MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024

MINIMUM_RENTAL_PRICE = Decimal("100.00")


def validate_image_extension(value):
    validator = FileExtensionValidator(
        allowed_extensions=ALLOWED_IMAGE_EXTENSIONS,
        message=(
            f"Only {', '.join(ALLOWED_IMAGE_EXTENSIONS).upper()} image files are allowed."
        ),
    )

    validator(value)


def validate_image_size(value):
    if not value:
        return

    file_size = value.size

    if file_size > MAX_IMAGE_SIZE_BYTES:
        raise ValidationError(
            _(
                f"Image size must be less than {MAX_IMAGE_SIZE_MB} MB."
            )
        )


def validate_positive_amount(value):
    if value is None:
        raise ValidationError(_("Amount is required."))

    try:
        decimal_value = Decimal(value)
    except Exception:
        raise ValidationError(_("Enter a valid amount."))

    if decimal_value < 0:
        raise ValidationError(_("Amount cannot be negative."))


def validate_minimum_rental_price(value):
    if value is None:
        return

    try:
        decimal_value = Decimal(value)
    except Exception:
        raise ValidationError(_("Enter a valid rental price."))

    if decimal_value < MINIMUM_RENTAL_PRICE:
        raise ValidationError(
            _(
                f"Minimum rental price must be at least ₹{MINIMUM_RENTAL_PRICE} per day."
            )
        )


def validate_razorpay_order_id(value):
    if not value:
        return

    value = str(value).strip()

    if not value.startswith("order_"):
        raise ValidationError(
            _("Invalid Razorpay order id.")
        )

    if len(value) < 10:
        raise ValidationError(
            _("Razorpay order id is too short.")
        )


def validate_razorpay_payment_id(value):
    if not value:
        return

    value = str(value).strip()

    if not value.startswith("pay_"):
        raise ValidationError(
            _("Invalid Razorpay payment id.")
        )

    if len(value) < 10:
        raise ValidationError(
            _("Razorpay payment id is too short.")
        )


def validate_not_future_date(value):
    from django.utils import timezone

    if not value:
        return

    today = timezone.localdate()

    if value > today:
        raise ValidationError(
            _("Future date is not allowed.")
        )


def validate_phone_number(value):
    if not value:
        raise ValidationError(_("Phone number is required."))

    value = str(value).strip()

    allowed_chars = set("0123456789+- ")

    if not all(char in allowed_chars for char in value):
        raise ValidationError(
            _("Phone number contains invalid characters.")
        )

    digits = "".join(filter(str.isdigit, value))

    if len(digits) < 10 or len(digits) > 15:
        raise ValidationError(
            _("Phone number must contain 10 to 15 digits.")
        )


def validate_booking_days(value):
    if value is None:
        return

    if value <= 0:
        raise ValidationError(
            _("Booking days must be greater than zero.")
        )

    if value > 365:
        raise ValidationError(
            _("Booking duration cannot exceed 365 days.")
        )


def validate_file_name_length(value):
    if not value:
        return

    filename = os.path.basename(value.name)

    if len(filename) > 150:
        raise ValidationError(
            _("File name is too long.")
        )


def validate_text_no_script(value):
    if not value:
        return

    lower_value = str(value).lower()

    blocked_patterns = [
        "<script",
        "</script>",
        "javascript:",
        "onerror=",
        "onclick=",
    ]

    for pattern in blocked_patterns:
        if pattern in lower_value:
            raise ValidationError(
                _("Invalid text content detected.")
            )