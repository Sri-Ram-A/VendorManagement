"""
Convert a single vendor's loguru JSONL log file into a {nodes, links}
graph for react-force-graph-3d.

Usage:
    python logs_to_graph.py path/to/21-06-2026.jsonl > graph.json
"""

import json
import os
import re
import sys
from collections import OrderedDict

DOC_TYPE_RE = re.compile(r"doc_type=([A-Za-z0-9_]+)")


def collapse_source(source: str) -> str:
    """'core.tasks:parse_and_vectorize_document:69' -> 'core.tasks:parse_and_vectorize_document'"""
    parts = source.rsplit(":", 1)
    return parts[0] if len(parts) == 2 and parts[1].isdigit() else source


def extract_doc_type(record: dict) -> str | None:
    extra = record.get("extra", {})
    if "doc_type" in extra:
        return extra["doc_type"]
    match = DOC_TYPE_RE.search(record.get("message", ""))
    return match.group(1) if match else None


def parse_extract_llm_raw(message: str) -> tuple[str, dict] | None:
    """
    EXTRACT_LLM_RAW messages look like:
        'EXTRACT_LLM_RAW | doc_type=MSA\\n{...json blob...}'
    Returns (doc_type, fields_dict) or None if it doesn't match / doesn't parse.
    """
    if "EXTRACT_LLM_RAW" not in message:
        return None

    doc_type_match = DOC_TYPE_RE.search(message)
    doc_type = doc_type_match.group(1) if doc_type_match else "UNKNOWN"

    # payload is everything after the first newline
    if "\n" not in message:
        return None
    json_blob = message.split("\n", 1)[1]
    try:
        parsed = json.loads(json_blob)
    except json.JSONDecodeError:
        return None

    fields = parsed.get("fields", {})
    return doc_type, fields


def build_graph(jsonl_path: str) -> dict:
    nodes = OrderedDict()   # id -> node dict
    links = []              # list of {source, target, ...}
    link_counts = {}        # (source_id, target_id) -> weight, to dedupe repeated edges

    def add_node(node_id: str, **fields):
        if node_id not in nodes:
            nodes[node_id] = {"id": node_id, **fields}
        return node_id

    def add_link(source_id: str, target_id: str, link_type: str, **fields):
        key = (source_id, target_id, link_type)
        if key in link_counts:
            link_counts[key]["weight"] += 1
        else:
            link_counts[key] = {
                "source": source_id,
                "target": target_id,
                "type": link_type,
                "weight": 1,
                **fields,
            }

    vendor_id = None
    prev_func_id = None
    vid = None  # short vendor scope prefix, set once vendor_id is known

    with open(jsonl_path, "r") as f:
        for raw_line in f:
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            try:
                envelope = json.loads(raw_line)
            except json.JSONDecodeError:
                continue  # skip malformed lines rather than crash the whole run

            record = envelope.get("record", envelope)  # tolerate flat-JSON fallback too
            extra = record.get("extra", {})
            level_name = record.get("level", {}).get("name", "INFO")
            message = record.get("message", "")
            timestamp = record.get("time", {}).get("timestamp")
            source = extra.get("source") or f"{record.get('module','?')}:{record.get('function','?')}:{record.get('line','?')}"

            if vendor_id is None:
                vendor_id = extra.get("vendor_id", "unknown_vendor")
                vid = vendor_id[:8]  # short prefix, keeps ids readable
                add_node(f"vendor:{vendor_id}", label=vendor_id, type="vendor", val=20)

            func_id = f"fn:{vid}:{collapse_source(source)}"
            add_node(func_id, label=collapse_source(source), type="function", val=6, vendor_id=vendor_id)

            # sequential flow edge (empirical call graph)
            if prev_func_id is None:
                add_link(f"vendor:{vendor_id}", func_id, "entry")
            elif prev_func_id != func_id:
                add_link(prev_func_id, func_id, "flow", last_message=message)
            prev_func_id = func_id

            # document edges
            doc_type = extract_doc_type(record)
            if doc_type:
                doc_id = f"doc:{vid}:{doc_type}"
                add_node(doc_id, label=doc_type, type="document", val=10, vendor_id=vendor_id)
                add_link(func_id, doc_id, "touches")

            # LLM-extracted field nodes: explode EXTRACT_LLM_RAW into one
            # node per field, carrying its value + source excerpt for hover.
            extracted = parse_extract_llm_raw(message)
            if extracted:
                ex_doc_type, fields = extracted
                ex_doc_id = f"doc:{vid}:{ex_doc_type}"
                add_node(ex_doc_id, label=ex_doc_type, type="document", val=10, vendor_id=vendor_id)
                for field_name, field_data in fields.items():
                    if not isinstance(field_data, dict):
                        continue
                    field_id = f"field:{vid}:{ex_doc_type}:{field_name}"
                    value = field_data.get("value")
                    source_excerpt = field_data.get("source_excerpt", "")
                    add_node(
                        field_id,
                        label=field_name,
                        type="field",
                        val=4,
                        vendor_id=vendor_id,
                        value=json.dumps(value) if not isinstance(value, str) else value,
                        source_excerpt=source_excerpt,
                    )
                    add_link(ex_doc_id, field_id, "extracted")

            # error nodes
            if level_name in ("ERROR", "CRITICAL"):
                err_id = f"err:{vid}:{func_id}:{timestamp}"
                add_node(err_id, label=message[:60], type="error", val=8, vendor_id=vendor_id, full_message=message)
                add_link(func_id, err_id, "raises")

    links = list(link_counts.values())
    return {"nodes": list(nodes.values()), "links": links}


def build_combined_graph(media_dir: str) -> dict:
    """
    Walk media_dir/<vendor_id>/logs/*.jsonl for every vendor folder and merge
    each vendor's graph into one combined {nodes, links} structure.
    Node IDs are already vendor-scoped by build_graph, so no collisions.
    """
    import glob

    combined_nodes = OrderedDict()
    combined_links = []

    jsonl_paths = sorted(glob.glob(os.path.join(media_dir, "*", "logs", "*.jsonl")))
    if not jsonl_paths:
        print(f"No .jsonl files found under {media_dir}/*/logs/", file=sys.stderr)

    for path in jsonl_paths:
        graph = build_graph(path)
        for node in graph["nodes"]:
            combined_nodes[node["id"]] = node  # later runs win if same id re-appears
        combined_links.extend(graph["links"])
        print(f"  merged {path}: {len(graph['nodes'])} nodes, {len(graph['links'])} links", file=sys.stderr)

    return {"nodes": list(combined_nodes.values()), "links": combined_links}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage:", file=sys.stderr)
        print("  Single vendor:   python logs_to_graph.py path/to/21-06-2026.jsonl > graph.json", file=sys.stderr)
        print("  All vendors:     python logs_to_graph.py path/to/media > graph.json", file=sys.stderr)
        sys.exit(1)

    target = sys.argv[1]

    if os.path.isdir(target):
        graph = build_combined_graph(target)
    else:
        graph = build_graph(target)

    print(json.dumps(graph, indent=2))