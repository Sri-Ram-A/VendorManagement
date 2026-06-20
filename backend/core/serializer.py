# core/serializers.py
import json
from rest_framework import serializers
from .models import Vendor


class VendorIngestionSerializer(serializers.ModelSerializer):
    declared_data_categories = serializers.ListField(
        child=serializers.ChoiceField(choices=Vendor.DataCategory.choices),
        required=False,
        default=list,
    )
    declared_systems_accessed = serializers.CharField(required=False)
    documents = serializers.ListField(
        child=serializers.FileField(allow_empty_file=False, use_url=False),
        write_only=True,
        required=True,
        help_text=(
            "Upload files simultaneously. File names must contain structural keywords "
            "to match types correctly: 'MSA' for contracts, 'DPA' for privacy guidelines, "
            "'SOC' for audits, or 'PCI'/'AOC' for processing compliance."
        ),
    )

    class Meta:
        model = Vendor
        fields = [
            "vendor_name",
            "vendor_type",
            "business_owner",
            "annual_spend",
            "declared_data_categories",
            "declared_systems_accessed",
            "documents",
        ]
    def validate_declared_systems_accessed(self, value):
            if value in ("", None):
                return []
                
            # 1. Attempt to parse it as a native JSON array first
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return parsed
            except (json.JSONDecodeError, TypeError):
                # If JSON decoding fails, gracefully fall back to parsing it as a comma-separated string
                pass

            # 2. Comma-separated string parsing path
            if isinstance(value, str):
                # Split by commas and strip out accidental whitespace
                cleaned_list = [item.strip() for item in value.split(",") if item.strip()]
                return cleaned_list
                
            raise serializers.ValidationError("Must be a valid JSON array or a comma-separated string.")