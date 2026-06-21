#!/usr/bin/env python3
"""
generate_samples.py

Batch-generates N synthetic 4-document compliance bundles (SOC2, PCI-DSS AoC,
MSA, DPA) by templating vars.tex and recompiling with pdflatex.

Usage:
    python3 generate_samples.py --count 50 --outdir samples/

Each sample gets its own subfolder: samples/sample_0001/{soc2,pci_dss,msa,dpa}.pdf
plus the vars.tex used, so you can pair the PDFs with their ground-truth
field values for training/eval labels.
"""

import argparse
import random
import shutil
import subprocess
from pathlib import Path

VENDOR_NAMES = [
    "Sentrix Cyber Solutions LLC", "Vantage Threat Labs Inc.", "Quoram Data Systems LLC",
    "Beacon Ridge Technologies LLC", "Cobalt Stream Networks Inc.", "Atlas Ferry Payments LLC",
    "Northwind Processing Corp.", "Halcyon Ledger Systems LLC",
]
VENDOR_STATES = ["Delaware", "Nevada", "Texas", "California", "New York"]
CLIENT_NAMES = [
    "Helios Capital Markets N.V.", "Meridian Global Bank S.A.", "Castellan Trust \\& Co.",
    "Argosy Financial Group plc", "Ondine Asset Management S.A.",
]
CLIENT_COUNTRIES = ["the Netherlands", "France", "Germany", "Ireland", "Luxembourg"]
AUDIT_FIRMS = [
    "Granite Peak Assurance \\& Risk Advisory LLP", "Castlebridge Audit Partners LLP",
    "Northfield Assurance Group LLP",
]
ROOT_CAUSES = [
    "a misconfigured cron scheduler that silently failed after a credential rotation",
    "an expired service account token that blocked the rotation job",
    "a regional failover that left the rotation service unscheduled",
]
SUBPROCESSOR_PAIRS = [
    ("Amazon Web Services (AWS)", "eu-central-1 (Frankfurt)", "Secure cloud infrastructure and data hosting",
     "Databricks Data Cloud", "Data warehousing and analytics processing"),
    ("Google Cloud Platform (GCP)", "europe-west1 (Belgium)", "Secure cloud infrastructure and data hosting",
     "Snowflake Data Cloud", "Data warehousing and analytics processing"),
    ("Microsoft Azure", "West Europe (Netherlands)", "Secure cloud infrastructure and data hosting",
     "Fivetran", "Data pipeline orchestration"),
]


def rand_date(year_low=2025, year_high=2026):
    import datetime
    start = datetime.date(year_low, 1, 1)
    end = datetime.date(year_high, 12, 31)
    delta = (end - start).days
    d = start + datetime.timedelta(days=random.randint(0, delta))
    return d.strftime("%B %-d, %Y")


def build_vars(idx: int) -> str:
    vendor = random.choice(VENDOR_NAMES)
    client = random.choice(CLIENT_NAMES)
    sp1, sp1r, sp1p, sp2, sp2p = random.choice(SUBPROCESSOR_PAIRS)

    fields = {
        "VendorName": vendor,
        "VendorAddress": f"{random.randint(100,9999)} Meridian Way, Suite {random.randint(100,999)}, Austin, TX 787{random.randint(10,99)}",
        "VendorState": random.choice(VENDOR_STATES),
        "SystemName": "Unified Payment Gateway Platform",
        "ClientName": client,
        "ClientCountry": random.choice(CLIENT_COUNTRIES),
        "ClientAddress": "Zuidplein 80, 1077 XV Amsterdam, the Netherlands",
        "ClientLegalForm": "naamloze vennootschap",
        "AuditFirm": random.choice(AUDIT_FIRMS),
        "AuditPeriodStart": "April 1, 2025",
        "AuditPeriodEnd": "March 31, 2026",
        "SOCReportDate": rand_date(2026, 2026),
        "SOCEngagementTitle": "Partner, Risk Advisory Services Engagement Director",
        "ExceptionCriteria": "Security and Confidentiality (CC6.3)",
        "ExceptionID": f"CC6.3-{random.randint(1,20):02d}",
        "ExceptionSampleSize": str(random.choice([20, 25, 30, 40])),
        "ExceptionAffectedCount": str(random.randint(2, 10)),
        "ExceptionThresholdDays": "90",
        "ExceptionActualDays": str(random.randint(150, 400)),
        "ExceptionRootCause": random.choice(ROOT_CAUSES),
        "RemediationDate": rand_date(2026, 2026),
        "PCIVersion": "4.0",
        "PCIAttestationDate": rand_date(2026, 2026),
        "PCIAttestationRef": f"{vendor.split()[0].upper()}-AoC-PCIv4-2026",
        "PCIAssessmentStart": "February 2, 2026",
        "PCIAssessmentEnd": "February 13, 2026",
        "PCIServiceType": "Payment Gateway Services, Authorization Routing",
        "PCIAssessorName": random.choice(["Renata Oduya", "Marcus Vance", "Elena Brandt", "Tomas Reyes"]),
        "PCIAssessorTitle": f"Director of Infrastructure Operations, {vendor}",
        "PCIAssessmentMode": "Self-Assessed / Vendor Internal Certification Program",
        "PCIEncryptionStandard": "AES-256",
        "PCITransitStandard": "TLS 1.3",
        "MSARef": f"HCM-MSA-2026-{vendor.split()[0].upper()}-{random.randint(1,99):02d}",
        "EffectiveDate": "January 1, 2026",
        "InitialTermMonths": str(random.choice([12, 24, 36])),
        "GoverningLawState": "New York",
        "VenueCounty": "New York County, New York",
        "LiabilityCapAmount": f"{random.choice(['Three','Four','Five','Ten'])} Million United States Dollars",
        "PaymentTermDays": str(random.choice([15, 30, 45])),
        "LatePaymentRate": "1.5\\%",
        "CureDays": "30",
        "ConfidentialitySurvivalYears": str(random.choice([3, 5, 7])),
        "RequiredCertifications": "PCI DSS Level 1 certification, ISO 27001, and SOC 2 Type II",
        "DPAGoverningLaw": "the laws of the Netherlands and applicable EU data protection law",
        "BreachNotificationEmail": "security-incidents@helioscm.example",
        "BreachNotificationHours": str(random.choice([24, 48, 72])),
        "PostTerminationRetentionDays": str(random.choice([30, 60, 90])),
        "DataSubjectCategories": "Retail Brokerage Customers and Institutional Counterparties",
        "AuditFrequency": "once per year",
        "AuditNoticeContext": "reasonable notice",
        "SubprocessorOneName": sp1,
        "SubprocessorOneRegion": sp1r,
        "SubprocessorOnePurpose": sp1p,
        "SubprocessorTwoName": sp2,
        "SubprocessorTwoRegion": "As designated by Processor (subject to EU adequacy or safeguards)",
        "SubprocessorTwoPurpose": sp2p,
        "SubprocessorNoticeDays": "30",
        "SubprocessorObjectionDays": "15",
    }

    lines = [f"% AUTO-GENERATED -- sample {idx}"]
    for k, v in fields.items():
        lines.append(f"\\newcommand{{\\{k}}}{{{v}}}")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=5)
    ap.add_argument("--outdir", type=str, default="samples")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    random.seed(args.seed)
    here = Path(__file__).parent
    outroot = here / args.outdir
    outroot.mkdir(parents=True, exist_ok=True)

    docs = ["soc2", "pci_dss", "msa", "dpa"]

    for i in range(1, args.count + 1):
        sample_dir = outroot / f"sample_{i:04d}"
        sample_dir.mkdir(parents=True, exist_ok=True)

        # copy static templates
        shutil.copy(here / "preamble.tex", sample_dir / "preamble.tex")
        for d in docs:
            shutil.copy(here / f"{d}.tex", sample_dir / f"{d}.tex")

        # write fresh vars.tex for this sample
        (sample_dir / "vars.tex").write_text(build_vars(i))

        for d in docs:
            subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", f"{d}.tex"],
                cwd=sample_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            # run twice for stable headers/refs (cheap insurance, not strictly needed here)
            subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", f"{d}.tex"],
                cwd=sample_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )

        # clean aux files, keep .tex + .pdf
        for ext in ("aux", "log", "out"):
            for f in sample_dir.glob(f"*.{ext}"):
                f.unlink()

        print(f"[{i}/{args.count}] {sample_dir}")


if __name__ == "__main__":
    main()
