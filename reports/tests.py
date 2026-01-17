"""ABOUTME: Comprehensive test suite for statement parsing functionality.
ABOUTME: Tests schemas, services, tasks, and admin integration.
"""
import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile

from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from pydantic import ValidationError

from .models import StatementUpload
from .schemas import (
    AccountStatementExtraction,
    AccountSummary,
    Transaction,
    CreditCardSpecificSummary,
    StatementPeriod,
)
from .services import StatementParserService, StatementDataPopulatorService
from .tasks import parse_and_populate_statement
from assets.models import Asset, AssetHistory
from liabilities.models import Liability, LiabilityHistory
from currencies.models import Currency

User = get_user_model()


class SchemaValidationTests(TestCase):
    """Test Pydantic schema validation."""

    def test_valid_credit_card_extraction(self):
        """Test that valid credit card data passes validation."""
        data = {
            "account_summary": {
                "account_type": "CREDIT_CARD",
                "institution_name": "Chase Bank",
                "account_number_masked": "XXXX1234",
                "currency": "USD",
                "closing_balance": "1250.50",
                "statement_period": {
                    "start_date": "2024-10-01",
                    "end_date": "2024-10-31",
                },
            },
            "transactions": [
                {
                    "description": "Amazon Purchase",
                    "transaction_type": "PURCHASE",
                    "amount": "-50.00",
                    "posting_date": "2024-10-15",
                }
            ],
            "parsing_confidence": "0.95",
        }

        extraction = AccountStatementExtraction.model_validate(data)
        self.assertEqual(extraction.account_summary.account_type, "CREDIT_CARD")
        self.assertEqual(len(extraction.transactions), 1)
        self.assertEqual(extraction.parsing_confidence, Decimal("0.95"))

    def test_valid_checking_extraction(self):
        """Test that valid checking account data passes validation."""
        data = {
            "account_summary": {
                "account_type": "CHECKING",
                "institution_name": "Bank of America",
                "account_number_masked": "****5678",
                "currency": "USD",
                "opening_balance": "5000.00",
                "closing_balance": "4750.25",
            },
            "transactions": [],
            "parsing_confidence": "0.88",
        }

        extraction = AccountStatementExtraction.model_validate(data)
        self.assertEqual(extraction.account_summary.account_type, "CHECKING")
        self.assertEqual(len(extraction.transactions), 0)

    def test_invalid_account_summary_no_period_or_balances(self):
        """Test that account summary without period or balances fails validation."""
        data = {
            "account_summary": {
                "account_type": "CREDIT_CARD",
                "institution_name": "Chase",
            },
            "transactions": [],
        }

        with self.assertRaises(ValidationError) as context:
            AccountStatementExtraction.model_validate(data)

        self.assertIn("period or opening/closing balances", str(context.exception))

    def test_currency_code_uppercase_validation(self):
        """Test that currency codes are uppercased."""
        transaction = Transaction(
            description="Test",
            transaction_type="PURCHASE",
            amount=Decimal("100.00"),
            currency="usd",
        )
        self.assertEqual(transaction.currency, "USD")


class StatementParserServiceTests(TestCase):
    """Test StatementParserService."""

    @patch("reports.services.genai.Client")
    def test_parse_statement_success(self, mock_client_class):
        """Test successful statement parsing."""
        # Create a temporary PDF file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(b"fake pdf content")
            tmp_path = tmp.name

        try:
            # Mock Gemini API response
            mock_response = Mock()
            mock_response.text = json.dumps(
                {
                    "account_summary": {
                        "account_type": "CREDIT_CARD",
                        "institution_name": "Test Bank",
                        "currency": "USD",
                        "closing_balance": "100.00",
                    },
                    "transactions": [],
                    "parsing_confidence": "0.90",
                }
            )

            mock_client = Mock()
            mock_client.models.generate_content.return_value = mock_response
            mock_client_class.return_value = mock_client

            # Test parsing
            parser = StatementParserService()
            extraction = parser.parse_statement(tmp_path)

            self.assertIsInstance(extraction, AccountStatementExtraction)
            self.assertEqual(extraction.account_summary.institution_name, "Test Bank")
            self.assertEqual(extraction.parsing_confidence, Decimal("0.90"))

        finally:
            # Cleanup
            Path(tmp_path).unlink()

    def test_parse_statement_file_not_found(self):
        """Test parsing with non-existent file."""
        parser = StatementParserService()

        with self.assertRaises(FileNotFoundError):
            parser.parse_statement("/nonexistent/file.pdf")

    @patch("reports.services.genai.Client")
    def test_parse_statement_empty_response(self, mock_client_class):
        """Test parsing with empty API response."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(b"fake pdf content")
            tmp_path = tmp.name

        try:
            mock_response = Mock()
            mock_response.text = ""

            mock_client = Mock()
            mock_client.models.generate_content.return_value = mock_response
            mock_client_class.return_value = mock_client

            parser = StatementParserService()

            with self.assertRaises(ValueError) as context:
                parser.parse_statement(tmp_path)

            self.assertIn("Empty response", str(context.exception))

        finally:
            Path(tmp_path).unlink()


class StatementDataPopulatorServiceTests(TransactionTestCase):
    """Test StatementDataPopulatorService."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass"
        )
        self.currency = Currency.objects.create(code="USD", name="US Dollar", symbol="$")

    def test_populate_credit_card_new(self):
        """Test populating a new credit card liability."""
        extraction_data = {
            "account_summary": {
                "account_type": "CREDIT_CARD",
                "institution_name": "Chase Bank",
                "account_number_masked": "XXXX1234",
                "currency": "USD",
                "closing_balance": "1500.00",
                "credit_card_summary": {
                    "credit_limit": "5000.00",
                    "minimum_payment_due": "50.00",
                    "payment_due_date": "2024-11-15",
                },
            },
            "transactions": [],
            "parsing_confidence": "0.95",
        }

        extraction = AccountStatementExtraction.model_validate(extraction_data)
        populator = StatementDataPopulatorService()

        result = populator.populate_from_extraction(self.user, extraction)

        self.assertTrue(result["created"])
        self.assertFalse(result["updated"])
        self.assertIn("liability", result)

        liability = result["liability"]
        self.assertEqual(liability.user, self.user)
        self.assertEqual(liability.creditor, "Chase Bank")
        self.assertEqual(liability.balance, Decimal("1500.00"))
        self.assertEqual(liability.credit_limit, Decimal("5000.00"))
        self.assertEqual(liability.liability_type, Liability.CREDIT_CARD)

        # Check history was created
        history = LiabilityHistory.objects.filter(liability=liability).first()
        self.assertIsNotNone(history)
        self.assertEqual(history.source, LiabilityHistory.STATEMENT_UPLOAD)

    def test_populate_credit_card_update_existing(self):
        """Test updating an existing credit card liability."""
        # Create existing liability
        liability = Liability.objects.create(
            user=self.user,
            name="Chase Bank - XXXX1234",
            liability_type=Liability.CREDIT_CARD,
            balance=Decimal("1000.00"),
            currency=self.currency,
            creditor="Chase Bank",
            account_number="XXXX1234",
        )

        extraction_data = {
            "account_summary": {
                "account_type": "CREDIT_CARD",
                "institution_name": "Chase Bank",
                "account_number_masked": "XXXX1234",
                "currency": "USD",
                "closing_balance": "1500.00",
            },
            "transactions": [],
            "parsing_confidence": "0.95",
        }

        extraction = AccountStatementExtraction.model_validate(extraction_data)
        populator = StatementDataPopulatorService()

        result = populator.populate_from_extraction(self.user, extraction)

        self.assertFalse(result["created"])
        self.assertTrue(result["updated"])

        liability.refresh_from_db()
        self.assertEqual(liability.balance, Decimal("1500.00"))

    def test_populate_checking_account_new(self):
        """Test populating a new checking account asset."""
        extraction_data = {
            "account_summary": {
                "account_type": "CHECKING",
                "institution_name": "Bank of America",
                "account_number_masked": "****5678",
                "currency": "USD",
                "closing_balance": "3250.75",
            },
            "transactions": [],
            "parsing_confidence": "0.92",
        }

        extraction = AccountStatementExtraction.model_validate(extraction_data)
        populator = StatementDataPopulatorService()

        result = populator.populate_from_extraction(self.user, extraction)

        self.assertTrue(result["created"])
        self.assertFalse(result["updated"])
        self.assertIn("asset", result)

        asset = result["asset"]
        self.assertEqual(asset.user, self.user)
        self.assertEqual(asset.institution, "Bank of America")
        self.assertEqual(asset.value, Decimal("3250.75"))
        self.assertEqual(asset.asset_type, Asset.CASH)

        # Check history was created
        history = AssetHistory.objects.filter(asset=asset).first()
        self.assertIsNotNone(history)
        self.assertEqual(history.source, AssetHistory.STATEMENT_UPLOAD)

    def test_populate_checking_account_update_existing(self):
        """Test updating an existing checking account asset."""
        # Create existing asset
        asset = Asset.objects.create(
            user=self.user,
            name="Bank of America Checking - ****5678",
            asset_type=Asset.CASH,
            value=Decimal("2000.00"),
            currency=self.currency,
            institution="Bank of America",
            account_number="****5678",
        )

        extraction_data = {
            "account_summary": {
                "account_type": "CHECKING",
                "institution_name": "Bank of America",
                "account_number_masked": "****5678",
                "currency": "USD",
                "closing_balance": "3250.75",
            },
            "transactions": [],
            "parsing_confidence": "0.92",
        }

        extraction = AccountStatementExtraction.model_validate(extraction_data)
        populator = StatementDataPopulatorService()

        result = populator.populate_from_extraction(self.user, extraction)

        self.assertFalse(result["created"])
        self.assertTrue(result["updated"])

        asset.refresh_from_db()
        self.assertEqual(asset.value, Decimal("3250.75"))

    def test_populate_unsupported_account_type(self):
        """Test that unsupported account types raise an error."""
        extraction_data = {
            "account_summary": {
                "account_type": "LOAN",
                "institution_name": "Some Bank",
                "currency": "USD",
                "closing_balance": "5000.00",
            },
            "transactions": [],
        }

        extraction = AccountStatementExtraction.model_validate(extraction_data)
        populator = StatementDataPopulatorService()

        with self.assertRaises(ValueError) as context:
            populator.populate_from_extraction(self.user, extraction)

        self.assertIn("Unsupported account type", str(context.exception))

    def test_currency_creation_if_not_exists(self):
        """Test that currency is created if it doesn't exist."""
        # Delete the existing USD currency
        Currency.objects.all().delete()

        extraction_data = {
            "account_summary": {
                "account_type": "CHECKING",
                "institution_name": "Test Bank",
                "currency": "EUR",
                "closing_balance": "1000.00",
            },
            "transactions": [],
        }

        extraction = AccountStatementExtraction.model_validate(extraction_data)
        populator = StatementDataPopulatorService()

        result = populator.populate_from_extraction(self.user, extraction)

        self.assertTrue(result["created"])
        self.assertTrue(Currency.objects.filter(code="EUR").exists())


class CeleryTaskTests(TransactionTestCase):
    """Test Celery tasks."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass"
        )
        Currency.objects.create(code="USD", name="US Dollar", symbol="$")

    @patch("reports.tasks.StatementParserService")
    @patch("reports.tasks.StatementDataPopulatorService")
    def test_parse_and_populate_statement_success(
        self, mock_populator_class, mock_parser_class
    ):
        """Test successful statement parsing and population task."""
        # Create statement upload
        upload = StatementUpload.objects.create(
            user=self.user,
            file=SimpleUploadedFile("test.pdf", b"fake content"),
            upload_type=StatementUpload.CREDIT_CARD_STATEMENT,
            status=StatementUpload.PENDING,
        )

        # Mock parser
        mock_extraction = Mock()
        mock_extraction.model_dump.return_value = {"test": "data"}
        mock_extraction.parsing_confidence = Decimal("0.95")

        mock_parser = Mock()
        mock_parser.parse_statement.return_value = mock_extraction
        mock_parser_class.return_value = mock_parser

        # Mock populator
        mock_populator = Mock()
        mock_populator.populate_from_extraction.return_value = {
            "created": True,
            "updated": False,
            "history_count": 1,
        }
        mock_populator_class.return_value = mock_populator

        # Run task
        result = parse_and_populate_statement(upload.id)

        self.assertEqual(result["status"], "success")
        upload.refresh_from_db()
        self.assertEqual(upload.status, StatementUpload.COMPLETED)
        self.assertIsNotNone(upload.parsed_data)

    def test_parse_and_populate_statement_not_found(self):
        """Test task with non-existent upload."""
        result = parse_and_populate_statement(99999)

        self.assertEqual(result["status"], "error")
        self.assertIn("not found", result["message"])


class StatementUploadModelTests(TestCase):
    """Test StatementUpload model methods."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass"
        )

    def test_mark_as_processing(self):
        """Test marking upload as processing."""
        upload = StatementUpload.objects.create(
            user=self.user,
            file=SimpleUploadedFile("test.pdf", b"fake"),
            upload_type=StatementUpload.BANK_STATEMENT,
        )

        upload.mark_as_processing()
        self.assertEqual(upload.status, StatementUpload.PROCESSING)

    def test_mark_as_completed(self):
        """Test marking upload as completed."""
        upload = StatementUpload.objects.create(
            user=self.user,
            file=SimpleUploadedFile("test.pdf", b"fake"),
            upload_type=StatementUpload.BANK_STATEMENT,
        )

        parsed_data = {"test": "data"}
        upload.mark_as_completed(parsed_data, Decimal("95.50"))

        self.assertEqual(upload.status, StatementUpload.COMPLETED)
        self.assertEqual(upload.parsed_data, parsed_data)
        self.assertEqual(upload.confidence_score, Decimal("95.50"))
        self.assertIsNotNone(upload.processed_at)

    def test_mark_as_failed(self):
        """Test marking upload as failed."""
        upload = StatementUpload.objects.create(
            user=self.user,
            file=SimpleUploadedFile("test.pdf", b"fake"),
            upload_type=StatementUpload.BANK_STATEMENT,
        )

        upload.mark_as_failed("Test error message")

        self.assertEqual(upload.status, StatementUpload.FAILED)
        self.assertEqual(upload.error_message, "Test error message")
        self.assertIsNotNone(upload.processed_at)

    def test_is_processed_property(self):
        """Test is_processed property."""
        upload = StatementUpload.objects.create(
            user=self.user,
            file=SimpleUploadedFile("test.pdf", b"fake"),
            upload_type=StatementUpload.BANK_STATEMENT,
        )

        self.assertFalse(upload.is_processed)

        upload.status = StatementUpload.COMPLETED
        self.assertTrue(upload.is_processed)

        upload.status = StatementUpload.FAILED
        self.assertTrue(upload.is_processed)

    def test_is_successful_property(self):
        """Test is_successful property."""
        upload = StatementUpload.objects.create(
            user=self.user,
            file=SimpleUploadedFile("test.pdf", b"fake"),
            upload_type=StatementUpload.BANK_STATEMENT,
        )

        self.assertFalse(upload.is_successful)

        upload.status = StatementUpload.COMPLETED
        self.assertTrue(upload.is_successful)

        upload.status = StatementUpload.FAILED
        self.assertFalse(upload.is_successful)
