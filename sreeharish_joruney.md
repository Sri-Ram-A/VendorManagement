views.py
  └── process_vendor_onboarding_pipeline.delay(vendor_id)
                    ↓
          [Task 1 - Root]
          Check vendor exists
          Find PENDING documents
          Build chord
                    ↓
    ┌───────────────────────────────┐
    │         CHORD HEADER          │
    │  parse_and_vectorize (MSA)    │
    │  parse_and_vectorize (DPA)    │  ← all run in parallel
    │  parse_and_vectorize (SOC2)   │
    │  parse_and_vectorize (PCI)    │
    └───────────────────────────────┘
                    ↓ (all 4 done)
          [Task 2 - Audit]
          Reconstruct markdown from ChromaDB
          → run_compliance_audit_orchestrator()
            Phase 1: extract facts from each doc
            Phase 2: agent verification loop (tools)
          Save extracted_legal_bounds to DB
          Save trace_log to DB
                    ↓
          compute_and_save_score.delay()
                    ↓
          [Task 3 - Scoring]
          Calculate risk score
          Set GREEN/YELLOW/RED status


the above pipeline is working 
the clients cohere.py is changed 
