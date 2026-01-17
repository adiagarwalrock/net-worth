"""ABOUTME: Centralized enums for all type choices across the application.
ABOUTME: Ensures consistency between database models and LLM extraction schemas.
"""
from enum import Enum


class StrEnum(str, Enum):
    """
    Base class for string enums that work with both Django and Pydantic.

    Inherits from str to ensure values are strings.
    Compatible with Django's choices and Pydantic's field types.
    """

    @classmethod
    def choices(cls):
        """Return Django-compatible choices."""
        return [(member.value, member.name.replace('_', ' ').title()) for member in cls]

    @classmethod
    def values(cls):
        """Return list of all enum values."""
        return [member.value for member in cls]


class AssetType(StrEnum):
    """Asset type enumeration matching database choices."""

    CASH = 'CASH'
    INVESTMENT = 'INVESTMENT'
    REAL_ESTATE = 'REAL_ESTATE'
    VEHICLE = 'VEHICLE'
    PRECIOUS_METALS = 'PRECIOUS_METALS'
    CRYPTOCURRENCY = 'CRYPTOCURRENCY'
    OTHER = 'OTHER'

    @classmethod
    def choices(cls):
        """Return Django-compatible choices with custom labels."""
        return [
            (cls.CASH.value, 'Cash & Bank Accounts'),
            (cls.INVESTMENT.value, 'Investment Portfolio'),
            (cls.REAL_ESTATE.value, 'Real Estate'),
            (cls.VEHICLE.value, 'Vehicle'),
            (cls.PRECIOUS_METALS.value, 'Precious Metals'),
            (cls.CRYPTOCURRENCY.value, 'Cryptocurrency'),
            (cls.OTHER.value, 'Other'),
        ]


class LiabilityType(StrEnum):
    """Liability type enumeration matching database choices."""

    CREDIT_CARD = 'CREDIT_CARD'
    MORTGAGE = 'MORTGAGE'
    AUTO_LOAN = 'AUTO_LOAN'
    STUDENT_LOAN = 'STUDENT_LOAN'
    MEDICAL_LOAN = 'MEDICAL_LOAN'
    PERSONAL_LOAN = 'PERSONAL_LOAN'
    LINE_OF_CREDIT = 'LINE_OF_CREDIT'
    OTHER = 'OTHER'

    @classmethod
    def choices(cls):
        """Return Django-compatible choices with custom labels."""
        return [
            (cls.CREDIT_CARD.value, 'Credit Card'),
            (cls.MORTGAGE.value, 'Mortgage/Home Loan'),
            (cls.AUTO_LOAN.value, 'Auto/Vehicle Loan'),
            (cls.STUDENT_LOAN.value, 'Student/Education Loan'),
            (cls.MEDICAL_LOAN.value, 'Medical Loan'),
            (cls.PERSONAL_LOAN.value, 'Personal Loan'),
            (cls.LINE_OF_CREDIT.value, 'Line of Credit'),
            (cls.OTHER.value, 'Other'),
        ]


class AccountType(StrEnum):
    """
    Account types for statement parsing.
    Maps to either Asset (deposit accounts) or Liability (credit/loan accounts).
    """

    # Deposit accounts (map to Asset.CASH)
    CHECKING = 'CHECKING'
    SAVINGS = 'SAVINGS'
    CURRENT = 'CURRENT'
    MONEY_MARKET = 'MONEY_MARKET'

    # Credit accounts (map to Liability.CREDIT_CARD)
    CREDIT_CARD = 'CREDIT_CARD'

    # Loan accounts (map to various Liability types)
    LOAN = 'LOAN'
    MORTGAGE = 'MORTGAGE'
    AUTO_LOAN = 'AUTO_LOAN'
    STUDENT_LOAN = 'STUDENT_LOAN'
    PERSONAL_LOAN = 'PERSONAL_LOAN'

    @classmethod
    def choices(cls):
        """Return Django-compatible choices with custom labels."""
        return [
            (cls.CHECKING.value, 'Checking Account'),
            (cls.SAVINGS.value, 'Savings Account'),
            (cls.CURRENT.value, 'Current Account'),
            (cls.MONEY_MARKET.value, 'Money Market Account'),
            (cls.CREDIT_CARD.value, 'Credit Card'),
            (cls.LOAN.value, 'Loan (Generic)'),
            (cls.MORTGAGE.value, 'Mortgage'),
            (cls.AUTO_LOAN.value, 'Auto Loan'),
            (cls.STUDENT_LOAN.value, 'Student Loan'),
            (cls.PERSONAL_LOAN.value, 'Personal Loan'),
        ]


class TransactionType(StrEnum):
    """Transaction type enumeration for statement parsing."""

    DEBIT = 'DEBIT'
    CREDIT = 'CREDIT'
    FEE = 'FEE'
    INTEREST = 'INTEREST'
    TRANSFER = 'TRANSFER'
    PAYMENT = 'PAYMENT'
    WITHDRAWAL = 'WITHDRAWAL'
    DEPOSIT = 'DEPOSIT'
    PURCHASE = 'PURCHASE'
    REFUND = 'REFUND'
    OTHER = 'OTHER'


class StatementUploadStatus(StrEnum):
    """Status enumeration for statement upload processing."""

    PENDING = 'PENDING'
    PROCESSING = 'PROCESSING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'


class HistorySource(StrEnum):
    """Source enumeration for tracking how asset/liability values were recorded."""

    MANUAL = 'MANUAL'
    STATEMENT_UPLOAD = 'STATEMENT_UPLOAD'
    API_SYNC = 'API_SYNC'

    @classmethod
    def choices(cls):
        """Return Django-compatible choices with custom labels."""
        return [
            (cls.MANUAL.value, 'Manual Entry'),
            (cls.STATEMENT_UPLOAD.value, 'Statement Upload'),
            (cls.API_SYNC.value, 'API Sync'),
        ]


class HouseholdRole(StrEnum):
    """Household member role enumeration."""

    OWNER = 'OWNER'
    MEMBER = 'MEMBER'
    VIEWER = 'VIEWER'


class InvitationStatus(StrEnum):
    """Household invitation status enumeration."""

    PENDING = 'PENDING'
    ACCEPTED = 'ACCEPTED'
    DECLINED = 'DECLINED'
    EXPIRED = 'EXPIRED'
