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
prompt.py is changed and field names arent matching from llm so that is fixed 



now these tasks run properly
Accepts PDF uploads via REST API
Converts them to markdown using Docling
Stores them in ChromaDB for RAG
Extracts structured compliance fields using LLM
Runs an agentic verification loop with real tools
Scores the vendor with explainable rules
Generates an AI risk narrative
Saves everything to DB

and commited to hari_pro branch

then dataset created 

# Ashford Clearing Networks
curl -X POST http://127.0.0.1:8000/api/vendors/ingest \
  -F "vendor_name=Ashford Clearing Networks" \
  -F "vendor_type=Clearing Network" \
  -F "business_owner=Sreehari" \
  -F "documents=@/home/sreeharishtj/Documents/Obsidian Vault/files/vendor-vault/Ashford Clearing Networks/MasterServicesAgreement.pdf" \
  -F "documents=@/home/sreeharishtj/Documents/Obsidian Vault/files/vendor-vault/Ashford Clearing Networks/Data_Processing_Addendum.pdf" \
  -F "documents=@/home/sreeharishtj/Documents/Obsidian Vault/files/vendor-vault/Ashford Clearing Networks/PCI_DSS.pdf" \
  -F "documents=@/home/sreeharishtj/Documents/Obsidian Vault/files/vendor-vault/Ashford Clearing Networks/SOC2.pdf"

# Cascade Settlement Group
curl -X POST http://127.0.0.1:8000/api/vendors/ingest \
  -F "vendor_name=Cascade Settlement Group" \
  -F "vendor_type=Settlement Provider" \
  -F "business_owner=Sreehari" \
  -F "documents=@/home/sreeharishtj/Documents/Obsidian Vault/files/vendor-vault/Cascade Settlement Group/MasterServicesAgreement.pdf" \
  -F "documents=@/home/sreeharishtj/Documents/Obsidian Vault/files/vendor-vault/Cascade Settlement Group/Data_Processing_Addendum.pdf" \
  -F "documents=@/home/sreeharishtj/Documents/Obsidian Vault/files/vendor-vault/Cascade Settlement Group/PCI_DSS.pdf" \
  -F "documents=@/home/sreeharishtj/Documents/Obsidian Vault/files/vendor-vault/Cascade Settlement Group/SOC2.pdf"

# Helios
curl -X POST http://127.0.0.1:8000/api/vendors/ingest \
  -F "vendor_name=Helios" \
  -F "vendor_type=Technology Provider" \
  -F "business_owner=Sreehari" \
  -F "documents=@/home/sreeharishtj/Documents/Obsidian Vault/files/vendor-vault/Helios/MasterServicesAgreement.pdf" \
  -F "documents=@/home/sreeharishtj/Documents/Obsidian Vault/files/vendor-vault/Helios/Data_Processing_Addendum.pdf" \
  -F "documents=@/home/sreeharishtj/Documents/Obsidian Vault/files/vendor-vault/Helios/PCI_DSS.pdf" \
  -F "documents=@/home/sreeharishtj/Documents/Obsidian Vault/files/vendor-vault/Helios/SOC2.pdf"

# Meridian Pay Solution
curl -X POST http://127.0.0.1:8000/api/vendors/ingest \
  -F "vendor_name=Meridian Pay Solution" \
  -F "vendor_type=Payment Processor" \
  -F "business_owner=Sreehari" \
  -F "documents=@/home/sreeharishtj/Documents/Obsidian Vault/files/vendor-vault/Meridian Pay Solution/MasterServicesAgreement.pdf" \
  -F "documents=@/home/sreeharishtj/Documents/Obsidian Vault/files/vendor-vault/Meridian Pay Solution/Data_Processing_Addendum.pdf" \
  -F "documents=@/home/sreeharishtj/Documents/Obsidian Vault/files/vendor-vault/Meridian Pay Solution/PCI_DSS.pdf" \
  -F "documents=@/home/sreeharishtj/Documents/Obsidian Vault/files/vendor-vault/Meridian Pay Solution/SOC2.pdf"

# Vertex Transact Corp
curl -X POST http://127.0.0.1:8000/api/vendors/ingest \
  -F "vendor_name=Vertex Transact Corp" \
  -F "vendor_type=Transaction Provider" \
  -F "business_owner=Sreehari" \
  -F "documents=@/home/sreeharishtj/Documents/Obsidian Vault/files/vendor-vault/Vertex Transact Corp/MasterServicesAgreement.pdf" \
  -F "documents=@/home/sreeharishtj/Documents/Obsidian Vault/files/vendor-vault/Vertex Transact Corp/Data_Processing_Addendum.pdf" \
  -F "documents=@/home/sreeharishtj/Documents/Obsidian Vault/files/vendor-vault/Vertex Transact Corp/PCI_DSS.pdf" \
  -F "documents=@/home/sreeharishtj/Documents/Obsidian Vault/files/vendor-vault/Vertex Transact Corp/SOC2.pdf"

# NimBus
curl -X POST http://127.0.0.1:8000/api/vendors/ingest \
  -F "vendor_name=NimBus" \
  -F "vendor_type=Cloud Storage Provider" \
  -F "business_owner=Sreehari" \
  -F "documents=@/home/sreeharishtj/Desktop/society/VendorManagement/data/Master_Services_Agreement.pdf" \
  -F "documents=@/home/sreeharishtj/Desktop/society/VendorManagement/data/Data_Processing_Addendum.pdf" \
  -F "documents=@/home/sreeharishtj/Desktop/society/VendorManagement/data/PCI_DSS.pdf" \
  -F "documents=@/home/sreeharishtj/Desktop/society/VendorManagement/data/SOC2.pdf"


  ok while ingesting hopeless people have sent the data sent now hackthon ends in 5 hours 

  ok dataset downloaded and then commited to hari_pro

you can check analytics there get request has been implemented
custom dataset is present in data folder , if you set that folder to obsidian then you will get graphs 
official dataset is in Problem_06_Vendor_Risk 