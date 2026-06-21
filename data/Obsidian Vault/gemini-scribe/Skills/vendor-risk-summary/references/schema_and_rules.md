# Vendor Risk Summary -- Schema & Rules

## Output JSON schema

```json
{
  "vendor": "string -- vendor/company name as stated in the documents",
  "vendor_folder": "string -- path that was processed",
  "generated_date": "YYYY-MM-DD",
  "documents_reviewed": ["list of filenames actually found and read"],
  "documents_missing": ["list of the 4 expected doc types not found, if any"],
  "overall_risk": {
    "score": "integer 0-100, see rubric below",
    "rating": "Low | Medium | High | Critical",
    "key_drivers": ["short list of the 2-4 findings that most influenced the score"],
    "methodology_note": "one sentence describing how the score was derived -- always include this, it's what makes the number defensible"
  },
  "topics": [
    "NETWORK SECURITY: <finding or 'Not assessed...'>",
    "COMPLIANCE STATUS: <finding>",
    "CONTRACT INFO: <finding>",
    "BREACH HISTORY: <finding>",
    "IDENTITY ACCESS: <finding>",
    "DATA PROTECTION: <finding>",
    "SUPPLY CHAIN: <finding>",
    "ENDPOINT SECURITY: <finding or 'Not assessed...'>"
  ],
  "citations": {
    "<topic name>": "which document + section/page the finding came from, e.g. 'SOC2 Report, Exception CC6.3-04' or 'MSA §5.3'"
  }
}
```

Keep `topics` as flat strings in `"LABEL: finding."` form, matching the user's original
format -- that's the part they'll scan quickly. Put the detail and provenance in
`citations` so every claim is traceable back to a page/section without cluttering the
headline string.

## Topic-by-topic: what each one actually draws from

| Topic | Typical source | Notes |
|---|---|---|
| **NETWORK SECURITY** | Usually none of the 4 docs | These are legal/audit docs, not scan output. Almost always "Not assessed." Only fill with a real finding if a document explicitly states something (e.g. SOC2 testing scope mentions a specific control). |
| **COMPLIANCE STATUS** | SOC2 (opinion, exceptions, period), PCI-DSS AoC (validation status, self-assessed vs QSA, attestation date/expiry) | Check attestation/report dates against today's date to flag if anything has lapsed. |
| **CONTRACT INFO** | MSA (effective date, term length, expiry, fees if stated, liability cap, governing law) | Compute days-to-expiry if you know today's date. |
| **BREACH HISTORY** | SOC2 exceptions section, sometimes DPA breach-notification clause (procedural, not historical) | Only report an actual past breach if a document states one occurred. A breach-notification *procedure* (e.g. "must notify within 24 hours") is not breach history -- don't conflate the two. |
| **IDENTITY ACCESS** | DPA TOMs (MFA, role-based access, least privilege -- usually stated as a requirement, not a measured gap) | Distinguish "DPA requires MFA" (a contractual commitment) from "X% of accounts lack MFA" (a measured finding) -- only state the latter if a document actually reports it. |
| **DATA PROTECTION** | DPA TOMs (encryption at rest/in transit, standards used), SOC2 exceptions touching encryption/key management | This is usually the richest category -- both DPA and SOC2 typically speak to it. |
| **SUPPLY CHAIN** | DPA subprocessor list (names, regions, purposes) | Note any subprocessor whose region creates a data-residency question (e.g. processing outside an expected jurisdiction). |
| **ENDPOINT SECURITY** | Usually none of the 4 docs | Same as Network Security -- almost always "Not assessed" unless explicitly stated. |
| **OVERALL RISK** | Synthesized from all of the above | See rubric below. Never a bare number with no explanation. |

## Anti-fabrication rule (expanded)

The user's original example included findings like "port 8080 exposed," "2 unpatched CVEs,"
"MFA missing for 14% of admin accounts," and "EDR software absent." None of that kind of
data lives in an MSA, DPA, PCI-DSS attestation, or SOC2 report -- those come from active
security scanning tools, not contract/audit text. If this skill always produced numbers in
that shape regardless of source content, it would be fabricating evidence that *looks*
authoritative every single run -- which is far more dangerous than an honest gap, especially
if the output feeds a real vendor decision.

Rule: **every specific number, date, or named fact in `topics` must trace to actual text in
the extraction.** If nothing supports a topic, write exactly what's missing and why
(document type doesn't cover it, vs. document exists but doesn't address it, vs. document
wasn't found at all). These are different situations and the wording should say which one:

- `"Not assessed -- not covered by MSA/DPA/PCI-DSS/SOC2 document types"` (structural gap)
- `"Not stated in [Document] -- [topic] is not addressed in the reviewed text"` (document exists, silent on this)
- `"Cannot assess -- [Document] was not found in vendor folder"` (missing document)

## Risk score rubric (transparent, not arbitrary)

Start at 100 and subtract. This keeps the score auditable -- always list which deductions
applied in `key_drivers`.

| Finding (if present in source text) | Deduction |
|---|---|
| SOC2 report has any noted exception | -10 to -20 depending on severity/duration described |
| PCI-DSS attestation is self-assessed rather than independent QSA | -10 |
| SOC2 or PCI attestation has expired (report/attestation date >1 year old) | -15 |
| Contract expiring within 60 days with no renewal mentioned | -5 |
| DPA breach-notification window >24h, or no named subprocessor safeguards | -5 |
| A confirmed historical breach is stated in any document | -25 |
| Encryption/key-management exception (e.g. stale keys, weak cipher) stated in SOC2 | -10 |
| No exceptions found anywhere, both attestations current and QSA/independent | +0 (stays high) |

Floor at 0, cap at 100. Map to rating: 80-100 Low, 60-79 Medium, 35-59 High, 0-34 Critical.
If a category was structurally unassessable (Network/Endpoint Security), do **not** treat
the absence of data as a finding either way -- don't penalize or reward for it.
