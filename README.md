Understand this problem statement CLaudeAI
# Real Incidents:
Case 1: Vendor breach exposing customer PII → No notification from vendor (contract unclear)
Case 2: Contractor access never revoked after project ended → Sold data to competitor
Case 3: Cloud backup vendor changed terms → Now claiming data ownership
Case 4: Payment processor security downgrade → Exposed during PCI-DSS audit

# The Challenge:
Vendor risk assessment is spreadsheet-based (inconsistent, outdated)
⏰ No clear scoring system (“Is this vendor acceptable?”)
Auditors ask “Who has access to customer data?” → Can’t answer
Continuous monitoring impossible (manually check each vendor quarterly?)
No playbook for handling vendor breaches/issues

# Compliance Impact:
GDPR Article 28: Data Processor requirements (vendors MUST meet standards)
GDPR Article 33: Breach notification (if vendor is breached, you’re liable)
SOX 404: Dependency on third parties = internal control risk
NIST SP 800-53 SA-9: Third-party services security requirements

# Challenege Overview:
Build a system to:
Inventory all vendors/third-parties and their access/risks
Assess vendor security posture and compliance
Score vendor risk level (traffic light system)
Monitor vendor risk continuously (certifications, breaches)
Alert on risk changes (vendor downgrade, new breach)
Support contract negotiation (risk-based SLAs)
Track remediation (when vendor fixes issues)
Data Reality & Edge Cases

# Vendor Management Nightmares:
Vendors change frequently (security downgrades, breaches discovered later)
Data access scope poorly documented (“they access the main database”?)
Breach databases incomplete (not all breaches publicized)
Certifications expire (vendor had SOC 2, expires next month)
Financial health deteriorates (vendor bankruptcy risk?)
Third-party incidents (vendor got breached → you’re notified late)
Conflicting information (vendor says SOC 2 current, but expired)

# Ambiguity in Risk:
Is a small vendor with no SOC 2 riskier than large vendor with old audit?
Breach 5 years ago vs recent incident – which matters more?
Vendor fixing 1 breach vs vendor dismissing breach concerns?
How to weight data access scope + compliance posture + financial health?

# Approach Options
Option A: AI-Powered Vendor Intelligence (Advanced)
Best for: Data scientists, security researchers

## Technical Approach:
Data ingestion from multiple sources:
Contract documents (extract: data access, SLAs, compliance requirements)
Security assessments (questionnaires, audit reports, certifications)
Breach databases (check if vendor is breached)
Public records (financial health, regulatory issues)
Third-party integrations (vendor’s own API for SOC 2 status, etc.)

## LLM-assisted analysis:
Extract contract obligations using NLP (identify data access permissions)
Summarize vendor compliance (parse SOC 2, ISO 27001 reports into structured format)
Generate risk narratives (“Vendor has SOC 2 Type II but uses older encryption”)

## Risk scoring engine:
Combine: Breach history + Data access scope + Compliance maturity + Financial stability
Dynamically recalculate when new info appears
Output: Red/Yellow/Green with change alerts
Dashboard:
Portfolio view (100 vendors, see who’s risky at a glance)
New breach detection (monitor public breach databases)
Certification tracking (when SOC 2 expires?)
Stack: Python, LLM API, web scraping, breach DB APIs, Pandas, Plotly
Complexity:  (5/5)

Effort: 45-55 hours

Right Now this is my plan, lets assume A user from my company uploads  various files , For E.G. I right now have a vendor named NimBus and I have 4 documents from them Master Agreement MSA,DATA PROCESSING ADDENDUM (DPA),PAYMENT CARD INDUSTRY (PCI) DATA SECURITYSTANDARDATTESTATION OF COMPLIANCE (AoC),INDEPENDENT SERVICE AUDITOR’S REPORT Now other vendors in my sociiete geenral is my company..will have multiple other vendors,See right now I want to make this as the goal : 

# My Idea
Lets say user uplaods such multiple documents at a time (which can be clearly seen in the views.py,serializers and tasks.py) then I am giving it to celery where I want the following processes or tasks to happen 
- Docling for conversio of the PDFs ad stuff to a Markdown file
- Using this Markdown file and storing it in the Chromadb (chroma.db) Database which can be furhter used as a RAG based system fro user queries (where history can be cached in frontend -- which we can see later)
- Using this markdown file another process can be done where a LLM model perform the extraction of crucial data : My plan was to give each pdf to the LLM and extract a structured LLM response (which can then also be displayed as a graph in the frontend):but I am not getting how to proceed
- In order to perform Compliance checks , the LLM Model itself can then perform fucntio toolcalling : where Model can decide whether it needs to search the internet for getting information on any subject wrt the given markdown for each file
- So basically if You see using a single markdown per file I thought of making a model which can then be used to provide me structured data as output which can then be used to multiple things 
1. Where It is put into RAG database (which again can be acessed by the model by toolcalling)
2. Model decides to check internet in order to get more information on the vendor and complaince rules (again here multiple APIs can be used such as Tavily , Serper , DuckDUckGo,RSS Feeds etc. -- But I need some good suggestion on this)in order to acess public records as well as websites like Am I Pawned etc etc (which I dont have much information about) in order too check breaches 
3. Perform JSon extraction of the given data in order to store current status of the vendors
4. Another most important thing is the formation of a knowledge graph or activities of what the LLM is doing at each step - at each step the model output has to be somehow converted into knowledgeble graphs . E.g. When the PDF is fed into the model
   1. Model extracts relevant information from the markdown and then Stores it into the Vendor Model,thereby updating the current/inital stage
   2. Model needs to perform assesments
      1. Model can use fxn toolcall and use own chromaDB database for getting Data on the company (which again must be made as a knowledge graph showing which points are being retrieved) , which must be compulsory because updating database is needed at each step
      2. After a continuous while-loop kinda analysis -- in the next step model might ask to check the internet for which we can use already existing python tools like newspaper2k , tavily , duckduckgo and many other recent ones 
      3. Next is a model-agnostic , programatic search in order to search for any records on vendor breaches (which again can be a google search or perfer the custom vector database) 
      4. Next or the final steps is going through the public records to understand the financial health of the particular vendor
      5. Finally the model can geenrate a summary showing everything which has been done where it has done JSON extraction ,followed by Security assesments using its geenrated quesions and finding answers, followed by a programatic analysis of the breach databases and public records on the vendor
   3. The entire above pipeline showed the procedure when user actually uploads a file about that particular vendor -- moving forward one of the most important stage is the Vendor Metrics and a KPI based analysis of past metrics. See till now checking and answering and everything through this textual based system was ok , but to convert this into mathematical data and store a history of records on this data we need proepr criteria/stats for assigning -- because direct mathematical formula like Weighted Moving Average , etc etc is explainable but I am not understanding how to convert that into a number/score/some range is difficult which I am unable to understand -- But I feel with this AI model sumamry something can be done
5. Next is the Dashboard for which I had this idea where I thought that whatever delibarations is being amde by the AI model, or whatever information is being retrieved by my functions can actually be logged as a TIMESTAMP.txt file for a particular vendor - showing enitre procedure  as some markdown file , I thought then I will have  it sent to the frontend and render it - but obviously the more eyecatchy ones would be the knowledge graphs and also more specifically supposing consider the below as an example .txt or .md whatever
```md
# Backend Processing began for Vendor - NimBUS
1. Debug : Converted PDF into Markdown file
2. Debug : Searching Database for any related information on the parsed document
3. Debug : Providing information to LLM for processing
4. Info : LLM perfomed JSON extraction - {...}
5. Debug : Performing Security assessments - Predefined questions asked to the model
6. Info : Model outputs a structured JSON asking program to search internet using Tavily (Costly Operation) with reason - {...questions of the model}
7. Debug : Retrieved {..informations} from our vector database with the following file evidence {...file_id,page numbers} (Less-Costly Operation)
8. Info : Answers retrieved from the internet and also embedded in another vector-database (name : custom-browser)
```
And So On - and i planned of either displaying this to the user of a frontend (i dont know why but will again look like some chatbot only) or converting this logs into a actual knowledge base where now for e,g, lets sat if someone sees number 4. LLM perforned JSON extraction , then another LLM can simply do the task of conveting into knowledge , No idea about this help me , or the knowledge graph can show 3 annswers retrieved with embedding IDS : {...something} clicking which we can show them..or the best way is to better log every answer and every disussio in this markdown file itself - since anyhow computation is happening so why to waste it
Finally comes the score calculation which I have no idea about - where simply asking model to suggest a score is also not correct
6. Another feature of dashbaord is present in every website now-a-days an AI powered RAG based chatbot with also the feature of an Auto complete or AI based prompt enhancement 
Now I need your suggestions so that we can start coding  in PEP8 style simple , fucntion based coding approaches with proper use of loguru and debugging at each and every step, and I also think we can configure loguru with some special color to log where i cna use some extension such as Log File Highlighter to view logs and maybe a background process or something which can continuosly update my Next JS frontend
- Honestly many of these things is doable , but my main pain points or worry is about the knowledge graph and Scoring which is very crucial to this project





________________________++++++++++++++++++++++++++++______________________________________



This is gold — it confirms the actual pipeline flow. Now let's look at the backend structure.Two apps: `core` (the main pipeline) and `analytics`. Let's look at core's urls.py and structure.Now let's look at the analytics app urls, since that's also mentioned ("analytics there get request has been implemented").Now let's look at orchestrator.py, prompts.py, tools.py, scoring.py, serializer.py, and clients folder.Excellent, very clear. Now tools.py, prompts.py, scoring.py, serializer.py, clients/ folder.Let me see the truncated middle part and remaining helper files: serializer.py, clients/, analytics/models.py.Now let's look at clients/ (chroma.py, docling.py, cohere.py) and serializer.py.Now let's check `analytics/models.py` (VendorRegistry) and `data_uploader.py`, and the Problem_06 README/notebooks for the autoencoder/image piece the user described.Now let's read the Problem_06 README and PROBLEM_STATEMENT_06.md for the image/autoencoder description, plus check the notebooks briefly to confirm what the user described.Alright, I went through the whole zip — README.md, JOURNEY.md, sreeharish_joruney.md, then every file under `backend/`, plus the three notebooks in `Problem_06_Vendor_Risk/`. Here's the full flow, no diagrams, just text.

## What this project actually is

It's a Django + DRF backend for vendor (third-party) risk management for a bank/Société Générale-style hackathon (PS3/PS6 — Vendor Risk). A user uploads a vendor's compliance documents (MSA, DPA, SOC2, PCI-DSS), the system parses them, extracts structured legal facts using an LLM, optionally verifies facts using external tools (breach DBs, news, SEC filings), and computes a rule-based risk score (RED/YELLOW/GREEN). Separately, there's a tabular ML classifier for anomaly detection, and — as you said — a third, **not wired in**, image-based autoencoder anomaly detector that lives only in notebooks.

The repo root has two Django apps: `core` (the ingestion + LLM audit pipeline) and `analytics` (read endpoints + the deployed ML prediction endpoint).

---

## URL routing — top level

`backend/backend/urls.py` mounts:
- `admin/` — Django admin
- `api/` → `core.urls`
- `api/analytics/` → `analytics.urls`
- `api/schema/` and `api/docs/` — drf-spectacular OpenAPI schema and Swagger UI

So there are really only four functional endpoints in the whole project. I'll go through each one.

---

## URL 1 — `POST /api/vendors/ingest` (core app)

This is the entry point. It's handled by `VendorDocumentIngestionView` in `core/views.py`.

What it calls and what happens:

1. The request body is validated by `VendorIngestionSerializer` (`core/serializer.py`). It expects `vendor_name`, `vendor_type`, `business_owner`, optional `annual_spend`, `declared_data_categories`, `declared_systems_accessed`, and a list of `documents` (multipart file uploads). The serializer has a custom `validate_declared_systems_accessed` that accepts either a JSON array string or a comma-separated string and normalizes it to a list.

2. A `Vendor` row is created in the DB (`core/models.py`) with `status = PROCESSING`. The `Vendor` model is the central record: it stores `extracted_legal_bounds` (JSON field holding every legally extracted fact), `discovered_infrastructure` (manually/externally populated technical access scope), `execution_trace_log` (a growing text log used as an audit trail), and `current_risk_score` / `previous_risk_score`.

3. For each uploaded file, the view guesses its document type from the filename — looks for "DPA", "SOC", "PCI"/"AOC" substrings, defaults to "MSA" otherwise — and creates a `VendorDocument` row pointing at the saved file on disk (path pattern: `compliance_vault/<vendor_name>/<doc_type>/<uuid>_<filename>`).

4. It then calls `process_vendor_onboarding_pipeline.delay(vendor_id=...)` — this hands off to **Celery**, so the HTTP response returns immediately with `{vendor_id, current_status: "PROCESSING"}`. Everything below this point runs asynchronously in a Celery worker process, not in the request/response cycle.

### What happens inside the Celery pipeline (core/tasks.py)

**Task 1 — `process_vendor_onboarding_pipeline`** (the root task): Loads the vendor, finds all `VendorDocument` rows still in `PENDING` extraction status, and builds a Celery **chord**: it fires one `parse_and_vectorize_document` task per document, all in parallel, with a callback task (`execute_vendor_compliance_audit`) that only runs once all of them finish.

**Task 2 — `parse_and_vectorize_document`** (runs once per document, in parallel): This is where Docling and ChromaDB come in.
- Calls `get_converter()` from `clients/docling.py`, which lazily builds a singleton `docling.document_converter.DocumentConverter`.
- Calls `converter.convert(pdf_path)` then `.document.export_to_markdown()` — this is the actual PDF → Markdown conversion you mentioned.
- Passes that markdown into `get_vector_store().vectorize_markdown_content(...)` from `clients/chroma.py`. This splits the markdown on double-newlines into paragraph chunks, keeps short lines too if they look like a metric (contain a colon or digits — so things like "Level: 1" or "SLA: 99.9%" survive even if short), then writes each chunk into a ChromaDB collection named `vendor_<uuid>` using Chroma's default embedding function. Each chunk is stored with metadata `{source_document_type, chunk_index}` so order can be reconstructed later.
- Marks the `VendorDocument.extraction_status` as `SUCCESS` or `FAILED`.

**Task 3 — `execute_vendor_compliance_audit`** (the chord callback, runs once after all documents are parsed): 
- Confirms at least one document succeeded.
- For every successfully parsed document, calls `get_vector_store().read_document_chunks_in_order(...)`, which pulls all chunks for that document type back out of Chroma sorted by `chunk_index` and joins them back into one markdown string — i.e., it reconstructs the document from the vector store rather than re-reading the PDF.
- Hands `documents_payload = {doc_type: markdown_text}` to `run_compliance_audit_orchestrator()` in `core/orchestrator.py`. This is described as a "pure reasoning" function — it does no DB or Chroma access itself.

### Inside the orchestrator — this is the LLM extraction + agent loop

Phase 1 — deterministic extraction (`extract_all_documents`): for each document, one call to `call_cohere()` (`clients/cohere.py`, using Cohere's `command-r-plus-08-2024` model with `response_format: json_object` when JSON is forced) using `EXTRACTION_SYSTEM_PROMPT` from `core/prompts.py`. The prompt tells the model to extract only explicit facts — contract dates, breach notification hours, liability caps, SOC2 opinion type, PCI assessor type, subprocessors, etc. — and never guess. Each extracted field is wrapped in a `FactValue` (value, trust_tier, source document type, source excerpt, timestamp). Trust tier is assigned by document type: SOC2/PCI = tier 1 (independent audit), DPA/MSA = tier 2 (contract text). Facts are merged into a single `running_bounds` dict via `merge_fact()`, which has explicit conflict-resolution logic: a higher-trust (lower-number) source always overwrites a lower-trust one, and any actual disagreement gets logged as a conflict.

Phase 2 — bounded agentic verification loop (`run_verification_loop`): up to 4 turns (`MAX_AGENT_STEPS = 4`). Each turn calls Cohere again with `AGENT_SYSTEM_PROMPT`, giving the model the list of available tools and the facts extracted so far, and asks it to return a structured JSON `AgentTurn`: a question it's investigating, an optional tool name + args, a summary, any new extracted fields, and a `continue_loop` flag. If the model picks a tool, `dispatch_agent_tool_call()` looks it up in `TOOL_REGISTRY` (`core/tools.py`) and actually calls it. The available tools are:
- `query_vendor_rag` — searches that vendor's own ChromaDB collection (the RAG piece)
- `search_xposedornot_breach` — hits the XposedOrNot public breach API
- `search_tavily` — Tavily web search
- `search_serpapi_news` — Google News via SerpAPI
- `search_news_breach_signal` — GNews search for breach/ransomware/bankruptcy keywords tied to the vendor name
- `search_sec_edgar` — SEC EDGAR full-text search for public filings
- `scrape_public_url_content` — scrapes a given URL (Newspaper4k first, BeautifulSoup fallback)

Each external/costly tool is wrapped with `call_with_budget()`, which caps each vendor+tool combination at 5 calls per rolling 24 hours using Django's cache, to stop the agent from burning API quota. Any new fields the agent discovers this turn (trust_tier = 4, since OSINT is less trustworthy than the contract itself) get merged into `running_bounds` the same conflict-aware way, and folded into the next turn's prompt. The loop stops early if the model sets `continue_loop = 0`, or hits the 4-turn cap.

After both phases, `build_trace_log()` writes a human-readable markdown trace block (extraction phase summary, each agent turn with its tool/result, any conflicts found) — this is exactly the kind of step-by-step audit log you described wanting in your README, and it's appended to `Vendor.execution_trace_log`.

Back in `execute_vendor_compliance_audit`, the orchestrator's result is saved onto the `Vendor` row (`extracted_legal_bounds`, `execution_trace_log`), then it calls `compute_and_save_score.delay(vendor_id)` — handing off to the third stage.

### Scoring (core/scoring.py)

This is deliberately **not** an LLM call for the number itself — it's a deterministic rule engine, explicitly designed (per the code comments) so every point on the score is traceable to a named rule function, not an opaque LLM-guessed number.

Four weighted components, combined as a weighted sum (not equal weights):
- `breach_intelligence` (35%) — fires on a missing/too-long breach notification SLA (>72h violates GDPR Art.33), or on agent-sourced recent breach signals.
- `compliance_maturity` (25%) — fires if there's no SOC2/PCI docs at all, a qualified SOC2 opinion, a self-assessed (not independent QSA) PCI AoC, or an expired certification (with points scaling by days expired, capped at 80).
- `data_blast_radius` (20%) — based on `Vendor.discovered_infrastructure` (a manually/externally populated list of systems and their data sensitivity) mapped through `ACCESS_WEIGHT_BY_SENSITIVITY` (PCI cardholder data = 100, public marketing = 10, etc.); uncapped liability for breaches actually *subtracts* points (it's good for the bank).
- `financial_stability` (20%) — based on agent-sourced financial distress/decline signals, or a flat 15-point penalty if no financial check was even performed.

The four component scores combine into `total_score`, clamped 0–100, then mapped to a band: ≥80 = `QUARANTINED_RED`, ≥50 = `CONDITIONAL_YELLOW`, else `VERIFIED_GREEN`. A final Cohere call (`generate_risk_narrative`, using the non-JSON reasoning model `command-a-reasoning-08-2025` this time) writes a 2–4 sentence narrative — but it's explicitly constrained to only describe the rules that actually fired, sorted by point impact, so it can't invent risk factors. The score, band, narrative, and a scoring trace block are saved onto the `Vendor` row, and `previous_risk_score` is shifted from the old `current_risk_score` first, so you get a trend signal over time.

That's the entire ingest → extract → verify → score pipeline triggered by one `POST`.

---

## URL 2 — `GET /api/analytics/vendors/` (analytics app)

`VendorListView.get()` — straightforward. Pulls every `Vendor` row ordered by newest first, returns a list of `{vendor_id, vendor_name, vendor_type, business_owner, status, current_risk_score, previous_risk_score, created_at, updated_at}`. This is your portfolio dashboard feed.

## URL 3 — `GET /api/analytics/vendors/<uuid>/`

`VendorDetailView.get()` — fetches one `Vendor` by primary key, 404s if not found. Returns the full profile: everything from the list view plus `annual_spend`, `risk_narrative_summary`, `declared_data_categories`, `declared_systems_accessed`, the full `extracted_legal_bounds` dict (every fact with its trust tier and source), the full `execution_trace_log` text, and the list of associated documents (type, extraction status, upload date, whether expired). This is the single-vendor detail page — everything the pipeline produced, in one response.

## URL 4 — `GET /api/analytics/vendors/<vendor_id>/predict/`

This is the **only ML model actually wired into the backend** — `VendorRiskPredictionView`. It does NOT read from the `Vendor`/`VendorDocument` models from the ingest pipeline at all. Instead it reads from a separate model, `VendorRegistry` (`analytics/models.py`), which mirrors the columns of `vendor_registry.csv` directly (a synthetic 200+-row dataset from `Problem_06_Vendor_Risk/`, loaded into the DB by `data_uploader.py`).

At Django import time, three artifacts are loaded once from `analytics/ml_models/`: `vendor_anomaly_model.pkl`, `label_encoder.pkl`, `feature_names.pkl`. Looking at how these were actually produced (`train_xgboost.ipynb`): despite the notebook's name, XGBoost and SHAP were experimented with, but the model that actually got saved to `vendor_anomaly_model.pkl` is a **RandomForestClassifier** (100 trees, class-balanced, 8 output classes, ~92% cross-validated accuracy).

On a request: looks up the `VendorRegistry` row, converts it to a one-row DataFrame, runs `build_features_simple()` — which engineers ~17 features (breach-status flags, data-scope sensitivity flags, risk-score bucket flags, contract-days-left and expiry flags, certificate expiry counts/percentages, annual spend) — then calls `_rf_model.predict()` and `.predict_proba()`. Output is the predicted `anomaly_type` (one of 8 classes, e.g. `LOW_RISK_VENDOR`, `EXPIRED_CERTIFICATION`, `BREACHED_VENDOR_HIGH_ACCESS`, etc.), a boolean `is_anomaly` (true if it's anything other than `LOW_RISK_VENDOR`), a confidence percentage, and the full probability distribution across all 8 classes.

---

## The dynamic/image-based risk model — confirmed NOT in the backend

I checked: there is no reference anywhere in `core/` or `analytics/` to `best_autoencoder.pt`, `best_heatmap_model.pt`, or anything resembling this pipeline. It exists only as two notebooks, `image_coder.ipynb` and `reconstruct.ipynb` (near-identical), inside `Problem_06_Vendor_Risk/`. Here's the flow that's actually implemented in those notebooks, matching what you described:

Step 1 — feature engineering. Nine features are pulled per vendor from `vendor_registry.csv`: `risk_score`, `breach_status` (mapped to an ordinal 0–3 severity), `compliance_certifications` (count of certs), `contract_days_left` (days until contract end), `annual_spend`, `data_access_scope` (ordinal 0–3), `audit_days_since` (days since last audit), `vendor_type` (category code), and a synthetic ninth feature `audit_to_contract_risk` (stale-audit-days divided by contract-days-left — a compounding-risk signal).

Step 2 — tabular-to-image conversion, exactly what you described. Each of the 9 features is normalized to 0–1 using the 1st/99th percentile of that feature across the dataset (clipped), then mapped through the "turbo" colormap to get an RGB color. A 48×48 image is built as a 3×3 grid of solid 16×16-pixel colored tiles, one tile per feature, in a fixed, documented layout — so every vendor's full tabular profile becomes one small RGB image where each block's color encodes one feature's value.

Step 3 — autoencoder. A convolutional autoencoder (`ConvAutoencoderTightBottleneck`) is built with an encoder that downsamples 48→24→12→6→2 through four conv+pool stages, bottlenecking at a tight 2×2×32 (128-dimensional) latent space, then a mirrored decoder that reconstructs back to 48×48×3. Critically — and this matches exactly what you said — it's trained **only on vendors labeled non-anomalous** (`is_anomaly == False`), so the model only ever learns what a "normal" vendor's image looks like. It never sees anomalous examples during training.

Step 4 — reconstruction error as anomaly score. At inference, every vendor's image (normal and anomalous alike) is passed through the trained autoencoder, and the per-vendor reconstruction error is computed as mean squared error between the original image and its reconstruction. Vendors the autoencoder has never seen the pattern of (i.e., risky/anomalous ones) reconstruct poorly, so they get a high error — that error value itself is the anomaly/risk score. The notebook also computes a **per-block** error (re-slicing the 48×48 image back into its original 9 feature tiles and computing error within each tile separately), which tells you which specific feature drove the anomaly — e.g., if the `compliance_certifications` block has the highest local error, an expired-certification anomaly is implicated. This is the explainability layer: not just "this vendor is risky" but "risky because of this specific tile/feature."

Step 5 — validation. The notebook checks that this actually works by plotting the reconstruction-error histogram for normal vs. anomalous vendors (anomalous vendors should cluster at higher error) and computing ROC-AUC using reconstruction error as the anomaly score against the true `is_anomaly` labels.

There's a related but separate model in the same notebook — `best_heatmap_model.pt` — which is a *supervised* model (not an autoencoder) trained with the 48×48 input image as input and a synthetic Gaussian-blob heatmap as the target output (a heatmap with a hotspot centered on whichever feature block caused that vendor's labeled anomaly type, weighted by severity). That one needs labels to train and is really a separate explainability experiment; the unsupervised autoencoder reconstruction-error approach is the one that matches what you described as "dynamic risk prediction."

So to directly answer the "is it implemented" question: the conversion code, the autoencoder architecture, the training loop, and the reconstruction-error scoring all exist and work in the notebook with saved weights (`best_autoencoder.pt`). What's missing is the bridge — there's no `clients/` module, no Celery task, and no view that loads `best_autoencoder.pt`, builds the 48×48 image for a given vendor at request time, runs it through the model, and writes the reconstruction error back onto the `Vendor` row or exposes it through an endpoint the way `VendorRiskPredictionView` does for the RandomForest model.