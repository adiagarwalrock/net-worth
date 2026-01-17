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

# ---------------------------------------------------------------------------
# Constrained types
# ---------------------------------------------------------------------------

CurrencyCode = constr(pattern=r"^[A-Z]{3}$")
Money = condecimal(max_digits=18, decimal_places=4)
ConfidenceScore = condecimal(ge=0, le=1, max_digits=3, decimal_places=2)


class StatementPeriod(BaseModel):
    """Date range covered by a statement.
    Includes start, end, and issue dates if available.
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

    transaction_type: Literal[
        "DEBIT",
        "CREDIT",
        "PAYMENT",
        "REFUND",
        "FEE",
        "INTEREST",
        "TRANSFER_IN",
        "TRANSFER_OUT",
        "CASH_WITHDRAWAL",
        "PURCHASE",
        "OTHER",
    ] = Field(
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

    @field_validator("currency")
    @classmethod
    def uppercase_currency(cls, value: Optional[str]) -> Optional[str]:
        """Normalize currency codes.
        Ensures any currency code is uppercase 3 letters.
        """
        return value.upper() if value is not None else None

    @field_validator("original_currency")
    @classmethod
    def uppercase_original_currency(cls, value: Optional[str]) -> Optional[str]:
        """Normalize original currency codes.
        Ensures any original currency code is uppercase 3 letters.
        """
        return value.upper() if value is not None else None


class RewardsSummary(BaseModel):
    """Rewards or cashback summary.
    Mainly useful for credit card statements.
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
    account_type: Literal[
        "CREDIT_CARD",
        "CHECKING",
        "SAVINGS",
        "CURRENT",
        "MONEY_MARKET",
        "LOAN",
        "OTHER",
    ] = Field(
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
        """Validate summary context.
        Require at least a statement period or balances to be present.
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


prompt = """
You are a highly reliable data-extraction agent.
Your task: Extract *all relevant structured information* from the provided account statement text and output it **strictly in JSON format** following the schema defined. Do not output any additional explanation, narrative, or markdown wrappers—only the JSON.
Here are the requirements:

1. **Scope**
   - The text supplied is a bank or credit-card statement (checking / savings / current / credit card) containing summary information, a list of transactions, and possibly rewards or fees.
   - You must identify the institution name, account holder, account number mask (e.g., “XXXX1234”), account type, currency, statement period, opening and closing balances, total credits/debits, and all individual transactions.
   - For credit-card statements: also extract previous balance, payments & credits, purchases, cash advances, interest charged, fees charged, credit limit, available credit, minimum payment and payment due date.
   - For deposit accounts (checking/savings/current): also extract average daily balance, interest earned, overdraft fees, ATM withdrawals count, other fees.

2. **Transactions extraction**
   - For each transaction, capture: transaction_id (if present), posting_date, transaction_date (if different), description (original description line), transaction_type (one of: DEBIT, CREDIT, PAYMENT, REFUND, FEE, INTEREST, TRANSFER_IN, TRANSFER_OUT, CASH_WITHDRAWAL, PURCHASE, OTHER), amount (signed in account currency), currency (if listed, else assume account currency), balance_after_transaction (if shown), original_amount & original_currency (if foreign-currency transaction), category (inferred if possible), merchant (structured merchant info: name, category, city, country, raw_merchant_line), metadata (any extra key/value you infer).

3. **Output format**
   - Follow the JSON schema exactly. Use property ordering if your schema includes `propertyOrdering`.
   - Output **valid JSON** (no trailing commas, no comments, no markdown).
   - Do **not** include explanatory text, headers, or narrative.
   - If you cannot locate a particular field in the input text, either omit it (if optional) or set it to `null` (if required but missing).
   - Provide an overall `parsing_confidence` score between 0 and 1 (e.g., 0.85) reflecting how confident you are in this extraction.

4. **Instructions to avoid errors**
   - Do not wrap your JSON inside markdown code fences.
   - Do not output any additional keys beyond those defined in the schema.
   - Do not output narrative or commentary.
   - Do not reorder the schema fields unless you follow the defined order via `propertyOrdering`.
   - For dates, use `YYYY-MM-DD` format.
   - For currency codes, use uppercase three-letter codes (e.g., USD, EUR).
   - For amounts, use decimal numbers (no currency symbols, no thousands separators, use dot as decimal point).
   - If a transaction description clearly indicates a merchant, attempt to populate merchant.name; if not, merchant may be omitted or null.
   - If the input text contains foreign currency data, capture original_amount and original_currency in addition to amount and currency.

5. **Validation expectations**
   - The schema is rigid: if your output fails schema validation, the ingestion pipeline will reject it.
   - You are expected to perform the cleaning, parsing, categorization and mapping of raw text lines into structured fields.

6. **Final check before output**
   - Read your JSON output: check it is valid.
   - Confirm that no extra text (like “Here is the result”) appears.
   - Confirm all mandatory fields for the account summary are present or set to `null` if missing.
   - Confirm each transaction is represented correctly as an object in the `transactions` list.

You may begin now. The statement text will follow.


""".strip()

from google import genai
from google.genai import types
import pathlib

client = genai.Client(api_key="")

# Retrieve and encode the PDF byte
filepath = pathlib.Path("/content/01aug23 2 30sep24.pdf")


response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[
        types.Part.from_bytes(
            data=filepath.read_bytes(),
            mime_type="application/pdf",
        ),
        prompt,
    ],
    config={
        "response_mime_type": "application/json",
        "response_json_schema": AccountStatementExtraction.model_json_schema(),
    },
)
