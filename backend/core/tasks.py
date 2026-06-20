import uuid
import json
from loguru import logger
from celery import shared_task
from django.db.models import QuerySet
from docling.document_converter import DocumentConverter

from . import prompts
from .models import Vendor, VendorDocument
from .model import call_cohere  


@shared_task(name="pipeline.orchestrate_vendor_documents")
def orchestrate_vendor_documents(vendor_id_str: str):
    """
    Asynchronous Core Task. Coordinates parallel document generation routines,
    Docling text layouts processing, and structured LLM analysis loops.
    """
    vendor_id = uuid.UUID(vendor_id_str)
    try:
        vendor = Vendor.objects.get(pk=vendor_id)
    except Vendor.DoesNotExist:
        logger.error(f"[CELERY_ERROR] Vendor {vendor_id_str} not found.")
        return
    converter = DocumentConverter()
    documents: QuerySet[VendorDocument] = vendor.documents.all()
    aggregated_corpus = ""
    for document in documents:
        try:
            pdf_path = document.file.path
            result = converter.convert(pdf_path)
            markdown = result.document.export_to_markdown()
            document.extraction_status = VendorDocument.ExtractionStatus.SUCCESS
            document.save()
            aggregated_corpus += f"\n\n--- {document.document_type} ---\n{markdown}"

        except Exception as e:
            document.extraction_status = VendorDocument.ExtractionStatus.FAILED
            document.save()
            logger.exception(e)

    if not aggregated_corpus.strip():
        vendor.status = Vendor.Status.PENDING
        vendor.save()
        return

    try:
        system_prompt = prompts.json_extract
        raw_json_response = call_cohere(
            system_prompt=system_prompt, user_message=aggregated_corpus, force_json=True
        )

        # Save parsed structures directly to the database layer
        vendor.compliance_payload = json.loads(raw_json_response)
        vendor.status = (
            Vendor.Status.PENDING
        )  # Ready for manual analysis scoring reviews
        vendor.save()

        logger.info(
            f"[PIPELINE_COMPLETE] Vendor extraction finalized for ID: {vendor_id_str}"
        )

    except Exception as pipeline_err:
        logger.critical(
            f"[PIPELINE_CRITICAL_ERROR] Cohere parsing failed: {str(pipeline_err)}"
        )
        vendor.status = Vendor.Status.PENDING
        vendor.save()
