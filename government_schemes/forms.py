from django import forms
from django.core.exceptions import ValidationError
from .models import GovernmentScheme


class GovernmentSchemeForm(forms.ModelForm):
    class Meta:
        model = GovernmentScheme
        fields = [
            "scheme_name",
            "scheme_code",
            "category",
            "short_description",
            "description",
            "benefits",
            "eligibility",
            "required_documents",
            "state",
            "country",
            "start_date",
            "end_date",
            "official_link",
            "apply_link",
            "scheme_image",
            "scheme_document",
            "contact_person",
            "contact_number",
            "status",
            "is_featured",
        ]

        widgets = {
            "scheme_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter scheme name",
            }),
            "scheme_code": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter scheme code",
            }),
            "category": forms.Select(attrs={
                "class": "form-select",
            }),
            "short_description": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter short description",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Enter full description",
            }),
            "benefits": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Enter scheme benefits",
            }),
            "eligibility": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Enter eligibility details",
            }),
            "required_documents": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Enter required documents",
            }),
            "state": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter state name",
            }),
            "country": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter country name",
            }),
            "start_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),
            "end_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),
            "official_link": forms.URLInput(attrs={
                "class": "form-control",
                "placeholder": "Enter official website link",
            }),
            "apply_link": forms.URLInput(attrs={
                "class": "form-control",
                "placeholder": "Enter apply link",
            }),
            "scheme_image": forms.ClearableFileInput(attrs={
                "class": "form-control",
                "accept": "image/jpeg,image/jpg,image/png,image/webp",
            }),
            "scheme_document": forms.ClearableFileInput(attrs={
                "class": "form-control",
                "accept": ".pdf,.doc,.docx",
            }),
            "contact_person": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter contact person name",
            }),
            "contact_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter contact number",
            }),
            "status": forms.Select(attrs={
                "class": "form-select",
            }),
            "is_featured": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        required_fields = [
            "scheme_name",
            "scheme_code",
            "description",
            "benefits",
            "eligibility",
            "start_date",
            "country",
        ]

        for field_name in required_fields:
            self.fields[field_name].required = True

        self.fields["country"].initial = "India"

        if self.instance and self.instance.pk:
            self.fields["scheme_code"].disabled = True
            self.fields["scheme_code"].required = False

    # =========================
    # Text Cleaning
    # =========================
    def clean_scheme_name(self):
        scheme_name = self.cleaned_data.get("scheme_name")

        if scheme_name:
            scheme_name = scheme_name.strip()

        if not scheme_name:
            raise ValidationError("Scheme name is required.")

        return scheme_name

    def clean_scheme_code(self):
        scheme_code = self.cleaned_data.get("scheme_code")

        if self.instance and self.instance.pk:
            return self.instance.scheme_code

        if scheme_code:
            scheme_code = scheme_code.strip().upper()

        if not scheme_code:
            raise ValidationError("Scheme code is required.")

        qs = GovernmentScheme.objects.filter(scheme_code=scheme_code)

        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise ValidationError("This scheme code already exists.")

        return scheme_code

    def clean_short_description(self):
        value = self.cleaned_data.get("short_description")
        return value.strip() if value else value

    def clean_description(self):
        value = self.cleaned_data.get("description")

        if value:
            value = value.strip()

        if not value:
            raise ValidationError("Description is required.")

        return value

    def clean_benefits(self):
        value = self.cleaned_data.get("benefits")

        if value:
            value = value.strip()

        if not value:
            raise ValidationError("Benefits are required.")

        return value

    def clean_eligibility(self):
        value = self.cleaned_data.get("eligibility")

        if value:
            value = value.strip()

        if not value:
            raise ValidationError("Eligibility is required.")

        return value

    def clean_required_documents(self):
        value = self.cleaned_data.get("required_documents")
        return value.strip() if value else value

    def clean_state(self):
        value = self.cleaned_data.get("state")
        return value.strip() if value else value

    def clean_country(self):
        value = self.cleaned_data.get("country")

        if value:
            value = value.strip()

        return value or "India"

    def clean_contact_person(self):
        value = self.cleaned_data.get("contact_person")
        return value.strip() if value else value

    def clean_contact_number(self):
        value = self.cleaned_data.get("contact_number")

        if value:
            value = value.strip()
            digits = (
                value.replace("+", "")
                .replace("-", "")
                .replace(" ", "")
            )

            if not digits.isdigit():
                raise ValidationError(
                    "Contact number must contain only digits, spaces, +, or -."
                )

            if len(digits) < 10:
                raise ValidationError(
                    "Contact number must be at least 10 digits."
                )

        return value

    # =========================
    # File Validation
    # =========================
    def clean_scheme_image(self):
        image = self.cleaned_data.get("scheme_image")

        if image:
            max_size = 2 * 1024 * 1024

            if image.size > max_size:
                raise ValidationError("Scheme image size must not exceed 2 MB.")

            allowed_content_types = [
                "image/jpeg",
                "image/jpg",
                "image/png",
                "image/webp",
            ]

            content_type = getattr(image, "content_type", None)

            if content_type and content_type not in allowed_content_types:
                raise ValidationError(
                    "Only JPG, JPEG, PNG, and WEBP images are allowed."
                )

        return image

    def clean_scheme_document(self):
        document = self.cleaned_data.get("scheme_document")

        if document:
            max_size = 5 * 1024 * 1024

            if document.size > max_size:
                raise ValidationError("Scheme document size must not exceed 5 MB.")

            allowed_content_types = [
                "application/pdf",
                "application/msword",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ]

            content_type = getattr(document, "content_type", None)

            if content_type and content_type not in allowed_content_types:
                raise ValidationError(
                    "Only PDF, DOC, and DOCX documents are allowed."
                )

        return document

    # =========================
    # Object Level Validation
    # =========================
    def clean(self):
        cleaned_data = super().clean()

        category = cleaned_data.get("category")
        state = cleaned_data.get("state")
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        official_link = cleaned_data.get("official_link")
        apply_link = cleaned_data.get("apply_link")

        if category == GovernmentScheme.CategoryChoices.STATE and not state:
            self.add_error(
                "state",
                "State is required for state government schemes.",
            )

        if start_date and end_date and end_date < start_date:
            self.add_error(
                "end_date",
                "End date cannot be earlier than start date.",
            )

        if official_link and not str(official_link).startswith(("http://", "https://")):
            self.add_error(
                "official_link",
                "Official link must start with http:// or https://.",
            )

        if apply_link and not str(apply_link).startswith(("http://", "https://")):
            self.add_error(
                "apply_link",
                "Apply link must start with http:// or https://.",
            )

        return cleaned_data