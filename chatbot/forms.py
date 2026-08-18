from django import forms


class ChatbotMessageForm(forms.Form):
    message = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Ask your farming question...",
            }
        ),
    )

    image_file = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(
            attrs={
                "class": "form-control",
                "accept": "image/*",
            }
        ),
    )

    pdf_file = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(
            attrs={
                "class": "form-control",
                "accept": "application/pdf",
            }
        ),
    )

    def clean(self):
        cleaned_data = super().clean()

        message = cleaned_data.get("message")
        image_file = cleaned_data.get("image_file")
        pdf_file = cleaned_data.get("pdf_file")

        if not message and not image_file and not pdf_file:
            raise forms.ValidationError(
                "At least one input is required: message, image, or PDF."
            )

        return cleaned_data

    def clean_pdf_file(self):
        pdf_file = self.cleaned_data.get("pdf_file")

        if pdf_file:
            if pdf_file.content_type != "application/pdf":
                raise forms.ValidationError("Only PDF files are allowed.")

            max_size = 5 * 1024 * 1024

            if pdf_file.size > max_size:
                raise forms.ValidationError("PDF file size must be less than 5 MB.")

        return pdf_file

    def clean_image_file(self):
        image_file = self.cleaned_data.get("image_file")

        if image_file:
            allowed_types = [
                "image/jpeg",
                "image/jpg",
                "image/png",
                "image/webp",
            ]

            if image_file.content_type not in allowed_types:
                raise forms.ValidationError(
                    "Only JPG, JPEG, PNG and WEBP images are allowed."
                )

            max_size = 5 * 1024 * 1024

            if image_file.size > max_size:
                raise forms.ValidationError("Image file size must be less than 5 MB.")

        return image_file