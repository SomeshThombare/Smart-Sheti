# =========================================================
# IMPORTS
# =========================================================
from django.conf import settings
from django.contrib.auth import authenticate
from django.db import transaction

from rest_framework import serializers

from .models import (
    CustomUser,
    FarmerProfile,
    AdminProfile,
    OTPVerification,
)

from .utils import (
    normalize_username,
    normalize_email,
    normalize_mobile_number,
)

# =========================================================
# Common Helper Functions
# =========================================================
def normalize_email(value):
    if not value:
        return ""
    return str(value).strip().lower()


def normalize_username(value):
    if not value:
        return ""
    return str(value).strip().lower()


def normalize_mobile_number(value):
    if not value:
        return ""

    value = str(value).strip().replace(" ", "").replace("-", "")

    if value.startswith("+91"):
        value = value[3:]
    elif value.startswith("91") and len(value) == 12:
        value = value[2:]

    return value


# =========================================================
# OTP Serializer
# =========================================================
class SendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    mobile_number = serializers.CharField(max_length=20, required=True)

    def validate_email(self, value):
        value = normalize_email(value)

        if not value:
            raise serializers.ValidationError("Email is required.")

        return value

    def validate_mobile_number(self, value):
        value = normalize_mobile_number(value)

        if not value:
            raise serializers.ValidationError("Mobile number is required.")

        if len(value) != 10 or not value.isdigit():
            raise serializers.ValidationError(
                "Enter a valid 10-digit Indian mobile number."
            )

        if value[0] not in "6789":
            raise serializers.ValidationError(
                "Enter a valid 10-digit Indian mobile number."
            )

        return value
    
    
    
# =========================================================
# Verify OTP Serializer
# =========================================================

from rest_framework import serializers


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False, allow_blank=True)
    mobile_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    email_otp = serializers.CharField(max_length=6, required=False, allow_blank=True)
    mobile_otp = serializers.CharField(max_length=6, required=False, allow_blank=True)

    def validate_email(self, value):
        if not value:
            return ""
        return normalize_email(value)

    def validate_mobile_number(self, value):
        if not value:
            return ""

        value = normalize_mobile_number(value)

        if len(value) != 10 or not value.isdigit() or value[0] not in "6789":
            raise serializers.ValidationError(
                "Enter a valid 10-digit Indian mobile number."
            )

        return value

    def validate_email_otp(self, value):
        if not value:
            return ""

        value = str(value).strip()

        if len(value) != 6 or not value.isdigit():
            raise serializers.ValidationError(
                "Email OTP must be exactly 6 digits."
            )

        return value

    def validate_mobile_otp(self, value):
        if not value:
            return ""

        value = str(value).strip()

        if len(value) != 6 or not value.isdigit():
            raise serializers.ValidationError(
                "Mobile OTP must be exactly 6 digits."
            )

        return value

    def validate(self, attrs):
        email = attrs.get("email", "")
        mobile_number = attrs.get("mobile_number", "")
        email_otp = attrs.get("email_otp", "")
        mobile_otp = attrs.get("mobile_otp", "")

        pending_profile_update = self.context.get("pending_profile_update")

        # =====================================================
        # PROFILE UPDATE FLOW
        # =====================================================
        if pending_profile_update:
            email_changed = pending_profile_update.get("email_changed", False)
            mobile_changed = pending_profile_update.get("mobile_changed", False)

            if email_changed and not email_otp:
                raise serializers.ValidationError({
                    "email_otp": ["Email OTP is required."]
                })

            if mobile_changed and not mobile_otp:
                raise serializers.ValidationError({
                    "mobile_otp": ["Mobile OTP is required."]
                })

            return attrs

        # =====================================================
        # NORMAL OTP FLOW
        # =====================================================
        if not email and not mobile_number:
            raise serializers.ValidationError({
                "contact": ["Email or mobile number is required."]
            })

        if email and not email_otp:
            raise serializers.ValidationError({
                "email_otp": ["Email OTP is required."]
            })

        if mobile_number and not mobile_otp:
            raise serializers.ValidationError({
                "mobile_otp": ["Mobile OTP is required."]
            })

        return attrs
    
# =========================================================
# Farmer Profile Serializer
# =========================================================
class FarmerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmerProfile
        fields = [
            "gender",
            "village",
            "taluka",
            "district",
            "state",
            "pincode",
            "full_address",
        ]

    def validate_village(self, value):
        return value.strip().title()

    def validate_taluka(self, value):
        return value.strip().title()

    def validate_district(self, value):
        return value.strip().title()

    def validate_state(self, value):
        return value.strip().title()

    def validate_pincode(self, value):
        value = str(value).strip()

        if len(value) != 6 or not value.isdigit():
            raise serializers.ValidationError("Enter a valid 6-digit pincode.")

        return value

    def validate_full_address(self, value):
        return value.strip()


# =========================================================
# Admin Profile Serializer
# =========================================================
class AdminProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminProfile
        fields = [
            "admin_secret_code",
        ]
        extra_kwargs = {
            "admin_secret_code": {"write_only": True}  # 🔐 Hide in response
        }

    def validate_admin_secret_code(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError("Admin secret code is required.")

        return value
    
    



# =========================================================
# Farmer Registration Serializer
# =========================================================
class FarmerRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    gender = serializers.ChoiceField(
        choices=FarmerProfile.GenderChoices.choices,
        write_only=True,
    )
    village = serializers.CharField(write_only=True)
    taluka = serializers.CharField(write_only=True)
    district = serializers.CharField(write_only=True)
    state = serializers.CharField(write_only=True)
    pincode = serializers.CharField(write_only=True)
    full_address = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = [
            "first_name",
            "last_name",
            "username",
            "email",
            "country_code",
            "mobile_number",
            "language_preference",
            "password",
            "gender",
            "village",
            "taluka",
            "district",
            "state",
            "pincode",
            "full_address",
        ]

    def validate_first_name(self, value):
        value = str(value).strip().title()
        if not value:
            raise serializers.ValidationError("First name is required.")
        return value

    def validate_last_name(self, value):
        value = str(value).strip().title()
        if not value:
            raise serializers.ValidationError("Last name is required.")
        return value

    def validate_username(self, value):
        value = normalize_username(value)
        if not value:
            raise serializers.ValidationError("Username is required.")

        if CustomUser.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("This username is already taken.")

        return value

    def validate_email(self, value):
        value = normalize_email(value)
        if not value:
            raise serializers.ValidationError("Email is required.")

        if CustomUser.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("This email is already registered.")

        return value

    def validate_country_code(self, value):
        value = str(value).strip()
        if value != "+91":
            raise serializers.ValidationError("Only +91 country code is allowed.")
        return value

    def validate_mobile_number(self, value):
        value = normalize_mobile_number(value)

        if not value:
            raise serializers.ValidationError("Mobile number is required.")

        if len(value) != 10 or not value.isdigit():
            raise serializers.ValidationError("Enter a valid 10-digit Indian mobile number.")

        if value[0] not in "6789":
            raise serializers.ValidationError("Enter a valid 10-digit Indian mobile number.")

        if CustomUser.objects.filter(mobile_number=value).exists():
            raise serializers.ValidationError("This mobile number is already registered.")

        return value

    def validate_village(self, value):
        value = str(value).strip().title()
        if not value:
            raise serializers.ValidationError("Village is required.")
        return value

    def validate_taluka(self, value):
        value = str(value).strip().title()
        if not value:
            raise serializers.ValidationError("Taluka is required.")
        return value

    def validate_district(self, value):
        value = str(value).strip().title()
        if not value:
            raise serializers.ValidationError("District is required.")
        return value

    def validate_state(self, value):
        value = str(value).strip().title()
        if not value:
            raise serializers.ValidationError("State is required.")
        return value

    def validate_pincode(self, value):
        value = str(value).strip()

        if len(value) != 6 or not value.isdigit():
            raise serializers.ValidationError("Enter a valid 6-digit pincode.")

        return value

    def validate_full_address(self, value):
        value = str(value).strip()
        if not value:
            raise serializers.ValidationError("Full address is required.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        gender = validated_data.pop("gender")
        village = validated_data.pop("village")
        taluka = validated_data.pop("taluka")
        district = validated_data.pop("district")
        state = validated_data.pop("state")
        pincode = validated_data.pop("pincode")
        full_address = validated_data.pop("full_address")
        password = validated_data.pop("password")

        user = CustomUser(**validated_data)
        user.role = CustomUser.RoleChoices.FARMER
        user.is_staff = False
        user.is_superuser = False
        user.is_active = False
        user.set_password(password)
        user.save()

        FarmerProfile.objects.update_or_create(
            user=user,
            defaults={
                "gender": gender,
                "village": village,
                "taluka": taluka,
                "district": district,
                "state": state,
                "pincode": pincode,
                "full_address": full_address,
            },
        )

        return user
    
    


# =========================================================
# Admin Registration Serializer
# =========================================================
class AdminRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    admin_secret_code = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = [
            "first_name",
            "last_name",
            "username",
            "email",
            "country_code",
            "mobile_number",
            "language_preference",
            "admin_secret_code",
            "password",
        ]

    def validate_first_name(self, value):
        value = str(value).strip().title()
        if not value:
            raise serializers.ValidationError("First name is required.")
        return value

    def validate_last_name(self, value):
        value = str(value).strip().title()
        if not value:
            raise serializers.ValidationError("Last name is required.")
        return value

    def validate_username(self, value):
        value = normalize_username(value)

        if not value:
            raise serializers.ValidationError("Username is required.")

        if CustomUser.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("This username is already taken.")

        return value

    def validate_email(self, value):
        value = normalize_email(value)

        if not value:
            raise serializers.ValidationError("Email is required.")

        if CustomUser.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("This email is already registered.")

        return value

    def validate_country_code(self, value):
        value = str(value).strip()

        if value != "+91":
            raise serializers.ValidationError("Only +91 country code is allowed.")

        return value

    def validate_mobile_number(self, value):
        value = normalize_mobile_number(value)

        if not value:
            raise serializers.ValidationError("Mobile number is required.")

        if len(value) != 10 or not value.isdigit():
            raise serializers.ValidationError("Enter a valid 10-digit Indian mobile number.")

        if value[0] not in "6789":
            raise serializers.ValidationError("Enter a valid 10-digit Indian mobile number.")

        if CustomUser.objects.filter(mobile_number=value).exists():
            raise serializers.ValidationError("This mobile number is already registered.")

        return value

    def validate_admin_secret_code(self, value):
        value = str(value).strip()
        expected_code = getattr(settings, "ADMIN_SECRET_CODE", "")

        if not expected_code:
            raise serializers.ValidationError("Admin secret code is not configured.")

        if value != expected_code:
            raise serializers.ValidationError("Invalid admin secret code.")

        return value

    @transaction.atomic
    def create(self, validated_data):
        admin_secret_code = validated_data.pop("admin_secret_code")
        password = validated_data.pop("password")

        user = CustomUser(**validated_data)
        user.role = CustomUser.RoleChoices.ADMIN
        user.is_staff = True
        user.is_superuser = False
        user.is_active = False
        user.set_password(password)
        user.save()

        AdminProfile.objects.update_or_create(
            user=user,
            defaults={
                "admin_secret_code": admin_secret_code,
            },
        )

        return user
    
    



# =========================================================
# Full Farmer Profile Serializer
# =========================================================
class FarmerFullProfileSerializer(serializers.ModelSerializer):
    farmer_profile = FarmerProfileSerializer(read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "first_name",
            "last_name",
            "username",
            "email",
            "country_code",
            "mobile_number",
            "language_preference",
            "role",
            "is_active",
            "date_joined",
            "farmer_profile",
        ]




# =========================================================
# Full Admin Profile Serializer
# =========================================================
class AdminFullProfileSerializer(serializers.ModelSerializer):
    admin_profile = AdminProfileSerializer(read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "first_name",
            "last_name",
            "username",
            "email",
            "country_code",
            "mobile_number",
            "language_preference",
            "role",
            "is_active",
            "date_joined",
            "admin_profile",
        ]
        read_only_fields = [
            "id",
            "role",
            "is_active",
            "date_joined",
            "admin_profile",
        ]



# =========================================================
# Login Serializer
# =========================================================
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        request = self.context.get("request")

        username = attrs.get("username")
        password = attrs.get("password")

        if not username or not password:
            raise serializers.ValidationError(
                "Username and password are required."
            )

        # Normalize input (optional but recommended)
        username = username.strip()

        user = authenticate(
            request=request,
            username=username,
            password=password,
        )

        if user is None:
            raise serializers.ValidationError({
                "detail": ["Invalid username/email/mobile number or password."]
            })

        # Check if user is active
        if not user.is_active:
            raise serializers.ValidationError({
                "detail": ["User account is inactive. Please verify OTP first."]
            })

        attrs["user"] = user
        return attrs
    


# =========================================================
# User Update Serializer
# =========================================================
class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            "first_name",
            "last_name",
            "email",
            "country_code",
            "mobile_number",
            "language_preference",
        ]

    def validate_first_name(self, value):
        value = str(value).strip().title()
        if not value:
            raise serializers.ValidationError("First name is required.")
        return value

    def validate_last_name(self, value):
        value = str(value).strip().title()
        if not value:
            raise serializers.ValidationError("Last name is required.")
        return value

    def validate_email(self, value):
        value = normalize_email(value)

        if not value:
            raise serializers.ValidationError("Email is required.")

        qs = CustomUser.objects.filter(email__iexact=value).exclude(
            pk=self.instance.pk
        )

        if qs.exists():
            raise serializers.ValidationError("This email is already registered.")

        return value

    def validate_country_code(self, value):
        value = str(value).strip()

        if value != "+91":
            raise serializers.ValidationError("Only +91 country code is allowed.")

        return value

    def validate_mobile_number(self, value):
        value = normalize_mobile_number(value)

        if not value:
            raise serializers.ValidationError("Mobile number is required.")

        if len(value) != 10 or not value.isdigit():
            raise serializers.ValidationError(
                "Enter a valid 10-digit Indian mobile number."
            )

        if value[0] not in "6789":
            raise serializers.ValidationError(
                "Enter a valid 10-digit Indian mobile number."
            )

        qs = CustomUser.objects.filter(mobile_number=value).exclude(
            pk=self.instance.pk
        )

        if qs.exists():
            raise serializers.ValidationError(
                "This mobile number is already registered."
            )

        return value
    
    
    
    
# =========================================================
# Farmer Profile Update Serializer
# =========================================================
class FarmerProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmerProfile
        fields = [
            "gender",
            "village",
            "taluka",
            "district",
            "state",
            "pincode",
            "full_address",
        ]

    def validate_village(self, value):
        value = str(value).strip().title()
        if not value:
            raise serializers.ValidationError("Village is required.")
        return value

    def validate_taluka(self, value):
        value = str(value).strip().title()
        if not value:
            raise serializers.ValidationError("Taluka is required.")
        return value

    def validate_district(self, value):
        value = str(value).strip().title()
        if not value:
            raise serializers.ValidationError("District is required.")
        return value

    def validate_state(self, value):
        value = str(value).strip().title()
        if not value:
            raise serializers.ValidationError("State is required.")
        return value

    def validate_pincode(self, value):
        value = str(value).strip()

        if not value:
            raise serializers.ValidationError("Pincode is required.")

        if len(value) != 6 or not value.isdigit():
            raise serializers.ValidationError(
                "Enter a valid 6-digit pincode."
            )

        return value

    def validate_full_address(self, value):
        value = str(value).strip()

        if not value:
            raise serializers.ValidationError("Full address is required.")

        return value
    
    
    
    
# =========================================================
# OTPVerification Serializer
# =========================================================

class OTPVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = OTPVerification
        fields = [
            "id",
            "email",
            "mobile_number",
            "email_otp",
            "mobile_otp",
            "purpose",
            "is_email_verified",
            "is_mobile_verified",
            "is_verified",
            "expires_at",
        ]

        read_only_fields = [
            "id",
            "is_email_verified",
            "is_mobile_verified",
            "is_verified",
            "expires_at",
        ]

    def validate_email(self, value):
        if value:
            value = normalize_email(value)

        return value

    def validate_mobile_number(self, value):
        if value:
            value = normalize_mobile_number(value)

            if len(value) != 10 or not value.isdigit():
                raise serializers.ValidationError(
                    "Enter a valid 10-digit Indian mobile number."
                )

            if value[0] not in "6789":
                raise serializers.ValidationError(
                    "Enter a valid 10-digit Indian mobile number."
                )

        return value

    def validate_email_otp(self, value):
        if value:
            value = str(value).strip()

            if len(value) != 6 or not value.isdigit():
                raise serializers.ValidationError(
                    "Email OTP must be exactly 6 digits."
                )

        return value

    def validate_mobile_otp(self, value):
        if value:
            value = str(value).strip()

            if len(value) != 6 or not value.isdigit():
                raise serializers.ValidationError(
                    "Mobile OTP must be exactly 6 digits."
                )

        return value

    def validate_purpose(self, value):
        if value:
            value = str(value).strip().lower()

        valid_purposes = [
            "general",
            "registration",
            "forgot_password",
            "update_email",
            "update_mobile",
            "update_profile",
        ]

        if value not in valid_purposes:
            raise serializers.ValidationError(
                "Invalid OTP purpose."
            )

        return value

    def validate(self, attrs):
        email = attrs.get("email")
        mobile_number = attrs.get("mobile_number")
        email_otp = attrs.get("email_otp")
        mobile_otp = attrs.get("mobile_otp")

        if not email and not mobile_number:
            raise serializers.ValidationError(
                {
                    "contact": [
                        "Email or mobile number is required."
                    ]
                }
            )

        if email and not email_otp:
            raise serializers.ValidationError(
                {
                    "email_otp": [
                        "Email OTP is required when email is provided."
                    ]
                }
            )

        if mobile_number and not mobile_otp:
            raise serializers.ValidationError(
                {
                    "mobile_otp": [
                        "Mobile OTP is required when mobile number is provided."
                    ]
                }
            )

        return attrs