from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone


# =========================================================
# Common Base Model
# =========================================================
class TimeStampedUserTrackingModel(models.Model):
    created_by_user = models.CharField(max_length=100, blank=True, null=True)
    updated_by_user = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    _current_user = None

    class Meta:
        abstract = True

    def set_user_context(self, user):
        self._current_user = user

        username = None
        if user and getattr(user, "is_authenticated", False):
            username = getattr(user, "username", None) or str(user)

        if username:
            username = username.strip().lower()
            if not self.pk and not self.created_by_user:
                self.created_by_user = username
            self.updated_by_user = username

    def normalize_user_tracking_fields(self):
        if self.created_by_user:
            self.created_by_user = self.created_by_user.strip().lower()
        if self.updated_by_user:
            self.updated_by_user = self.updated_by_user.strip().lower()


# =========================================================
# Validators
# =========================================================
name_validator = RegexValidator(
    regex=r"^[A-Za-z\s]+$",
    message="Only letters and spaces are allowed.",
)

username_validator = RegexValidator(
    regex=r"^[a-z0-9]+$",
    message="Username must contain lowercase letters and numbers only.",
)

mobile_number_validator = RegexValidator(
    regex=r"^[6-9]\d{9}$",
    message="Enter a valid 10-digit Indian mobile number.",
)

pincode_validator = RegexValidator(
    regex=r"^\d{6}$",
    message="Enter a valid 6-digit pincode.",
)

country_code_validator = RegexValidator(
    regex=r"^\+\d{1,4}$",
    message="Enter a valid country code like +91.",
)

otp_validator = RegexValidator(
    regex=r"^\d{6}$",
    message="OTP must be exactly 6 digits.",
)

admin_secret_code_validator = RegexValidator(
    regex=r"^[A-Za-z0-9@#_\-]+$",
    message="Admin secret code can contain letters, numbers, @, #, _, and - only.",
)


def default_otp_expiry():
    return timezone.now() + timedelta(minutes=5)


# =========================================================
# Custom User Model
# =========================================================
class CustomUser(AbstractUser):
    class RoleChoices(models.TextChoices):
        ADMIN = "admin", "Admin"
        FARMER = "farmer", "Farmer"

    class LanguageChoices(models.TextChoices):
        ENGLISH = "en", "English"
        MARATHI = "mr", "Marathi"
        HINDI = "hi", "Hindi"

    first_name = models.CharField(
        max_length=100,
        validators=[name_validator],
        verbose_name="First Name",
    )

    last_name = models.CharField(
        max_length=100,
        validators=[name_validator],
        verbose_name="Last Name",
    )

    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[username_validator],
        db_index=True,
        verbose_name="Username",
        help_text="Use lowercase letters and numbers only.",
    )

    email = models.EmailField(
        unique=True,
        db_index=True,
        verbose_name="Email Address",
    )

    country_code = models.CharField(
        max_length=5,
        default="+91",
        validators=[country_code_validator],
        verbose_name="Country Code",
    )

    mobile_number = models.CharField(
        max_length=10,
        unique=True,
        validators=[mobile_number_validator],
        db_index=True,
        verbose_name="Mobile Number",
    )

    language_preference = models.CharField(
        max_length=2,
        choices=LanguageChoices.choices,
        default=LanguageChoices.ENGLISH,
        db_index=True,
        verbose_name="Language Preference",
    )

    role = models.CharField(
        max_length=20,
        choices=RoleChoices.choices,
        db_index=True,
        verbose_name="Role",
    )

    REQUIRED_FIELDS = [
        "email",
        "country_code",
        "mobile_number",
        "role",
        "first_name",
        "last_name",
    ]

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-date_joined"]
        indexes = [
            models.Index(fields=["username"]),
            models.Index(fields=["email"]),
            models.Index(fields=["mobile_number"]),
            models.Index(fields=["role"]),
            models.Index(fields=["language_preference"]),
            models.Index(fields=["date_joined"]),
        ]

    def __str__(self):
        return f"{self.username} - {self.role}"

    def clean(self):
        super().clean()
        self._normalize_fields()
        errors = {}

        if not self.first_name:
            errors["first_name"] = "First name is required."

        if not self.last_name:
            errors["last_name"] = "Last name is required."

        if not self.username:
            errors["username"] = "Username is required."

        if not self.email:
            errors["email"] = "Email is required."

        if not self.country_code:
            errors["country_code"] = "Country code is required."

        if not self.mobile_number:
            errors["mobile_number"] = "Mobile number is required."

        if not self.role:
            errors["role"] = "Role is required."

        if self.email:
            duplicate_email_qs = CustomUser.objects.filter(
                email__iexact=self.email
            ).exclude(pk=self.pk)
            if duplicate_email_qs.exists():
                errors["email"] = "This email is already registered."

        if self.mobile_number:
            duplicate_mobile_qs = CustomUser.objects.filter(
                mobile_number=self.mobile_number
            ).exclude(pk=self.pk)
            if duplicate_mobile_qs.exists():
                errors["mobile_number"] = "This mobile number is already registered."

        if self.username:
            duplicate_username_qs = CustomUser.objects.filter(
                username__iexact=self.username
            ).exclude(pk=self.pk)
            if duplicate_username_qs.exists():
                errors["username"] = "This username is already taken."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self._normalize_fields()
        self.full_clean()
        super().save(*args, **kwargs)

    def _normalize_fields(self):
        if self.first_name:
            self.first_name = self.first_name.strip().title()

        if self.last_name:
            self.last_name = self.last_name.strip().title()

        if self.username:
            self.username = self.username.strip().lower()

        if self.email:
            self.email = self.email.strip().lower()

        if self.country_code:
            self.country_code = self.country_code.strip()

        if self.mobile_number:
            self.mobile_number = self.mobile_number.strip()


# =========================================================
# Farmer Profile Model
# =========================================================
class FarmerProfile(TimeStampedUserTrackingModel):
    class GenderChoices(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"
        OTHER = "other", "Other"

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="farmer_profile",
        limit_choices_to={"role": CustomUser.RoleChoices.FARMER},
    )

    gender = models.CharField(
        max_length=10,
        choices=GenderChoices.choices,
        verbose_name="Gender",
    )

    village = models.CharField(
        max_length=100,
        db_index=True,
        verbose_name="Village",
    )

    taluka = models.CharField(
        max_length=100,
        db_index=True,
        verbose_name="Taluka",
    )

    district = models.CharField(
        max_length=100,
        db_index=True,
        verbose_name="District",
    )

    state = models.CharField(
        max_length=100,
        db_index=True,
        verbose_name="State",
    )

    pincode = models.CharField(
        max_length=6,
        validators=[pincode_validator],
        db_index=True,
        verbose_name="Pincode",
    )

    full_address = models.TextField(
        verbose_name="Full Address",
    )

    class Meta:
        verbose_name = "Farmer Profile"
        verbose_name_plural = "Farmer Profiles"
        ordering = ["user__username"]
        indexes = [
            models.Index(fields=["village"]),
            models.Index(fields=["taluka"]),
            models.Index(fields=["district"]),
            models.Index(fields=["state"]),
            models.Index(fields=["pincode"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"Farmer - {self.user.username}"

    def clean(self):
        super().clean()
        self._normalize_fields()
        errors = {}

        if self.user and self.user.role != CustomUser.RoleChoices.FARMER:
            errors["user"] = "This profile can only be assigned to a farmer user."

        if not self.gender:
            errors["gender"] = "Gender is required."

        if not self.village:
            errors["village"] = "Village is required."

        if not self.taluka:
            errors["taluka"] = "Taluka is required."

        if not self.district:
            errors["district"] = "District is required."

        if not self.state:
            errors["state"] = "State is required."

        if not self.pincode:
            errors["pincode"] = "Pincode is required."

        if not self.full_address:
            errors["full_address"] = "Full address is required."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self._normalize_fields()
        self.full_clean()
        super().save(*args, **kwargs)

    def _normalize_fields(self):
        text_fields = ["village", "taluka", "district", "state", "full_address"]
        for field in text_fields:
            value = getattr(self, field, None)
            if isinstance(value, str):
                setattr(self, field, value.strip())

        if self.village:
            self.village = self.village.title()

        if self.taluka:
            self.taluka = self.taluka.title()

        if self.district:
            self.district = self.district.title()

        if self.state:
            self.state = self.state.title()

        if self.pincode:
            self.pincode = self.pincode.strip()

        self.normalize_user_tracking_fields()


# =========================================================
# Admin Profile Model
# =========================================================
class AdminProfile(TimeStampedUserTrackingModel):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="admin_profile",
        limit_choices_to={"role": CustomUser.RoleChoices.ADMIN},
    )

    admin_secret_code = models.CharField(
        max_length=100,
        validators=[admin_secret_code_validator],
        verbose_name="Admin Secret Code",
    )

    class Meta:
        verbose_name = "Admin Profile"
        verbose_name_plural = "Admin Profiles"
        ordering = ["user__username"]
        indexes = [
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"Admin - {self.user.username}"

    def clean(self):
        super().clean()
        self._normalize_fields()
        errors = {}

        if self.user and self.user.role != CustomUser.RoleChoices.ADMIN:
            errors["user"] = "This profile can only be assigned to an admin user."

        if not self.admin_secret_code:
            errors["admin_secret_code"] = "Admin secret code is required."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self._normalize_fields()
        self.full_clean()
        super().save(*args, **kwargs)

    def _normalize_fields(self):
        if self.admin_secret_code:
            self.admin_secret_code = self.admin_secret_code.strip()

        self.normalize_user_tracking_fields()

# =========================================================
# OTP Verification Model
# =========================================================

class OTPVerification(TimeStampedUserTrackingModel):
    PURPOSE_CHOICES = [
        ("general", "General"),
        ("registration", "Registration"),
        ("forgot_password", "Forgot Password"),
        ("update_email", "Update Email"),
        ("update_mobile", "Update Mobile"),
        ("update_profile", "Update Profile"),
    ]

    email = models.EmailField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="Email Address",
    )

    mobile_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        validators=[mobile_number_validator],
        db_index=True,
        verbose_name="Mobile Number",
    )

    email_otp = models.CharField(
        max_length=6,
        blank=True,
        null=True,
        validators=[otp_validator],
        verbose_name="Email OTP",
    )

    mobile_otp = models.CharField(
        max_length=6,
        blank=True,
        null=True,
        validators=[otp_validator],
        verbose_name="Mobile OTP",
    )

    purpose = models.CharField(
        max_length=50,
        choices=PURPOSE_CHOICES,
        default="general",
        db_index=True,
        verbose_name="OTP Purpose",
    )

    is_email_verified = models.BooleanField(
        default=False,
        verbose_name="Email Verified",
    )

    is_mobile_verified = models.BooleanField(
        default=False,
        verbose_name="Mobile Verified",
    )

    is_verified = models.BooleanField(
        default=False,
        verbose_name="OTP Verified",
    )

    expires_at = models.DateTimeField(
        default=default_otp_expiry,
        verbose_name="Expires At",
    )

    class Meta:
        verbose_name = "OTP Verification"
        verbose_name_plural = "OTP Verifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["mobile_number"]),
            models.Index(fields=["purpose"]),
            models.Index(fields=["is_verified"]),
            models.Index(fields=["is_email_verified"]),
            models.Index(fields=["is_mobile_verified"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        email = self.email or "No Email"
        mobile = self.mobile_number or "No Mobile"
        return f"{email} - {mobile} - {self.purpose}"

    def clean(self):
        super().clean()
        self._normalize_fields()

        errors = {}

        if not self.email and not self.mobile_number:
            errors["contact"] = "Email or mobile number is required."

        if self.email and not self.email_otp:
            errors["email_otp"] = "Email OTP is required when email is provided."

        if self.mobile_number and not self.mobile_otp:
            errors["mobile_otp"] = "Mobile OTP is required when mobile number is provided."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self._normalize_fields()

        self.is_email_verified = bool(self.is_email_verified)
        self.is_mobile_verified = bool(self.is_mobile_verified)

        self.is_verified = self.is_email_verified or self.is_mobile_verified

        self.full_clean()
        super().save(*args, **kwargs)

    def _normalize_fields(self):
        if self.email:
            self.email = self.email.strip().lower()

        if self.mobile_number:
            self.mobile_number = self.mobile_number.strip()

        if self.email_otp:
            self.email_otp = self.email_otp.strip()

        if self.mobile_otp:
            self.mobile_otp = self.mobile_otp.strip()

        if self.purpose:
            self.purpose = self.purpose.strip().lower()

        self.normalize_user_tracking_fields()

    def is_expired(self):
        return timezone.now() > self.expires_at

    def is_fully_verified(self):
        if self.email and self.mobile_number:
            return self.is_email_verified and self.is_mobile_verified

        if self.email:
            return self.is_email_verified

        if self.mobile_number:
            return self.is_mobile_verified

        return False