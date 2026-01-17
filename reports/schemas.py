"""ABOUTME: Pydantic schemas for bank/credit card statement parsing.
ABOUTME: Defines structured output format for LLM-based statement extraction.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import List, Optional, Literal, Dict, Any

from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    field_validator,
    constr,
    condecimal,
)

from common.enums import AccountType, TransactionType

# ---------------------------------------------------------------------------
# Constrained types
# ---------------------------------------------------------------------------

CurrencyCode = constr(pattern=r"^[A-Z]{3}$")
Money = condecimal(max_digits=18, decimal_places=4)
ConfidenceScore = condecimal(ge=0, le=1, max_digits=3, decimal_places=2)


class StatementPeriod(BaseModel):
    """Date range covered by a statement.

    Includes start, end, and issue dates if available.

    Inputs:
        start_date: First date included in this statement period
        end_date: Last date included in this statement period
        statement_issue_date: Official statement issue or generation date
    """

    model_config = ConfigDict(extra="forbid")

    start_date: Optional[date] = Field(
        default=None,
        description="First date included in this statement period, if available.",
    )
    end_date: Optional[date] = Field(
        default=None,
        description="Last date included in this statement period, if available.",
    )
    statement_issue_date: Optional[date] = Field(
        default=None,
        description="Official statement issue or generation date, if present.",
    )


class MerchantInfo(BaseModel):
    """Normalized merchant or counterparty data.

    Helps capture structured details from raw description lines.

    Inputs:
        name: Clean merchant name or counterparty name
        category: Inferred merchant category or MCC-like label
        city: Merchant city or location text
        country: Merchant country code or name
        raw_merchant_line: Original merchant text line from statement
    """

    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = Field(
        default=None,
        description="Clean merchant name or counterparty name.",
    )
    category: Optional[str] = Field(
        default=None,
        description="Inferred merchant category or MCC-like label.",
    )
    city: Optional[str] = Field(
        default=None,
        description="Merchant city or location text if available.",
    )
    country: Optional[str] = Field(
        default=None,
        description="Merchant country code or name if available.",
    )
    raw_merchant_line: Optional[str] = Field(
        default=None,
        description="Original merchant text line exactly as seen in the statement.",
    )


class Transaction(BaseModel):
    """Single transaction entry from a statement.

    Captures dates, amount, type, merchant and optional FX data.

    Inputs:
        transaction_id: Statement specific id or reference number
        posting_date: Posting date recorded by the bank
        transaction_date: Actual date of the transaction
        description: Human readable description from statement
        transaction_type: Normalized semantic type
        amount: Signed amount in account currency
        currency: Three letter currency code
        balance_after_transaction: Running balance after this transaction
        original_amount: Original foreign currency amount
        original_currency: Original foreign currency code
        category: Optional spending or income category
        merchant: Structured merchant data
        metadata: Extra key-value details
    """

    model_config = ConfigDict(extra="forbid")

    transaction_id: Optional[str] = Field(
        default=None,
        description="Statement specific id, reference number, or any unique key if visible.",
    )
    posting_date: Optional[date] = Field(
        default=None,
        description="Posting date recorded by the bank or issuer.",
    )
    transaction_date: Optional[date] = Field(
        default=None,
        description="Actual date of the transaction, if different from posting date.",
    )
    description: str = Field(
        ...,
        description="Human readable description of the transaction from the statement.",
    )

    transaction_type: TransactionType = Field(
        ...,
        description="Normalized semantic type of the transaction.",
    )

    amount: Money = Field(
        ...,
        description=(
            "Signed amount in the account currency. "
            "Use negative for debits if the statement uses signed values."
        ),
    )
    currency: Optional[CurrencyCode] = Field(
        default=None,
        description="Three letter currency code for the transaction. If missing, assume account currency.",
    )

    balance_after_transaction: Optional[Money] = Field(
        default=None,
        description="Running balance immediately after this transaction, if shown.",
    )

    original_amount: Optional[Money] = Field(
        default=None,
        description="Original foreign currency amount, if FX transaction.",
    )
    original_currency: Optional[CurrencyCode] = Field(
        default=None,
        description="Original foreign currency code, if FX transaction.",
    )
    category: Optional[str] = Field(
        default=None,
        description="Optional spending or income category inferred by the model.",
    )
    merchant: Optional[MerchantInfo] = Field(
        default=None,
        description="Structured merchant data extracted from the description.",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Any extra key value details that are useful but not covered by other fields.",
    )

    @field_validator("currency", mode="before")
    @classmethod
    def uppercase_currency(cls, value: Optional[str]) -> Optional[str]:
        """Normalize currency codes to uppercase before validation."""
        return value.upper() if value is not None else None

    @field_validator("original_currency", mode="before")
    @classmethod
    def uppercase_original_currency(cls, value: Optional[str]) -> Optional[str]:
        """Normalize original currency codes to uppercase before validation."""
        return value.upper() if value is not None else None


class RewardsSummary(BaseModel):
    """Rewards or cashback summary.

    Mainly useful for credit card statements.

    Inputs:
        points_earned_in_period: Total reward points/miles earned
        points_redeemed_in_period: Total reward points/miles redeemed
        points_balance_end: Reward points/miles balance at end
        cashback_earned_in_period: Total cashback earned
        cashback_redeemed_in_period: Total cashback redeemed
    """

    model_config = ConfigDict(extra="forbid")

    points_earned_in_period: Optional[int] = Field(
        default=None,
        description="Total reward points or miles earned in this statement period.",
    )
    points_redeemed_in_period: Optional[int] = Field(
        default=None,
        description="Total reward points or miles redeemed in this statement period.",
    )
    points_balance_end: Optional[int] = Field(
        default=None,
        description="Reward points or miles balance at the end of the period.",
    )
    cashback_earned_in_period: Optional[Money] = Field(
        default=None,
        description="Total cashback earned in this statement period, if applicable.",
    )
    cashback_redeemed_in_period: Optional[Money] = Field(
        default=None,
        description="Total cashback redeemed or applied in this period, if applicable.",
    )


class CreditCardSpecificSummary(BaseModel):
    """Summary specific to credit card statements.

    Includes prior balance, purchases, interest, fees and due details.

    Inputs:
        previous_balance: Balance from previous statement
        payments_and_credits: Total payments and credits applied
        purchases: Total purchase volume posted
        cash_advances: Total cash advances
        interest_charged: Total finance charges or interest billed
        fees_charged: Total fees charged
        statement_balance: Final statement balance
        credit_limit: Total credit limit on account
        available_credit: Available credit at statement close
        minimum_payment_due: Minimum payment due
        payment_due_date: Due date for minimum payment
    """

    model_config = ConfigDict(extra="forbid")

    previous_balance: Optional[Money] = Field(
        default=None,
        description="Balance from the previous statement.",
    )
    payments_and_credits: Optional[Money] = Field(
        default=None,
        description="Total payments and credits applied in the current period.",
    )
    purchases: Optional[Money] = Field(
        default=None,
        description="Total purchase volume posted in this statement period.",
    )
    cash_advances: Optional[Money] = Field(
        default=None,
        description="Total cash advances in this period, if available.",
    )
    interest_charged: Optional[Money] = Field(
        default=None,
        description="Total finance charges or interest billed in this period.",
    )
    fees_charged: Optional[Money] = Field(
        default=None,
        description="Total fees charged in this period such as late fees or annual fees.",
    )
    statement_balance: Optional[Money] = Field(
        default=None,
        description="Final statement balance that must be paid.",
    )
    credit_limit: Optional[Money] = Field(
        default=None,
        description="Total credit limit on the account if listed.",
    )
    available_credit: Optional[Money] = Field(
        default=None,
        description="Available credit at statement close, if provided.",
    )
    minimum_payment_due: Optional[Money] = Field(
        default=None,
        description="Minimum payment due for the card.",
    )
    payment_due_date: Optional[date] = Field(
        default=None,
        description="Due date for at least the minimum payment.",
    )


class DepositAccountSpecificSummary(BaseModel):
    """Summary for checking, savings or current accounts.

    Captures interest, fees, overdrafts and ATM metrics.

    Inputs:
        average_daily_balance: Average daily balance for period
        interest_earned: Total interest credited
        overdraft_fees: Total overdraft or insufficient funds fees
        atm_withdrawals_count: Count of ATM withdrawals
        other_fees: Total non-overdraft service fees
    """

    model_config = ConfigDict(extra="forbid")

    average_daily_balance: Optional[Money] = Field(
        default=None,
        description="Average daily balance for the period if provided.",
    )
    interest_earned: Optional[Money] = Field(
        default=None,
        description="Total interest credited in this period.",
    )
    overdraft_fees: Optional[Money] = Field(
        default=None,
        description="Total overdraft or insufficient funds fees charged in this period.",
    )
    atm_withdrawals_count: Optional[int] = Field(
        default=None,
        description="Count of ATM withdrawals in this period, if extractable.",
    )
    other_fees: Optional[Money] = Field(
        default=None,
        description="Total non overdraft service fees, maintenance fees, etc.",
    )


class AccountSummary(BaseModel):
    """High level summary for a single account statement.

    Includes owner, account identifiers, currency and balances.

    Inputs:
        account_holder_name: Primary account holder name
        account_number_masked: Account/card number with masking
        institution_name: Bank or card issuer name
        account_type: Type of financial account
        currency: Primary account currency code
        statement_period: Date range and issue date
        opening_balance: Balance at start of period
        closing_balance: Balance at end of period
        total_credits: Total inbound credits
        total_debits: Total outbound debits
        credit_card_summary: Credit card specific fields
        deposit_account_summary: Checking/savings specific fields
    """

    model_config = ConfigDict(extra="forbid")

    account_holder_name: Optional[str] = Field(
        default=None,
        description="Primary account holder name as shown on the statement.",
    )
    account_number_masked: Optional[str] = Field(
        default=None,
        description="Account or card number with masking (for example XXXX1234).",
    )
    institution_name: Optional[str] = Field(
        default=None,
        description="Bank or card issuer name.",
    )
    account_type: AccountType = Field(
        ...,
        description="Type of financial account represented by this statement.",
    )
    currency: Optional[CurrencyCode] = Field(
        default=None,
        description="Primary account currency code used in the statement.",
    )

    statement_period: Optional[StatementPeriod] = Field(
        default=None,
        description="Date range and issue date of the statement.",
    )

    opening_balance: Optional[Money] = Field(
        default=None,
        description="Account balance at the start of the statement period.",
    )
    closing_balance: Optional[Money] = Field(
        default=None,
        description="Account balance at the end of the statement period.",
    )
    total_credits: Optional[Money] = Field(
        default=None,
        description="Total inbound credits for the period.",
    )
    total_debits: Optional[Money] = Field(
        default=None,
        description="Total outbound debits for the period.",
    )

    credit_card_summary: Optional[CreditCardSpecificSummary] = Field(
        default=None,
        description="Additional fields relevant only to credit card statements.",
    )
    deposit_account_summary: Optional[DepositAccountSpecificSummary] = Field(
        default=None,
        description="Additional fields relevant only to checking or savings accounts.",
    )


class AccountStatementExtraction(BaseModel):
    """Top level extraction for a single account statement.

    Intended as the direct structured output of an LLM call.

    Inputs:
        account_summary: Structured summary of account and statement
        transactions: List of all transactions detected
        rewards_summary: Optional rewards information
        notes: Free form notes for caveats or assumptions
        parsing_confidence: Overall confidence score (0-1)

    Outputs:
        Validated AccountStatementExtraction object
    """

    model_config = ConfigDict(extra="forbid")

    account_summary: AccountSummary = Field(
        ...,
        description="Structured summary of the account and statement level information.",
    )
    transactions: List[Transaction] = Field(
        default_factory=list,
        description="List of all transactions detected in the statement.",
    )
    rewards_summary: Optional[RewardsSummary] = Field(
        default=None,
        description="Optional rewards information for credit card statements.",
    )
    notes: Optional[str] = Field(
        default=None,
        description="Free form notes where the model can put important caveats or assumptions.",
    )
    parsing_confidence: Optional[ConfidenceScore] = Field(
        default=None,
        description="Overall confidence score between 0 and 1 for this extraction.",
    )

    @field_validator("account_summary")
    @classmethod
    def require_period_or_balances(cls, value: AccountSummary) -> AccountSummary:
        """Validate that summary has sufficient context.

        Inputs:
            value: AccountSummary object to validate

        Outputs:
            Validated AccountSummary object

        Raises:
            ValueError: If neither period nor balances are present
        """
        if (
            value.statement_period is None
            and value.opening_balance is None
            and value.closing_balance is None
        ):
            raise ValueError(
                "At least statement_period or opening/closing balances should be present."
            )
        return value


# LLM Prompt for statement extraction
STATEMENT_EXTRACTION_PROMPT = """
You are a professional data-extraction assistant specialized in analyzing account statements (checking, savings, current accounts or credit cards).
Your goal is to parse the full statement document and produce **only** a JSON output matching the defined schema exactly. Do not add narrative, explanation, or markdown wrappers.

### Role
You act as an expert financial document parser, familiar with banking terminology, credit-card statements, foreign-currency transactions, masked account numbers, rewards summaries and merchant normalization.

### Instructions
1. Read the full statement text (PDF, table or plain text) that follows.
2. Identify and extract all relevant high-level summary fields: account holder name, masked account number, institution name, account type, currency, opening balance, closing balance, period (start and end dates and issue date), total credits, total debits.
3. If the statement is a credit card statement, also extract: previous balance, payments & credits, purchases, cash advances, interest charged, fees charged, statement balance, credit limit, available credit, minimum payment, payment due date.
4. If the statement is a deposit/checking/savings/current account, also extract: average daily balance, interest earned, overdraft fees, ATM withdrawals count, other fees.
5. Extract each transaction line as follows:
   - transaction_id (if present)
   - posting_date and transaction_date (if distinct)
   - description (original text)
   - transaction_type (one of DEBIT, CREDIT, PAYMENT, REFUND, FEE, INTEREST, TRANSFER_IN, TRANSFER_OUT, CASH_WITHDRAWAL, PURCHASE, OTHER)
   - amount in account currency (signed, no currency symbol)
   - currency code (3-letter uppercase)
   - balance_after_transaction (if displayed)
   - original_amount & original_currency (if foreign currency)
   - category (optional inferred)
   - merchant object: name, category, city, country, raw_merchant_line (optional)
   - metadata (optional additional key/value info).
6. Compute and include an overall `parsing_confidence` score between 0 and 1 (decimal, e.g., 0.87) reflecting your confidence in the extraction.

### Constraints & Format
- Output exactly one JSON object that matches the schema.
- Do not output anything else — no headings, no explanation, no markdown fences.
- Use full ISO dates (YYYY-MM-DD) for all dates.
- Use uppercase three-letter currency codes (USD, EUR, etc.).
- Amounts must be decimal numbers (e.g., 1234.56), no currency symbols, no thousands separators.
- If a field is optional and you cannot determine a value, set it to `null` or omit it if allowed.
- Do not output extra fields beyond those defined in the schema.
- Ensure the JSON is valid (no trailing commas, properly quoted keys/values).
- Maintain the field ordering prescribed by the schema if applicable.

### Final Check
Before outputting, verify:
- The `account_summary` has either a `statement_period` or both opening and closing balances.
- Each transaction object includes the required fields.
- There are no narrative remarks or commentary outside the JSON structure.

Begin now. After this instruction, the account statement content will be provided for parsing.
""".strip()
