from django import forms
from django.core.exceptions import ValidationError

from .models import CropPredictionHistory


# ======================================================
# 1. INPUT FORM
# Used by Admin and Farmer to generate crop prediction
# ======================================================
class CropRecommendationForm(forms.Form):
    nitrogen = forms.FloatField(
        label="Nitrogen (N)",
        min_value=0,
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "placeholder": "Enter Nitrogen value",
            "step": "0.01",
            "min": "0",
        }),
    )

    phosphorus = forms.FloatField(
        label="Phosphorus (P)",
        min_value=0,
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "placeholder": "Enter Phosphorus value",
            "step": "0.01",
            "min": "0",
        }),
    )

    potassium = forms.FloatField(
        label="Potassium (K)",
        min_value=0,
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "placeholder": "Enter Potassium value",
            "step": "0.01",
            "min": "0",
        }),
    )

    temperature = forms.FloatField(
        label="Temperature °C",
        min_value=-50,
        max_value=100,
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "placeholder": "Enter Temperature",
            "step": "0.01",
            "min": "-50",
            "max": "100",
        }),
    )

    humidity = forms.FloatField(
        label="Humidity %",
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "placeholder": "Enter Humidity",
            "step": "0.01",
            "min": "0",
            "max": "100",
        }),
    )

    ph = forms.FloatField(
        label="Soil pH",
        min_value=0,
        max_value=14,
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "placeholder": "Enter Soil pH",
            "step": "0.01",
            "min": "0",
            "max": "14",
        }),
    )

    rainfall = forms.FloatField(
        label="Rainfall mm",
        min_value=0,
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "placeholder": "Enter Rainfall",
            "step": "0.01",
            "min": "0",
        }),
    )

    # ==================================================
    # FIELD VALIDATION
    # ==================================================
    def clean_nitrogen(self):
        return self._clean_positive_number(
            self.cleaned_data.get("nitrogen"),
            "Nitrogen",
        )

    def clean_phosphorus(self):
        return self._clean_positive_number(
            self.cleaned_data.get("phosphorus"),
            "Phosphorus",
        )

    def clean_potassium(self):
        return self._clean_positive_number(
            self.cleaned_data.get("potassium"),
            "Potassium",
        )

    def clean_temperature(self):
        value = self.cleaned_data.get("temperature")

        if value is None:
            raise ValidationError(
                "Temperature value is required."
            )

        value = float(value)

        if value < -50 or value > 100:
            raise ValidationError(
                "Temperature must be between -50 and 100."
            )

        return value

    def clean_humidity(self):
        value = self.cleaned_data.get("humidity")

        if value is None:
            raise ValidationError(
                "Humidity value is required."
            )

        value = float(value)

        if value < 0 or value > 100:
            raise ValidationError(
                "Humidity must be between 0 and 100."
            )

        return value

    def clean_ph(self):
        value = self.cleaned_data.get("ph")

        if value is None:
            raise ValidationError(
                "pH value is required."
            )

        value = float(value)

        if value < 0 or value > 14:
            raise ValidationError(
                "pH must be between 0 and 14."
            )

        return value

    def clean_rainfall(self):
        return self._clean_positive_number(
            self.cleaned_data.get("rainfall"),
            "Rainfall",
        )

    # ==================================================
    # COMMON VALIDATION
    # ==================================================
    def _clean_positive_number(
        self,
        value,
        field_label,
    ):
        if value is None:
            raise ValidationError(
                f"{field_label} value is required."
            )

        value = float(value)

        if value < 0:
            raise ValidationError(
                f"{field_label} cannot be negative."
            )

        return value


# ======================================================
# 2. HISTORY FORM
# Used by Admin to create/edit crop history
# ======================================================
class CropPredictionHistoryForm(forms.ModelForm):

    class Meta:
        model = CropPredictionHistory

        fields = [
            "user",
            "nitrogen",
            "phosphorus",
            "potassium",
            "temperature",
            "humidity",
            "ph",
            "rainfall",
            "predicted_crop",
        ]

        widgets = {
            "user": forms.Select(attrs={
                "class": "form-select",
            }),

            "nitrogen": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter Nitrogen value",
                "step": "0.01",
                "min": "0",
            }),

            "phosphorus": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter Phosphorus value",
                "step": "0.01",
                "min": "0",
            }),

            "potassium": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter Potassium value",
                "step": "0.01",
                "min": "0",
            }),

            "temperature": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter Temperature",
                "step": "0.01",
                "min": "-50",
                "max": "100",
            }),

            "humidity": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter Humidity",
                "step": "0.01",
                "min": "0",
                "max": "100",
            }),

            "ph": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter Soil pH",
                "step": "0.01",
                "min": "0",
                "max": "14",
            }),

            "rainfall": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter Rainfall",
                "step": "0.01",
                "min": "0",
            }),

            "predicted_crop": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter Predicted Crop",
            }),
        }

    # ==================================================
    # INIT
    # ==================================================
    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop(
            "request_user",
            None,
        )

        super().__init__(*args, **kwargs)

        required_fields = [
            "nitrogen",
            "phosphorus",
            "potassium",
            "temperature",
            "humidity",
            "ph",
            "rainfall",
            "predicted_crop",
        ]

        for field_name in required_fields:
            self.fields[field_name].required = True

    # ==================================================
    # FIELD VALIDATION
    # ==================================================
    def clean_nitrogen(self):
        return self._clean_positive_number(
            self.cleaned_data.get("nitrogen"),
            "Nitrogen",
        )

    def clean_phosphorus(self):
        return self._clean_positive_number(
            self.cleaned_data.get("phosphorus"),
            "Phosphorus",
        )

    def clean_potassium(self):
        return self._clean_positive_number(
            self.cleaned_data.get("potassium"),
            "Potassium",
        )

    def clean_temperature(self):
        value = self.cleaned_data.get("temperature")

        if value is None:
            raise ValidationError(
                "Temperature value is required."
            )

        value = float(value)

        if value < -50 or value > 100:
            raise ValidationError(
                "Temperature must be between -50 and 100."
            )

        return value

    def clean_humidity(self):
        value = self.cleaned_data.get("humidity")

        if value is None:
            raise ValidationError(
                "Humidity value is required."
            )

        value = float(value)

        if value < 0 or value > 100:
            raise ValidationError(
                "Humidity must be between 0 and 100."
            )

        return value

    def clean_ph(self):
        value = self.cleaned_data.get("ph")

        if value is None:
            raise ValidationError(
                "pH value is required."
            )

        value = float(value)

        if value < 0 or value > 14:
            raise ValidationError(
                "pH must be between 0 and 14."
            )

        return value

    def clean_rainfall(self):
        return self._clean_positive_number(
            self.cleaned_data.get("rainfall"),
            "Rainfall",
        )

    def clean_predicted_crop(self):
        value = self.cleaned_data.get(
            "predicted_crop"
        )

        if value:
            value = str(value).strip().title()

        if not value:
            raise ValidationError(
                "Predicted crop is required."
            )

        return value

    # ==================================================
    # COMMON VALIDATION
    # ==================================================
    def _clean_positive_number(
        self,
        value,
        field_label,
    ):
        if value is None:
            raise ValidationError(
                f"{field_label} value is required."
            )

        value = float(value)

        if value < 0:
            raise ValidationError(
                f"{field_label} cannot be negative."
            )

        return value

    # ==================================================
    # OBJECT VALIDATION
    # ==================================================
    def clean(self):
        cleaned_data = super().clean()

        user = cleaned_data.get("user")

        predicted_crop = cleaned_data.get(
            "predicted_crop"
        )

        if not predicted_crop:
            self.add_error(
                "predicted_crop",
                "Predicted crop is required.",
            )

        if (
            self.request_user
            and user
            and user != self.request_user
        ):
            self.add_error(
                "user",
                (
                    "You cannot create crop prediction "
                    "history for another user."
                ),
            )

        return cleaned_data