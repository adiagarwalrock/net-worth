"""
Models for statement uploads and parsing.
"""
from django.conf import settings
from django.db import models


class StatementUpload(models.Model):
    """
    Represents an uploaded financial statement for LLM parsing.

    Users can upload bank statements, credit card statements, etc.,
    which are then parsed using LLM to extract financial data.

    Attributes:
        user: User who uploaded the statement
        file: Uploaded file (PDF, CSV, Excel, Image)
        upload_type: Type of statement
        status: Processing status
        parsed_data: JSON data extracted from statement by LLM
        confidence_score: Confidence score of parsing (0-100)
        uploaded_at: When file was uploaded
        processed_at: When processing completed
        error_message: Error message if processing failed
    """
    # Upload Type Choices
    BANK_STATEMENT = 'BANK_STATEMENT'
    CREDIT_CARD_STATEMENT = 'CREDIT_CARD_STATEMENT'
    INVESTMENT_STATEMENT = 'INVESTMENT_STATEMENT'
    LOAN_STATEMENT = 'LOAN_STATEMENT'
    PROPERTY_VALUATION = 'PROPERTY_VALUATION'
    OTHER = 'OTHER'

    UPLOAD_TYPE_CHOICES = [
        (BANK_STATEMENT, 'Bank Statement'),
        (CREDIT_CARD_STATEMENT, 'Credit Card Statement'),
        (INVESTMENT_STATEMENT, 'Investment Statement'),
        (LOAN_STATEMENT, 'Loan Statement'),
        (PROPERTY_VALUATION, 'Property Valuation'),
        (OTHER, 'Other'),
    ]

    # Status Choices
    PENDING = 'PENDING'
    PROCESSING = 'PROCESSING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'
    REVIEWED = 'REVIEWED'

    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (PROCESSING, 'Processing'),
        (COMPLETED, 'Completed'),
        (FAILED, 'Failed'),
        (REVIEWED, 'Reviewed & Confirmed'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='statement_uploads',
        help_text="User who uploaded the statement"
    )
    file = models.FileField(
        upload_to='statements/%Y/%m/%d/',
        help_text="Uploaded statement file"
    )
    upload_type = models.CharField(
        max_length=30,
        choices=UPLOAD_TYPE_CHOICES,
        help_text="Type of financial statement"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING,
        help_text="Processing status"
    )
    parsed_data = models.JSONField(
        null=True,
        blank=True,
        help_text="JSON data extracted from statement by LLM"
    )
    confidence_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Confidence score of parsing (0-100)"
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When file was uploaded"
    )
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When processing completed"
    )
    error_message = models.TextField(
        null=True,
        blank=True,
        help_text="Error message if processing failed"
    )

    class Meta:
        verbose_name = "Statement Upload"
        verbose_name_plural = "Statement Uploads"
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['user', '-uploaded_at']),
            models.Index(fields=['status', '-uploaded_at']),
        ]

    def __str__(self):
        return f"{self.get_upload_type_display()} - {self.user.username} ({self.get_status_display()})"

    @property
    def is_processed(self):
        """Check if statement has been processed."""
        return self.status in [self.COMPLETED, self.REVIEWED, self.FAILED]

    @property
    def is_successful(self):
        """Check if statement was successfully processed."""
        return self.status in [self.COMPLETED, self.REVIEWED]

    def mark_as_processing(self):
        """Mark statement as currently being processed."""
        self.status = self.PROCESSING
        self.save(update_fields=['status'])

    def mark_as_completed(self, parsed_data, confidence_score):
        """
        Mark statement as successfully processed.

        Args:
            parsed_data: Dictionary of parsed data
            confidence_score: Confidence score (0-100)
        """
        from django.utils import timezone
        self.status = self.COMPLETED
        self.parsed_data = parsed_data
        self.confidence_score = confidence_score
        self.processed_at = timezone.now()
        self.save(update_fields=['status', 'parsed_data', 'confidence_score', 'processed_at'])

    def mark_as_failed(self, error_message):
        """
        Mark statement processing as failed.

        Args:
            error_message: Description of the error
        """
        from django.utils import timezone
        self.status = self.FAILED
        self.error_message = error_message
        self.processed_at = timezone.now()
        self.save(update_fields=['status', 'error_message', 'processed_at'])

    def mark_as_reviewed(self):
        """Mark statement as reviewed and confirmed by user."""
        self.status = self.REVIEWED
        self.save(update_fields=['status'])
