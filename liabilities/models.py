"""
Liability tracking models for various debt types.
"""
from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class Liability(models.Model):
    """
    Represents a financial liability (debt) owed by a user.

    Supports multiple liability types:
    - Credit Cards
    - Mortgages/Home Loans
    - Auto Loans
    - Student Loans
    - Medical Loans
    - Personal Loans
    - Other Debts

    Attributes:
        user: Owner of this liability
        name: Liability name/description
        liability_type: Category of liability
        balance: Current outstanding balance
        currency: Currency in which balance is denominated
        creditor: Lender/creditor name
        account_number: Last 4 digits or masked account number (optional)
        interest_rate: Annual interest rate percentage
        monthly_payment: Monthly payment amount
        credit_limit: Credit limit (for credit cards)
        payment_due_date: Day of month payment is due
        notes: Additional notes
        is_active: Soft delete flag
        created_at: Creation timestamp
        updated_at: Last update timestamp
        last_valued_at: When balance was last updated
    """
    # Liability Type Choices
    CREDIT_CARD = 'CREDIT_CARD'
    MORTGAGE = 'MORTGAGE'
    AUTO_LOAN = 'AUTO_LOAN'
    STUDENT_LOAN = 'STUDENT_LOAN'
    MEDICAL_LOAN = 'MEDICAL_LOAN'
    PERSONAL_LOAN = 'PERSONAL_LOAN'
    LINE_OF_CREDIT = 'LINE_OF_CREDIT'
    OTHER = 'OTHER'

    LIABILITY_TYPE_CHOICES = [
        (CREDIT_CARD, 'Credit Card'),
        (MORTGAGE, 'Mortgage/Home Loan'),
        (AUTO_LOAN, 'Auto/Vehicle Loan'),
        (STUDENT_LOAN, 'Student/Education Loan'),
        (MEDICAL_LOAN, 'Medical Loan'),
        (PERSONAL_LOAN, 'Personal Loan'),
        (LINE_OF_CREDIT, 'Line of Credit'),
        (OTHER, 'Other'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='liabilities',
        help_text="Owner of this liability"
    )
    name = models.CharField(
        max_length=200,
        help_text="Liability name or description"
    )
    liability_type = models.CharField(
        max_length=20,
        choices=LIABILITY_TYPE_CHOICES,
        help_text="Category of liability"
    )
    balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Current outstanding balance"
    )
    currency = models.ForeignKey(
        'currencies.Currency',
        on_delete=models.PROTECT,
        related_name='liabilities',
        help_text="Currency in which balance is denominated"
    )
    creditor = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Lender or creditor name"
    )
    account_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Masked account number (e.g., ****1234)"
    )
    interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[
            MinValueValidator(Decimal('0.00')),
            MaxValueValidator(Decimal('100.00'))
        ],
        help_text="Annual interest rate percentage (e.g., 5.25 for 5.25%)"
    )
    monthly_payment = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Monthly payment amount"
    )
    credit_limit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Credit limit (for credit cards and lines of credit)"
    )
    payment_due_date = models.IntegerField(
        blank=True,
        null=True,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(31)
        ],
        help_text="Day of month payment is due (1-31)"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes about this liability"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this liability is currently active (soft delete)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_valued_at = models.DateTimeField(
        auto_now=True,
        help_text="When balance was last updated"
    )

    class Meta:
        verbose_name = "Liability"
        verbose_name_plural = "Liabilities"
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', 'liability_type', 'is_active']),
            models.Index(fields=['user', 'is_active', '-updated_at']),
        ]

    def __str__(self):
        return f"{self.name} - {self.currency.code} {self.balance}"

    def get_balance_in_currency(self, target_currency):
        """
        Convert liability balance to target currency.

        Args:
            target_currency: Currency object to convert to

        Returns:
            Decimal: Balance in target currency
        """
        if self.currency == target_currency:
            return self.balance

        from currencies.services import CurrencyService
        return CurrencyService.convert(
            amount=self.balance,
            from_currency=self.currency,
            to_currency=target_currency
        )

    def get_credit_utilization(self):
        """
        Calculate credit utilization percentage (for credit cards).

        Returns:
            Decimal: Credit utilization percentage or None if not applicable
        """
        if self.liability_type == self.CREDIT_CARD and self.credit_limit:
            if self.credit_limit > 0:
                return (self.balance / self.credit_limit) * 100
        return None

    def save(self, *args, **kwargs):
        """
        Override save to create history record on balance change.
        """
        is_new = self.pk is None
        old_balance = None

        if not is_new:
            try:
                old_liability = Liability.objects.get(pk=self.pk)
                old_balance = old_liability.balance
            except Liability.DoesNotExist:
                pass

        super().save(*args, **kwargs)

        # Create history record if balance changed or new liability
        if is_new or (old_balance and old_balance != self.balance):
            LiabilityHistory.objects.create(
                liability=self,
                balance=self.balance,
                currency=self.currency,
                source=LiabilityHistory.MANUAL
            )


class LiabilityHistory(models.Model):
    """
    Historical record of liability balances over time.

    Attributes:
        liability: Liability this history belongs to
        balance: Balance at this point in time
        currency: Currency of the balance
        recorded_at: Timestamp of this record
        source: How this balance was recorded
    """
    MANUAL = 'MANUAL'
    STATEMENT_UPLOAD = 'STATEMENT_UPLOAD'
    API_SYNC = 'API_SYNC'

    SOURCE_CHOICES = [
        (MANUAL, 'Manual Entry'),
        (STATEMENT_UPLOAD, 'Statement Upload'),
        (API_SYNC, 'API Sync'),
    ]

    liability = models.ForeignKey(
        Liability,
        on_delete=models.CASCADE,
        related_name='history',
        help_text="Liability this history belongs to"
    )
    balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Balance at this point in time"
    )
    currency = models.ForeignKey(
        'currencies.Currency',
        on_delete=models.PROTECT,
        related_name='liability_history',
        help_text="Currency of the balance"
    )
    recorded_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp of this record"
    )
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default=MANUAL,
        help_text="How this balance was recorded"
    )

    class Meta:
        verbose_name = "Liability History"
        verbose_name_plural = "Liability Histories"
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['liability', '-recorded_at']),
        ]

    def __str__(self):
        return f"{self.liability.name} - {self.currency.code} {self.balance} at {self.recorded_at}"
