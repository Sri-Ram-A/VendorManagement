# core/tasks.py
import os
import uuid
import json
from celery import shared_task, chord
from django.db import transaction
from django.db.models import QuerySet
from django.conf import settings

from clients.chroma import get_vector_store
from clients.docling import get_converter
from backend.vendor_logging import get_vendor_logger
from .models import Vendor, VendorDocument
from .orchestrator import run_compliance_audit_orchestrator
from .scoring import compute_and_save_score


@shared_task(name="core.tasks.process_vendor_onboarding_pipeline")
def process_vendor_onboarding_pipeline(vendor_id: str) -> str:
    """
    Orchestration Root. Fetches the vendor tracking records, maps uploaded
    binary payloads, and triggers a parallel Celery canvas pipeline.
    """
    v_logger = get_vendor_logger(vendor_id)
    v_logger.info("pipeline_initialized", stage="orchestration_root", target_vendor_id=vendor_id)
    
    # 0. Check Vendor is created in the database
    try:
        vendor = Vendor.objects.get(pk=uuid.UUID(vendor_id))
    except Vendor.DoesNotExist:
        v_logger.critical("vendor_not_found_abort", target_vendor_id=vendor_id)
        return f"VENDOR_NOT_FOUND: {vendor_id}"
        
    documents: QuerySet[VendorDocument] = vendor.documents.filter(
        extraction_status=VendorDocument.ExtractionStatus.PENDING
    )
    
    # 1. Check if uploaded documents extracts
    if not documents.exists():
        v_logger.debug("no_pending_documents_found", transition="immediate_analysis")
        execute_vendor_compliance_audit.delay(vendor_id)
        return "NO_DOCUMENTS_PENDING"

    # 2. Define child signatures for parallel background execution pools
    task_signatures = [
        parse_and_vectorize_document.s(str(doc.document_id), vendor_id)
        for doc in documents
    ]
    v_logger.info("fan_out_spawned", document_count=len(task_signatures), vendor_name=vendor.vendor_name)

    # Execute Chord Canvas pattern: Run all extractions in parallel, then invoke compliance callback
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
        
        v_logger.info(
            "markdown_extraction_start", 
            doc_type=document.document_type, 
            doc_name=document.file.name, 
            doc_id=document_id_str
        )
        
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
            
        v_logger.info("vectorization_success", doc_type=document.document_type, doc_id=document_id_str)
        return True

    except Exception as error_exception:
        v_logger.error(
            "document_conversion_pipeline_failed", 
            doc_id=document_id_str, 
            error=str(error_exception)
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
    # 1. load the vendor, bail out cleanly if it doesn't exist
    v_logger = get_vendor_logger(vendor_id)
    v_logger.info("parallel_extractions_complete", action="launching_llm_inference")
    
    try:
        vendor = Vendor.objects.get(pk=uuid.UUID(vendor_id))
    except Vendor.DoesNotExist:
        v_logger.critical("audit_engine_aborted", reason="vendor_reference_lost")
        return "VENDOR_NOT_FOUND"

    # 2. confirm at least one document parsed successfully
    successful_docs = vendor.documents.filter(
        extraction_status=VendorDocument.ExtractionStatus.SUCCESS
    )
    if not successful_docs.exists():
        v_logger.error("audit_aborted_no_assets", reason="zero_valid_documents_extracted")
        vendor.status = Vendor.Status.PENDING
        vendor.save(update_fields=["status"])
        return "NO_VALID_DOCUMENTS_EXTRACTED"
        
    v_logger.info("reconstructing_markdown", dynamic_doc_count=successful_docs.count())

    # 3. flip status to PROCESSING so the dashboard shows work in progress
    vendor.status = Vendor.Status.PROCESSING
    vendor.save(update_fields=["status"])

    # 4. fetch + reconstruct markdown for every successfully parsed document
    documents_payload = {}
    for document in successful_docs:
        full_markdown = get_vector_store().read_document_chunks_in_order(
            vendor_id, document.document_type
        )
        if full_markdown.strip():
            documents_payload[document.document_type] = full_markdown
        else:
            v_logger.warning("skip_empty_document_chunks", doc_type=document.document_type)

    # 5. hand off to the pure reasoning orchestrator
    result = run_compliance_audit_orchestrator(
        vendor_id=vendor_id,
        vendor_name=vendor.vendor_name,
        documents_payload=documents_payload,
        existing_bounds=vendor.extracted_legal_bounds,
    )

    # 6. log structured outputs including the raw AI output if necessary
    v_logger.info(
        "orchestrator_complete", 
        fields_extracted_count=len(result.get("fields_extracted", [])), 
        conflicts_count=len(result.get("conflicts", [])),
        raw_llm_output=result.get("extracted_legal_bounds")  # Stored straight as native inner object!
    )

    # 7. hand off to scoring
    compute_and_save_score.delay(vendor_id)

    # 8. Persist and resolve trace path metrics onto the Vendor model row
    relative_log_path = os.path.relpath(v_logger.log_file, settings.MEDIA_ROOT)
    vendor.extracted_legal_bounds = result["extracted_legal_bounds"]
    vendor.execution_trace_log = relative_log_path
    vendor.save(update_fields=["extracted_legal_bounds", "execution_trace_log"])

    return f"AUDIT_COMPLETE: fields={len(result['fields_extracted'])}"