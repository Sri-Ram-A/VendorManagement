import uuid
from django.utils import timezone
from django.db import models


# Create your models here.
class Vendor(models.Model):
    # System & Workflow States
    class Status(models.TextChoices):
        PENDING = "PENDING_ASSESSMENT", "Pending Assessment"
        PROCESSING = "PROCESSING", "Processing Ingestion Pipeline"
        GREEN = "VERIFIED_GREEN", "Verified Low Risk"
        YELLOW = "CONDITIONAL_YELLOW", "Conditional Medium Risk"
        RED = "QUARANTINED_RED", "Critical High Risk Action Required"

    # Industry-Standard Standardized Data Categories
    class DataCategory(models.TextChoices):
        PCI = "PCI_CARDHOLDER_DATA", "Credit Card Details / PAN / CVV"
        PII = "CUSTOMER_PII", "Personally Identifiable Info (Names, Addresses)"
        AUTH = "CREDENTIALS_AUTH", "Authentication Hashes / API Tokens"
        FIN = "FINANCIAL_RECORDS", "Corporate Accounting / Trade Ledger Data"
        PUB = "PUBLIC_MARKETING", "Publicly Available Marketing Assets"

    # Core Metadata Fields
    vendor_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor_name = models.CharField(
        max_length=255,
        unique=True,
        help_text="Official corporate legal name. Example: 'NimbusPay LLC'",
    )
    vendor_type = models.CharField(
        max_length=100,
        help_text="Operational grouping. Example: 'Payment Gateway', 'Cloud Infra Storage'",
    )
    business_owner = models.CharField(
        max_length=255,
        help_text="Internal bank manager monitoring this relationship. Example: 'John Doe (Treasury Desk)'",
    )
    annual_spend = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Used to measure financial criticality. Example: 1250000.00",
    )
    status = models.CharField(
        max_length=30, choices=Status.choices, default=Status.PENDING
    )
    # Static Input Boundaries (Using JSONField but enforcing our DataCategory Enum values)
    declared_data_categories = models.JSONField(
        default=list,
        blank=True,
        help_text="List of asset classes requested. Expected items from Vendor.DataCategory enum. Example: ['CUSTOMER_PII', 'PCI_CARDHOLDER_DATA']",
    )
    declared_systems_accessed = models.JSONField(
        default=list,
        blank=True,
        help_text="List of logical technical target endpoints. Example: ['Core_Production_DB', 'Swift_Gateway_Network']",
    )
    # Automated Structural JSON Payload (Populated by Ingestion views)
    compliance_payload = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "Standardized schema populated via LLM extraction extraction containing keys like: "
            "contract_end_date (str), pci_assessor_type (str), soc2_has_qualified_opinion (bool), "
            "breach_notification_hours (int), and liability_cap_usd (float)."
        ),
    )
    # Analytical Cache Metrics
    current_risk_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Calculated dynamic scale score from 0.00 (Zero Risk) to 100.00 (Extreme Risk)",
    )
    previous_risk_score = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00
    )
    risk_narrative_summary = models.TextField(
        blank=True,
        null=True,
        help_text="AI generated summary explaining the scoring logic or hidden defects caught by cross-checks.",
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
        return f"{self.vendor_name} [{self.get_status_display()}] - Risk: {self.current_risk_score}"


def vendor_document_path(instance, filename):
    return f"vendors/{instance.vendor.vendor_name}/{instance.document_type}/{filename}"


class VendorDocument(models.Model):
    # Document Type submitted
    class DocumentType(models.TextChoices):
        MSA = "MSA", "Master Services Agreement"
        DPA = "DPA", "Data Processing Addendum"
        SOC2 = "SOC2_TYPE2", "SOC 2 Type II Compliance Report"
        PCI = "PCI_DSS_AOC", "PCI-DSS Attestation of Compliance"

    # Whether Document processing is completed during ingestion
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
        upload_to=vendor_document_path,
        help_text="Location pointer for raw binary. Example: 'vendor_compliance_vault/nimbus_pci.pdf'",
    )
    document_reference = models.CharField(
        max_length=100,
        blank=True,
        help_text="Corporate document cross-reference tracking ID. Example: 'SG-MSA-2026-NIMBUS-09'",
    )
    # Date processing markers
    issued_date = models.DateField(
        null=True, blank=True, help_text="Date signed or published. Example: 2026-01-01"
    )
    expiry_date = models.DateField(
        null=True,
        blank=True,
        help_text="Calculated date of expiration. Example: 2027-01-01",
    )
    extraction_status = models.CharField(
        max_length=20,
        choices=ExtractionStatus.choices,
        default=ExtractionStatus.PENDING,
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_expired(self) -> bool:
        """Helper logic allowing views to instantly determine active coverage limits."""
        if self.expiry_date:
            return self.expiry_date < timezone.now().date()
        return False

    def __str__(self):
        return f"{self.vendor.vendor_name} - {self.get_document_type_display()} ({self.extraction_status})"


class VendorAccessGrant(models.Model):
    # Sensitivity currently
    class TechnicalSensitivity(models.TextChoices):
        HIGH = "PCI_HIGH_CRITICALITY", "Direct Production Card Environment Access"
        MED = "RESTRICTED_PII", "Internal Systems Handling Client Identity Records"
        LOW = "LOW_IMPACT_ZONE", "General Purpose Sandbox or Corporate Chat Channel"

    # Status currently provided
    class GrantStatus(models.TextChoices):
        ACTIVE = "ACTIVE", "Active Provisioned Key Entity"
        REVOKED = "REVOKED", "De-provisioned Safe Endpoint"
        ORPHANED = (
            "ORPHANED",
            "Active Token Detected Without a Valid Underpining Contract",
        )

    grant_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey(
        Vendor, on_delete=models.CASCADE, related_name="access_grants"
    )
    system_name = models.CharField(
        max_length=255,
        help_text="The technical target identified in corporate config. Example: 'prod-rds-cluster-01'",
    )
    data_sensitivity = models.CharField(
        max_length=50, choices=TechnicalSensitivity.choices
    )
    access_type = models.CharField(
        max_length=50,
        help_text="The network strategy protocol used. Example: 'IAM_AWS_ROLE', 'OKTA_SAML_GROUP', 'SSH_KEY'",
    )
    grant_status = models.CharField(
        max_length=20, choices=GrantStatus.choices, default=GrantStatus.ACTIVE
    )

    last_used = models.DateTimeField(
        null=True, blank=True, help_text="Last detected network packet timestamps."
    )
    revoked_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when corporate directory severed the link.",
    )

    def __str__(self):
        return f"{self.vendor.vendor_name} -> {self.system_name} ({self.grant_status})"
