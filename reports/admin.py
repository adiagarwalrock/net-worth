"""
Admin configuration for StatementUpload model.
"""
from django.contrib import admin
from .models import StatementUpload


@admin.register(StatementUpload)
class StatementUploadAdmin(admin.ModelAdmin):
    """
    Admin interface for StatementUpload model.
    """
    list_display = ['user', 'upload_type', 'status', 'confidence_score', 'uploaded_at', 'processed_at', 'is_processed', 'is_successful']
    list_filter = ['status', 'upload_type', 'uploaded_at', 'processed_at']
    search_fields = ['user__username', 'error_message']
    ordering = ['-uploaded_at']
    readonly_fields = ['uploaded_at', 'processed_at', 'is_processed', 'is_successful']
    date_hierarchy = 'uploaded_at'

    fieldsets = (
        ('Upload Information', {
            'fields': ('user', 'file', 'upload_type'),
        }),
        ('Processing Status', {
            'fields': ('status', 'confidence_score', 'is_processed', 'is_successful'),
        }),
        ('Parsed Data', {
            'fields': ('parsed_data',),
            'classes': ('collapse',),
        }),
        ('Error Information', {
            'fields': ('error_message',),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('uploaded_at', 'processed_at'),
            'classes': ('collapse',),
        }),
    )

    def get_queryset(self, request):
        """Optimize query with select_related."""
        return super().get_queryset(request).select_related('user')

    actions = ['mark_as_pending', 'mark_as_processing']

    def mark_as_pending(self, request, queryset):
        """Mark selected uploads as pending."""
        updated = queryset.update(status=StatementUpload.PENDING)
        self.message_user(request, f"{updated} statement(s) marked as pending.")
    mark_as_pending.short_description = "Mark selected as Pending"

    def mark_as_processing(self, request, queryset):
        """Mark selected uploads as processing."""
        for upload in queryset:
            upload.mark_as_processing()
        self.message_user(request, f"{queryset.count()} statement(s) marked as processing.")
    mark_as_processing.short_description = "Mark selected as Processing"
