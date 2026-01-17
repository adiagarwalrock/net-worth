"""ABOUTME: Celery tasks for asynchronous statement processing.
ABOUTME: Handles background parsing and data population of uploaded statements.
"""
import logging
from decimal import Decimal

from celery import shared_task
from pydantic import ValidationError

from .models import StatementUpload
from .services import StatementParserService, StatementDataPopulatorService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def parse_and_populate_statement(self, statement_upload_id: int):
    """Parse a statement file and populate Asset/Liability models.

    Inputs:
        statement_upload_id: ID of StatementUpload record to process

    Outputs:
        Dict with status and results

    This task:
    1. Marks statement as PROCESSING
    2. Parses file with Gemini LLM
    3. Populates Asset or Liability models
    4. Marks statement as COMPLETED or FAILED
    """
    upload: StatementUpload | None = None
    try:
        # Get the upload record
        upload = StatementUpload.objects.get(id=statement_upload_id)
        upload.mark_as_processing()

        logger.info(f"Processing statement upload {upload.id}: {upload.file.name}")

        # Get file path
        file_path = upload.file.path

        # Determine MIME type
        mime_type = _get_mime_type(upload.file.name)

        # Parse statement with Gemini
        parser = StatementParserService()
        extraction = parser.parse_statement(file_path, mime_type=mime_type)

        # Convert to dict for storage
        parsed_data = extraction.model_dump(mode="json")

        # Populate Asset/Liability models
        populator = StatementDataPopulatorService()
        result = populator.populate_from_extraction(
            user=upload.user,
            extraction=extraction,
            statement_upload_id=upload.id,
        )

        # Convert confidence to percentage (0-100)
        confidence_score = Decimal("0.00")
        if extraction.parsing_confidence:
            confidence_score = Decimal(str(extraction.parsing_confidence)) * 100

        # Mark as completed
        upload.mark_as_completed(
            parsed_data=parsed_data, confidence_score=confidence_score
        )

        logger.info(
            f"Successfully processed statement {upload.id}. "
            f"Created: {result.get('created')}, Updated: {result.get('updated')}"
        )

        return {
            "status": "success",
            "statement_upload_id": upload.id,
            "confidence": float(confidence_score),
            "result": {
                "created": result.get("created"),
                "updated": result.get("updated"),
                "history_count": result.get("history_count"),
            },
        }

    except StatementUpload.DoesNotExist:
        error_msg = f"StatementUpload {statement_upload_id} not found"
        logger.error(error_msg)
        return {"status": "error", "message": error_msg}

    except ValidationError as e:
        error_msg = f"Pydantic validation error: {str(e)}"
        logger.error(f"Statement {statement_upload_id} validation failed: {error_msg}")
        if upload:
            upload.mark_as_failed(error_msg)
        return {"status": "error", "message": error_msg}

    except FileNotFoundError as e:
        error_msg = f"File not found: {str(e)}"
        logger.error(f"Statement {statement_upload_id} file missing: {error_msg}")
        if upload:
            upload.mark_as_failed(error_msg)
        return {"status": "error", "message": error_msg}

    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(f"Statement {statement_upload_id} processing failed: {error_msg}")

        # Retry the task without marking as failed (status updated only after max retries)
        try:
            raise self.retry(exc=e, countdown=60 * (2**self.request.retries))
        except self.MaxRetriesExceededError:
            # Only mark as failed after exhausting all retries
            if upload:
                upload.mark_as_failed(f"Max retries exceeded. {error_msg}")
            return {"status": "error", "message": error_msg}


def _get_mime_type(filename: str) -> str:
    """Determine MIME type from filename.

    Inputs:
        filename: Name of the file

    Outputs:
        MIME type string
    """
    filename_lower = filename.lower()

    if filename_lower.endswith(".pdf"):
        return "application/pdf"
    elif filename_lower.endswith(".png"):
        return "image/png"
    elif filename_lower.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    elif filename_lower.endswith(".gif"):
        return "image/gif"
    elif filename_lower.endswith(".webp"):
        return "image/webp"
    else:
        return "application/pdf"  # Default to PDF
