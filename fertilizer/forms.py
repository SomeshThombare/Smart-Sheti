from django import forms
from django.core.exceptions import ValidationError

from .models import FertilizerRecommendationHistory


# ======================================================
# 1. INPUT FORM
# Used by Admin and Farmer to generate recommendation
# ======================================================
class FertilizerRecommendationInputForm(forms.Form):
    crop_type = forms.ChoiceField(
        label="Crop Type",
        choices=FertilizerRecommendationHistory.CropChoices.choices,
        widget=forms.Select(attrs={
            "class": "form-select",
        }),
    )

    soil_color = forms.ChoiceField(
        label="Soil Color",
        choices=FertilizerRecommendationHistory.SoilColorChoices.choices,
        widget=forms.Select(attrs={
            "class": "form-select",
        }),
    )

    N = forms.FloatField(
        label="Nitrogen",
        min_value=0,
        initial=80,
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "placeholder": "Enter Nitrogen value",
            "step": "0.01",
            "min": "0",
        }),
    )

    P = forms.FloatField(
        label="Phosphorus",
        min_value=0,
        initial=50,
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "placeholder": "Enter Phosphorus value",
            "step": "0.01",
            "min": "0",
        }),
    )

    K = forms.FloatField(
        label="Potassium",
        min_value=0,
        initial=100,
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "placeholder": "Enter Potassium value",
            "step": "0.01",
            "min": "0",
        }),
    )

    pH = forms.FloatField(
        label="Soil pH",
        min_value=0,
        max_value=14,
        initial=6.5,
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "placeholder": "Enter soil pH value",
            "step": "0.01",
            "min": "0",
            "max": "14",
        }),
    )

    rainfall = forms.FloatField(
        label="Rainfall",
        min_value=0,
        initial=1000,
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "placeholder": "Enter rainfall value",
            "step": "0.01",
            "min": "0",
        }),
    )

    temperature = forms.FloatField(
        label="Temperature",
        min_value=-50,
        max_value=100,
        initial=25,
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "placeholder": "Enter temperature value",
            "step": "0.01",
            "min": "-50",
            "max": "100",
        }),
    )

    def clean_crop_type(self):
        value = self.cleaned_data.get("crop_type")

        if value:
            value = str(value).strip().title()

        if not value:
            raise ValidationError("Crop is required.")

        if value not in FertilizerRecommendationHistory.CropChoices.values:
            raise ValidationError("Invalid crop selected.")

        return value

    def clean_soil_color(self):
        value = self.cleaned_data.get("soil_color")

        if value:
            value = str(value).strip().title()

        if not value:
            raise ValidationError("Soil color is required.")

        if value not in FertilizerRecommendationHistory.SoilColorChoices.values:
            raise ValidationError("Invalid soil color selected.")

        return value

    def clean_N(self):
        return self._clean_positive_number(
            self.cleaned_data.get("N"),
            "Nitrogen"
        )

    def clean_P(self):
        return self._clean_positive_number(
            self.cleaned_data.get("P"),
            "Phosphorus"
        )

    def clean_K(self):
        return self._clean_positive_number(
            self.cleaned_data.get("K"),
            "Potassium"
        )

    def clean_pH(self):
        value = self.cleaned_data.get("pH")

        if value is None:
            raise ValidationError("pH value is required.")

        value = float(value)

        if value < 0 or value > 14:
            raise ValidationError("pH must be between 0 and 14.")

        return value

    def clean_rainfall(self):
        return self._clean_positive_number(
            self.cleaned_data.get("rainfall"),
            "Rainfall"
        )

    def clean_temperature(self):
        value = self.cleaned_data.get("temperature")

        if value is None:
            raise ValidationError("Temperature is required.")

        value = float(value)

        if value < -50 or value > 100:
            raise ValidationError("Temperature must be between -50 and 100.")

        return value

    def _clean_positive_number(self, value, field_label):
        if value is None:
            raise ValidationError(f"{field_label} value is required.")

        value = float(value)

        if value < 0:
            raise ValidationError(f"{field_label} cannot be negative.")

        return value


# ======================================================
# 2. HISTORY FORM
# Used by Admin to create/edit history records
# Farmer should normally only view history
# ======================================================
class FertilizerRecommendationHistoryForm(forms.ModelForm):
    class Meta:
        model = FertilizerRecommendationHistory
        fields = [
            "user",
            "user_type",
            "crop",
            "soil_color",
            "nitrogen",
            "phosphorus",
            "potassium",
            "ph",
            "rainfall",
            "temperature",
            "recommendation_result",
        ]

        widgets = {
            "user": forms.Select(attrs={
                "class": "form-select",
            }),
            "user_type": forms.Select(attrs={
                "class": "form-select",
            }),
            "crop": forms.Select(attrs={
                "class": "form-select",
            }),
            "soil_color": forms.Select(attrs={
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
            "ph": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter pH value",
                "step": "0.01",
                "min": "0",
                "max": "14",
            }),
            "rainfall": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter rainfall value",
                "step": "0.01",
                "min": "0",
            }),
            "temperature": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter temperature value",
                "step": "0.01",
                "min": "-50",
                "max": "100",
            }),
            "recommendation_result": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": "Enter recommendation result JSON",
            }),
        }

    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop("request_user", None)
        self.request_user_type = kwargs.pop("request_user_type", None)

        super().__init__(*args, **kwargs)

        required_fields = [
            "user",
            "user_type",
            "crop",
            "soil_color",
            "nitrogen",
            "phosphorus",
            "potassium",
            "ph",
            "rainfall",
            "temperature",
            "recommendation_result",
        ]

        for field_name in required_fields:
            self.fields[field_name].required = True

        if self.request_user:
            self.fields["user"].initial = self.request_user

        if self.request_user_type:
            self.fields["user_type"].initial = self.request_user_type

    def clean_user_type(self):
        value = self.cleaned_data.get("user_type")

        if value:
            value = str(value).strip().lower()

        if not value:
            raise ValidationError("User type is required.")

        if value not in FertilizerRecommendationHistory.UserTypeChoices.values:
            raise ValidationError("Invalid user type selected.")

        return value

    def clean_crop(self):
        value = self.cleaned_data.get("crop")

        if value:
            value = str(value).strip().title()

        if not value:
            raise ValidationError("Crop is required.")

        if value not in FertilizerRecommendationHistory.CropChoices.values:
            raise ValidationError("Invalid crop selected.")

        return value

    def clean_soil_color(self):
        value = self.cleaned_data.get("soil_color")

        if value:
            value = str(value).strip().title()

        if not value:
            raise ValidationError("Soil color is required.")

        if value not in FertilizerRecommendationHistory.SoilColorChoices.values:
            raise ValidationError("Invalid soil color selected.")

        return value

    def clean_nitrogen(self):
        return self._clean_positive_number(
            self.cleaned_data.get("nitrogen"),
            "Nitrogen"
        )

    def clean_phosphorus(self):
        return self._clean_positive_number(
            self.cleaned_data.get("phosphorus"),
            "Phosphorus"
        )

    def clean_potassium(self):
        return self._clean_positive_number(
            self.cleaned_data.get("potassium"),
            "Potassium"
        )

    def clean_ph(self):
        value = self.cleaned_data.get("ph")

        if value is None:
            raise ValidationError("pH value is required.")

        value = float(value)

        if value < 0 or value > 14:
            raise ValidationError("pH must be between 0 and 14.")

        return value

    def clean_rainfall(self):
        return self._clean_positive_number(
            self.cleaned_data.get("rainfall"),
            "Rainfall"
        )

    def clean_temperature(self):
        value = self.cleaned_data.get("temperature")

        if value is None:
            raise ValidationError("Temperature is required.")

        value = float(value)

        if value < -50 or value > 100:
            raise ValidationError("Temperature must be between -50 and 100.")

        return value

    def clean_recommendation_result(self):
        value = self.cleaned_data.get("recommendation_result")

        if not value:
            raise ValidationError("Recommendation result is required.")

        if not isinstance(value, dict):
            raise ValidationError("Recommendation result must be a valid JSON object.")

        return value

    def _clean_positive_number(self, value, field_label):
        if value is None:
            raise ValidationError(f"{field_label} value is required.")

        value = float(value)

        if value < 0:
            raise ValidationError(f"{field_label} cannot be negative.")

        return value

    def clean(self):
        cleaned_data = super().clean()

        user = cleaned_data.get("user")
        user_type = cleaned_data.get("user_type")
        crop = cleaned_data.get("crop")
        soil_color = cleaned_data.get("soil_color")

        if not user:
            self.add_error("user", "User is required.")

        if not user_type:
            self.add_error("user_type", "User type is required.")

        if not crop:
            self.add_error("crop", "Crop is required.")

        if not soil_color:
            self.add_error("soil_color", "Soil color is required.")

        if self.request_user and user and user != self.request_user:
            self.add_error(
                "user",
                "You cannot create recommendation history for another user."
            )

        return cleaned_data