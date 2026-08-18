import random
import string
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify

from .constants import (
    BOOKING_CODE_PREFIX,
    EQUIPMENT_CODE_PREFIX,
)


def generate_random_string(length=6):
    return "".join(
        random.choices(
            string.ascii_uppercase + string.digits,
            k=length,
        )
    )


def generate_equipment_code():
    from .models import Equipment

    last_equipment = (
        Equipment.objects.only("id", "equipment_code")
        .order_by("-id")
        .first()
    )

    next_id = last_equipment.id + 1 if last_equipment else 1

    while True:
        equipment_code = f"{EQUIPMENT_CODE_PREFIX}{next_id:04d}"

        if not Equipment.objects.filter(equipment_code=equipment_code).exists():
            return equipment_code

        next_id += 1


def generate_booking_code():
    from .models import EquipmentBooking

    last_booking = (
        EquipmentBooking.objects.only("id", "booking_code")
        .order_by("-id")
        .first()
    )

    next_id = last_booking.id + 1 if last_booking else 1

    while True:
        booking_code = f"{BOOKING_CODE_PREFIX}{next_id:04d}"

        if not EquipmentBooking.objects.filter(booking_code=booking_code).exists():
            return booking_code

        next_id += 1


def generate_unique_slug(model_class, value, slug_field="slug", instance_id=None):
    base_slug = slugify(value or "")

    if not base_slug:
        base_slug = generate_random_string(8).lower()

    slug = base_slug
    counter = 1

    while True:
        queryset = model_class.objects.filter(**{slug_field: slug})

        if instance_id:
            queryset = queryset.exclude(pk=instance_id)

        if not queryset.exists():
            return slug

        slug = f"{base_slug}-{counter}"
        counter += 1


def to_decimal(value, default="0.00"):
    try:
        return Decimal(str(value if value is not None else default))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(default)


def calculate_booking_total_days(start_date, end_date):
    if not start_date or not end_date:
        return 0

    total_days = (end_date - start_date).days + 1

    if total_days < 1:
        return 0

    return total_days


def calculate_booking_total_amount(total_days, rental_price_per_day):
    try:
        total_days = int(total_days or 0)
    except (TypeError, ValueError):
        total_days = 0

    rental_price_per_day = to_decimal(rental_price_per_day)

    total_amount = Decimal(total_days) * rental_price_per_day

    return total_amount.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def convert_rupees_to_paise(amount):
    amount = to_decimal(amount)

    return int(
        (amount * Decimal("100")).quantize(
            Decimal("1"),
            rounding=ROUND_HALF_UP,
        )
    )


def convert_paise_to_rupees(amount):
    amount = to_decimal(amount, default="0")

    return (amount / Decimal("100")).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def get_client_ip_address(request):
    if not request:
        return ""

    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()

    return request.META.get("REMOTE_ADDR", "")


def get_user_full_name(user):
    if not user:
        return ""

    if hasattr(user, "get_full_name"):
        full_name = user.get_full_name()

        if full_name and full_name.strip():
            return full_name.strip().title()

    username = getattr(user, "username", "")

    return str(username).strip().title()


def get_user_email(user):
    if not user:
        return ""

    email = getattr(user, "email", "")

    return str(email).strip().lower()


def normalize_phone_number(phone_number):
    if not phone_number:
        return ""

    return str(phone_number).strip()


def build_absolute_media_url(request, file_field):
    if not file_field:
        return None

    try:
        url = file_field.url
    except Exception:
        return None

    if request:
        return request.build_absolute_uri(url)

    domain = getattr(settings, "SITE_DOMAIN", "")

    if domain:
        return f"{domain}{url}"

    return url


def get_today():
    return timezone.localdate()


def format_decimal_amount(amount):
    amount = to_decimal(amount)

    return f"{amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):.2f}"


def booking_is_expired(booking):
    if not booking:
        return False

    if not getattr(booking, "booking_end_date", None):
        return False

    return booking.booking_end_date < timezone.localdate()


def booking_is_active(booking):
    if not booking:
        return False

    if (
        not getattr(booking, "booking_start_date", None)
        or not getattr(booking, "booking_end_date", None)
    ):
        return False

    today = timezone.localdate()

    return booking.booking_start_date <= today <= booking.booking_end_date


def equipment_is_available(equipment):
    if not equipment:
        return False

    return (
        getattr(equipment, "is_active", False)
        and str(getattr(equipment, "equipment_status", "")).lower() == "available"
        and str(getattr(equipment, "approval_status", "")).lower() == "approved"
    )


def generate_razorpay_notes(booking):
    equipment = getattr(booking, "equipment", None)

    return {
        "booking_code": getattr(booking, "booking_code", ""),
        "equipment_code": getattr(equipment, "equipment_code", ""),
        "equipment_name": getattr(equipment, "equipment_name", ""),
        "farmer_id": getattr(booking, "farmer_user_id", ""),
        "customer_name": getattr(booking, "customer_full_name", ""),
        "customer_phone": getattr(booking, "customer_phone_number", ""),
        "customer_email": getattr(booking, "customer_email_address", ""),
    }


def safe_strip(value):
    if value is None:
        return None

    return str(value).strip()


def safe_lower(value):
    if value is None:
        return None

    return str(value).strip().lower()


def safe_upper(value):
    if value is None:
        return None

    return str(value).strip().upper()


def safe_title(value):
    if value is None:
        return None

    return str(value).strip().title()

