# filepath: core/orchestrator.py

import json
from datetime import datetime
from typing import Literal, Optional, Any
from pydantic import BaseModel, Field

from backend.vendor_logging import get_vendor_logger
from clients.cohere import call_cohere
from core.prompts import EXTRACTION_SYSTEM_PROMPT, AGENT_SYSTEM_PROMPT
from core.tools import TOOL_REGISTRY


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


class FactValue(BaseModel):
    value: Any
    trust_tier: int  # 1=independent audit, 2=contract text, 3=public record, 4=OSINT, 5=self-reported
    source_document_type: Optional[str] = None
    source_excerpt: Optional[str] = None
    extracted_at: str


TRUST_TIER_BY_DOC_TYPE = {"SOC2": 1, "PCI": 1, "DPA": 2, "MSA": 2}
MAX_AGENT_STEPS = 4


def run_compliance_audit_orchestrator(
    vendor_id: str, vendor_name: str, documents_payload: dict, existing_bounds: dict
) -> dict[str, Any]:
    log = get_vendor_logger(vendor_id)
    log.info(
        f"ORCHESTRATOR_START | vendor={vendor_name} | docs={list(documents_payload.keys())}"
    )

    running_bounds = dict(existing_bounds)
    conflicts = []

    running_bounds, extraction_conflicts = extract_all_documents(
        vendor_id, documents_payload, running_bounds
    )
    conflicts.extend(extraction_conflicts)
    log.info(f"PHASE_1_DONE | fields_extracted={list(running_bounds.keys())}")

    agent_turns = run_verification_loop(vendor_id, vendor_name, running_bounds)
    running_bounds, agent_conflicts = merge_agent_turns(running_bounds, agent_turns)
    conflicts.extend(agent_conflicts)
    log.info(
        f"PHASE_2_DONE | agent_steps={len(agent_turns)} | total_conflicts={len(conflicts)}"
    )

    return {
        "vendor_id": vendor_id,
        "extracted_legal_bounds": running_bounds,
        "fields_extracted": list(running_bounds.keys()),
        "agent_steps_run": len(agent_turns),
        "conflicts": conflicts,
    }


def extract_all_documents(
    vendor_id: str,
    documents_payload: dict[str, str],
    running_bounds: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    log = get_vendor_logger(vendor_id)
    conflicts: list[dict[str, Any]] = []

    for doc_type, markdown_text in documents_payload.items():
        log.info(f"EXTRACT_START | doc_type={doc_type} | chars={len(markdown_text)}")

        raw_response = call_cohere(
            system_prompt=EXTRACTION_SYSTEM_PROMPT,
            user_message=f"Document type: {doc_type}\n\n{markdown_text}",
            force_json=True,
            temperature=0.1,
        )
        log.ai(f"EXTRACT_LLM_RAW | doc_type={doc_type}\n{raw_response}")

        try:
            parsed = json.loads(raw_response)
        except json.JSONDecodeError as e:
            log.error(f"EXTRACT_JSON_FAIL | doc_type={doc_type} | error={e}")
            continue

        fields_block = parsed.get("fields", {})
        if not fields_block:
            log.warning(
                f"EXTRACT_EMPTY | doc_type={doc_type} | no fields returned by model"
            )
            continue

        trust_tier = TRUST_TIER_BY_DOC_TYPE.get(doc_type, 3)
        now_iso = datetime.utcnow().isoformat()
        structured_fields: dict[str, dict[str, Any]] = {}

        for field_name, field_data in fields_block.items():
            # Guard: field_data must be a dict with a "value" key
            if not isinstance(field_data, dict):
                log.warning(
                    f"EXTRACT_FIELD_SKIP | field={field_name} | reason=field_data is not a dict, got {type(field_data).__name__}={field_data!r}"
                )
                continue

            raw_value = field_data.get("value")
            if raw_value is None:
                log.warning(
                    f"EXTRACT_FIELD_SKIP | field={field_name} | reason=value key missing or null"
                )
                continue

            fact = FactValue(
                value=raw_value,
                trust_tier=trust_tier,
                source_document_type=doc_type,
                source_excerpt=field_data.get("source_excerpt", ""),
                extracted_at=now_iso,
            ).model_dump()

            structured_fields[field_name] = fact
            log.debug(
                f"EXTRACT_FIELD | field={field_name} | value={raw_value!r} | excerpt={field_data.get('source_excerpt', '')[:80]!r}"
            )

        log.info(
            f"EXTRACT_DONE | doc_type={doc_type} | fields={list(structured_fields.keys())}"
        )

        for field_name, fact_value in structured_fields.items():
            running_bounds, conflict = merge_fact(
                running_bounds, field_name, fact_value
            )
            if conflict:
                log.warning(
                    f"MERGE_CONFLICT | field={field_name} | resolution={conflict['resolution']} | old={conflict['old_value']!r} | new={conflict['new_value']!r}"
                )
                conflicts.append(conflict)

    return running_bounds, conflicts


def run_verification_loop(
    vendor_id: str, vendor_name: str, running_bounds: dict
) -> list[dict]:
    log = get_vendor_logger(vendor_id)
    turn_log = []
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

    for step in range(1, MAX_AGENT_STEPS + 1):
        log.info(f"AGENT_STEP_START | step={step}/{MAX_AGENT_STEPS}")
        turn = run_single_agent_turn(
            vendor_id, vendor_name, tool_descriptions, facts_summary
        )

        if turn is None:
            log.error(
                f"AGENT_STEP_ABORT | step={step} | reason=LLM output failed validation"
            )
            break

        log.info(f"AGENT_QUESTION | step={step} | question={turn.question!r}")
        log.debug(f"AGENT_REASON   | step={step} | reason={turn.reason!r}")

        tool_result = dispatch_agent_tool_call(vendor_id, turn)

        if turn.extracted_fields:
            log.ai(
                f"AGENT_FIELDS   | step={step} | fields={json.dumps(turn.extracted_fields, default=str)}"
            )
        log.info(f"AGENT_SUMMARY  | step={step} | summary={turn.summary!r}")

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

        if turn.extracted_fields:
            current = json.loads(facts_summary)
            current.update(turn.extracted_fields)
            facts_summary = json.dumps(current, default=str)

        if turn.continue_loop == 0:
            log.info(
                f"AGENT_STOP | step={step} | reason=model signaled continue_loop=0"
            )
            break
    else:
        log.warning(
            f"AGENT_STOP | reason=hit MAX_AGENT_STEPS={MAX_AGENT_STEPS} without natural stop"
        )

    return turn_log


def run_single_agent_turn(
    vendor_id: str, vendor_name: str, tool_descriptions: str, facts_summary: str
) -> Optional[AgentTurn]:
    log = get_vendor_logger(vendor_id)
    system_prompt = AGENT_SYSTEM_PROMPT.format(
        tool_descriptions=tool_descriptions, existing_facts=facts_summary
    )

    # log.ai(f"AGENT_LLM_SYSTEM_PROMPT\n{system_prompt}")

    raw_response = call_cohere(
        system_prompt=system_prompt,
        user_message=f"Vendor context: {vendor_name}. Verify outstanding risk profiles.",
        force_json=True,
        temperature=0.2,
    )
    log.ai(f"AGENT_LLM_RAW_RESPONSE\n{raw_response}")

    try:
        return AgentTurn.model_validate_json(raw_response)
    except Exception as e:
        log.error(f"AGENT_TURN_PARSE_FAIL | error={e}")
        return None


def dispatch_agent_tool_call(vendor_id: str, turn: AgentTurn) -> Optional[dict]:
    if not turn.tool:
        return None
    log = get_vendor_logger(vendor_id)
    if turn.tool not in TOOL_REGISTRY:
        log.warning(f"TOOL_NOT_FOUND | tool={turn.tool!r} | skipping")
        return None
    log.info(f"TOOL_CALL  | tool={turn.tool} | args={json.dumps(turn.tool_args)}")
    result = TOOL_REGISTRY[turn.tool](vendor_id, **turn.tool_args)
    log.ai(
        f"TOOL_RESULT | tool={turn.tool} | status={result.get('status')} | data={json.dumps(result, default=str)}"
    )
    return result


def merge_fact(
    running_bounds: dict, field_name: str, new_fact: dict
) -> tuple[dict, Optional[dict]]:
    existing = running_bounds.get(field_name)
    if existing is None:
        running_bounds[field_name] = new_fact
        return running_bounds, None

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

    return running_bounds, None


def merge_agent_turns(
    running_bounds: dict, agent_turns: list[dict]
) -> tuple[dict, list[dict]]:
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
