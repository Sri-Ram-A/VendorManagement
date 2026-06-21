# filepath: backend/analytics/models.py
import uuid
from django.db import models


class VendorRegistry(models.Model):
    """Raw vendor registry data, mirrors vendor_registry.csv columns."""

    vendor_id = models.CharField(max_length=64, primary_key=True)  # use CSV's vendor_id directly as PK
    vendor_name = models.CharField(max_length=255)
    vendor_type = models.CharField(max_length=128, blank=True, null=True)
    contact_name = models.CharField(max_length=255, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    compliance_certifications = models.TextField(blank=True, null=True)   # raw pipe-delimited string, e.g. "SOC2:2025-01-01|ISO27001:2024-06-01"
    data_access_scope = models.CharField(max_length=128, blank=True, null=True)
    risk_score = models.FloatField()
    breach_status = models.CharField(max_length=128, blank=True, null=True)
    annual_spend = models.FloatField(blank=True, null=True)
    contract_end_date = models.DateField(blank=True, null=True)
    last_audit_date = models.DateField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "vendor_registry"

    def __str__(self):
        return f"{self.vendor_id} - {self.vendor_name}"

    def to_dict(self):
        """Matches the raw CSV row shape expected by build_features_simple / predict_vendor."""
        return {
            "vendor_id": self.vendor_id,
            "vendor_name": self.vendor_name,
            "vendor_type": self.vendor_type,
            "contact_name": self.contact_name,
            "contact_email": self.contact_email,
            "compliance_certifications": self.compliance_certifications,
            "data_access_scope": self.data_access_scope,
            "risk_score": self.risk_score,
            "breach_status": self.breach_status,
            "annual_spend": self.annual_spend,
            "contract_end_date": self.contract_end_date.isoformat() if self.contract_end_date else None,
            "last_audit_date": self.last_audit_date.isoformat() if self.last_audit_date else None,
        }