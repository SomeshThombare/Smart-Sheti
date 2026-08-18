from django import forms


class DiseaseUploadForm(forms.Form):
    image = forms.ImageField(
        label="Upload Crop Image",
        widget=forms.FileInput(
            attrs={
                "class": "form-control",
                "accept": "image/jpeg,image/png,image/jpg",
            }
        )
    )


class PredictionSearchForm(forms.Form):
    search = forms.CharField(
        required=False,
        label="Search",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Search farmer, crop, disease...",
            }
        )
    )

    crop = forms.CharField(
        required=False,
        label="Crop",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Example: Rice",
            }
        )
    )

    status = forms.ChoiceField(
        required=False,
        choices=(
            ("", "All Status"),
            ("SUCCESS", "Success"),
            ("FAILED", "Failed"),
        ),
        widget=forms.Select(attrs={"class": "form-control"})
    )