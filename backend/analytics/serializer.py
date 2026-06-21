from rest_framework import serializers
from core.models import Vendor, VendorDocument


class VendorDocumentSerializer(serializers.ModelSerializer):
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = VendorDocument
        fields = [
            "document_id",
            "document_type",
            "extraction_status",
            "uploaded_at",
            "is_expired",
        ]


class VendorListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = [
            "vendor_id",
            "vendor_name",
            "vendor_type",
            "business_owner",
            "status",
            "current_risk_score",
            "previous_risk_score",
            "created_at",
            "updated_at",
        ]


class VendorDetailSerializer(serializers.ModelSerializer):
    documents = VendorDocumentSerializer(many=True, read_only=True)

    class Meta:
        model = Vendor
        fields = [
            "vendor_id",
            "vendor_name",
            "vendor_type",
            "business_owner",
            "annual_spend",
            "status",
            "current_risk_score",
            "previous_risk_score",
            "risk_narrative_summary",
            "declared_data_categories",
            "declared_systems_accessed",
            "extracted_legal_bounds",
            "execution_trace_log",
            "documents",
            "created_at",
            "updated_at",
        ]
