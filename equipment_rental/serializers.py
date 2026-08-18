from django.utils import timezone
from rest_framework import serializers

from .constants import (
    APPROVAL_STATUS_APPROVED,
    EQUIPMENT_STATUS_MAINTENANCE,
    PAYMENT_METHOD_CHOICES,
    PAYMENT_METHOD_UPI,
    PAYMENT_STATUS_PAID,
    PAYMENT_STATUS_PENDING,
    BOOKING_STATUS_PENDING,
    BOOKING_STATUS_CONFIRMED,
    BOOKING_STATUS_CANCELLED,
    BOOKING_STATUS_COMPLETED,
    MAX_BOOKING_DAYS,
)

from .models import Equipment, EquipmentBooking

from .utils import (
    build_absolute_media_url,
    safe_title,
    safe_strip,
    safe_upper,
    safe_lower,
)


class EquipmentSerializer(serializers.ModelSerializer):
    equipment_image_url = serializers.SerializerMethodField()
    identity_field_label = serializers.SerializerMethodField()
    equipment_status_display = serializers.CharField(
        source="get_equipment_status_display",
        read_only=True,
    )
    approval_status_display = serializers.CharField(
        source="get_approval_status_display",
        read_only=True,
    )
    equipment_category_display = serializers.CharField(
        source="get_equipment_category_display",
        read_only=True,
    )

    class Meta:
        model = Equipment
        fields = [
            "id",
            "equipment_name",
            "equipment_code",
            "equipment_slug",
            "equipment_category",
            "equipment_category_display",
            "equipment_brand",
            "owner_name",
            "equipment_identity_number",
            "identity_field_label",
            "equipment_description",
            "rental_price_per_day",
            "location_city",
            "equipment_image",
            "equipment_image_url",
            "equipment_status",
            "equipment_status_display",
            "approval_status",
            "approval_status_display",
            "approved_by_user",
            "approved_at",
            "is_active",
            "created_by_user",
            "updated_by_user",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "equipment_slug",
            "equipment_image_url",
            "identity_field_label",
            "equipment_status_display",
            "approval_status_display",
            "equipment_category_display",
            "approved_by_user",
            "approved_at",
            "created_by_user",
            "updated_by_user",
            "created_at",
            "updated_at",
        ]

    def get_equipment_image_url(self, obj):
        request = self.context.get("request")
        return build_absolute_media_url(request, obj.equipment_image)

    def get_identity_field_label(self, obj):
        return obj.get_identity_field_label()

    def validate_equipment_name(self, value):
        return safe_title(value)

    def validate_equipment_code(self, value):
        return safe_upper(value)

    def validate_equipment_brand(self, value):
        return safe_title(value)

    def validate_owner_name(self, value):
        return safe_title(value)

    def validate_equipment_identity_number(self, value):
        return safe_upper(value)

    def validate_equipment_description(self, value):
        return safe_strip(value)

    def validate_location_city(self, value):
        return safe_title(value)

    def update(self, instance, validated_data):
        request = self.context.get("request")

        validated_data.pop("equipment_code", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if request and request.user.is_authenticated:
            instance.set_user_context(request.user)

        instance.save()
        return instance

    def create(self, validated_data):
        request = self.context.get("request")
        equipment = Equipment(**validated_data)

        if request and request.user.is_authenticated:
            equipment.set_user_context(request.user)

        equipment.save()
        return equipment


class EquipmentPublicSerializer(serializers.ModelSerializer):
    equipment_image_url = serializers.SerializerMethodField()
    equipment_status_display = serializers.CharField(
        source="get_equipment_status_display",
        read_only=True,
    )

    class Meta:
        model = Equipment
        fields = [
            "id",
            "equipment_name",
            "equipment_code",
            "equipment_slug",
            "equipment_category",
            "equipment_brand",
            "equipment_description",
            "rental_price_per_day",
            "location_city",
            "equipment_image_url",
            "equipment_status",
            "equipment_status_display",
        ]

        read_only_fields = fields

    def get_equipment_image_url(self, obj):
        request = self.context.get("request")
        return build_absolute_media_url(request, obj.equipment_image)


class EquipmentBookingSerializer(serializers.ModelSerializer):
    equipment_data = EquipmentPublicSerializer(
        source="equipment",
        read_only=True,
    )

    farmer_username = serializers.CharField(
        source="farmer_user.username",
        read_only=True,
    )

    farmer_email = serializers.EmailField(
        source="farmer_user.email",
        read_only=True,
    )

    booking_status_display = serializers.CharField(
        source="get_booking_status_display",
        read_only=True,
    )

    payment_status_display = serializers.CharField(
        source="get_payment_status_display",
        read_only=True,
    )

    amount_in_paise = serializers.IntegerField(read_only=True)
    is_paid = serializers.BooleanField(read_only=True)
    is_active_booking = serializers.BooleanField(read_only=True)
    can_edit = serializers.SerializerMethodField()
    can_cancel = serializers.SerializerMethodField()

    class Meta:
        model = EquipmentBooking
        fields = [
            "id",
            "booking_code",
            "booking_slug",
            "farmer_user",
            "farmer_username",
            "farmer_email",
            "equipment",
            "equipment_data",
            "customer_full_name",
            "customer_phone_number",
            "customer_email_address",
            "customer_full_address",
            "booking_created_date",
            "booking_start_date",
            "booking_end_date",
            "booking_total_days",
            "booking_rental_price_per_day",
            "booking_total_amount",
            "amount_in_paise",
            "payment_status",
            "payment_status_display",
            "payment_method",
            "razorpay_order_id",
            "payment_transaction_id",
            "razorpay_signature",
            "payment_failure_reason",
            "payment_paid_at",
            "booking_status",
            "booking_status_display",
            "booking_notes",
            "is_paid",
            "is_active_booking",
            "can_edit",
            "can_cancel",
            "created_by_user",
            "updated_by_user",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "booking_code",
            "booking_slug",
            "farmer_user",
            "farmer_username",
            "farmer_email",
            "equipment_data",
            "booking_total_days",
            "booking_rental_price_per_day",
            "booking_total_amount",
            "amount_in_paise",
            "payment_status",
            "payment_status_display",
            "payment_method",
            "razorpay_order_id",
            "payment_transaction_id",
            "razorpay_signature",
            "payment_failure_reason",
            "payment_paid_at",
            "booking_status",
            "booking_status_display",
            "is_paid",
            "is_active_booking",
            "can_edit",
            "can_cancel",
            "created_by_user",
            "updated_by_user",
            "created_at",
            "updated_at",
        ]

    def get_can_edit(self, obj):
        return obj.can_edit()

    def get_can_cancel(self, obj):
        return obj.can_cancel()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["equipment"].queryset = Equipment.objects.filter(
            is_active=True,
            approval_status=APPROVAL_STATUS_APPROVED,
        ).exclude(
            equipment_status=EQUIPMENT_STATUS_MAINTENANCE,
        ).order_by("equipment_name")

        request = self.context.get("request")

        if request and request.user.is_authenticated:
            role = (
                getattr(request.user, "role", None)
                or getattr(request.user, "user_type", None)
                or ""
            ).lower()

            is_admin = (
                request.user.is_staff
                or request.user.is_superuser
                or role == "admin"
            )

            if not is_admin:
                admin_only_fields = [
                    "farmer_user",
                    "farmer_username",
                    "farmer_email",
                    "payment_method",
                    "razorpay_order_id",
                    "payment_transaction_id",
                    "razorpay_signature",
                    "payment_failure_reason",
                    "created_by_user",
                    "updated_by_user",
                ]

                for field_name in admin_only_fields:
                    self.fields.pop(field_name, None)

    def validate_customer_full_name(self, value):
        return safe_title(value)

    def validate_customer_phone_number(self, value):
        return safe_strip(value)

    def validate_customer_email_address(self, value):
        return safe_lower(value)

    def validate_customer_full_address(self, value):
        return safe_strip(value)

    def validate_booking_notes(self, value):
        return safe_strip(value)

    def validate(self, attrs):
        request = self.context.get("request")
        today = timezone.localdate()
        max_date = today + timezone.timedelta(days=MAX_BOOKING_DAYS)

        created_date = attrs.get(
            "booking_created_date",
            getattr(self.instance, "booking_created_date", today),
        )

        start_date = attrs.get(
            "booking_start_date",
            getattr(self.instance, "booking_start_date", None),
        )

        end_date = attrs.get(
            "booking_end_date",
            getattr(self.instance, "booking_end_date", None),
        )

        equipment = attrs.get(
            "equipment",
            getattr(self.instance, "equipment", None),
        )

        if created_date and created_date < today:
            raise serializers.ValidationError({
                "booking_created_date": "Booking created date cannot be in the past."
            })

        if created_date and created_date > max_date:
            raise serializers.ValidationError({
                "booking_created_date": f"Booking created date can be only within next {MAX_BOOKING_DAYS} days."
            })

        if start_date and start_date < today:
            raise serializers.ValidationError({
                "booking_start_date": "Booking start date cannot be in the past."
            })

        if start_date and start_date > max_date:
            raise serializers.ValidationError({
                "booking_start_date": f"Booking start date can be only within next {MAX_BOOKING_DAYS} days."
            })

        if end_date and end_date < today:
            raise serializers.ValidationError({
                "booking_end_date": "Booking end date cannot be in the past."
            })

        if end_date and end_date > max_date:
            raise serializers.ValidationError({
                "booking_end_date": f"Booking end date can be only within next {MAX_BOOKING_DAYS} days."
            })

        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError({
                "booking_end_date": "Booking end date cannot be earlier than booking start date."
            })

        if equipment and start_date and end_date:
            overlapping_qs = EquipmentBooking.objects.filter(
                equipment=equipment,
                booking_status__in=[
                    BOOKING_STATUS_PENDING,
                    BOOKING_STATUS_CONFIRMED,
                ],
                booking_start_date__lte=end_date,
                booking_end_date__gte=start_date,
            )

            if self.instance and self.instance.pk:
                overlapping_qs = overlapping_qs.exclude(pk=self.instance.pk)

            overlapping_booking = overlapping_qs.order_by("-booking_end_date").first()

            if overlapping_booking:
                next_available_date = (
                    overlapping_booking.booking_end_date
                    + timezone.timedelta(days=1)
                )

                raise serializers.ValidationError({
                    "equipment": (
                        f"This equipment is already booked for selected dates. "
                        f"You can book it from {next_available_date}."
                    )
                })

        if self.instance and self.instance.pk:
            if self.instance.payment_status == PAYMENT_STATUS_PAID:
                raise serializers.ValidationError("Paid booking cannot be edited.")

            if self.instance.booking_status in [
                BOOKING_STATUS_CANCELLED,
                BOOKING_STATUS_COMPLETED,
            ]:
                raise serializers.ValidationError(
                    "Cancelled or completed booking cannot be edited."
                )

        if request and request.user.is_authenticated:
            attrs["_request_user"] = request.user

        return attrs

    def create(self, validated_data):
        request_user = validated_data.pop("_request_user", None)

        booking = EquipmentBooking(**validated_data)

        if request_user and request_user.is_authenticated:
            booking.set_user_context(request_user)

            if not booking.farmer_user_id:
                booking.farmer_user = request_user

        booking.payment_status = PAYMENT_STATUS_PENDING
        booking.booking_status = BOOKING_STATUS_PENDING
        booking.save()

        return booking

    def update(self, instance, validated_data):
        request_user = validated_data.pop("_request_user", None)

        protected_fields = [
            "payment_status",
            "booking_status",
            "razorpay_order_id",
            "payment_transaction_id",
            "razorpay_signature",
            "payment_method",
            "payment_paid_at",
            "payment_failure_reason",
            "booking_code",
            "booking_slug",
            "farmer_user",
        ]

        for field in protected_fields:
            validated_data.pop(field, None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if request_user and request_user.is_authenticated:
            instance.set_user_context(request_user)

        instance.save()
        return instance


class RazorpayOrderSerializer(serializers.Serializer):
    booking_code = serializers.CharField(read_only=True)
    razorpay_key_id = serializers.CharField(read_only=True)
    razorpay_order_id = serializers.CharField(read_only=True)
    amount = serializers.IntegerField(read_only=True)
    currency = serializers.CharField(read_only=True)
    customer_name = serializers.CharField(read_only=True)
    customer_email = serializers.EmailField(read_only=True, allow_null=True)
    customer_phone = serializers.CharField(read_only=True)


class RazorpayPaymentVerifySerializer(serializers.Serializer):
    razorpay_order_id = serializers.CharField(required=True)
    razorpay_payment_id = serializers.CharField(required=True)
    razorpay_signature = serializers.CharField(required=True)

    payment_method = serializers.ChoiceField(
        choices=PAYMENT_METHOD_CHOICES,
        default=PAYMENT_METHOD_UPI,
        required=False,
    )

    def validate_razorpay_order_id(self, value):
        value = safe_strip(value)

        if not value or not value.startswith("order_"):
            raise serializers.ValidationError("Invalid Razorpay order id.")

        return value

    def validate_razorpay_payment_id(self, value):
        value = safe_strip(value)

        if not value or not value.startswith("pay_"):
            raise serializers.ValidationError("Invalid Razorpay payment id.")

        return value

    def validate_razorpay_signature(self, value):
        value = safe_strip(value)

        if not value:
            raise serializers.ValidationError("Razorpay signature is required.")

        return value