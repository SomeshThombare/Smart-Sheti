from django.db import models
from django.core.validators import RegexValidator, FileExtensionValidator
from django.core.exceptions import ValidationError
from django.utils.text import slugify


class GovernmentScheme(models.Model):
    class StatusChoices(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"

    class CategoryChoices(models.TextChoices):
        CENTRAL = "central", "Central Government"
        STATE = "state", "State Government"
        LOAN = "loan", "Loan"
        SUBSIDY = "subsidy", "Subsidy"
        GRANT = "grant", "Grant"
        INSURANCE = "insurance", "Insurance"
        OTHER = "other", "Other"

    scheme_name = models.CharField(max_length=200)

    scheme_code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        validators=[
            RegexValidator(
                regex=r"^[A-Z0-9_-]+$",
                message="Scheme code must contain only uppercase letters, numbers, underscore, or hyphen.",
            )
        ],
    )

    slug = models.SlugField(
        max_length=220,
        unique=True,
        blank=True,
        db_index=True,
    )

    category = models.CharField(
        max_length=20,
        choices=CategoryChoices.choices,
        default=CategoryChoices.OTHER,
        db_index=True,
    )

    short_description = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )

    description = models.TextField()

    benefits = models.TextField()

    eligibility = models.TextField()

    required_documents = models.TextField(
        blank=True,
        null=True,
    )

    state = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    country = models.CharField(
        max_length=100,
        default="India",
    )

    start_date = models.DateField()

    end_date = models.DateField(
        blank=True,
        null=True,
    )

    official_link = models.URLField(
        blank=True,
        null=True,
    )

    apply_link = models.URLField(
        blank=True,
        null=True,
    )

    scheme_image = models.ImageField(
        upload_to="government_schemes/images/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["jpg", "jpeg", "png", "webp"],
            )
        ],
    )

    scheme_document = models.FileField(
        upload_to="government_schemes/documents/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["pdf", "doc", "docx"],
            )
        ],
    )

    contact_person = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    contact_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r"^[0-9+\- ]{8,15}$",
                message="Enter a valid contact number.",
            )
        ],
    )

    status = models.CharField(
        max_length=10,
        choices=StatusChoices.choices,
        default=StatusChoices.ACTIVE,
        db_index=True,
    )

    is_featured = models.BooleanField(
        default=False,
        db_index=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Government Scheme"
        verbose_name_plural = "Government Schemes"
        indexes = [
            models.Index(fields=["scheme_code"]),
            models.Index(fields=["slug"]),
            models.Index(fields=["category"]),
            models.Index(fields=["status"]),
            models.Index(fields=["is_featured"]),
            models.Index(fields=["start_date"]),
            models.Index(fields=["end_date"]),
            models.Index(fields=["category", "status"]),
            models.Index(fields=["status", "is_featured"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(end_date__isnull=True)
                    | models.Q(end_date__gte=models.F("start_date"))
                ),
                name="government_scheme_end_date_gte_start_date",
            )
        ]

    def __str__(self):
        return f"{self.scheme_name} ({self.scheme_code})"

    # =========================
    # Validation
    # =========================
    def clean(self):
        self._normalize_fields()

        errors = {}

        if not self.scheme_name:
            errors["scheme_name"] = "Scheme name is required."

        if not self.scheme_code:
            errors["scheme_code"] = "Scheme code is required."

        if not self.description:
            errors["description"] = "Description is required."

        if not self.benefits:
            errors["benefits"] = "Benefits are required."

        if not self.eligibility:
            errors["eligibility"] = "Eligibility is required."

        if not self.start_date:
            errors["start_date"] = "Start date is required."

        if self.start_date and self.end_date and self.end_date < self.start_date:
            errors["end_date"] = "End date cannot be earlier than start date."

        if self.category == self.CategoryChoices.STATE and not self.state:
            errors["state"] = "State is required for state government schemes."

        if self.official_link and not str(self.official_link).startswith(("http://", "https://")):
            errors["official_link"] = "Official link must start with http:// or https://."

        if self.apply_link and not str(self.apply_link).startswith(("http://", "https://")):
            errors["apply_link"] = "Apply link must start with http:// or https://."

        if self.pk:
            old_obj = (
                GovernmentScheme.objects
                .filter(pk=self.pk)
                .only("scheme_code")
                .first()
            )

            if old_obj and old_obj.scheme_code != self.scheme_code:
                errors["scheme_code"] = "Scheme code cannot be changed once created."

        if errors:
            raise ValidationError(errors)

    # =========================
    # Save
    # =========================
    def save(self, *args, **kwargs):
        self._normalize_fields()

        if not self.slug:
            self.slug = self._generate_unique_slug()

        self.full_clean()
        super().save(*args, **kwargs)

    # =========================
    # Normalization
    # =========================
    def _normalize_fields(self):
        nullable_text_fields = [
            "short_description",
            "required_documents",
            "state",
            "contact_person",
            "contact_number",
        ]

        required_text_fields = [
            "scheme_name",
            "description",
            "benefits",
            "eligibility",
            "country",
        ]

        for field in nullable_text_fields:
            value = getattr(self, field, None)

            if isinstance(value, str):
                value = value.strip()
                setattr(self, field, value if value else None)

        for field in required_text_fields:
            value = getattr(self, field, None)

            if isinstance(value, str):
                setattr(self, field, value.strip())

        if self.scheme_code:
            self.scheme_code = str(self.scheme_code).strip().upper()

        if self.country:
            self.country = str(self.country).strip().title()
        else:
            self.country = "India"

        if self.state:
            self.state = str(self.state).strip().title()

        if self.contact_person:
            self.contact_person = str(self.contact_person).strip().title()

    # =========================
    # Slug
    # =========================
    def _generate_unique_slug(self):
        base_value = self.scheme_name or self.scheme_code or "scheme"
        base_slug = slugify(base_value) or "scheme"

        slug = base_slug
        counter = 1

        while (
            GovernmentScheme.objects
            .filter(slug=slug)
            .exclude(pk=self.pk)
            .exists()
        ):
            slug = f"{base_slug}-{counter}"
            counter += 1

        return slug