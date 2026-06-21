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