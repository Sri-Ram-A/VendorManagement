# filepath: core/orchestrator.py
"""
Core orchestration file managing bounded execution steps.
Integrates structural extraction, validation loops, and conflict merging.
"""

import json
import uuid
from datetime import datetime
from typing import Literal, Optional, List, Dict, Any
from pydantic import BaseModel, Field

from backend.logging import get_vendor_logger
from clients.cohere import call_cohere
from clients.chroma import get_vector_store
from core.models import Vendor, VendorDocument
from core.prompts import EXTRACTION_SYSTEM_PROMPT, AGENT_SYSTEM_PROMPT
from core.tools import TOOL_REGISTRY


class AgentTurn(BaseModel):
    """ The mandatory schema shape mapping for each step of the LLM verification loop. """
    question: str = Field(description="The specific risk question this turn is analyzing")
    reason: str = Field(description="Why this investigation point impacts the vendor's enterprise risk profile")
    tool: Optional[str] = Field(default=None, description="Name of the tool from TOOL_REGISTRY to call, or null")
    tool_args: dict = Field(default_factory=dict, description="Generic arguments matching the tool's signature")
    summary: str = Field(description="Clear overview of facts uncovered or verified during this loop iteration")
    extracted_fields: dict = Field(default_factory=dict, description="Any new domain facts discovered this turn")
    knowledge_graph_triplets: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Atomic relationships discovered: [{'subject': '...', 'predicate': '...', 'object': '...'}]"
    )
    continue_loop: Literal[0, 1] = Field(description="1 to continue investigation, 0 if verification is complete")


class FactValue(BaseModel):
    """ Structured envelope wrapping fields in Vendor.extracted_legal_bounds. """
    value: Any
    trust_tier: int  # 1=Independent audit, 2=Contract text, 3=Public record, 4=OSINT, 5=Self-reported
    source_document_type: Optional[str] = None
    source_excerpt: Optional[str] = None
    extracted_at: str


TRUST_TIER_BY_DOC_TYPE = {"SOC2": 1, "PCI": 1, "DPA": 2, "MSA": 2}

#  PIPELINE COORDINATION ENTRYPOINT]
def run_compliance_audit_orchestrator(vendor_id: str) -> dict:
    """ Coordinates document extractions, validation loops, and database syncs. """
    v_logger = get_vendor_logger(vendor_id)
    vendor = Vendor.objects.get(pk=uuid.UUID(vendor_id))
    successful_docs = vendor.documents.filter(
        extraction_status=VendorDocument.ExtractionStatus.SUCCESS
    )
    v_logger.info(f"ORCHESTRATOR_START: Processing vendor={vendor.vendor_name}")

    vendor.status = Vendor.Status.PROCESSING
    vendor.save(update_fields=["status"])
    
    running_bounds = dict(vendor.extracted_legal_bounds)
    conflicts_this_run = []

    rag_manager = get_vector_store()
    for document in successful_docs:
        collection = rag_manager.get_vendor_collection(vendor_id)
        doc_data = collection.get(where={"source_document_type": document.document_type})
        
        # [CRITICAL: RECONSTRUCT CHUNKS SEQUENTIALLY]
        chunks_with_idx = []
        for text, meta in zip(doc_data.get("documents", []), doc_data.get("metadatas", [])):
            chunks_with_idx.append((meta.get("chunk_index", 0), text))
        
        chunks_with_idx.sort(key=lambda x: x[0])
        full_markdown = "\n\n".join([item[1] for item in chunks_with_idx])

        if not full_markdown.strip():
            continue

        new_facts = extract_facts_from_document(vendor_id, document.document_type, full_markdown)

        for field_name, fact_value in new_facts.items():
            running_bounds, conflict = merge_fact(running_bounds, field_name, fact_value)
            if conflict:
                conflicts_this_run.append(conflict)

    vendor.extracted_legal_bounds = running_bounds
    vendor.save(update_fields=["extracted_legal_bounds"])

    agent_turns, network_graph_edges = run_verification_loop(vendor_id, vendor)

    for turn in agent_turns:
        for field_name, value in turn.get("extracted_fields", {}).items():
            agent_fact = FactValue(
                value=value,
                trust_tier=4,
                source_document_type=None,
                source_excerpt=turn.get("summary", ""),
                extracted_at=datetime.utcnow().isoformat(),
            ).model_dump()
            running_bounds, conflict = merge_fact(running_bounds, field_name, agent_fact)
            if conflict:
                conflicts_this_run.append(conflict)

    #  TIMELINE STREAM MARKDOWN LOG GENERATION]
    trace_lines = [
        f"# Compliance audit trace — {vendor.vendor_name}",
        f"Timestamp: {datetime.utcnow().isoformat()}\n",
        "## Deterministic Document Extraction Phase",
        f"Extracted Field Keys: {list(running_bounds.keys())}\n",
        f"## Bounded Agent Verification Loop Phase ({len(agent_turns)} Iterations)"
    ]
    for turn in agent_turns:
        trace_lines.append(
            f"- Step {turn['step']}: {turn['question']} [tool={turn['tool'] or 'none'}, status={turn['tool_result_status'] or 'n/a'}]"
        )
        trace_lines.append(f"  -> {turn['summary']}")
        
    if conflicts_this_run:
        trace_lines.append(f"\n## Data Discrepancy Contours Detected ({len(conflicts_this_run)})")
        for c in conflicts_this_run:
            trace_lines.append(f"- {c['field_name']}: Resolved via {c['resolution']}")

    vendor.execution_trace_log = vendor.execution_trace_log + "\n\n" + "\n".join(trace_lines)
    vendor.extracted_legal_bounds = running_bounds
    vendor.knowledge_graph_data = {"edges": network_graph_edges}
    
    vendor.save(update_fields=["execution_trace_log", "extracted_legal_bounds", "knowledge_graph_data"])
    v_logger.success("ORCHESTRATOR_DONE: Vendor row updates successfully synchronized.")

    return {
        "vendor_id": vendor_id,
        "fields_extracted": list(running_bounds.keys()),
        "agent_steps_run": len(agent_turns),
        "conflicts": conflicts_this_run,
    }

#  DOCUMENT EXTRACTION COMPONENT]
def extract_facts_from_document(vendor_id: str, document_type: str, markdown_text: str) -> dict:
    """ Runs a one-shot extraction across sequential text chunks from a document. """
    v_logger = get_vendor_logger(vendor_id)
    v_logger.info(f"EXTRACT_START: document_type={document_type}")

    raw_response = call_cohere(
        system_prompt=EXTRACTION_SYSTEM_PROMPT,
        user_message=f"Document Type Space: {document_type}\n\nContent Content Text:\n{markdown_text}",
        force_json=True,
        temperature=0.1,
    )

    try:
        parsed = json.loads(raw_response)
    except json.JSONDecodeError:
        v_logger.error(f"EXTRACT_FAILED: Malformed JSON from model for type {document_type}")
        return {}

    trust_tier = TRUST_TIER_BY_DOC_TYPE.get(document_type, 3)
    now_iso = datetime.utcnow().isoformat()

    structured_fields = {}
    for field_name, field_data in parsed.get("fields", {}).items():
        structured_fields[field_name] = FactValue(
            value=field_data.get("value"),
            trust_tier=trust_tier,
            source_document_type=document_type,
            source_excerpt=field_data.get("source_excerpt", ""),
            extracted_at=now_iso,
        ).model_dump()

    return structured_fields


#  CONFLICT-AWARE RECORD MERGING]
def merge_fact(existing_bounds: dict, field_name: str, new_fact: dict) -> tuple[dict, Optional[dict]]:
    """ Combines a newly discovered fact with existing data based on its source trust tier. """
    existing = existing_bounds.get(field_name)
    if existing is None:
        existing_bounds[field_name] = new_fact
        return existing_bounds, None

    if new_fact["trust_tier"] < existing["trust_tier"]:
        conflict = {
            "field_name": field_name,
            "old_value": existing["value"],
            "old_trust_tier": existing["trust_tier"],
            "new_value": new_fact["value"],
            "new_trust_tier": new_fact["trust_tier"],
            "resolution": "NEW_VALUE_ADOPTED_HIGHER_TRUST",
        }
        existing_bounds[field_name] = new_fact
        return existing_bounds, conflict

    if new_fact["value"] != existing["value"]:
        conflict = {
            "field_name": field_name,
            "old_value": existing["value"],
            "old_trust_tier": existing["trust_tier"],
            "new_value": new_fact["value"],
            "new_trust_tier": new_fact["trust_tier"],
            "resolution": "EXISTING_VALUE_RETAINED_TRUST_TIER_DOMINANCE",
        }
        return existing_bounds, conflict

    return existing_bounds, None


#  AGENTIC EXTERNAL INTEGRATION LOOP]
def run_verification_loop(vendor_id: str, vendor: Vendor) -> tuple[list[dict], list[dict]]:
    """ Bounded verification loop that runs external tool queries step-by-step. """
    v_logger = get_vendor_logger(vendor_id)
    turn_log = []
    accumulated_graph_edges = []
    max_steps = 4

    tool_descriptions = "\n".join(f"- {name}" for name in TOOL_REGISTRY.keys())
    existing_facts_summary = json.dumps(
        {k: v.get("value") for k, v in vendor.extracted_legal_bounds.items()}, default=str
    )

    for step in range(1, max_steps + 1):
        v_logger.info(f"AGENT_STEP: {step}/{max_steps}")
        system_prompt = AGENT_SYSTEM_PROMPT.format(
            tool_descriptions=tool_descriptions, existing_facts=existing_facts_summary
        )
        
        raw_response = call_cohere(
            system_prompt=system_prompt,
            user_message=f"Vendor context: {vendor.vendor_name}. Verify outstanding risk profiles.",
            force_json=True,
            temperature=0.2,
        )

        try:
            turn = AgentTurn.model_validate_json(raw_response)
        except Exception as e:
            v_logger.error(f"AGENT_TURN_PARSE_FAILED: {str(e)}")
            break

        tool_result = None
        if turn.tool and turn.tool in TOOL_REGISTRY:
            v_logger.info(f"AGENT_TOOL_CALL: executing tool={turn.tool}")
            tool_result = TOOL_REGISTRY[turn.tool](vendor_id, **turn.tool_args)

        #  RESTRUCTURE DATA FOR KNOWLEDGE GRAPH REreactflow]
        if turn.knowledge_graph_triplets:
            for triplet in turn.knowledge_graph_triplets:
                accumulated_graph_edges.append({
                    "id": f"edge_{uuid.uuid4().hex[:6]}",
                    "source": triplet.get("subject"),
                    "relation": triplet.get("predicate"),
                    "target": triplet.get("object"),
                    "detected_at_step": step
                })

        turn_log.append({
            "step": step,
            "question": turn.question,
            "reason": turn.reason,
            "tool": turn.tool,
            "tool_result_status": tool_result.get("status") if tool_result else None,
            "summary": turn.summary,
            "extracted_fields": turn.extracted_fields,
        })

        if turn.extracted_fields:
            current_dict = json.loads(existing_facts_summary)
            current_dict.update(turn.extracted_fields)
            existing_facts_summary = json.dumps(current_dict, default=str)

        if turn.continue_loop == 0:
            v_logger.info("AGENT_STOP: Loop terminated normally.")
            break

    return turn_log, accumulated_graph_edges


