"""ABOUTME: Admin configuration for StatementUpload model.
ABOUTME: Includes actions for parsing statements and viewing results.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
import json

from .models import StatementUpload
from .tasks import parse_and_populate_statement


@admin.register(StatementUpload)
class StatementUploadAdmin(admin.ModelAdmin):
    """Admin interface for StatementUpload model with parsing capabilities."""

    list_display = [
        "user",
        "upload_type",
        "status",
        "confidence_score",
        "uploaded_at",
        "processed_at",
        "is_processed",
        "is_successful",
    ]
    list_filter = ["status", "upload_type", "uploaded_at", "processed_at"]
    search_fields = ["user__username", "error_message"]
    ordering = ["-uploaded_at"]
    readonly_fields = [
        "uploaded_at",
        "processed_at",
        "is_processed",
        "is_successful",
        "formatted_parsed_data",
    ]
    date_hierarchy = "uploaded_at"

    fieldsets = (
        (
            "Upload Information",
            {
                "fields": ("user", "file", "upload_type"),
            },
        ),
        (
            "Processing Status",
            {
                "fields": (
                    "status",
                    "confidence_score",
                    "is_processed",
                    "is_successful",
                ),
            },
        ),
        (
            "Parsed Data",
            {
                "fields": ("formatted_parsed_data",),
                "classes": ("collapse",),
            },
        ),
        (
            "Error Information",
            {
                "fields": ("error_message",),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("uploaded_at", "processed_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_queryset(self, request):
        """Optimize query with select_related."""
        return super().get_queryset(request).select_related("user")

    def formatted_parsed_data(self, obj):
        """Display parsed data as formatted JSON.

        Inputs:
            obj: StatementUpload instance

        Outputs:
            HTML formatted JSON or empty string
        """
        if obj.parsed_data:
            try:
                formatted = json.dumps(obj.parsed_data, indent=2)
                return format_html("<pre>{}</pre>", formatted)
            except Exception:
                return str(obj.parsed_data)
        return ""

    formatted_parsed_data.short_description = "Parsed Data (JSON)"

    actions = [
        "mark_as_pending",
        "mark_as_processing",
        "trigger_parsing",
    ]

    def mark_as_pending(self, request, queryset):
        """Mark selected uploads as pending.

        Inputs:
            request: HttpRequest object
            queryset: QuerySet of StatementUpload objects
        """
        updated = queryset.update(status=StatementUpload.PENDING)
        self.message_user(request, f"{updated} statement(s) marked as pending.")

    mark_as_pending.short_description = "Mark selected as Pending"

    def mark_as_processing(self, request, queryset):
        """Mark selected uploads as processing.

        Inputs:
            request: HttpRequest object
            queryset: QuerySet of StatementUpload objects
        """
        for upload in queryset:
            upload.mark_as_processing()
        self.message_user(
            request, f"{queryset.count()} statement(s) marked as processing."
        )

    mark_as_processing.short_description = "Mark selected as Processing"

    def trigger_parsing(self, request, queryset):
        """Trigger Celery task to parse and populate selected statements.

        Inputs:
            request: HttpRequest object
            queryset: QuerySet of StatementUpload objects
        """
        count = 0
        for upload in queryset:
            # Only trigger for PENDING or FAILED statements
            if upload.status in [StatementUpload.PENDING, StatementUpload.FAILED]:
                parse_and_populate_statement.delay(upload.id)
                count += 1

        self.message_user(
            request,
            f"Triggered parsing for {count} statement(s). "
            f"Check back in a few moments for results.",
        )

    trigger_parsing.short_description = "Parse and Populate Selected Statements"
