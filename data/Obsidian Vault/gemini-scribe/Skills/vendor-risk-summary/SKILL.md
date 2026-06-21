---
name: vendor-risk-summary
description: Use this skill whenever the user mentions a vendor by name alongside their Obsidian vendor vault, references a vendor folder or note path (e.g. ".../Obsidian Vault/vendor1/vendor1.md"), or asks to summarize, assess, or risk-score a vendor's compliance documents (MSA, DPA, PCI-DSS, SOC2). Trigger this even if the user just says a vendor name or folder name with no other context (e.g. "vendor1", "check acme corp") when an Obsidian vendor vault is in play -- don't wait for them to say "summary" or "risk" explicitly. Produces a structured JSON risk summary covering network security, compliance status, contract info, breach history, overall risk, identity/access, data protection, supply chain, and endpoint security.
---

# Vendor Risk Summary

Reads a vendor's Obsidian note plus its four compliance PDFs (Master Services Agreement,
Data Processing Addendum, PCI-DSS Attestation, SOC2 Report) and produces one structured
JSON risk summary.

## Workflow

1. **Resolve the vendor folder.** The user will give you either a vendor name or a path.
   - If they gave a full path (e.g. `/home/sreeharishtj/Documents/Obsidian Vault/vendor1/vendor1.md`),
     use it directly.
   - If they only gave a vendor name (e.g. "vendor1" or "acme corp"), assume it lives at
     `~/Documents/Obsidian Vault/<vendor>/` unless the user has told you a different vault
     root earlier in the conversation -- ask if you're not sure.

2. **Extract.** Run the bundled script:
   ```bash
   python3 scripts/extract_vendor_docs.py "<vendor_folder_or_note_path>"
   ```
   This finds the vendor's `.md` note and the four PDFs (fuzzy filename matching --
   doesn't need exact names), pulls raw text from all of them, and prints one combined
   dump tagged by source document. It also tells you which of the four documents were
   **not found** -- this matters for step 4.

3. **Read the combined extraction carefully.** This is real text from real documents --
   ground every claim in it.

4. **Fill the JSON schema below.** Follow `references/schema_and_rules.md` for the exact
   field definitions, the anti-fabrication rule, and the risk-scoring rubric. Read that
   file before writing the summary -- don't wing the schema from memory.

5. **Write the output.** Save as `<vendor>_risk_summary.json` in the vendor's folder, and
   show the user the JSON inline as well.

## Critical rule (do not skip)

**Never invent specific technical findings that aren't in the source text.** MSA/DPA/PCI-DSS/SOC2
documents are legal and audit-attestation text -- they do not contain network scan data
(open ports, CVE counts, SSL cipher details) or endpoint telemetry (EDR presence) unless a
document explicitly states it. If a category has no supporting text, say so plainly
(`"Not assessed -- not covered by MSA/DPA/PCI-DSS/SOC2 document types"`) instead of producing
a plausible-sounding number. A specific-sounding fabricated stat is worse than an honest gap,
since the user may feed this into a real vendor decision. Full detail on this in
`references/schema_and_rules.md`.

See `references/schema_and_rules.md` for the full JSON schema, field-by-field source
mapping (which document each topic typically draws from), and the risk-score rubric.
