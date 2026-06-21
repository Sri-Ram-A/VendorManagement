import uuid
from django.db import models
from django.utils import timezone


class Vendor(models.Model):
    """
    Maintains the authoritative compliance profile, risk scores,
    and execution tracking trace logs for a third-party entity.
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending Assessment"
        PROCESSING = "PROCESSING", "Processing Ingestion Pipeline"
        GREEN = "VERIFIED", "Verified Low Risk"
        YELLOW = "CONDITIONAL", "Conditional Medium Risk"
        RED = "QUARANTINED", "Critical High Risk Action Required"

    class DataCategory(models.TextChoices):
        PCI = "PCI_CARDHOLDER_DATA", "Credit Card Details / PAN / CVV"
        PII = "CUSTOMER_PII", "Personally Identifiable Info (Names, Addresses)"
        AUTH = "CREDENTIALS_AUTH", "Authentication Hashes / API Tokens"
        FIN = "FINANCIAL_RECORDS", "Corporate Accounting / Trade Ledger Data"
        PUB = "PUBLIC_MARKETING", "Publicly Available Marketing Assets"

    # Core Metadata Identity Fields
    vendor_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor_name = models.CharField(
        max_length=255,
        unique=True,
        help_text="Official legal corporate name of the vendor entity.",
    )
    vendor_type = models.CharField(
        max_length=100,
        help_text="Operational categorization. e.g., 'Cloud Storage Provider'.",
    )
    business_owner = models.CharField(
        max_length=255,
        help_text="Internal enterprise manager overseeing the relationship.",
    )
    annual_spend = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    status = models.CharField(
        max_length=30, choices=Status.choices, default=Status.PENDING
    )
    declared_data_categories = models.JSONField(
        default=list,
        blank=True,
        help_text="List of asset classes intended to be shared with this vendor.",
    )
    declared_systems_accessed = models.JSONField(
        default=list,
        blank=True,
        help_text="List of targeted system logical endpoints the vendor can access.",
    )
    extracted_legal_bounds = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            """
            - contract_end_date, contract_start_date (ISO strings)
            - breach_notification_hours (integer numbers)
            - data_return_deadline_days (integer numbers)
            - subprocessors_disclosed (array of text strings)
            - data_categories_processed (array of text strings)
            - liability_cap_usd (numeric float/integer value)
            - liability_uncapped_for_security_breach (boolean)
            - cert_termination_right (boolean)
            - soc2_opinion_type ("qualified" or "unqualified")
            - soc2_audit_period_end (ISO string)
            - pci_dss_level (integer or string value)
            - pci_assessor_type ("independent_qsa" or "self_assessed")
            """
        ),
    )
    discovered_infrastructure = models.JSONField(
        default=list,
        blank=True,
        help_text=(
            "Array of live discovered endpoint configurations. Expected structure:\n"
            "[\n"
            "  {'system_name': 'prod-db-01', 'data_sensitivity': 'PCI_HIGH_CRITICALITY'}\n"
            "]"
        ),
    )
    execution_trace_log = models.FileField(
        upload_to="", 
        null=True,
        blank=True,
        help_text="Relative path to the latest audit trace log file for this vendor.",
    )
    current_risk_score = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00
    )
    previous_risk_score = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00
    )
    risk_narrative_summary = models.TextField(
        blank=True,
        null=True,
        help_text="AI-generated audit rationale explaining compliance exceptions or structural defects.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Vendor Profile Ledger"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["current_risk_score"]),
        ]

    def __str__(self):
        return f"{self.vendor_id} | {self.vendor_name} | {self.get_status_display()} | - Risk: {self.current_risk_score}"


def vendor_document_path_resolver(instance, filename: str) -> str:
    unique_prefix = uuid.uuid4().hex[:12]
    return f"{instance.vendor.vendor_id}/docs/{unique_prefix}_{filename}"


class VendorDocument(models.Model):
    """
    Digital Evidence Vault tracking physical security documentation files,
    parsing pipelines, and operational expiration lifecycles.
    """

    class DocumentType(models.TextChoices):
        MSA = "MSA", "Master Services Agreement"
        DPA = "DPA", "Data Processing Addendum"
        SOC2 = "SOC2_TYPE2", "SOC 2 Type II Compliance Report"
        PCI = "PCI_DSS_AOC", "PCI-DSS Attestation of Compliance"

    class ExtractionStatus(models.TextChoices):
        PENDING = "PENDING", "Pending Engine Queue"
        SUCCESS = "SUCCESS", "Parsed and Validated"
        FAILED = "FAILED", "Pipeline Error Processing File"

    document_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey(
        Vendor, on_delete=models.CASCADE, related_name="documents"
    )
    document_type = models.CharField(max_length=30, choices=DocumentType.choices)
    file = models.FileField(
        upload_to=vendor_document_path_resolver,
        help_text="Path pointer targeting the raw file binary payload stored on disk.",
    )
    document_reference = models.CharField(
        max_length=100,
        blank=True,
        help_text="Internal compliance cross-reference tracking tracking hash.",
    )

    # Chronological Life Safety Metrics
    issued_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)

    # Ingestion Pipeline Status
    extraction_status = models.CharField(
        max_length=20,
        choices=ExtractionStatus.choices,
        default=ExtractionStatus.PENDING,
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_expired(self) -> bool:
        """Determines if the structural document lifetime has lapsed relative to system execution time."""
        if self.expiry_date:
            return self.expiry_date < timezone.now().date()
        return False

    def __str__(self):
        return f"{self.vendor.vendor_name} - {self.get_document_type_display()} ({self.extraction_status})"
