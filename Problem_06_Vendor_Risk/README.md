# Problem 06: Third-Party & Vendor Risk Management - Sample Datasets

## Overview
Sample dataset for Problem Statement 06 - managing and monitoring vendor/third-party risks.

## Files Included

### 1. `vendor_registry.csv` (200+ vendor records)
**Comprehensive central vendor registry** with comprehensive risk and compliance data across diverse vendors.

**Columns:**
- `vendor_id` - Unique identifier
- `vendor_name` - Company name
- `vendor_category` - Type (CRM, Cloud, Payment Processing, etc.)
- `vendor_size` - Small, Mid-market, Large
- `contract_start_date` - When contract began
- `contract_end_date` - When contract ends
- `data_access_scope` - What systems/data they can access
- `data_sensitivity` - Level of data access (LOW-CRITICAL)
- `annual_spend` - Contract value
- `soc2_type2` - Do they have SOC 2 Type II cert?
- `soc2_expiry` - When cert expires
- `iso27001` - Do they have ISO 27001?
- `gdpr_dpa` - Do they have GDPR Data Processing Agreement?
- `breach_history` - Any known breaches?
- `financial_rating` - Credit rating (A+, A, B, etc.)
- `country` - Where they're based
- `renewal_status` - auto_renewal, pending_renewal, needs_renewal, etc.
- `risk_score` - Overall risk (0-100)

## High-Risk Vendors to Notice

### 1. VND-0010 (ITServiceProvider) - SCORE: 85  CRITICAL
- **Issue**: Active ransomware breach (Mar 2025)
- **Data Access**: All systems (CRITICAL)
- **Cert Status**: No SOC 2, no ISO
- **Financial**: D rating (viability concern)
- **Country**: India
- **Status**: CONTRACT EXPIRED (needs renewal decision!)
- **Action**: PrioritizeHigh-risk vendor review

### 2. VND-0004 (LegacyIntegration Corp) - SCORE: 72  HIGH
- **Issue**: No certifications, no GDPR DPA
- **Data Access**: Custom API + Database
- **Contract**: Expires Sept 2026 (soon)
- **Country**: India
- **Status**: Needs renewal (compliance gap)
- **Action**: Require compliance remediation

### 3. VND-0001 (CloudBackup Inc) - SCORE: 68  HIGH
- **Issue**: Recent breach (Jan 2024, unencrypted backup)
- **Note**: SOC 2 expires Sept 2026 (soon)
- **Status**: Pending approval (renewal holds up)
- **Action**: Request updated SOC 2, evaluate breach response

### 4. VND-0006 (DataAnalytics Pro) - SCORE: 55  MEDIUM
- **Issue**: Contract EXPIRED (needs renewal)
- **Note**: SOC 2 expired (Dec 2025)
- **Gap**: No GDPR DPA
- **Status**: Needs immediate renewal action
- **Action**: Urgent contract & compliance review

## Low-Risk Vendors (Baseline)

**VND-0003 (AWSCloud) - SCORE: 25**  BEST
- Large, mature vendor
- All certs current (SOC 2, ISO, GDPR)
- No breach history
- Financial rating: A+
- Status: Auto-renewal

**VND-0012 (LoggingService) - SCORE: 20**  GOOD
- Large, stable vendor
- Current certs + compliance
- Critical data, but trusted vendor
- Status: Auto-renewal

## How to Use

### Load in Python:
```python
import pandas as pd
from datetime import datetime

# Load vendor registry
vendors = pd.read_csv('vendor_registry.csv', parse_dates=['contract_start_date', 'contract_end_date', 'soc2_expiry'])
print(f"Total vendors tracked: {len(vendors)}")

# High-risk vendors
high_risk = vendors[vendors['risk_score'] >= 70]
print(f"\nHigh-risk vendors: {len(high_risk)}")
print(high_risk[['vendor_name', 'risk_score', 'data_sensitivity', 'renewal_status']])

# Contracts expiring soon (30 days)
today = pd.Timestamp.now()
expiring = vendors[(vendors['contract_end_date'] - today).dt.days <= 30]
print(f"\nContracts expiring within 30 days: {len(expiring)}")

# Missing compliance
no_soc2 = vendors[vendors['soc2_type2'] == False]
no_gdpr = vendors[vendors['gdpr_dpa'] == False]
print(f"\nVendors without SOC 2: {len(no_soc2)}")
print(f"Vendors without GDPR DPA: {len(no_gdpr)}")

# Breach history
breached = vendors[vendors['breach_history'].notna()]
print(f"\nVendors with known breaches: {len(breached)}")
```

### Analysis Ideas:

1. **Risk Scoring**: Combine data access + financial health + cert status + breach history
2. **Contract Management**: Track expiry dates, auto-renewal status
3. **Compliance Gap**: Which vendors missing SOC 2, ISO, GDPR DPA?
4. **Breach Monitoring**: Any recent breaches in vendor ecosystem?
5. **Financial Viability**: D-rated vendors may not stay in business
6. **Data Sensitivity**: Highest risk = critical data access + low cert status
7. **Portfolio Health**: What % of vendors are "healthy" (low risk)?

## Risk Scoring Formula (Suggested)

```
Risk_Score = DataAccess_Weight + Cert_Gap + Breach_Factor + Financial_Risk + Contract_Risk

1. Data Sensitivity (0-40 pts)
   CRITICAL: 40 pts
   HIGH: 30 pts
   MEDIUM: 20 pts
   LOW: 5 pts

2. Certification Gaps (0-30 pts)
   Missing SOC 2: +15 pts
   Missing ISO: +10 pts
   Missing GDPR DPA: +5 pts

3. Breach History (0-20 pts)
   Recent (< 12 mo): +20 pts
   Old (12-24 mo): +10 pts
   None: 0 pts

4. Financial Health (0-10 pts)
   Rating C or below: +10 pts
   Rating B-: +5 pts
   Rating B or better: 0 pts

5. Contract Risk (0-10 pts)
   Expired: +10 pts
   Expiring (< 90 days): +5 pts
   Current: 0 pts
```

## Real-World Scenarios

1. **Vendor Breach** (VND-0010 example)
   - Mar 2025 ransomware incident
   - Manage fallback procedures
   - Notify customers if impacted
   - Evaluate replacement vendor

2. **Compliance Gap** (VND-0004)
   - Vendor has data access but NO certifications
   - Contract renewal blocked until compliance achieved
   - Negotiate compliance remediation plan

3. **Expired Contract** (VND-0006, VND-0010)
   - Contract date passed
   - Vendor legally has no ongoing agreement
   - Must either: renew, terminate, or formally extend

4. **Financial Risk** (VND-0010: D rating)
   - If vendor fails financially
   - Data serviceability risk
   - Business continuity risk

## Data Characteristics

- **Vendors**: 15 samples (realistic enterprises have  500-2000)
- **Time Range**: 2018-2027 (contract history)
- **Cert Status**: Mix of current, expired, none
- **Countries**: USA, Canada, China, India (varied risk)
- **Risk Scores**: 20-85 (wide range)
- **Data Sensitivity**: LOW → CRITICAL

## Monitoring Framework

Build system to:
1. **Alert on contract expiry** (60/30/7 days out)
2. **Monitor breach databases** for vendor names
3. **Track cert expirations** (auto-alert when < 90 days)
4. **Trigger renewal** when contract nearing end
5. **Risk recalculation** when new information appears

## Expected Output

Comprehensive vendor risk dashboard showing:
- **Portfolio summary**: # vendors by risk level
- **Red flags**: High-risk vendors requiring action
- **Compliance scorecard**: % with current certs
- **Contract timeline**: Renewals due
- **New vendor onboarding**: Evaluation checklist

## Next Steps

1. **Load vendor data** and understand portfolio
2. **Calculate risk scores** for each
3. **Identify High-risk vendors** requiring attention
4. **Build compliance tracker** for certifications
5. **Create alert system** for expiries/breaches
6. **Generate quarterly reports** for leadership

---

See [PROBLEM_STATEMENT_06.md](../../PROBLEM_STATEMENT_06.md) for full details.
