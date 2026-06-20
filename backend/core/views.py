import uuid
from rest_framework import serializers, status
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from drf_spectacular.utils import extend_schema, inline_serializer
from django.core.files.uploadedfile import UploadedFile

from .models import Vendor, VendorDocument
from .tasks import orchestrate_vendor_documents
from .serializer import VendorIngestionSerializer


class VendorIngestionView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    serializer_class = VendorIngestionSerializer

    @extend_schema(
        request=VendorIngestionSerializer,
        responses={
            201: inline_serializer(
                name="IngestionAcceptedResponse",
                fields={
                    "message": serializers.CharField(),
                    "vendor_id": serializers.UUIDField(),
                    "current_status": serializers.CharField(),
                },
            )
        },
        description="Onboards a vendor and shifts heavy document processing off to background task workers.",
    )
    def post(self, request: Request, *args, **kwargs) -> Response:
        serializer = VendorIngestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        uploaded_files: list[UploadedFile] = validated_data.pop("documents")

        # 1. Initialize the baseline Vendor profile record state
        vendor = Vendor.objects.create(
            vendor_name=validated_data["vendor_name"],
            vendor_type=validated_data["vendor_type"],
            business_owner=validated_data["business_owner"],
            annual_spend=validated_data.get("annual_spend"),
            declared_data_categories=validated_data.get("declared_data_categories", []),
            declared_systems_accessed=validated_data.get(
                "declared_systems_accessed", []
            ),
            status=Vendor.Status.PROCESSING,
        )

        # 2. Stage file payloads on local disks to make them accessible to your tasks
        for file_obj in uploaded_files:
            filename = file_obj.name.upper()
            doc_type = VendorDocument.DocumentType.MSA
            if "DPA" in filename:
                doc_type = VendorDocument.DocumentType.DPA
            elif "SOC" in filename:
                doc_type = VendorDocument.DocumentType.SOC2
            elif "PCI" in filename or "AOC" in filename:
                doc_type = VendorDocument.DocumentType.PCI

        VendorDocument.objects.create(
            vendor=vendor, document_type=doc_type, file=file_obj
        )
        # 3. Hand processing over to Celery background task workers
        orchestrate_vendor_documents.delay(vendor_id_str=str(vendor.vendor_id))

        return Response(
            {
                "message": "Vendor profile initiated. Document extraction queued in background tasks.",
                "vendor_id": vendor.vendor_id,
                "current_status": vendor.status,
            },
            status=status.HTTP_201_CREATED,
        )
