# filepath: core/orchestrator.py
"""
Pure reasoning orchestrator. No Django ORM access, no ChromaDB access —
tasks.py is responsible for fetching documents and saving results.
This file only: takes markdown in, returns structured facts + a summary out.
"""

import json
import uuid
from datetime import datetime
from typing import Literal, Optional, Any

from pydantic import BaseModel, Field

from backend.logging import get_vendor_logger
from clients.cohere import call_cohere
from core.prompts import EXTRACTION_SYSTEM_PROMPT, AGENT_SYSTEM_PROMPT
from core.tools import TOOL_REGISTRY


# 1. schema — one LLM verification turn must match this shape exactly
class AgentTurn(BaseModel):
    question: str = Field(
        description="The specific risk question this turn is analyzing"
    )
    reason: str = Field(description="Why this matters for the vendor's risk profile")
    tool: Optional[str] = Field(
        default=None, description="Tool name from TOOL_REGISTRY, or null"
    )
    tool_args: dict = Field(
        default_factory=dict, description="Arguments for the chosen tool"
    )
    summary: str = Field(description="What was learned this turn")
    extracted_fields: dict = Field(
        default_factory=dict, description="New facts discovered this turn"
    )
    continue_loop: Literal[0, 1] = Field(description="1 to keep going, 0 to stop")


# 2. schema — every value stored in extracted_legal_bounds takes this shape
class FactValue(BaseModel):
    value: Any
    trust_tier: int  # 1=independent audit, 2=contract text, 3=public record, 4=OSINT, 5=self-reported
    source_document_type: Optional[str] = None
    source_excerpt: Optional[str] = None
    extracted_at: str


# 3. constants
TRUST_TIER_BY_DOC_TYPE = {"SOC2": 1, "PCI": 1, "DPA": 2, "MSA": 2}
MAX_AGENT_STEPS = 4


# 4. entrypoint — call this from tasks.py once you've assembled documents_payload
def run_compliance_audit_orchestrator(
    vendor_id: str, vendor_name: str, documents_payload: dict, existing_bounds: dict
) -> dict[str, Any]:
    """
    Run the compliance audit orchestrator for a given vendor and their documents.

    Parameters
    ----------
    vendor_id:
        UUID string for logging and traceability. (vendor.vendor_id)
    vendor_name:
        Human-readable vendor name for logs and traceability. (vendor.vendor_name)
    documents_payload:
        Mapping of {document_type: markdown_text}. 
    existing_bounds:
        Previously extracted facts to seed the process. 

    Returns
    -------
    ```dict

        {
            "vendor_id": ...,
            "extracted_legal_bounds": ...,
            "fields_extracted": [...],
            "agent_steps_run": ...,
            "conflicts": [...],
            "trace_log_append": ...
        }

    ```
    """
    # 4.1 start from whatever facts already exist on the vendor
    v_logger = get_vendor_logger(vendor_id)
    v_logger.info(
        f"ORCHESTRATOR_START: vendor={vendor_name} documents={list(documents_payload.keys())}"
    )
    running_bounds = dict(existing_bounds)
    conflicts = []

    # 4.2 phase one — deterministic extraction, one call per document
    running_bounds, extraction_conflicts = extract_all_documents(
        vendor_id, documents_payload, running_bounds
    )
    conflicts.extend(extraction_conflicts)
    v_logger.info(f"PHASE_1_DONE: fields={list(running_bounds.keys())}")

    # 4.3 phase two — bounded agentic verification loop
    agent_turns = run_verification_loop(vendor_id, vendor_name, running_bounds)
    running_bounds, agent_conflicts = merge_agent_turns(running_bounds, agent_turns)
    conflicts.extend(agent_conflicts)
    v_logger.info(f"PHASE_2_DONE: steps={len(agent_turns)}")

    # 4.4 build the trace log text — this is returned, tasks.py decides where to save it
    trace_log = build_trace_log(vendor_name, running_bounds, agent_turns, conflicts)

    # 4.5 return one plain summary dict — tasks.py writes this onto the Vendor row
    return {
        "vendor_id": vendor_id,
        "extracted_legal_bounds": running_bounds,
        "fields_extracted": list(running_bounds.keys()),
        "agent_steps_run": len(agent_turns),
        "conflicts": conflicts,
        "trace_log_append": trace_log,
    }


# 5. phase one — deterministic extraction, no tool-calling
def extract_all_documents(
    vendor_id: str,
    documents_payload: dict[str, str],
    running_bounds: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """
    Extract facts from all uploaded documents, merge them into a single
    canonical bounds object, and collect any conflicts discovered along the way.
    """
    v_logger = get_vendor_logger(vendor_id)
    conflicts: list[dict[str, Any]] = []

    for doc_type, markdown_text in documents_payload.items():
        # 1) one cheap LLM call per document
        raw_response = call_cohere(
            system_prompt=EXTRACTION_SYSTEM_PROMPT,
            user_message=f"Document type: {doc_type}\n\n{markdown_text}",
            force_json=True,
            temperature=0.1,
        )

        # 2) guard against malformed JSON
        try:
            parsed = json.loads(raw_response)
        except json.JSONDecodeError:
            v_logger.error(f"EXTRACT_FAILED: malformed JSON for doc_type={doc_type}")
            continue

        # 3) wrap each extracted field with trust metadata
        trust_tier = TRUST_TIER_BY_DOC_TYPE.get(doc_type, 3)
        now_iso = datetime.utcnow().isoformat()

        structured_fields: dict[str, dict[str, Any]] = {}

        for field_name, field_data in parsed.get("fields", {}).items():
            fact = FactValue(
                value=field_data.get("value"),
                trust_tier=trust_tier,
                source_document_type=doc_type,
                source_excerpt=field_data.get("source_excerpt", ""),
                extracted_at=now_iso,
            ).model_dump()

            structured_fields[field_name] = fact

        v_logger.info(
            f"EXTRACT_DONE: doc_type={doc_type} fields={list(structured_fields.keys())}"
        )

        # 4) merge each field into running_bounds and capture conflicts
        for field_name, fact_value in structured_fields.items():
            running_bounds, conflict = merge_fact(
                running_bounds, field_name, fact_value
            )
            if conflict:
                conflicts.append(conflict)

    return running_bounds, conflicts


# 6. phase two — bounded agentic verification loop
def run_verification_loop(
    vendor_id: str, vendor_name: str, running_bounds: dict
) -> list[dict]:
    # 6.1 set up the running facts summary the agent sees each turn
    v_logger = get_vendor_logger(vendor_id)
    turn_log = []
    # tool_descriptions = "\n".join(f"- {name}" for name in TOOL_REGISTRY.keys())
    tool_descriptions = """
    - query_vendor_rag: Search internal vendor documents. Args: {"question": "<string>"}
    - search_xposedornot_breach: Check public breach databases. Args: {"domain": "<vendor domain string e.g. nimbus.com>"}
    - search_tavily: Web search for vendor information. Args: {"query": "<search string>"}
    - search_serpapi_news: Search Google News. Args: {"query": "<search string>"}
    - search_news_breach_signal: Search for breach/bankruptcy news. Args: {"vendor_name": "<vendor name string>"}
    - search_sec_edgar: Search SEC public filings. Args: {"company_name": "<company name string>"}
    - scrape_public_url_content: Scrape a webpage. Args: {"target_url": "<full URL string>"}
    """
    facts_summary = json.dumps(
        {k: v.get("value") for k, v in running_bounds.items()}, default=str
    )

    # 6.2 hard-capped loop — never runs more than MAX_AGENT_STEPS turns
    for step in range(1, MAX_AGENT_STEPS + 1):
        v_logger.info(f"AGENT_STEP: {step}/{MAX_AGENT_STEPS}")
        turn = run_single_agent_turn(
            vendor_id, vendor_name, tool_descriptions, facts_summary
        )
        # 6.3 stop immediately if the model returned unparseable output
        if turn is None:
            break

        # 6.4 call the chosen tool, if any
        tool_result = dispatch_agent_tool_call(vendor_id, turn)

        # 6.5 log this turn
        turn_log.append(
            {
                "step": step,
                "question": turn.question,
                "reason": turn.reason,
                "tool": turn.tool,
                "tool_result_status": tool_result.get("status")
                if tool_result
                else None,
                "summary": turn.summary,
                "extracted_fields": turn.extracted_fields,
            }
        )

        # 6.6 fold this turn's findings into next turn's prompt context
        if turn.extracted_fields:
            current = json.loads(facts_summary)
            current.update(turn.extracted_fields)
            facts_summary = json.dumps(current, default=str)

        # 6.7 stop when the model signals it's done
        if turn.continue_loop == 0:
            v_logger.info("AGENT_STOP: model signaled continue_loop=0")
            break
    else:
        v_logger.warning(
            f"AGENT_STOP: hit MAX_AGENT_STEPS={MAX_AGENT_STEPS} without natural stop"
        )

    return turn_log


def run_single_agent_turn(
    vendor_id: str, vendor_name: str, tool_descriptions: str, facts_summary: str
) -> Optional[AgentTurn]:
    # 6.8 one LLM call, validated against AgentTurn
    v_logger = get_vendor_logger(vendor_id)
    system_prompt = AGENT_SYSTEM_PROMPT.format(
        tool_descriptions=tool_descriptions, existing_facts=facts_summary
    )
    raw_response = call_cohere(
        system_prompt=system_prompt,
        user_message=f"Vendor context: {vendor_name}. Verify outstanding risk profiles.",
        force_json=True,
        temperature=0.2,
    )
    try:
        return AgentTurn.model_validate_json(raw_response)
    except Exception as e:
        v_logger.error(f"AGENT_TURN_PARSE_FAILED: {str(e)}")
        return None


def dispatch_agent_tool_call(vendor_id: str, turn: AgentTurn) -> Optional[dict]:
    # 6.9 only call a tool if the model named a real one
    if not turn.tool or turn.tool not in TOOL_REGISTRY:
        return None
    v_logger = get_vendor_logger(vendor_id)
    v_logger.info(f"AGENT_TOOL_CALL: {turn.tool} args={turn.tool_args}")
    result = TOOL_REGISTRY[turn.tool](vendor_id, **turn.tool_args)
    v_logger.info(f"AGENT_TOOL_RESULT: status={result.get('status')}")
    return result


# 7. shared merge logic — used by both extraction phases
def merge_fact(
    running_bounds: dict, field_name: str, new_fact: dict
) -> tuple[dict, Optional[dict]]:
    # 7.1 no existing value — just write it
    existing = running_bounds.get(field_name)
    if existing is None:
        running_bounds[field_name] = new_fact
        return running_bounds, None

    # 7.2 new fact is more trustworthy — it wins, log what it overrode
    if new_fact["trust_tier"] < existing["trust_tier"]:
        conflict = {
            "field_name": field_name,
            "old_value": existing["value"],
            "old_trust_tier": existing["trust_tier"],
            "new_value": new_fact["value"],
            "new_trust_tier": new_fact["trust_tier"],
            "resolution": "NEW_VALUE_ADOPTED_HIGHER_TRUST",
        }
        running_bounds[field_name] = new_fact
        return running_bounds, conflict

    # 7.3 new fact is equal/lower trust and disagrees — flag, keep existing
    if new_fact["value"] != existing["value"]:
        conflict = {
            "field_name": field_name,
            "old_value": existing["value"],
            "old_trust_tier": existing["trust_tier"],
            "new_value": new_fact["value"],
            "new_trust_tier": new_fact["trust_tier"],
            "resolution": "EXISTING_VALUE_RETAINED_TRUST_TIER_DOMINANCE",
        }
        return running_bounds, conflict

    # 7.4 same value — nothing to do
    return running_bounds, None


def merge_agent_turns(
    running_bounds: dict, agent_turns: list[dict]
) -> tuple[dict, list[dict]]:
    # 7.5 fold every field the agent surfaced into running_bounds, tagged trust_tier=4
    conflicts = []
    for turn in agent_turns:
        for field_name, value in turn.get("extracted_fields", {}).items():
            agent_fact = FactValue(
                value=value,
                trust_tier=4,
                source_document_type=None,
                source_excerpt=turn.get("summary", ""),
                extracted_at=datetime.utcnow().isoformat(),
            ).model_dump()
            running_bounds, conflict = merge_fact(
                running_bounds, field_name, agent_fact
            )
            if conflict:
                conflicts.append(conflict)
    return running_bounds, conflicts


# 8. trace log builder — returns text, doesn't write anywhere itself
def build_trace_log(
    vendor_name: str,
    running_bounds: dict,
    agent_turns: list[dict],
    conflicts: list[dict],
) -> str:
    # 8.1 header
    lines = [
        f"# Compliance audit trace — {vendor_name}",
        f"Timestamp: {datetime.utcnow().isoformat()}\n",
        "## Deterministic document extraction phase",
        f"Extracted field keys: {list(running_bounds.keys())}\n",
        f"## Bounded agent verification loop phase ({len(agent_turns)} iterations)",
    ]
    # 8.2 per-turn lines
    for turn in agent_turns:
        lines.append(
            f"- Step {turn['step']}: {turn['question']} [tool={turn['tool'] or 'none'}, status={turn['tool_result_status'] or 'n/a'}]"
        )
        lines.append(f"  -> {turn['summary']}")
    # 8.3 conflicts, if any
    if conflicts:
        lines.append(f"\n## Data discrepancies detected ({len(conflicts)})")
        for c in conflicts:
            lines.append(f"- {c['field_name']}: resolved via {c['resolution']}")
    return "\n".join(lines)
