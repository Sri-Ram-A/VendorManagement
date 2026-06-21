import os
import django
import pandas as pd

# Django setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from analytics.models import VendorRegistry

CSV_PATH = "vendor_registry.csv"

df = pd.read_csv(CSV_PATH)

df["contract_end_date"] = pd.to_datetime(
    df["contract_end_date"], errors="coerce"
)
df["last_audit_date"] = pd.to_datetime(
    df["last_audit_date"], errors="coerce"
)

created = 0
updated = 0

for _, row in df.iterrows():
    obj, was_created = VendorRegistry.objects.update_or_create(
        vendor_id=row["vendor_id"],
        defaults={
            "vendor_name": row.get("vendor_name"),
            "vendor_type": row.get("vendor_type"),
            "contact_name": row.get("contact_name"),
            "contact_email": row.get("contact_email"),
            "compliance_certifications": row.get("compliance_certifications"),
            "data_access_scope": row.get("data_access_scope"),
            "risk_score": row.get("risk_score"),
            "breach_status": row.get("breach_status"),
            "annual_spend": row.get("annual_spend"),
            "contract_end_date": (
                row["contract_end_date"].date()
                if pd.notna(row["contract_end_date"])
                else None
            ),
            "last_audit_date": (
                row["last_audit_date"].date()
                if pd.notna(row["last_audit_date"])
                else None
            ),
        },
    )

    if was_created:
        created += 1
    else:
        updated += 1

print(f"Done. Created: {created}, Updated: {updated}")