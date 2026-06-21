# filepath: backend/analytics/views.py
from loguru import logger
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from core.models import Vendor


class VendorListView(APIView):
    """Returns all vendors with their current risk status and score."""

    @extend_schema(responses={200: dict})
    def get(self, request: Request) -> Response:
        logger.debug("VendorListView: fetching all vendor records.")
        vendors = Vendor.objects.all().order_by("-created_at")

        payload = [
            {
                "vendor_id": str(v.vendor_id),
                "vendor_name": v.vendor_name,
                "vendor_type": v.vendor_type,
                "business_owner": v.business_owner,
                "status": v.status,
                "current_risk_score": float(v.current_risk_score),
                "previous_risk_score": float(v.previous_risk_score),
                "created_at": v.created_at.isoformat(),
                "updated_at": v.updated_at.isoformat(),
            }
            for v in vendors
        ]

        return Response({"count": len(payload), "vendors": payload}, status=status.HTTP_200_OK)


class VendorDetailView(APIView):
    """Returns full compliance profile for a single vendor."""

    @extend_schema(responses={200: dict})
    def get(self, request: Request, vendor_id) -> Response:
        logger.debug(f"VendorDetailView: fetching vendor {vendor_id}")

        try:
            v = Vendor.objects.get(pk=vendor_id)
        except Vendor.DoesNotExist:
            return Response({"error": "Vendor not found."}, status=status.HTTP_404_NOT_FOUND)

        # Build document list
        documents = [
            {
                "document_id": str(doc.document_id),
                "document_type": doc.document_type,
                "extraction_status": doc.extraction_status,
                "uploaded_at": doc.uploaded_at.isoformat(),
                "is_expired": doc.is_expired,
            }
            for doc in v.documents.all()
        ]

        payload = {
            "vendor_id": str(v.vendor_id),
            "vendor_name": v.vendor_name,
            "vendor_type": v.vendor_type,
            "business_owner": v.business_owner,
            "annual_spend": float(v.annual_spend) if v.annual_spend else None,
            "status": v.status,
            "current_risk_score": float(v.current_risk_score),
            "previous_risk_score": float(v.previous_risk_score),
            "risk_narrative_summary": v.risk_narrative_summary,
            "declared_data_categories": v.declared_data_categories,
            "declared_systems_accessed": v.declared_systems_accessed,
            "extracted_legal_bounds": v.extracted_legal_bounds,
            "execution_trace_log": v.execution_trace_log,
            "documents": documents,
            "created_at": v.created_at.isoformat(),
            "updated_at": v.updated_at.isoformat(),
        }

        return Response(payload, status=status.HTTP_200_OK)