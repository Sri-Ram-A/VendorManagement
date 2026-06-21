# SreeHarish
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

# SriRam
# Docling setup
- If you get file not found error while running (put yout file path)  
mkdir -p /home/srirama/micromamba/envs/pytorch/lib/python3.12/site-packages/rapidocr/models

# Celery and Redis
```bash
## https://hub.docker.com/_/redis
podman run -d \
  --name redis-cc \
  -p 6379:6379 \
  -v redis_data:/data \
  redis
celery -A backend worker -l info
```

# Docker
```bash
micromamba install neo4j-python-driver -c conda-forge -y
mkdir -p ~/neo4j/data
podman run -d \
    --name neo4j-sg
    --publish=7474:7474 --publish=7687:7687 \
    --volume=$HOME/neo4j/data:/data \
    neo4j
```
`Ctrl+Shift+P` Run:Tasks -> Run all tasks
# Because fo chromadb
TypeError: Descriptors cannot be created directly.
If this call came from a _pb2.py file, your generated code is out of date and must be regenerated with protoc >= 3.19.0.
If you cannot immediately regenerate your protos, some other possible workarounds are:
 1. Downgrade the protobuf package to 3.20.x or lower.
 2. Set PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python (but this will use pure-Python parsing and will be much slower).
 pip install -U \
    opentelemetry-api \
    opentelemetry-sdk \
    opentelemetry-proto \
    opentelemetry-exporter-otlp-proto-grpc

python manage.py spectacular --file schema.yaml
npm install -D openapi-typescript
npm install openapi-fetch
npx openapi-typescript /home/srirama/Documents/sr_proj/VendorManagement/backend/schema.yaml -o ./types/schema.ts

24097cd2-e08c-4f04-97ad-497ae74c686d

micromamba activate pytorch
cd backend
python manage.py runserver
podman start redis-cc
celery -A backend worker -l info


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
