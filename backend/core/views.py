# backend/core/views.py
from loguru import logger
from rest_framework import serializers, status
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from drf_spectacular.utils import extend_schema, inline_serializer
from django.core.files.uploadedfile import UploadedFile

from .models import Vendor, VendorDocument
from .tasks import process_vendor_onboarding_pipeline
from .serializer import (
    VendorIngestionRequestSerializer,
    VendorIngestionResponseSerializer,
)
from backend.vendor_logging import get_vendor_logger


class VendorDocumentIngestionView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    serializer_class = VendorIngestionRequestSerializer

    @extend_schema(
        operation_id="vendor-ingestion",
        summary="Create vendor assessment",
        description="Uploads documents and starts asynchronous compliance analysis.",
        request=VendorIngestionRequestSerializer,
        responses={
            201: VendorIngestionResponseSerializer,
        },
    )
    def post(self, request: Request) -> Response:
        logger.debug("Recieved multipart third-party onboarding gateway validation.")

        # 0. Validate the payload
        serializer = VendorIngestionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        uploaded_files: list[UploadedFile] = validated_data.pop("documents")
        vendor_name = validated_data["vendor_name"]

        # 1. Initialize structural transactional model record state
        vendor, created = Vendor.objects.get_or_create(
            vendor_name=vendor_name,
            defaults={
                "vendor_type": validated_data["vendor_type"],
                "business_owner": validated_data["business_owner"],
                "annual_spend": validated_data.get("annual_spend"),
                "declared_data_categories": validated_data.get(
                    "declared_data_categories", []
                ),
                "declared_systems_accessed": validated_data.get(
                    "declared_systems_accessed", []
                ),
                "status": Vendor.Status.PROCESSING,
            },
        )
        if not created:
            vendor.status = Vendor.Status.PROCESSING
            vendor.save(update_fields=["status"])
        # Initialize the dynamic contextual logger instance for this vendor path
        v_logger = get_vendor_logger(vendor_id=str(vendor.vendor_id))
        v_logger.info(f"Initialized transactional ledger for vendor: '{vendor_name}'")

        # 2. Stage file payloads sequentially on local disks
        for file_obj in uploaded_files:
            filename = file_obj.name.upper()
            document_type = VendorDocument.DocumentType.MSA
            if "DPA" in filename:
                document_type = VendorDocument.DocumentType.DPA
            elif "SOC" in filename:
                document_type = VendorDocument.DocumentType.SOC2
            elif "PCI" in filename or "AOC" in filename:
                document_type = VendorDocument.DocumentType.PCI

            VendorDocument.objects.create(
                vendor=vendor, document_type=document_type, file=file_obj
            )
            v_logger.debug(f"Mapping: '{file_obj.name}' to type: {document_type}")

        # 3. Hand processing off to background task threads
        v_logger.info("Task passed on to Asynchronous Celery queue task managers.")
        process_vendor_onboarding_pipeline.delay(vendor_id=str(vendor.vendor_id))

        response = VendorIngestionResponseSerializer(
            {
                "message": "Vendor profile initiated. Document extraction queued in background tasks.",
                "vendor_id": vendor.vendor_id,
                "current_status": vendor.status,
            }
        )
        return Response(response.data, status=status.HTTP_201_CREATED)
