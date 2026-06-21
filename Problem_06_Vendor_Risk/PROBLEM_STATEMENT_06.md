#  Problem Statement 06: Third-Party & Vendor Risk Management

> **Enterprise Challenge:** 60% of data breaches involve third parties. Managing vendor risk at scale is a hiring/firing nightmare.

---

## The Business Problem

**Scenario:** Enterprise works with 1,000+ vendors:
- Cloud providers (AWS, Azure, Salesforce)
- Contractors & consultants
- Software vendors (antivirus, backup, security)
- Integration partners
- Managed service providers (MSPs)
- Payment processors, HR platforms, etc.

**The Nightmare:**
```
Q: "Does our backup vendor have SOC 2 certification?"
A: "Uh, let me check... no one knows. It's an email from 2022."

Q: "What data does Vendor X have access to?"
A: "Main database? Customer profiles? Not sure."

Q: "Our Payroll vendor was breached. Do we have a contract clause?"
A: "Found a PDF on someone's old machine. No risk assessment."

Q: "Can we use this new SaaS app?"
A: "IT security hasn't reviewed it yet. Been blocked for 3 months."

Result: Business moves at 10 mph because security can't answer simple questions.
```

**Real Incidents:**
- _Case 1:_ Vendor breach exposing customer PII → No notification from vendor (contract unclear)
- _Case 2:_ Contractor access never revoked after project ended → Sold data to competitor
- _Case 3:_ Cloud backup vendor changed terms → Now claiming data ownership
- _Case 4:_ Payment processor security downgrade → Exposed during PCI-DSS audit

**The Challenge:**
-  Vendor risk assessment is spreadsheet-based (inconsistent, outdated)
- ⏰ No clear scoring system ("Is this vendor acceptable?")
-  Auditors ask "Who has access to customer data?" → Can't answer
-  Continuous monitoring impossible (manually check each vendor quarterly?)
-  No playbook for handling vendor breaches/issues

**Compliance Impact:**
- GDPR Article 28: Data Processor requirements (vendors MUST meet standards)
- GDPR Article 33: Breach notification (if vendor is breached, you're liable)
- SOX 404: Dependency on third parties = internal control risk
- NIST SP 800-53 SA-9: Third-party services security requirements

---

## Challenge Overview

Build a system to:
1. **Inventory** all vendors/third-parties and their access/risks
2. **Assess** vendor security posture and compliance
3. **Score** vendor risk level (traffic light system)
4. **Monitor** vendor risk continuously (certifications, breaches)
5. **Alert** on risk changes (vendor downgrade, new breach)
6. **Support** contract negotiation (risk-based SLAs)
7. **Track** remediation (when vendor fixes issues)

---

##  Data Reality & Edge Cases

**Vendor Management Nightmares:**
- Vendors change frequently (security downgrades, breaches discovered later)
- Data access scope poorly documented ("they access the main database"?)
- Breach databases incomplete (not all breaches publicized)
- Certifications expire (vendor had SOC 2, expires next month)
- Financial health deteriorates (vendor bankruptcy risk?)
- Third-party incidents (vendor got breached → you're notified late)
- Conflicting information (vendor says SOC 2 current, but expired)

**Ambiguity in Risk:**
- Is a small vendor with no SOC 2 riskier than large vendor with old audit?
- Breach 5 years ago vs recent incident - which matters more?
- Vendor fixing 1 breach vs vendor dismissing breach concerns?
- How to weight data access scope + compliance posture + financial health?

---

##  Approach Options

### Option A: AI-Powered Vendor Intelligence (Advanced)
**Best for:** Data scientists, security researchers

**Technical Approach:**
- **Data ingestion** from multiple sources:
  - Contract documents (extract: data access, SLAs, compliance requirements)
  - Security assessments (questionnaires, audit reports, certifications)
  - Breach databases (check if vendor is breached)
  - Public records (financial health, regulatory issues)
  - Third-party integrations (vendor's own API for SOC 2 status, etc.)
- **LLM-assisted analysis:**
  - Extract contract obligations using NLP (identify data access permissions)
  - Summarize vendor compliance (parse SOC 2, ISO 27001 reports into structured format)
  - Generate risk narratives ("Vendor has SOC 2 Type II but uses older encryption")
- **Risk scoring engine:**
  - Combine: Breach history + Data access scope + Compliance maturity + Financial stability
  - Dynamically recalculate when new info appears
  - Output: Red/Yellow/Green with change alerts
- **Dashboard:**
  - Portfolio view (100 vendors, see who's risky at a glance)
  - New breach detection (monitor public breach databases)
  - Certification tracking (when SOC 2 expires?)

**Stack:** Python, LLM API, web scraping, breach DB APIs, Pandas, Plotly
**Complexity:**  (5/5)
**Effort:** 45-55 hours

---

### Option B: Vendor Risk Scorecard Builder (Intermediate)
**Best for:** Risk analysts, process engineers

**Technical Approach:**
- Build vendor risk framework:
  ```
  Vendor Risk = (Data_Sensitivity × Access_Scope) +
                Compliance_Gaps + Breach_History +
                Financial_Health

  Data Sensitivity: 1-10 (does vendor touch PII? Financials?)
  Access Scope: 1-10 (number of systems, read/write)
  Compliance: 1-10 (missing certifications, controls)
  Breach History: Points per incident (recent = more points)
  Financial: 1-10 (Dun & Bradstreet score, viability)
  ```
- Create vendor profile database:
  - Name, contract info, data access, assessments
  - Store risk scores (refresh quarterly/annually)
  - Track changes over time
- Build dashboard:
  - All vendors in grid (sorted by risk)
  - Filter/search capabilities
  - Drill-down for each vendor (see why they're risky)
- Alerts:
  - Contract expiring (60 days out)
  - Certification expiring (renewal needed)
  - Assessment overdue (should be re-assessed)
  - Known breach detected

**Stack:** Python, SQLite/PostgreSQL, Pandas, Flask web UI, Plotly visualizations
**Complexity:**  (3/5)
**Effort:** 30-40 hours

---

### Option C: Vendor Registry & Tracking System (Beginner-Intermediate)
**Best for:** Full-stack web developers

**Technical Approach:**
- Simple CRUD app to manage vendor info:
  - Vendor registry (add/edit/delete vendor)
  - Contract upload & tracking (start/end dates)
  - Access mapping (which systems? what data?)
  - Risk questions/checklist (e.g., "Has SOC 2?" yes/no)
  - Certifications (store PDF, expiry dates)
  - Contact tracking (who's the vendor liaison?)
- Dashboard features:
  - Sorted vendor list
  - Alert indicators (contract expiring, cert expired)
  - Simple bar chart: # vendors by risk level
  - Export to CSV for audits
- Email notifications:
  - Monthly vendor summary
  - Alerts on expiring contracts/certs

**Stack:** Python (Flask/Django), PostgreSQL, HTML/CSS/JS, file upload handling
**Complexity:**  (2/5)
**Effort:** 20-30 hours

---

## Sample Data Provided

**Files in `sample_data/`:**

| File | Records | Description |
|------|---------|-------------|
| `vendor_registry.csv` | 400 | All vendors: type, certifications+expiry dates, breach status, risk score, annual spend, contract dates |
| `vendor_labels.csv` | 400 | Ground truth: is_anomaly, anomaly_type, severity, expired_certifications, explanation |

**Anomaly distribution in labels (~80% flagged):**

> Note: High flag rate is intentional — vendor risk management is about *tiered response*, not binary safe/unsafe. Your solution should produce a ranked risk register, not just a pass/fail list.

| Anomaly Type | Severity | Example |
|--------------|----------|--------|
| `BREACHED_VENDOR_HIGH_ACCESS` | CRITICAL | Vendor breached in last 12mo + has PII/Financial access |
| `VENDOR_UNDER_INVESTIGATION` | CRITICAL | Vendor currently under security investigation |
| `HIGH_RISK_SCORE` | HIGH | Risk score > 80/100 |
| `EXPIRED_CERTIFICATION` | HIGH/MEDIUM | SOC2/ISO27001 expired on vendor with sensitive data access |
| `RECENTLY_BREACHED_VENDOR` | MEDIUM | Breach in last 12 months (lower scope) |
| `CONTRACT_EXPIRED_ACTIVE_ACCESS` | MEDIUM | Contract ended, potential orphaned access |
| `ELEVATED_RISK_VENDOR` | LOW | Risk score 65-80 — increased monitoring |

**Self-Evaluation:**
```python
import pandas as pd
from sklearn.metrics import precision_score, recall_score

labels = pd.read_csv('vendor_labels.csv')
# labels['predicted_anomaly'] = your_model.score_vendors(vendor_registry)

y_true = labels['is_anomaly'].astype(int)
y_pred = labels['predicted_anomaly'].astype(int)

print(f"Precision: {precision_score(y_true, y_pred):.2%}")
print(f"Recall:    {recall_score(y_true, y_pred):.2%}")

# Priority check: CRITICAL vendors should always be caught
critical = labels[labels['severity'] == 'CRITICAL']
print(f"CRITICAL vendor recall: {labels.loc[critical.index]['predicted_anomaly'].mean():.2%}")
```

**Evaluation focus:** For vendor risk, **recall on CRITICAL/HIGH** matters more than overall precision. Missing a breached vendor with access to customer PII is far worse than over-flagging a mid-risk vendor.

**Sample Vendor Record:**
```json
{
  "vendor_id": "VND-0285",
  "name": "CloudBackup Inc",
  "category": "Backup & Disaster Recovery",
  "contract_start": "2023-06-01",
  "contract_end": "2026-06-01",
  "data_access": {
    "systems": ["Database_Primary", "FileServer_Corporate"],
    "data_sensitivity": "HIGH",
    "access_type": "read_write"
  },
  "compliance": {
    "soc2_type2": true,
    "soc2_expiry": "2026-09-15",
    "iso27001": false,
    "gdpr_dpa": true
  },
  "breach_history": [
    {
      "date": "2024-01-15",
      "severity": "MEDIUM",
      "description": "Unencrypted backup exposed on S3"
    }
  ],
  "financial_rating": "B",
  "current_risk_score": 65,
  "risk_level": "MEDIUM"
}
```

**Ground Truth Labels:** 20 vendors flagged as "high risk" for evaluation

---

##  Success Criteria

| Metric | Target | Why |
|--------|--------|-----|
| **Vendor Coverage** | 95%+ vendors tracked | Know all third-party risk |
| **Risk Accuracy** | 80%+ align with auditor judgment | Scoring is meaningful |
| **Alert Timeliness** | Contract/cert alerts 30+ days early | Time for action |
| **Operational Efficiency** | 5 min to answer "Is vendor X compliant?" | Enable business |
| **Audit Readiness** | 15 min to generate vendor risk report | Auditors satisfied |

---

##  Deliverables

-  **Vendor registry** (centralized inventory)
-  **Risk scoring model** (formula + rationale)
-  **Contract extraction** (key terms from PDFs)
-  **Compliance tracking** (certs, SOC 2, ISO, GDPR)
-  **Dashboard** (portfolio view, alerts, filters)
-  **Integration recommendations** (connect to ITSM, procurement)
-  **Sample reports** (risk by category, trending, recommendations)

---

##  Framework Alignment

**GDPR Article 28:**
- Data Processor must have "appropriate technical and organizational measures"
- Vendor breach = potential GDPR breach
- Documentation required

**GDPR Article 33:**
- Breach notification within 72 hours
- Vendor breach affects your notification timeline

**NIST SP 800-53 SA-9:**
- Third-party service security requirements
- Regular vendor assessments required
- Incident response plan must address vendor breaches

**SOX 404:**
- Control dependencies on third parties
- Need to evaluate vendor controls
- Continuity/availability risks

---

##  Tips for Success

1. **Prioritize high-risk vendors first:** Start with who touches customer data
2. **Data access is the key filter:** If vendor doesn't touch sensitive data = lower priority
3. **Certification checking is easy win:** SOC 2, ISO 27001, GDPR DPA = automated checks
4. **Breach notification lag is real:** Check when vendor notifies vs when they were breached
5. **Financial health matters:** Can vendor survive ransomware? Are they viable long-term?
6. **Think breach scenario:** "If this vendor is breached, what's our liability?"
7. **Make it operational:** Can procurement use this for vendor selection?

---

##  Example Output

```
VENDOR RISK PORTFOLIO
=====================
Report Date: 2026-04-15
Total Vendors Tracked: 147

RISK SUMMARY

 LOW Risk: 89 vendors (61%)
 MEDIUM Risk: 45 vendors (31%)
 HIGH Risk: 13 vendors (8%)

RED FLAG VENDORS (Require Immediate Attention)


1. CyberBackup Solutions (VND-0285)
   Risk Score: 7.8/10 [HIGH]
   Issues:
    Known breach (Jan 2024): Unencrypted backups exposed
    SOC 2 Type II expires in 60 days (renewal status?)
    No GDPR DPA on file
   Access: Database + File Server (HIGH sensitivity)
   Action Required: Schedule compliance meeting

2. LegacyIntegration Corp (VND-0401)
   Risk Score: 7.5/10 [HIGH]
   Issues:
    Financial rating: C (viability concern)
    No SOC 2, ISO 27001
    Contract SLA vague on breach notification
    Limited data access (read-only, medium sensitivity)
   Action Required: Contract renegotiation or replacement

3. DevOps Contractor Team (VND-0512)
   Risk Score: 6.9/10 [MEDIUM-HIGH]
   Issues:
    Individual contractor (single point of failure)
    Background check due 45 days ago
    Limited access, 6-month contract
   Action Required: Extend access review, contract renewal decision

AUDIT-READY COMPLIANCE

 95% vendor coverage (143 of 150 key vendors tracked)
 GDPR DPA: 92% of vendors with data access have DPA
 SOC 2 Compliance: 78% (15 vendors awaiting new assessments)
 Contract Terms: 8 contracts need renewal/renegotiation

NEW VENDOR ONBOARDING (Last 30 Days)

2 new vendors added
Both require initial security assessment
Assessment template and process: [LINK]
```

---

##  Example Walkthrough

**Input: Vendor Record + Breach Data**
```json
{
  "vendor_id": "VND-0285",
  "name": "CyberBackup Solutions",
  "data_access": ["Backup_Database", "File_Server"],
  "soc2_expiry": "2026-06-15",
  "breach_history": ["Jan 2024: Unencrypted backups exposed"],
  "financial_rating": "A-",
  "gdpr_dpa": false
}
```

**Expected Output:**
```json
{
  "vendor_id": "VND-0285",
  "risk_score": 7.8,
  "risk_level": "HIGH",
  "risk_factors": [
    "Recent breach (Jan 2024): Unencrypted data exposed, potentially including backups",
    "SOC 2 expires in 60 days: Certification gap risk",
    "Missing GDPR DPA agreement despite processing EU data",
    "High-sensitivity data access (backups = full database copies)"
  ],
  "recommendation": "Schedule urgent compliance meeting; consider alternative vendor"
}
```

---

##  Evaluation Rubric (100 pts)

- **Risk Scoring (30 pts):** Combines data access + compliance + breach history + financial health intelligently
- **Breach Monitoring (20 pts):** Can detect and flag vendor breaches
- **Compliance Tracking (20 pts):** Monitors certifications, DPAs, contract terms
- **Portfolio View (15 pts):** Clear vendor dashboard with risk levels, priorities
- **Actionability (10 pts):** Clear next steps (renegotiate, replace, monitor)
- **Bonus (5 pts):** Onboarding workflow, contract terms analysis, mitigation tracking

---

##  Deliverables Checklist

- [ ] **GitHub Repo** - vendor assessment code
- [ ] **Jupyter Notebook** - portfolio analysis, risk distribution
- [ ] **Vendor Risk Database** - 147 vendors with comprehensive profiles
- [ ] **Risk Dashboard** - visual portfolio, risk heat map, priority list
- [ ] **Breach Monitoring** - track public breaches, flag affected vendors
- [ ] **Compliance Audit** - GDPR DPA, SOC 2, ISO 27001 status per vendor
- [ ] **5-Min Presentation** - problem → scoring formula → portfolio demo

---

##  Timeline

- **Day 1:** EDA → design risk scoring formula → build database
- **Day 2:** Implement dashboard → breach monitoring → compliance tracking → docs
- **Day 3 (opt):** Contract analysis → onboarding workflow → polish demo

---

##  Bonus Features

- Public breach monitoring (scan breach databases weekly) (+5)
- Contract terms extraction & analysis (+4)
- Vendor onboarding checklist & workflow (+3)
- Remediation tracking (vendor fixes > risk score improves) (+2)

---

##  FAQ

**Q: How do we weight risk factors?** A: Any weighting logic acceptable; document your choices.
**Q: Should we auto-block high-risk vendors?** A: Your call; show risk-reward analysis.
**Q: How frequently to re-assess?** A: Annual minimum + event-driven (breach → immediate).
**Q: Can we use public breach databases?** A: Yes! (e.g., Have I Been Pwned, Breach alerts).

---

##  Judge Guide

**Green Flags:** Balanced risk scoring, detects compliance gaps, audit-ready, actionable
**Red Flags:** Overly simplistic scoring, missing breach monitoring, poor documentation
**Questions:** "Explain your risk formula", "Show us highest-risk vendor", "How do you handle tie-ins across multiple contracts?", "How does this scale to 500+ vendors?"

---

**Download starter data & templates:** [DOWNLOAD_LINK]


