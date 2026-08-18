from django.contrib import admin
from django.utils.html import format_html
from .models import GovernmentScheme
from .forms import GovernmentSchemeForm


@admin.register(GovernmentScheme)
class GovernmentSchemeAdmin(admin.ModelAdmin):
    form = GovernmentSchemeForm

    list_display = (
        "scheme_name",
        "scheme_code",
        "category",
        "state",
        "country",
        "status",
        "is_featured",
        "start_date",
        "end_date",
        "scheme_image_thumb",
        "created_at",
    )

    list_filter = (
        "category",
        "status",
        "is_featured",
        "country",
        "state",
        "start_date",
        "end_date",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "scheme_name",
        "scheme_code",
        "slug",
        "short_description",
        "description",
        "benefits",
        "eligibility",
        "required_documents",
        "state",
        "country",
        "contact_person",
        "contact_number",
    )

    readonly_fields = (
        "slug",
        "created_at",
        "updated_at",
        "scheme_image_preview",
        "scheme_document_link",
    )

    ordering = ("-created_at",)
    list_per_page = 20
    date_hierarchy = "created_at"
    list_editable = ("status", "is_featured")
    save_on_top = True

    fieldsets = (
        ("Scheme Information", {
            "fields": (
                "scheme_name",
                "scheme_code",
                "slug",
                "category",
                "short_description",
                "description",
                "benefits",
                "eligibility",
                "required_documents",
            )
        }),
        ("Location & Validity", {
            "fields": (
                "state",
                "country",
                "start_date",
                "end_date",
            )
        }),
        ("Links & Files", {
            "fields": (
                "official_link",
                "apply_link",
                "scheme_image",
                "scheme_image_preview",
                "scheme_document",
                "scheme_document_link",
            )
        }),
        ("Contact Details", {
            "fields": (
                "contact_person",
                "contact_number",
            )
        }),
        ("Status Settings", {
            "fields": (
                "status",
                "is_featured",
            )
        }),
        ("System Information", {
            "fields": (
                "created_at",
                "updated_at",
            ),
            "classes": ("collapse",),
        }),
    )

    actions = (
        "mark_as_active",
        "mark_as_inactive",
        "mark_as_featured",
        "remove_from_featured",
    )

    def get_queryset(self, request):
        return super().get_queryset(request).only(
            "id",
            "scheme_name",
            "scheme_code",
            "slug",
            "category",
            "state",
            "country",
            "status",
            "is_featured",
            "start_date",
            "end_date",
            "scheme_image",
            "scheme_document",
            "created_at",
            "updated_at",
        )

    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)

        if obj:
            readonly.append("scheme_code")

        return readonly

    def scheme_image_preview(self, obj):
        if obj and obj.scheme_image:
            return format_html(
                """
                <img src="{}"
                     width="160"
                     height="100"
                     style="object-fit:cover; border-radius:8px; border:1px solid #ccc;" />
                """,
                obj.scheme_image.url,
            )

        return "No Image"

    scheme_image_preview.short_description = "Image Preview"

    def scheme_image_thumb(self, obj):
        if obj and obj.scheme_image:
            return format_html(
                """
                <img src="{}"
                     width="60"
                     height="40"
                     style="object-fit:cover; border-radius:4px; border:1px solid #ccc;" />
                """,
                obj.scheme_image.url,
            )

        return "-"

    scheme_image_thumb.short_description = "Image"

    def scheme_document_link(self, obj):
        if obj and obj.scheme_document:
            return format_html(
                '<a href="{}" target="_blank" style="font-weight:600;">View Document</a>',
                obj.scheme_document.url,
            )

        return "No Document"

    scheme_document_link.short_description = "Document"

    @admin.action(description="Mark selected schemes as Active")
    def mark_as_active(self, request, queryset):
        updated = queryset.update(status=GovernmentScheme.StatusChoices.ACTIVE)
        self.message_user(request, f"{updated} scheme(s) marked as Active.")

    @admin.action(description="Mark selected schemes as Inactive")
    def mark_as_inactive(self, request, queryset):
        updated = queryset.update(status=GovernmentScheme.StatusChoices.INACTIVE)
        self.message_user(request, f"{updated} scheme(s) marked as Inactive.")

    @admin.action(description="Mark selected schemes as Featured")
    def mark_as_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f"{updated} scheme(s) marked as Featured.")

    @admin.action(description="Remove selected schemes from Featured")
    def remove_from_featured(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f"{updated} scheme(s) removed from Featured.")