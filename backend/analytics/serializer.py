from rest_framework import serializers
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field

from core.models import Vendor, VendorDocument


class ErrorResponseSerializer(serializers.Serializer):
    detail = serializers.CharField(required=False)
    error = serializers.CharField(required=False)


class VendorDocumentSerializer(serializers.ModelSerializer):
    document_type = serializers.ChoiceField(
        choices=VendorDocument.DocumentType.choices,
        read_only=True,
    )
    extraction_status = serializers.ChoiceField(
        choices=VendorDocument.ExtractionStatus.choices,
        read_only=True,
    )
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
    status = serializers.ChoiceField(choices=Vendor.Status.choices, read_only=True)

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
    status = serializers.ChoiceField(choices=Vendor.Status.choices, read_only=True)
    declared_data_categories = serializers.ListField(
        child=serializers.ChoiceField(choices=Vendor.DataCategory.choices),
        read_only=True,
    )
    declared_systems_accessed = serializers.ListField(
        child=serializers.CharField(),
        read_only=True,
    )
    documents = VendorDocumentSerializer(many=True, read_only=True)
    execution_trace_log = serializers.SerializerMethodField()

    class Meta:
        model = Vendor
        fields = "__all__"

    @extend_schema_field(OpenApiTypes.URI)
    def get_execution_trace_log(self, obj) -> str | None:
        if not obj.execution_trace_log:
            return None

        request = self.context.get("request")
        if request is not None:
            return request.build_absolute_uri(obj.execution_trace_log.url)

        return obj.execution_trace_log.url


class VendorRiskPredictionResponseSerializer(serializers.Serializer):
    vendor_id = serializers.CharField()
    vendor_name = serializers.CharField()
    is_anomaly = serializers.BooleanField()
    anomaly_type = serializers.CharField()
    confidence = serializers.FloatField()
    all_probs = serializers.DictField(child=serializers.FloatField())
