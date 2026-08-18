from datetime import timedelta
from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .constants import (
    APPROVAL_STATUS_APPROVED,
    EQUIPMENT_STATUS_MAINTENANCE,
    PAYMENT_STATUS_PENDING,
    BOOKING_STATUS_PENDING,
    MAX_BOOKING_DAYS,
    MINIMUM_RENTAL_PRICE,
)

from .models import Equipment, EquipmentBooking

from .utils import (
    safe_title,
    safe_strip,
    safe_upper,
    safe_lower,
)


FORM_CONTROL = "form-control"
FORM_SELECT = "form-select"


class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = [
            "equipment_name",
            "equipment_code",
            "equipment_category",
            "equipment_brand",
            "owner_name",
            "equipment_identity_number",
            "equipment_description",
            "rental_price_per_day",
            "location_city",
            "equipment_image",
            "equipment_status",
            "approval_status",
            "is_active",
        ]

        widgets = {
            "equipment_name": forms.TextInput(attrs={
                "class": FORM_CONTROL,
                "placeholder": "Enter equipment name",
                "autocomplete": "off",
            }),
            "equipment_code": forms.TextInput(attrs={
                "class": FORM_CONTROL,
                "placeholder": "Auto generated if empty",
                "autocomplete": "off",
            }),
            "equipment_category": forms.Select(attrs={
                "class": FORM_SELECT,
            }),
            "equipment_brand": forms.TextInput(attrs={
                "class": FORM_CONTROL,
                "placeholder": "Enter brand name",
                "autocomplete": "off",
            }),
            "owner_name": forms.TextInput(attrs={
                "class": FORM_CONTROL,
                "placeholder": "Enter owner name",
                "autocomplete": "off",
            }),
            "equipment_identity_number": forms.TextInput(attrs={
                "class": FORM_CONTROL,
                "placeholder": "Engine / Vehicle / Chassis / Serial number",
                "autocomplete": "off",
            }),
            "equipment_description": forms.Textarea(attrs={
                "class": FORM_CONTROL,
                "rows": 4,
                "placeholder": "Enter equipment description",
            }),
            "rental_price_per_day": forms.NumberInput(attrs={
                "class": FORM_CONTROL,
                "min": str(MINIMUM_RENTAL_PRICE),
                "step": "0.01",
                "placeholder": "Enter rental price per day",
            }),
            "location_city": forms.TextInput(attrs={
                "class": FORM_CONTROL,
                "placeholder": "Enter city",
                "autocomplete": "off",
            }),
            "equipment_image": forms.ClearableFileInput(attrs={
                "class": FORM_CONTROL,
                "accept": "image/jpeg,image/jpg,image/png,image/webp",
            }),
            "equipment_status": forms.Select(attrs={
                "class": FORM_SELECT,
            }),
            "approval_status": forms.Select(attrs={
                "class": FORM_SELECT,
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            self.fields["equipment_code"].disabled = True
            self.fields["equipment_code"].help_text = "Equipment code cannot be changed after creation."

        for field in self.fields.values():
            field.error_messages.update({
                "required": f"{field.label} is required.",
                "invalid": f"Enter a valid {field.label}.",
            })

    def clean_equipment_name(self):
        return safe_title(self.cleaned_data.get("equipment_name"))

    def clean_equipment_code(self):
        if self.instance and self.instance.pk:
            return self.instance.equipment_code

        return safe_upper(self.cleaned_data.get("equipment_code"))

    def clean_equipment_brand(self):
        return safe_title(self.cleaned_data.get("equipment_brand"))

    def clean_owner_name(self):
        return safe_title(self.cleaned_data.get("owner_name"))

    def clean_equipment_identity_number(self):
        return safe_upper(self.cleaned_data.get("equipment_identity_number"))

    def clean_equipment_description(self):
        return safe_strip(self.cleaned_data.get("equipment_description"))

    def clean_location_city(self):
        return safe_title(self.cleaned_data.get("location_city"))

    def clean_rental_price_per_day(self):
        price = self.cleaned_data.get("rental_price_per_day")

        if price is None:
            raise ValidationError("Rental price per day is required.")

        if price < Decimal(MINIMUM_RENTAL_PRICE):
            raise ValidationError(
                f"Rental price per day must be at least {MINIMUM_RENTAL_PRICE} Rs."
            )

        return price

    def clean_equipment_image(self):
        image = self.cleaned_data.get("equipment_image")

        if image and hasattr(image, "size"):
            max_size = 2 * 1024 * 1024

            if image.size > max_size:
                raise ValidationError("Image size must be less than 2 MB.")

        return image

    def save(self, commit=True):
        equipment = super().save(commit=False)

        if self.user and getattr(self.user, "is_authenticated", False):
            equipment.set_user_context(self.user)

        if commit:
            equipment.save()
            self.save_m2m()

        return equipment


class EquipmentBookingForm(forms.ModelForm):
    class Meta:
        model = EquipmentBooking
        fields = [
            "equipment",
            "customer_full_name",
            "customer_phone_number",
            "customer_email_address",
            "customer_full_address",
            "booking_created_date",
            "booking_start_date",
            "booking_end_date",
            "booking_notes",
        ]

        widgets = {
            "equipment": forms.Select(attrs={
                "class": FORM_SELECT,
            }),
            "customer_full_name": forms.TextInput(attrs={
                "class": FORM_CONTROL,
                "placeholder": "Enter full name",
                "autocomplete": "name",
            }),
            "customer_phone_number": forms.TextInput(attrs={
                "class": FORM_CONTROL,
                "placeholder": "Enter phone number",
                "autocomplete": "tel",
            }),
            "customer_email_address": forms.EmailInput(attrs={
                "class": FORM_CONTROL,
                "placeholder": "Enter email address",
                "autocomplete": "email",
            }),
            "customer_full_address": forms.Textarea(attrs={
                "class": FORM_CONTROL,
                "rows": 3,
                "placeholder": "Enter full address",
            }),
            "booking_created_date": forms.DateInput(attrs={
                "class": FORM_CONTROL,
                "type": "date",
            }),
            "booking_start_date": forms.DateInput(attrs={
                "class": FORM_CONTROL,
                "type": "date",
            }),
            "booking_end_date": forms.DateInput(attrs={
                "class": FORM_CONTROL,
                "type": "date",
            }),
            "booking_notes": forms.Textarea(attrs={
                "class": FORM_CONTROL,
                "rows": 3,
                "placeholder": "Any special note",
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        today = timezone.localdate()
        max_date = today + timedelta(days=MAX_BOOKING_DAYS)

        self.fields["equipment"].queryset = Equipment.objects.filter(
            is_active=True,
            approval_status=Equipment.EquipmentApprovalStatusChoices.APPROVED,
        ).exclude(
            equipment_status=Equipment.EquipmentStatusChoices.MAINTENANCE,
        ).order_by("equipment_name")

        self.fields["booking_created_date"].initial = today

        for field_name in [
            "booking_created_date",
            "booking_start_date",
            "booking_end_date",
        ]:
            self.fields[field_name].widget.attrs["min"] = today.isoformat()
            self.fields[field_name].widget.attrs["max"] = max_date.isoformat()

        if self.instance and self.instance.pk:
            self.fields["equipment"].disabled = True

            if self.instance.payment_status == EquipmentBooking.PaymentStatusChoices.PAID:
                for field in self.fields.values():
                    field.disabled = True

        for field in self.fields.values():
            field.error_messages.update({
                "required": f"{field.label} is required.",
                "invalid": f"Enter a valid {field.label}.",
            })

    def clean_customer_full_name(self):
        return safe_title(self.cleaned_data.get("customer_full_name"))

    def clean_customer_phone_number(self):
        return safe_strip(self.cleaned_data.get("customer_phone_number"))

    def clean_customer_email_address(self):
        return safe_lower(self.cleaned_data.get("customer_email_address"))

    def clean_customer_full_address(self):
        return safe_strip(self.cleaned_data.get("customer_full_address"))

    def clean_booking_notes(self):
        return safe_strip(self.cleaned_data.get("booking_notes"))

    def clean_booking_created_date(self):
        date_value = self.cleaned_data.get("booking_created_date")
        today = timezone.localdate()
        max_date = today + timedelta(days=MAX_BOOKING_DAYS)

        if date_value:
            if date_value < today:
                raise ValidationError("Booking created date cannot be in the past.")

            if date_value > max_date:
                raise ValidationError(
                    f"Booking created date can be only within next {MAX_BOOKING_DAYS} days."
                )

        return date_value

    def clean_booking_start_date(self):
        date_value = self.cleaned_data.get("booking_start_date")
        today = timezone.localdate()
        max_date = today + timedelta(days=MAX_BOOKING_DAYS)

        if date_value:
            if date_value < today:
                raise ValidationError("Booking start date cannot be in the past.")

            if date_value > max_date:
                raise ValidationError(
                    f"Booking start date can be only within next {MAX_BOOKING_DAYS} days."
                )

        return date_value

    def clean_booking_end_date(self):
        date_value = self.cleaned_data.get("booking_end_date")
        today = timezone.localdate()
        max_date = today + timedelta(days=MAX_BOOKING_DAYS)

        if date_value:
            if date_value < today:
                raise ValidationError("Booking end date cannot be in the past.")

            if date_value > max_date:
                raise ValidationError(
                    f"Booking end date can be only within next {MAX_BOOKING_DAYS} days."
                )

        return date_value

    def clean(self):
        cleaned_data = super().clean()

        equipment = cleaned_data.get("equipment")
        start_date = cleaned_data.get("booking_start_date")
        end_date = cleaned_data.get("booking_end_date")

        if start_date and end_date and end_date < start_date:
            self.add_error(
                "booking_end_date",
                "Booking end date cannot be earlier than booking start date.",
            )

        if equipment and start_date and end_date:
            overlapping_qs = EquipmentBooking.objects.filter(
                equipment=equipment,
                booking_status__in=[
                    EquipmentBooking.BookingStatusChoices.PENDING,
                    EquipmentBooking.BookingStatusChoices.CONFIRMED,
                ],
                booking_start_date__lte=end_date,
                booking_end_date__gte=start_date,
            )

            if self.instance and self.instance.pk:
                overlapping_qs = overlapping_qs.exclude(pk=self.instance.pk)

            overlapping_booking = overlapping_qs.order_by("-booking_end_date").first()

            if overlapping_booking:
                next_available_date = overlapping_booking.booking_end_date + timedelta(days=1)

                self.add_error(
                    "equipment",
                    f"This equipment is already booked for selected dates. "
                    f"You can book it from {next_available_date}.",
                )

        return cleaned_data

    def save(self, commit=True):
        booking = super().save(commit=False)

        if self.user and getattr(self.user, "is_authenticated", False):
            booking.set_user_context(self.user)

            if not booking.farmer_user_id:
                booking.farmer_user = self.user

        if not booking.booking_created_date:
            booking.booking_created_date = timezone.localdate()

        if not booking.pk:
            booking.payment_status = PAYMENT_STATUS_PENDING
            booking.booking_status = BOOKING_STATUS_PENDING

        if commit:
            booking.save()
            self.save_m2m()

        return booking