---
name: vendor-risk-generator
description: Generates fictional vendor risk-assessment documents (SOC2, PCI_DSS, MasterServicesAgreement, Data_Processing_Addendum) for testing RAG search and Obsidian Graph View workflows. All vendors, auditors, and findings are synthetic and clearly labeled as such, never a real company.
---

# Vendor Risk Generator

## Purpose
Create realistic-but-entirely-fictional vendor compliance notes to test search, RAG indexing, and note-linking in Obsidian.

## Input
- Vendor profile: a fictional company name + industry (e.g. "Vendor Alpha, Payments Processing")
- Track record: "clean" or "flagged"
- Optional: a fictional incident shape to model loosely (e.g. "untested deploy, no staged rollout, mass downtime")

## Output structure
For each vendor, create a folder Vendors/{VendorName}/ containing exactly 4 markdown notes:

Vendors/
  Vendor-Alpha/
    SOC2.md
    PCI_DSS.md
    MasterServicesAgreement.md
    Data_Processing_Addendum.md

## File contents
SOC2.md - narrative summary of a fictional Type II review: scope, trust criteria covered, a markdown table with one realistic-shaped finding for "flagged" vendors (key rotation lapse, unpatched script, etc.) or "no exceptions noted" for "clean" vendors.

PCI_DSS.md - summary of fictional v4.0 validation status: a markdown table of requirement areas marked In Place / Not in Place, assessment date, service-provider level.

MasterServicesAgreement.md - summarized commercial terms: scope of services, fee structure, a fictional liability cap figure, termination triggers, governing law/jurisdiction.

Data_Processing_Addendum.md - data handling summary: categories of data processed, technical/organizational measures, a breach-notification window, a short list of fictional subprocessors and regions.

## Required header on every file
Every note MUST start with:

> WARNING: FICTIONAL TEST DATA - synthetic vendor, no real company, no real audit.
> For Obsidian RAG/search testing only. Not a real attestation.

## Hard constraints
- Never use a real company, auditor, or institution name.
- No signature blocks, no auditor firm letterhead, no "this report is intended solely for..." legal boilerplate that mimics a genuine signed attestation. These are summary notes, not formal certified documents.
- Never reference a real, identifiable incident by name. Only general incident shapes (bad deploy practices, detection gaps, etc.)

## After generation
In each of the 4 notes, add [[links]] to the vendor's other 3 notes, and tag with #vendorrisk and #clean or #flagged so Graph View clusters them and RAG can retrieve across the set.

## Repeat
Generate for 4 vendors total: 2 "clean," 2 "flagged."
