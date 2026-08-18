# =========================================================
# IMPORTS
# =========================================================
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError
from django.db import transaction
from django.contrib.auth import authenticate

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

User = get_user_model()


# =========================================================
# COMMON WIDGET CLASSES
# =========================================================
TEXT_INPUT_CLASS = "form-control"
SELECT_CLASS = "form-select"
TEXTAREA_CLASS = "form-control"


# =========================================================
# Common Helper Functions
# =========================================================
def normalize_email(value):
    return value.strip().lower() if value else value


def normalize_username(value):
    return value.strip().lower() if value else value


def normalize_mobile_number(value):
    value = str(value).strip().replace(" ", "").replace("-", "")

    if value.startswith("+91"):
        value = value[3:]
    elif value.startswith("91") and len(value) == 12:
        value = value[2:]

    return value


# =========================================================
# Login Form
# =========================================================
class UserLoginForm(forms.Form):
    username = forms.CharField(
        label="Username / Email / Mobile Number",
        max_length=150,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter username, email or mobile number",
        }),
    )

    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Enter password",
        }),
    )

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()

        username = cleaned_data.get("username")
        password = cleaned_data.get("password")

        if username and password:
            self.user_cache = authenticate(
                self.request,
                username=username,
                password=password,
            )

            if self.user_cache is None:
                raise forms.ValidationError(
                    "Invalid username/email/mobile number or password."
                )

        return cleaned_data

    def get_user(self):
        return self.user_cache
    

# =========================================================
# Send OTP Form
# =========================================================
class SendOTPForm(forms.Form):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            "class": TEXT_INPUT_CLASS,
            "placeholder": "Enter email address",
        })
    )

    mobile_number = forms.CharField(
        max_length=10,
        required=True,
        widget=forms.TextInput(attrs={
            "class": TEXT_INPUT_CLASS,
            "placeholder": "Enter 10 digit mobile number",
        })
    )

    def clean_email(self):
        email = self.cleaned_data.get("email")

        email = normalize_email(email)

        if not email:
            raise ValidationError("Email is required.")

        return email

    def clean_mobile_number(self):
        mobile_number = self.cleaned_data.get("mobile_number")

        mobile_number = normalize_mobile_number(mobile_number)

        if not mobile_number:
            raise ValidationError("Mobile number is required.")

        # Must be exactly 10 digits
        if len(mobile_number) != 10 or not mobile_number.isdigit():
            raise ValidationError("Enter a valid 10-digit Indian mobile number.")

        # Indian mobile numbers start with 6–9
        if mobile_number[0] not in "6789":
            raise ValidationError("Enter a valid 10-digit Indian mobile number.")

        return mobile_number

    def clean(self):
        cleaned_data = super().clean()

        email = cleaned_data.get("email")
        mobile_number = cleaned_data.get("mobile_number")

        # Optional: ensure at least one is provided (if your logic allows)
        if not email and not mobile_number:
            raise ValidationError("Email or mobile number is required.")

        return cleaned_data
    
# =========================================================
# Verify OTP Form
# =========================================================
class VerifyOTPForm(forms.Form):
    email = forms.EmailField(
        required=True,
        widget=forms.HiddenInput()
    )

    mobile_number = forms.CharField(
        required=True,
        widget=forms.HiddenInput()
    )

    email_otp = forms.CharField(
        label="Email OTP",
        max_length=6,
        min_length=6,
        required=True,
        widget=forms.TextInput(attrs={
            "class": TEXT_INPUT_CLASS,
            "placeholder": "Enter email OTP",
            "maxlength": "6",
        })
    )

    mobile_otp = forms.CharField(
        label="Mobile OTP",
        max_length=6,
        min_length=6,
        required=True,
        widget=forms.TextInput(attrs={
            "class": TEXT_INPUT_CLASS,
            "placeholder": "Enter mobile OTP",
            "maxlength": "6",
        })
    )

    def clean_email(self):
        email = normalize_email(self.cleaned_data.get("email"))

        if not email:
            raise ValidationError("Email is required.")

        return email

    def clean_mobile_number(self):
        mobile_number = normalize_mobile_number(
            self.cleaned_data.get("mobile_number")
        )

        if not mobile_number:
            raise ValidationError("Mobile number is required.")

        if len(mobile_number) != 10 or not mobile_number.isdigit():
            raise ValidationError("Enter a valid 10-digit Indian mobile number.")

        if mobile_number[0] not in "6789":
            raise ValidationError("Enter a valid 10-digit Indian mobile number.")

        return mobile_number

    def clean_email_otp(self):
        email_otp = self.cleaned_data.get("email_otp", "").strip()

        if len(email_otp) != 6 or not email_otp.isdigit():
            raise ValidationError("Email OTP must be 6 digits.")

        return email_otp

    def clean_mobile_otp(self):
        mobile_otp = self.cleaned_data.get("mobile_otp", "").strip()

        if len(mobile_otp) != 6 or not mobile_otp.isdigit():
            raise ValidationError("Mobile OTP must be 6 digits.")

        return mobile_otp
    
  


# =========================================================
# Farmer Registration Form
# =========================================================
class FarmerRegistrationForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            "class": TEXT_INPUT_CLASS,
            "placeholder": "Enter first name",
        })
    )

    last_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            "class": TEXT_INPUT_CLASS,
            "placeholder": "Enter last name",
        })
    )

    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            "class": TEXT_INPUT_CLASS,
            "placeholder": "Enter username",
        }),
        help_text="Use lowercase letters and numbers only."
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            "class": TEXT_INPUT_CLASS,
            "placeholder": "Enter email address",
        })
    )

    country_code = forms.CharField(
        max_length=5,
        initial="+91",
        widget=forms.TextInput(attrs={
            "class": TEXT_INPUT_CLASS,
            "placeholder": "+91",
            "readonly": "readonly",
        })
    )

    mobile_number = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            "class": TEXT_INPUT_CLASS,
            "placeholder": "Enter mobile number",
        })
    )

    language_preference = forms.ChoiceField(
        choices=CustomUser.LanguageChoices.choices,
        initial=CustomUser.LanguageChoices.ENGLISH,
        widget=forms.Select(attrs={
            "class": SELECT_CLASS,
        })
    )

    gender = forms.ChoiceField(
        choices=FarmerProfile.GenderChoices.choices,
        widget=forms.Select(attrs={
            "class": SELECT_CLASS,
        })
    )

    village = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            "class": TEXT_INPUT_CLASS,
            "placeholder": "Enter village",
        })
    )

    taluka = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            "class": TEXT_INPUT_CLASS,
            "placeholder": "Enter taluka",
        })
    )

    district = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            "class": TEXT_INPUT_CLASS,
            "placeholder": "Enter district",
        })
    )

    state = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            "class": TEXT_INPUT_CLASS,
            "placeholder": "Enter state",
        })
    )

    pincode = forms.CharField(
        max_length=6,
        widget=forms.TextInput(attrs={
            "class": TEXT_INPUT_CLASS,
            "placeholder": "Enter pincode",
        })
    )

    full_address = forms.CharField(
        widget=forms.Textarea(attrs={
            "class": TEXTAREA_CLASS,
            "placeholder": "Enter full address",
            "rows": 3,
        })
    )

    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            "class": TEXT_INPUT_CLASS,
            "placeholder": "Enter password",
        })
    )

    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            "class": TEXT_INPUT_CLASS,
            "placeholder": "Confirm password",
        })
    )

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
            "gender",
            "village",
            "taluka",
            "district",
            "state",
            "pincode",
            "full_address",
            "password1",
            "password2",
        ]

    def clean_first_name(self):
        first_name = self.cleaned_data.get("first_name", "").strip().title()

        if not first_name:
            raise ValidationError("First name is required.")

        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get("last_name", "").strip().title()

        if not last_name:
            raise ValidationError("Last name is required.")

        return last_name

    def clean_username(self):
        username = normalize_username(self.cleaned_data.get("username"))

        if not username:
            raise ValidationError("Username is required.")

        if CustomUser.objects.filter(username__iexact=username).exists():
            raise ValidationError("This username is already taken.")

        return username

    def clean_email(self):
        email = normalize_email(self.cleaned_data.get("email"))

        if not email:
            raise ValidationError("Email is required.")

        if CustomUser.objects.filter(email__iexact=email).exists():
            raise ValidationError("This email is already registered.")

        return email

    def clean_country_code(self):
        country_code = self.cleaned_data.get("country_code", "").strip()

        if country_code != "+91":
            raise ValidationError("Only +91 country code is allowed.")

        return country_code

    def clean_mobile_number(self):
        mobile_number = normalize_mobile_number(
            self.cleaned_data.get("mobile_number")
        )

        if not mobile_number:
            raise ValidationError("Mobile number is required.")

        if len(mobile_number) != 10 or not mobile_number.isdigit():
            raise ValidationError("Enter a valid 10-digit Indian mobile number.")

        if mobile_number[0] not in "6789":
            raise ValidationError("Enter a valid 10-digit Indian mobile number.")

        if CustomUser.objects.filter(mobile_number=mobile_number).exists():
            raise ValidationError("This mobile number is already registered.")

        return mobile_number

    def clean_village(self):
        village = self.cleaned_data.get("village", "").strip().title()

        if not village:
            raise ValidationError("Village is required.")

        return village

    def clean_taluka(self):
        taluka = self.cleaned_data.get("taluka", "").strip().title()

        if not taluka:
            raise ValidationError("Taluka is required.")

        return taluka

    def clean_district(self):
        district = self.cleaned_data.get("district", "").strip().title()

        if not district:
            raise ValidationError("District is required.")

        return district

    def clean_state(self):
        state = self.cleaned_data.get("state", "").strip().title()

        if not state:
            raise ValidationError("State is required.")

        return state

    def clean_pincode(self):
        pincode = self.cleaned_data.get("pincode", "").strip()

        if not pincode:
            raise ValidationError("Pincode is required.")

        if len(pincode) != 6 or not pincode.isdigit():
            raise ValidationError("Enter a valid 6-digit pincode.")

        return pincode

    def clean_full_address(self):
        full_address = self.cleaned_data.get("full_address", "").strip()

        if not full_address:
            raise ValidationError("Full address is required.")

        return full_address

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)

        user.role = CustomUser.RoleChoices.FARMER
        user.is_staff = False
        user.is_superuser = False
        user.is_active = False

        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.username = self.cleaned_data["username"]
        user.email = self.cleaned_data["email"]
        user.country_code = self.cleaned_data["country_code"]
        user.mobile_number = self.cleaned_data["mobile_number"]
        user.language_preference = self.cleaned_data["language_preference"]

        if commit:
            user.save()

            FarmerProfile.objects.update_or_create(
                user=user,
                defaults={
                    "gender": self.cleaned_data["gender"],
                    "village": self.cleaned_data["village"],
                    "taluka": self.cleaned_data["taluka"],
                    "district": self.cleaned_data["district"],
                    "state": self.cleaned_data["state"],
                    "pincode": self.cleaned_data["pincode"],
                    "full_address": self.cleaned_data["full_address"],
                },
            )

        return user
    


# =========================================================
# Admin Registration Form
# =========================================================
class AdminRegistrationForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            "class": TEXT_INPUT_CLASS,
            "placeholder": "Enter first name",
        })
    )

    last_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            "class": TEXT_INPUT_CLASS,
            "placeholder": "Enter last name",
        })
    )

    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            "class": TEXT_INPUT_CLASS,
            "placeholder": "Enter username",
        }),
        help_text="Use lowercase letters and numbers only.",
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            "class": TEXT_INPUT_CLASS,
            "placeholder": "Enter email address",
        })
    )

    country_code = forms.CharField(
        max_length=5,
        initial="+91",
        widget=forms.TextInput(attrs={
            "class": TEXT_INPUT_CLASS,
            "placeholder": "+91",
            "readonly": "readonly",
        })
    )

    mobile_number = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            "class": TEXT_INPUT_CLASS,
            "placeholder": "Enter mobile number",
        })
    )

    language_preference = forms.ChoiceField(
        choices=CustomUser.LanguageChoices.choices,
        initial=CustomUser.LanguageChoices.ENGLISH,
        widget=forms.Select(attrs={
            "class": SELECT_CLASS,
        })
    )

    admin_secret_code = forms.CharField(
        max_length=100,
        widget=forms.PasswordInput(attrs={
            "class": TEXT_INPUT_CLASS,
            "placeholder": "Enter admin secret code",
        })
    )

    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            "class": TEXT_INPUT_CLASS,
            "placeholder": "Enter password",
        })
    )

    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            "class": TEXT_INPUT_CLASS,
            "placeholder": "Confirm password",
        })
    )

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
            "password1",
            "password2",
        ]

    def clean_first_name(self):
        first_name = self.cleaned_data.get("first_name", "").strip().title()
        if not first_name:
            raise ValidationError("First name is required.")
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get("last_name", "").strip().title()
        if not last_name:
            raise ValidationError("Last name is required.")
        return last_name

    def clean_username(self):
        username = normalize_username(self.cleaned_data.get("username"))

        if not username:
            raise ValidationError("Username is required.")

        if CustomUser.objects.filter(username__iexact=username).exists():
            raise ValidationError("This username is already taken.")

        return username

    def clean_email(self):
        email = normalize_email(self.cleaned_data.get("email"))

        if not email:
            raise ValidationError("Email is required.")

        if CustomUser.objects.filter(email__iexact=email).exists():
            raise ValidationError("This email is already registered.")

        return email

    def clean_country_code(self):
        country_code = self.cleaned_data.get("country_code", "").strip()

        if country_code != "+91":
            raise ValidationError("Only +91 country code is allowed.")

        return country_code

    def clean_mobile_number(self):
        mobile_number = normalize_mobile_number(
            self.cleaned_data.get("mobile_number")
        )

        if not mobile_number:
            raise ValidationError("Mobile number is required.")

        if len(mobile_number) != 10 or not mobile_number.isdigit():
            raise ValidationError("Enter a valid 10-digit Indian mobile number.")

        if mobile_number[0] not in "6789":
            raise ValidationError("Enter a valid 10-digit Indian mobile number.")

        if CustomUser.objects.filter(mobile_number=mobile_number).exists():
            raise ValidationError("This mobile number is already registered.")

        return mobile_number

    def clean_admin_secret_code(self):
        admin_secret_code = self.cleaned_data.get("admin_secret_code", "").strip()
        expected_code = getattr(settings, "ADMIN_SECRET_CODE", "")

        if not expected_code:
            raise ValidationError("Admin secret code is not configured.")

        if admin_secret_code != expected_code:
            raise ValidationError("Invalid admin secret code.")

        return admin_secret_code

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)

        user.role = CustomUser.RoleChoices.ADMIN
        user.is_staff = True
        user.is_superuser = False
        user.is_active = False

        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.username = self.cleaned_data["username"]
        user.email = self.cleaned_data["email"]
        user.country_code = self.cleaned_data["country_code"]
        user.mobile_number = self.cleaned_data["mobile_number"]
        user.language_preference = self.cleaned_data["language_preference"]

        if commit:
            user.save()

            AdminProfile.objects.update_or_create(
                user=user,
                defaults={
                    "admin_secret_code": self.cleaned_data["admin_secret_code"],
                },
            )

        return user
    



# ============================================================
# Current Profile Update Form
# ============================================================
class CurrentProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "country_code",
            "mobile_number",
            "language_preference",
        ]

        widgets = {
            "username": forms.TextInput(attrs={"class": TEXT_INPUT_CLASS}),
            "first_name": forms.TextInput(attrs={"class": TEXT_INPUT_CLASS}),
            "last_name": forms.TextInput(attrs={"class": TEXT_INPUT_CLASS}),
            "email": forms.EmailInput(attrs={"class": TEXT_INPUT_CLASS}),
            "country_code": forms.TextInput(attrs={
                "class": TEXT_INPUT_CLASS,
                "readonly": "readonly",
            }),
            "mobile_number": forms.TextInput(attrs={"class": TEXT_INPUT_CLASS}),
            "language_preference": forms.Select(attrs={"class": SELECT_CLASS}),
        }


# =========================================================
# Farmer Profile Update Form
# =========================================================
class FarmerProfileUpdateForm(forms.ModelForm):
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

        widgets = {
            "gender": forms.Select(attrs={"class": SELECT_CLASS}),
            "village": forms.TextInput(attrs={"class": TEXT_INPUT_CLASS}),
            "taluka": forms.TextInput(attrs={"class": TEXT_INPUT_CLASS}),
            "district": forms.TextInput(attrs={"class": TEXT_INPUT_CLASS}),
            "state": forms.TextInput(attrs={"class": TEXT_INPUT_CLASS}),
            "pincode": forms.TextInput(attrs={"class": TEXT_INPUT_CLASS}),
            "full_address": forms.Textarea(attrs={
                "class": TEXTAREA_CLASS,
                "rows": 3,
            }),
        }

    def clean_village(self):
        return self.cleaned_data.get("village", "").strip().title()

    def clean_taluka(self):
        return self.cleaned_data.get("taluka", "").strip().title()

    def clean_district(self):
        return self.cleaned_data.get("district", "").strip().title()

    def clean_state(self):
        return self.cleaned_data.get("state", "").strip().title()

    def clean_pincode(self):
        pincode = self.cleaned_data.get("pincode", "").strip()

        if len(pincode) != 6 or not pincode.isdigit():
            raise ValidationError("Enter a valid 6-digit pincode.")

        return pincode

    def clean_full_address(self):
        return self.cleaned_data.get("full_address", "").strip()


# =========================================================
# User Update Form
# =========================================================
class UserUpdateForm(forms.ModelForm):
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

        widgets = {
            "first_name": forms.TextInput(attrs={"class": TEXT_INPUT_CLASS}),
            "last_name": forms.TextInput(attrs={"class": TEXT_INPUT_CLASS}),
            "email": forms.EmailInput(attrs={"class": TEXT_INPUT_CLASS}),
            "country_code": forms.TextInput(attrs={
                "class": TEXT_INPUT_CLASS,
                "readonly": "readonly",
            }),
            "mobile_number": forms.TextInput(attrs={"class": TEXT_INPUT_CLASS}),
            "language_preference": forms.Select(attrs={"class": SELECT_CLASS}),
        }

    def clean_first_name(self):
        first_name = self.cleaned_data.get("first_name", "").strip().title()

        if not first_name:
            raise ValidationError("First name is required.")

        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get("last_name", "").strip().title()

        if not last_name:
            raise ValidationError("Last name is required.")

        return last_name

    def clean_email(self):
        email = normalize_email(self.cleaned_data.get("email"))

        if not email:
            raise ValidationError("Email is required.")

        qs = CustomUser.objects.filter(email__iexact=email).exclude(
            pk=self.instance.pk
        )

        if qs.exists():
            raise ValidationError("This email is already registered.")

        return email

    def clean_country_code(self):
        country_code = self.cleaned_data.get("country_code", "").strip()

        if country_code != "+91":
            raise ValidationError("Only +91 country code is allowed.")

        return country_code

    def clean_mobile_number(self):
        mobile_number = normalize_mobile_number(
            self.cleaned_data.get("mobile_number")
        )

        if not mobile_number:
            raise ValidationError("Mobile number is required.")

        if len(mobile_number) != 10 or not mobile_number.isdigit():
            raise ValidationError("Enter a valid 10-digit Indian mobile number.")

        if mobile_number[0] not in "6789":
            raise ValidationError("Enter a valid 10-digit Indian mobile number.")

        qs = CustomUser.objects.filter(mobile_number=mobile_number).exclude(
            pk=self.instance.pk
        )

        if qs.exists():
            raise ValidationError("This mobile number is already registered.")

        return mobile_number



# =========================================================
# OTPVerification Model Form (Admin/Internal Use)
# =========================================================

class OTPVerificationForm(forms.ModelForm):
    class Meta:
        model = OTPVerification
        fields = [
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

        widgets = {
            "email": forms.EmailInput(attrs={"class": TEXT_INPUT_CLASS}),
            "mobile_number": forms.TextInput(attrs={"class": TEXT_INPUT_CLASS}),
            "email_otp": forms.TextInput(attrs={"class": TEXT_INPUT_CLASS}),
            "mobile_otp": forms.TextInput(attrs={"class": TEXT_INPUT_CLASS}),
            "purpose": forms.Select(attrs={"class": TEXT_INPUT_CLASS}),
            "is_email_verified": forms.CheckboxInput(),
            "is_mobile_verified": forms.CheckboxInput(),
            "is_verified": forms.CheckboxInput(),
            "expires_at": forms.DateTimeInput(
                attrs={
                    "class": TEXT_INPUT_CLASS,
                    "type": "datetime-local",
                }
            ),
        }

    def clean_email(self):
        email = self.cleaned_data.get("email")

        if email:
            email = normalize_email(email)

        return email

    def clean_mobile_number(self):
        mobile_number = self.cleaned_data.get("mobile_number")

        if mobile_number:
            mobile_number = normalize_mobile_number(mobile_number)

            if len(mobile_number) != 10 or not mobile_number.isdigit():
                raise ValidationError(
                    "Enter a valid 10-digit Indian mobile number."
                )

            if mobile_number[0] not in "6789":
                raise ValidationError(
                    "Enter a valid 10-digit Indian mobile number."
                )

        return mobile_number

    def clean_email_otp(self):
        email_otp = self.cleaned_data.get("email_otp")

        if email_otp:
            email_otp = email_otp.strip()

            if len(email_otp) != 6 or not email_otp.isdigit():
                raise ValidationError(
                    "Email OTP must be exactly 6 digits."
                )

        return email_otp

    def clean_mobile_otp(self):
        mobile_otp = self.cleaned_data.get("mobile_otp")

        if mobile_otp:
            mobile_otp = mobile_otp.strip()

            if len(mobile_otp) != 6 or not mobile_otp.isdigit():
                raise ValidationError(
                    "Mobile OTP must be exactly 6 digits."
                )

        return mobile_otp

    def clean(self):
        cleaned_data = super().clean()

        email = cleaned_data.get("email")
        mobile_number = cleaned_data.get("mobile_number")
        email_otp = cleaned_data.get("email_otp")
        mobile_otp = cleaned_data.get("mobile_otp")

        if not email and not mobile_number:
            raise ValidationError(
                "Email or mobile number is required."
            )

        if email and not email_otp:
            self.add_error(
                "email_otp",
                "Email OTP is required when email is provided.",
            )

        if mobile_number and not mobile_otp:
            self.add_error(
                "mobile_otp",
                "Mobile OTP is required when mobile number is provided.",
            )

        return cleaned_data