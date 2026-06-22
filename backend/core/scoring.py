"""
core/scoring.py

Deterministic, rule-based risk scoring engine. Reads Vendor.extracted_legal_bounds
(populated by orchestrator.py) plus Vendor.discovered_infrastructure, and produces
a traceable component-by-component score with a RED/YELLOW/GREEN band.

Design choice: every point added to the score is tied to one named rule function
returning (points, reason_string). The final narrative is built by concatenating
fired reasons — never freeform LLM scoring, never an opaque weighted sum.
"""

import uuid
from datetime import date, datetime
from typing import Optional

from celery import shared_task
from pydantic import BaseModel

from backend.vendor_logging import get_vendor_logger
from clients.cohere import call_cohere
from core.models import Vendor


# ============================================================
# CONSTANTS — weights and bands, named so they're easy to defend/tune
# ============================================================

COMPONENT_WEIGHTS = {
    "breach_intelligence": 0.35,
    "compliance_maturity": 0.25,
    "data_blast_radius": 0.20,
    "financial_stability": 0.20,
}

BAND_THRESHOLDS = [
    (80, "QUARANTINED"),
    (50, "CONDITIONAL"),
    (0, "VERIFIED"),
]

ACCESS_WEIGHT_BY_SENSITIVITY = {
    "PCI_CARDHOLDER_DATA": 100,
    "CUSTOMER_PII": 90,
    "CREDENTIALS_AUTH": 85,
    "FINANCIAL_RECORDS": 75,
    "PUBLIC_MARKETING": 10,
}


class ScoreBreakdown(BaseModel):
    """Structured output of one scoring run — saved to Vendor and used for the narrative."""

    breach_intelligence_score: float
    compliance_maturity_score: float
    data_blast_radius_score: float
    financial_stability_score: float
    total_score: float
    risk_band: str
    fired_rules: list[dict]  # [{rule, points, weight_category, reason}, ...]


# ============================================================
# HELPERS — safe field access, since extracted_legal_bounds is sparse
# ============================================================


def get_field_value(bounds: dict, field_name: str) -> Optional[object]:
    """
    Pulls the .value out of the nested FactValue shape, or None if the field
    was never extracted. Distinguishes 'never asked' from 'asked, found false'.
    """
    entry = bounds.get(field_name)
    if entry is None:
        return None
    return entry.get("value")


def field_was_extracted(bounds: dict, field_name: str) -> bool:
    """True only if this field exists in the dict at all — absence is itself a signal."""
    return field_name in bounds


def parse_date_safe(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value)).date()
    except (ValueError, TypeError):
        return None


# ============================================================
# RULE FUNCTIONS — each returns (points_0_to_100, reason_string)
# These are the units everything else is built from. Add new rules here only.
# ============================================================

# --- Compliance maturity rules ---


def rule_no_compliance_docs_on_file(bounds: dict) -> tuple[float, str]:
    """Vendor has neither a SOC2 opinion nor a PCI assessment on record at all."""
    has_soc2 = field_was_extracted(bounds, "soc2_opinion_type")
    has_pci = field_was_extracted(bounds, "pci_dss_level")
    if not has_soc2 and not has_pci:
        return 70.0, "No SOC2 or PCI compliance documentation on file"
    return 0.0, ""


def rule_soc2_qualified_opinion(bounds: dict) -> tuple[float, str]:
    opinion = get_field_value(bounds, "soc2_opinion_type")
    if opinion == "qualified":
        return (
            45.0,
            "SOC2 Type II report carries a QUALIFIED opinion (control exceptions noted)",
        )
    return 0.0, ""


def rule_pci_self_assessed(bounds: dict) -> tuple[float, str]:
    """The specific catch from the NimbusPay PCI AoC — internal self-attestation, not an independent QSA."""
    assessor_type = get_field_value(bounds, "pci_assessor_type")
    if assessor_type == "self_assessed":
        return (
            60.0,
            "PCI-DSS AoC was SELF-ASSESSED by vendor's own staff, not an independent QSA",
        )
    return 0.0, ""


def rule_cert_expired(
    bounds: dict, document_expiry_dates: list[date]
) -> tuple[float, str]:
    today = date.today()
    expired = [d for d in document_expiry_dates if d and d < today]
    if expired:
        days_expired = (today - min(expired)).days
        return min(
            30.0 + days_expired * 0.5, 80.0
        ), f"Certification expired {days_expired} days ago"
    return 0.0, ""


# --- Data blast radius rules ---


def rule_high_sensitivity_access(
    discovered_infrastructure: list[dict],
) -> tuple[float, str]:
    if not discovered_infrastructure:
        return (
            20.0,
            "No documented technical access scope — cannot verify access boundaries",
        )
    max_weight = max(
        (
            ACCESS_WEIGHT_BY_SENSITIVITY.get(item.get("data_sensitivity"), 30)
            for item in discovered_infrastructure
        ),
        default=30,
    )
    if max_weight >= 90:
        return float(
            max_weight
        ), "Vendor has live access to highly sensitive data (PCI/PII/credentials)"
    return float(max_weight), "Vendor access scope limited to lower-sensitivity systems"


def rule_liability_uncapped_for_breach(bounds: dict) -> tuple[float, str]:
    """Not a penalty by itself — uncapped liability is GOOD for the bank. Negative points."""
    uncapped = get_field_value(bounds, "liability_uncapped_for_security_breach")
    if uncapped is True:
        return (
            -10.0,
            "Contract has UNCAPPED liability for security breaches — favorable risk transfer",
        )
    return 0.0, ""


# --- Breach intelligence rules ---


def rule_breach_notification_window_long(bounds: dict) -> tuple[float, str]:
    hours = get_field_value(bounds, "breach_notification_hours")
    if hours is None:
        return (
            25.0,
            "No breach notification SLA found in contract — GDPR Art.33 exposure unclear",
        )
    if isinstance(hours, (int, float)) and hours > 72:
        return (
            35.0,
            f"Contractual breach notification window is {hours}h — exceeds GDPR's 72h requirement",
        )
    return 0.0, ""


def rule_recent_breach_signal(agent_findings: dict) -> tuple[float, str]:
    """Reads agent-sourced fields (trust_tier 4, written during the verification loop)."""
    breach_count = agent_findings.get("recent_breach_signal_count", 0)
    if breach_count and breach_count > 0:
        return (
            65.0,
            f"OSINT verification surfaced {breach_count} recent breach-related signal(s)",
        )
    return 0.0, ""


# --- Financial stability rules ---


def rule_financial_distress_signal(agent_findings: dict) -> tuple[float, str]:
    signal = agent_findings.get("financial_health_signal")
    if signal == "distressed":
        return (
            80.0,
            "Public records indicate financial distress (filings, layoffs, or insolvency signal)",
        )
    if signal == "declining":
        return 40.0, "Public records indicate declining financial health"
    return 0.0, ""


def rule_no_financial_signal_available(agent_findings: dict) -> tuple[float, str]:
    if "financial_health_signal" not in agent_findings:
        return 15.0, "No financial health verification was performed — unknown risk"
    return 0.0, ""


# ============================================================
# COMPONENT AGGREGATION — runs the relevant rules per category, caps at 100
# ============================================================


def score_compliance_maturity(
    bounds: dict, document_expiry_dates: list[date]
) -> tuple[float, list[dict]]:
    fired = []
    rules = [
        ("no_compliance_docs", rule_no_compliance_docs_on_file(bounds)),
        ("soc2_qualified_opinion", rule_soc2_qualified_opinion(bounds)),
        ("pci_self_assessed", rule_pci_self_assessed(bounds)),
        ("cert_expired", rule_cert_expired(bounds, document_expiry_dates)),
    ]
    total = 0.0
    for rule_name, (points, reason) in rules:
        if points > 0:
            total += points
            fired.append(
                {
                    "rule": rule_name,
                    "points": points,
                    "category": "compliance_maturity",
                    "reason": reason,
                }
            )
    return min(total, 100.0), fired


def score_data_blast_radius(
    bounds: dict, discovered_infrastructure: list[dict]
) -> tuple[float, list[dict]]:
    fired = []
    total = 0.0
    points, reason = rule_high_sensitivity_access(discovered_infrastructure)
    if points != 0:
        total += points
        fired.append(
            {
                "rule": "high_sensitivity_access",
                "points": points,
                "category": "data_blast_radius",
                "reason": reason,
            }
        )
    points, reason = rule_liability_uncapped_for_breach(bounds)
    if points != 0:
        total += points
        fired.append(
            {
                "rule": "liability_uncapped",
                "points": points,
                "category": "data_blast_radius",
                "reason": reason,
            }
        )
    return max(min(total, 100.0), 0.0), fired


def score_breach_intelligence(
    bounds: dict, agent_findings: dict
) -> tuple[float, list[dict]]:
    fired = []
    total = 0.0
    for rule_name, (points, reason) in [
        ("breach_notification_window", rule_breach_notification_window_long(bounds)),
        ("recent_breach_signal", rule_recent_breach_signal(agent_findings)),
    ]:
        if points > 0:
            total += points
            fired.append(
                {
                    "rule": rule_name,
                    "points": points,
                    "category": "breach_intelligence",
                    "reason": reason,
                }
            )
    return min(total, 100.0), fired


def score_financial_stability(agent_findings: dict) -> tuple[float, list[dict]]:
    fired = []
    total = 0.0
    for rule_name, (points, reason) in [
        ("financial_distress_signal", rule_financial_distress_signal(agent_findings)),
        (
            "no_financial_signal_available",
            rule_no_financial_signal_available(agent_findings),
        ),
    ]:
        if points > 0:
            total += points
            fired.append(
                {
                    "rule": rule_name,
                    "points": points,
                    "category": "financial_stability",
                    "reason": reason,
                }
            )
    return min(total, 100.0), fired


# ============================================================
# BAND MAPPING
# ============================================================


def total_score_to_band(total_score: float) -> str:
    for threshold, band in BAND_THRESHOLDS:
        if total_score >= threshold:
            return band
    return "VERIFIED"


# ============================================================
# NARRATIVE GENERATION — grounded in fired rules only, never freeform
# ============================================================

NARRATIVE_SYSTEM_PROMPT = """You write a short, factual risk narrative for a bank
compliance analyst. You are given a list of specific rules that fired during
scoring, each with the exact reason it fired. Write 2-4 sentences summarizing
WHY this vendor scored the way it did. Reference only the facts given — do not
invent details, do not soften language, do not add caveats not present in the data.
Lead with the single highest-point rule first."""


def generate_risk_narrative(
    vendor_name: str, total_score: float, risk_band: str, fired_rules: list[dict]
) -> str:
    if not fired_rules:
        return f"{vendor_name} has no risk factors on record. Score: {total_score:.1f} ({risk_band})."

    sorted_rules = sorted(fired_rules, key=lambda r: r["points"], reverse=True)
    facts_block = "\n".join(
        f"- [{r['category']}] {r['reason']} (+{r['points']:.0f} pts)"
        for r in sorted_rules
    )

    user_message = (
        f"Vendor: {vendor_name}\nTotal score: {total_score:.1f}/100\nBand: {risk_band}\n\n"
        f"Fired rules, highest impact first:\n{facts_block}"
    )
    return call_cohere(
        system_prompt=NARRATIVE_SYSTEM_PROMPT,
        user_message=user_message,
        force_json=False,
        temperature=0.2,
    )


# ============================================================
# ENTRYPOINT — called from execute_vendor_compliance_audit in tasks.py
# ============================================================


@shared_task(name="core.tasks.compute_and_save_score")
def compute_and_save_score(vendor_id: str) -> dict:
    v_logger = get_vendor_logger(vendor_id)

    # 0. Validate the payload
    vendor = Vendor.objects.get(pk=uuid.UUID(vendor_id))
    v_logger.info(f"SCORING_START: vendor={vendor.vendor_name}")

    bounds = vendor.extracted_legal_bounds or {}
    discovered_infrastructure = vendor.discovered_infrastructure or []

    # 1. Pull document expiry dates from related VendorDocument rows
    document_expiry_dates = list(
        vendor.documents.exclude(expiry_date__isnull=True).values_list(
            "expiry_date", flat=True
        )
    )

    # 2. Separate out agent-sourced findings (trust_tier 4 fields) from contract-extracted ones —
    #    these feed the breach/financial rules, which only make sense from OSINT, not contract text
    agent_findings = {
        field_name: entry.get("value")
        for field_name, entry in bounds.items()
        if entry.get("trust_tier") == 4
    }
    if any(f.startswith("recent_breach_signal") for f in agent_findings):
        agent_findings["recent_breach_signal_count"] = sum(
            1 for f in agent_findings if f.startswith("recent_breach_signal")
        )

    # 3. Run each component scorer independently — every fired rule is logged with its reason
    compliance_score, compliance_fired = score_compliance_maturity(
        bounds, document_expiry_dates
    )
    blast_radius_score, blast_radius_fired = score_data_blast_radius(
        bounds, discovered_infrastructure
    )
    breach_score, breach_fired = score_breach_intelligence(bounds, agent_findings)
    financial_score, financial_fired = score_financial_stability(agent_findings)

    all_fired_rules = (
        compliance_fired + blast_radius_fired + breach_fired + financial_fired
    )
    v_logger.info(f"RULES_FIRED: {[r['rule'] for r in all_fired_rules]}")

    # 4. Combine components using the named weights — simple weighted sum, no hidden constants
    total_score = (
        compliance_score * COMPONENT_WEIGHTS["compliance_maturity"]
        + blast_radius_score * COMPONENT_WEIGHTS["data_blast_radius"]
        + breach_score * COMPONENT_WEIGHTS["breach_intelligence"]
        + financial_score * COMPONENT_WEIGHTS["financial_stability"]
    )
    total_score = max(0.0, min(total_score, 100.0))
    risk_band = total_score_to_band(total_score)
    v_logger.info(f"SCORE_COMPUTED: total={total_score:.2f} band={risk_band}")

    # 5. Generate the grounded narrative — built only from fired_rules, no freeform guessing
    narrative = generate_risk_narrative(
        vendor.vendor_name, total_score, risk_band, all_fired_rules
    )
    v_logger.info(f"NARRATIVE_GENERATED: length={len(narrative)} chars")

    # 6. Shift current score to previous before overwriting — this is your trend/history signal
    vendor.previous_risk_score = vendor.current_risk_score
    vendor.current_risk_score = round(total_score, 2)
    vendor.status = risk_band
    vendor.risk_narrative_summary = narrative

    # 7. Persist everything in one save
    vendor.save(
        update_fields=[
            "previous_risk_score",
            "current_risk_score",
            "status",
            "risk_narrative_summary",
        ]
    )
    v_logger.success(
        f"SCORING_DONE: vendor={vendor.vendor_name} score={total_score:.2f} band={risk_band}"
    )

    return {
        "vendor_id": vendor_id,
        "total_score": total_score,
        "risk_band": risk_band,
        "fired_rules": all_fired_rules,
    }
