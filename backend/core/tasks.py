import os
import uuid
from celery import shared_task, chord
from django.db import transaction
from django.db.models import QuerySet

from clients.chroma import get_vector_store
from clients.docling import get_converter
from backend.logging import get_vendor_logger
from .models import Vendor, VendorDocument
from .orchestrator import run_compliance_audit_orchestrator


@shared_task(name="core.tasks.process_vendor_onboarding_pipeline")
def process_vendor_onboarding_pipeline(vendor_id: str) -> str:
    """
    Orchestration Root. Fetches the vendor tracking records, maps uploaded
    binary payloads, and triggers a parallel Celery canvas pipeline.
    """
    v_logger = get_vendor_logger(vendor_id)
    v_logger.info("Initializing multi-stage analysis worker pipeline orchestration.")
    # 0. Check Vendor is created in the database
    try:
        vendor = Vendor.objects.get(pk=uuid.UUID(vendor_id))
    except Vendor.DoesNotExist:
        v_logger.critical(f"Exiting : Target vendor UUID {vendor_id} not found.")
        return f"VENDOR_NOT_FOUND: {vendor_id}"
    documents: QuerySet[VendorDocument] = vendor.documents.filter(
        extraction_status=VendorDocument.ExtractionStatus.PENDING
    )
    # 1. Check if uploaded documents extracts
    if not documents.exists():
        v_logger.debug("No pending document. Transitioning to analysis.")
        execute_vendor_compliance_audit.delay(vendor_id)
        return "NO_DOCUMENTS_PENDING"

    # 2. Define child signatures for parallel background execution pools
    task_signatures = [
        parse_and_vectorize_document.s(str(doc.document_id), vendor_id)
        for doc in documents
    ]
    v_logger.info(f"Spawning fan-out processing for {len(task_signatures)} documents.")

    # Execute Chord Canvas pattern: Run all extractions in parallel, then invoke the compliance audit callback
    chord(task_signatures)(execute_vendor_compliance_audit.si(vendor_id))
    return f"ORCHESTRATION_DISPATCHED_FOR_VENDOR: {vendor.vendor_id}"


@shared_task(name="core.tasks.parse_and_vectorize_document")
def parse_and_vectorize_document(document_id_str: str, vendor_id: str) -> bool:
    """
    Isolated Worker Task. Uses Docling to parse a specific PDF file format asset into
    clean text, updates the storage tables, and feeds the local RAG vector engine layers.
    """
    v_logger = get_vendor_logger(vendor_id)

    try:
        # 0. Check whether document exists in database
        document = VendorDocument.objects.get(pk=uuid.UUID(document_id_str))
        pdf_path = document.file.path
        v_logger.info(f"Starting markdown extraction for {document.file.name}")
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"Binary file asset payload missing : {pdf_path}")

        # 1. Convert structural document layouts cleanly using Docling
        converter = get_converter()
        conversion_result = converter.convert(pdf_path)
        markdown_text = conversion_result.document.export_to_markdown()

        # 2. Feed text structures directly into your root ChromaDB manager instance
        rag_manager = get_vector_store()
        rag_manager.vectorize_markdown_content(
            vendor_id=vendor_id,
            document_type=document.document_type,
            markdown_text=markdown_text,
        )

        # 3. Update database metrics using atomic safe transaction boundaries
        with transaction.atomic():
            document.extraction_status = VendorDocument.ExtractionStatus.SUCCESS
            document.save(update_fields=["extraction_status"])
        v_logger.success(f"Vectorized document type node: {document.document_type}")
        return True

    except Exception as error_exception:
        v_logger.exception(
            f"Pipeline error caught during document conversion: {str(error_exception)}"
        )
        with transaction.atomic():
            doc_record = VendorDocument.objects.filter(
                pk=uuid.UUID(document_id_str)
            ).first()
            if doc_record:
                doc_record.extraction_status = VendorDocument.ExtractionStatus.FAILED
                doc_record.save(update_fields=["extraction_status"])
        return False


@shared_task(name="core.tasks.execute_vendor_compliance_audit")
def execute_vendor_compliance_audit(vendor_id: str) -> str:
    v_logger = get_vendor_logger(vendor_id)
    v_logger.info("All parallel file extractions complete. Launching LLM inference.")

    try:
        vendor = Vendor.objects.get(pk=uuid.UUID(vendor_id))
    except Vendor.DoesNotExist:
        v_logger.critical("Audit engine aborted: Vendor reference trace lost.")
        return "VENDOR_NOT_FOUND"

    successful_docs_count = vendor.documents.filter(
        extraction_status=VendorDocument.ExtractionStatus.SUCCESS
    ).count()
    if successful_docs_count == 0:
        v_logger.error("Zero documentation assets were successfully parsed.")
        vendor.status = Vendor.Status.PENDING
        vendor.save(update_fields=["status"])
        return "NO_VALID_DOCUMENTS_EXTRACTED"

    v_logger.info(f"Processed {successful_docs_count} docs. Initializing LLM loops.")
    result = run_compliance_audit_orchestrator(vendor_id)
    
    from core.scoring import compute_and_save_score
    compute_and_save_score.delay(vendor_id)

    return f"AUDIT_COMPLETE: fields={len(result['fields_extracted'])}"
