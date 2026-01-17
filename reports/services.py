"""ABOUTME: Business logic for statement parsing and data population.
ABOUTME: Integrates Google Gemini API for LLM-based statement extraction.
"""
import logging
from decimal import Decimal
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

from django.conf import settings
from django.utils import timezone
from pydantic import ValidationError

from google import genai
from google.genai import types

from .schemas import (
    AccountStatementExtraction,
    STATEMENT_EXTRACTION_PROMPT,
)
from assets.models import Asset, AssetHistory
from liabilities.models import Liability, LiabilityHistory
from currencies.models import Currency
from common.enums import AccountType, LiabilityType, AssetType

logger = logging.getLogger(__name__)


class StatementParserService:
    """Service for parsing financial statements using Google Gemini LLM.

    Uses structured output to extract account information, transactions,
    and balances from PDF or image files.

    The Gemini client is lazy-initialized on first use to avoid crashes
    when the service is instantiated but API key is not configured.
    """

    def __init__(self):
        """Initialize the service (client is lazy-initialized)."""
        self._client = None
        self._model = None

    def _get_client(self) -> tuple:
        """Lazy-initialize and return the Gemini client.

        Returns:
            tuple: (client, model) - Gemini client and model name

        Raises:
            ValueError: If API key is not configured
        """
        if self._client is None:
            api_key = settings.GOOGLE_GEMINI_API_KEY
            if not api_key:
                raise ValueError("GOOGLE_GEMINI_API_KEY is not configured in settings")

            self._client = genai.Client(api_key=api_key)
            self._model = settings.GEMINI_MODEL

        assert self._client is not None and self._model is not None
        return self._client, self._model

    def parse_statement(
        self, file_path: str, mime_type: str = "application/pdf"
    ) -> AccountStatementExtraction:
        """Parse a financial statement file using Gemini LLM.

        Inputs:
            file_path: Absolute path to the statement file
            mime_type: MIME type of the file (default: application/pdf)

        Outputs:
            AccountStatementExtraction: Parsed and validated statement data

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If API key is missing or response is invalid
            ValidationError: If LLM output doesn't match schema
        """
        filepath = Path(file_path)
        if not filepath.exists():
            raise FileNotFoundError(f"Statement file not found: {file_path}")

        # Lazy-initialize client on first use
        client, model = self._get_client()

        logger.info(f"Parsing statement file: {file_path} with model: {model}")

        try:
            response = client.models.generate_content(
                model=model,
                contents=[
                    types.Part.from_bytes(
                        data=filepath.read_bytes(),
                        mime_type=mime_type,
                    ),
                    STATEMENT_EXTRACTION_PROMPT,
                ],
                config={
                    "response_mime_type": "application/json",
                    "response_json_schema": AccountStatementExtraction.model_json_schema(),
                },
            )

            # Extract JSON from response
            if not response.text:
                raise ValueError("Empty response from Gemini API")

            # Parse and validate with Pydantic
            extraction = AccountStatementExtraction.model_validate_json(response.text)
            logger.info(
                f"Successfully parsed statement. Confidence: {extraction.parsing_confidence}"
            )
            return extraction

        except ValidationError as e:
            logger.error(f"Pydantic validation failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to parse statement: {e}")
            raise


class StatementDataPopulatorService:
    """Service for populating Asset/Liability models from parsed statement data.

    Maps structured statement data to Django models, creating or updating
    financial records with proper history tracking.
    """

    def populate_from_extraction(
        self,
        user,
        extraction: AccountStatementExtraction,
        statement_upload_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Populate Asset or Liability models from parsed statement data.

        Inputs:
            user: User object who owns the statement
            extraction: Parsed statement data
            statement_upload_id: Optional ID of the StatementUpload record

        Outputs:
            Dict with keys:
                - 'created': Boolean indicating if new record created
                - 'updated': Boolean indicating if existing record updated
                - 'asset': Asset object (if deposit account)
                - 'liability': Liability object (if credit card or loan)
                - 'history_count': Number of history records created

        Raises:
            ValueError: If currency code is invalid or account type unsupported
        """
        summary = extraction.account_summary
        account_type = summary.account_type

        logger.info(f"Populating data for account type: {account_type}")

        # Get or validate currency
        currency = self._get_or_create_currency(summary.currency)

        # Convert enum to value for comparison
        account_type_value = account_type.value if hasattr(account_type, 'value') else account_type

        # Route to appropriate handler using centralized enums
        if account_type_value == AccountType.CREDIT_CARD.value:
            return self._populate_credit_card(user, extraction, currency)
        elif account_type_value in [AccountType.LOAN.value, AccountType.MORTGAGE.value,
                                      AccountType.AUTO_LOAN.value, AccountType.STUDENT_LOAN.value,
                                      AccountType.PERSONAL_LOAN.value]:
            return self._populate_loan(user, extraction, currency)
        elif account_type_value in [AccountType.CHECKING.value, AccountType.SAVINGS.value,
                                     AccountType.CURRENT.value, AccountType.MONEY_MARKET.value]:
            return self._populate_deposit_account(user, extraction, currency)
        else:
            raise ValueError(f"Unsupported account type: {account_type}")

    def _get_or_create_currency(
        self, currency_code: Optional[str]
    ) -> Currency:
        """Get or create Currency object from code.

        Inputs:
            currency_code: Three-letter currency code (e.g., 'USD')

        Outputs:
            Currency: Currency object

        Raises:
            ValueError: If currency_code is None or invalid
        """
        if not currency_code:
            currency_code = settings.DEFAULT_CURRENCY

        # Ensure we have a string (for Pylance type checking)
        currency_code = str(currency_code).upper()

        try:
            currency, created = Currency.objects.get_or_create(
                code=currency_code,
                defaults={"name": currency_code, "symbol": currency_code},
            )
            if created:
                logger.info(f"Created new currency: {currency_code}")
            return currency
        except Exception as e:
            raise ValueError(f"Invalid currency code: {currency_code}") from e

    def _populate_credit_card(
        self, user, extraction: AccountStatementExtraction, currency: Currency
    ) -> Dict[str, Any]:
        """Populate Liability model from credit card statement.

        Inputs:
            user: User object
            extraction: Parsed statement data
            currency: Currency object

        Outputs:
            Dict with created/updated flags and liability object
        """
        summary = extraction.account_summary
        cc_summary = summary.credit_card_summary

        # Extract key fields
        institution = summary.institution_name or "Unknown Bank"
        account_number = summary.account_number_masked
        closing_balance = summary.closing_balance or Decimal("0.00")

        # Build name
        name = f"{institution} - {account_number}" if account_number else institution

        # Prepare defaults with credit card specific fields
        defaults = {
            "name": name,
            "balance": closing_balance,
            "currency": currency,
            "is_active": True,
        }

        # Add credit card specific fields to defaults if available
        if cc_summary:
            if cc_summary.credit_limit:
                defaults["credit_limit"] = cc_summary.credit_limit
            if cc_summary.minimum_payment_due:
                defaults["monthly_payment"] = cc_summary.minimum_payment_due
            if cc_summary.payment_due_date:
                defaults["payment_due_date"] = cc_summary.payment_due_date.day

        # Try to find existing liability
        liability, created = Liability.objects.get_or_create(
            user=user,
            creditor=institution,
            account_number=account_number,
            liability_type=Liability.CREDIT_CARD,
            defaults=defaults,
        )

        updated = False
        if not created and liability.balance != closing_balance:
            # Update existing liability
            liability.balance = closing_balance
            liability.currency = currency
            liability.is_active = True

            # Update credit card specific fields
            if cc_summary:
                if cc_summary.credit_limit:
                    liability.credit_limit = cc_summary.credit_limit
                if cc_summary.minimum_payment_due:
                    liability.monthly_payment = cc_summary.minimum_payment_due
                if cc_summary.payment_due_date:
                    liability.payment_due_date = cc_summary.payment_due_date.day

            liability.save(skip_history=True)
            updated = True

        # Create history entry manually with STATEMENT_UPLOAD source
        LiabilityHistory.objects.create(
            liability=liability,
            balance=closing_balance,
            currency=currency,
            source=LiabilityHistory.STATEMENT_UPLOAD,
        )

        logger.info(
            f"{'Created' if created else 'Updated'} liability: {liability.name} - {closing_balance}"
        )

        return {
            "created": created,
            "updated": updated,
            "liability": liability,
            "history_count": 1,
        }

    def _populate_loan(
        self, user, extraction: AccountStatementExtraction, currency: Currency
    ) -> Dict[str, Any]:
        """Populate Liability model from loan statement.

        Inputs:
            user: User object
            extraction: Parsed statement data
            currency: Currency object

        Outputs:
            Dict with created/updated flags and liability object
        """
        summary = extraction.account_summary

        # Extract key fields
        institution = summary.institution_name or "Unknown Lender"
        account_number = summary.account_number_masked
        closing_balance = summary.closing_balance or Decimal("0.00")

        # Build name
        name = f"{institution} - {account_number}" if account_number else institution

        # Infer loan type from institution name
        liability_type = self._infer_loan_type(institution, name)

        # Prepare defaults
        defaults = {
            "name": name,
            "balance": closing_balance,
            "currency": currency,
            "is_active": True,
        }

        # Try to find existing liability
        liability, created = Liability.objects.get_or_create(
            user=user,
            creditor=institution,
            account_number=account_number,
            liability_type=liability_type,
            defaults=defaults,
        )

        updated = False
        if not created and liability.balance != closing_balance:
            # Update existing liability
            liability.balance = closing_balance
            liability.currency = currency
            liability.is_active = True
            liability.save(skip_history=True)
            updated = True

        # Create history entry manually with STATEMENT_UPLOAD source
        LiabilityHistory.objects.create(
            liability=liability,
            balance=closing_balance,
            currency=currency,
            source=LiabilityHistory.STATEMENT_UPLOAD,
        )

        logger.info(
            f"{'Created' if created else 'Updated'} loan liability: {liability.name} - {closing_balance}"
        )

        return {
            "created": created,
            "updated": updated,
            "liability": liability,
            "history_count": 1,
        }

    def _infer_loan_type(self, institution: str, name: str) -> str:
        """Infer loan type from institution name.

        Inputs:
            institution: Institution name
            name: Full account name

        Outputs:
            str: Liability type constant (MORTGAGE, AUTO_LOAN, etc.)
        """
        text = (institution + " " + name).lower()

        # Check for specific loan types based on keywords
        if any(keyword in text for keyword in ["mortgage", "home loan", "housing"]):
            return Liability.MORTGAGE
        elif any(keyword in text for keyword in ["auto", "car", "vehicle"]):
            return Liability.AUTO_LOAN
        elif any(keyword in text for keyword in ["student", "education", "tuition"]):
            return Liability.STUDENT_LOAN
        elif any(keyword in text for keyword in ["medical", "health", "hospital"]):
            return Liability.MEDICAL_LOAN
        else:
            # Default to personal loan for generic loans
            return Liability.PERSONAL_LOAN

    def _populate_deposit_account(
        self, user, extraction: AccountStatementExtraction, currency: Currency
    ) -> Dict[str, Any]:
        """Populate Asset model from deposit account statement.

        Inputs:
            user: User object
            extraction: Parsed statement data
            currency: Currency object

        Outputs:
            Dict with created/updated flags and asset object
        """
        summary = extraction.account_summary

        # Extract key fields
        institution = summary.institution_name or "Unknown Bank"
        account_number = summary.account_number_masked
        closing_balance = summary.closing_balance or Decimal("0.00")

        # Build name
        account_type_value = summary.account_type.value if hasattr(summary.account_type, 'value') else summary.account_type
        account_type_display = account_type_value.replace("_", " ").title()
        name = (
            f"{institution} {account_type_display} - {account_number}"
            if account_number
            else f"{institution} {account_type_display}"
        )

        # Try to find existing asset
        asset, created = Asset.objects.get_or_create(
            user=user,
            institution=institution,
            account_number=account_number,
            asset_type=Asset.CASH,
            defaults={
                "name": name,
                "value": closing_balance,
                "currency": currency,
                "is_active": True,
            },
        )

        updated = False
        if not created and asset.value != closing_balance:
            # Update existing asset
            asset.value = closing_balance
            asset.currency = currency
            asset.is_active = True
            asset.save(skip_history=True)
            updated = True

        # Create history entry manually with STATEMENT_UPLOAD source
        AssetHistory.objects.create(
            asset=asset,
            value=closing_balance,
            currency=currency,
            source=AssetHistory.STATEMENT_UPLOAD,
        )

        logger.info(
            f"{'Created' if created else 'Updated'} asset: {asset.name} - {closing_balance}"
        )

        return {
            "created": created,
            "updated": updated,
            "asset": asset,
            "history_count": 1,
        }
