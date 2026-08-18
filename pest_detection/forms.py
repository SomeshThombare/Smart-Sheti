# pest_detection/forms.py

from django import forms

from .models import PestPrediction


ALLOWED_IMAGE_TYPES = [
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
]

ALLOWED_IMAGE_EXTENSIONS = [
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
]

MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB


class PestUploadForm(forms.Form):
    image = forms.ImageField(
        required=True,
        widget=forms.ClearableFileInput(
            attrs={
                "class": "form-control",
                "accept": "image/jpeg,image/jpg,image/png,image/webp",
            }
        ),
        error_messages={
            "required": "Please upload pest image.",
            "invalid": "Please upload a valid image file.",
        },
    )

    def clean_image(self):
        image = self.cleaned_data.get("image")

        if not image:
            raise forms.ValidationError("Please upload pest image.")

        if image.size > MAX_IMAGE_SIZE:
            raise forms.ValidationError("Image size must be less than 5 MB.")

        content_type = getattr(image, "content_type", "")

        if content_type not in ALLOWED_IMAGE_TYPES:
            raise forms.ValidationError(
                "Only JPG, JPEG, PNG and WEBP images are allowed."
            )

        file_name = image.name.lower()

        if not any(file_name.endswith(ext) for ext in ALLOWED_IMAGE_EXTENSIONS):
            raise forms.ValidationError(
                "Only .jpg, .jpeg, .png and .webp files are allowed."
            )

        return image


class PestPredictionSearchForm(forms.Form):
    STATUS_CHOICES = [
        ("", "All Status"),
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
    ]

    SORT_CHOICES = [
        ("-date", "Newest First"),
        ("date", "Oldest First"),
        ("-confidence", "High Confidence"),
        ("confidence", "Low Confidence"),
        ("pest_name", "Pest Name A-Z"),
        ("-pest_name", "Pest Name Z-A"),
        ("status", "Status A-Z"),
        ("-status", "Status Z-A"),
    ]

    PAGE_SIZE_CHOICES = [
        ("10", "10"),
        ("20", "20"),
        ("50", "50"),
        ("100", "100"),
    ]

    search = forms.CharField(
        required=False,
        max_length=255,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Search farmer, email, pest name or class name",
            }
        ),
    )

    status = forms.ChoiceField(
        required=False,
        choices=STATUS_CHOICES,
        widget=forms.Select(
            attrs={
                "class": "form-control",
            }
        ),
    )

    pest_name = forms.CharField(
        required=False,
        max_length=255,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter pest name",
            }
        ),
    )

    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "form-control",
            }
        ),
    )

    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "form-control",
            }
        ),
    )

    min_confidence = forms.FloatField(
        required=False,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "Min confidence",
                "step": "0.01",
            }
        ),
    )

    max_confidence = forms.FloatField(
        required=False,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "Max confidence",
                "step": "0.01",
            }
        ),
    )

    sort = forms.ChoiceField(
        required=False,
        choices=SORT_CHOICES,
        widget=forms.Select(
            attrs={
                "class": "form-control",
            }
        ),
    )

    page_size = forms.ChoiceField(
        required=False,
        choices=PAGE_SIZE_CHOICES,
        widget=forms.Select(
            attrs={
                "class": "form-control",
            }
        ),
    )

    def clean(self):
        cleaned_data = super().clean()

        date_from = cleaned_data.get("date_from")
        date_to = cleaned_data.get("date_to")
        min_confidence = cleaned_data.get("min_confidence")
        max_confidence = cleaned_data.get("max_confidence")

        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError(
                "Date from cannot be greater than date to."
            )

        if (
            min_confidence is not None
            and max_confidence is not None
            and min_confidence > max_confidence
        ):
            raise forms.ValidationError(
                "Minimum confidence cannot be greater than maximum confidence."
            )

        return cleaned_data


class PestPredictionAdminForm(forms.ModelForm):
    class Meta:
        model = PestPrediction
        fields = [
            "pest_name",
            "confidence",
            "solution",
            "class_name",
            "predicted_index",
            "severity",
            "treatment_priority",
            "top_predictions",
            "status",
            "error_message",
        ]

        widgets = {
            "pest_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Pest name",
                }
            ),
            "confidence": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "max": "100",
                }
            ),
            "solution": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": "Solution",
                }
            ),
            "class_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Class name",
                }
            ),
            "predicted_index": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                }
            ),
            "severity": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
            "treatment_priority": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Treatment priority",
                }
            ),
            "top_predictions": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Top predictions JSON",
                }
            ),
            "status": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
            "error_message": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Error message",
                }
            ),
        }

    def clean_confidence(self):
        confidence = self.cleaned_data.get("confidence")

        if confidence is None:
            return 0

        if confidence < 0 or confidence > 100:
            raise forms.ValidationError("Confidence must be between 0 and 100.")

        return confidence