"""
Convert a single vendor's loguru JSONL log file into a {nodes, links}
graph for react-force-graph-3d.

Usage:
    python logs_to_graph.py path/to/21-06-2026.jsonl > graph.json
"""

import json
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
                add_node(f"vendor:{vendor_id}", label=vendor_id, type="vendor", val=20)

            func_id = f"fn:{collapse_source(source)}"
            add_node(func_id, label=collapse_source(source), type="function", val=6)

            # sequential flow edge (empirical call graph)
            if prev_func_id is None:
                add_link(f"vendor:{vendor_id}", func_id, "entry")
            elif prev_func_id != func_id:
                add_link(prev_func_id, func_id, "flow", last_message=message[:80])
            prev_func_id = func_id

            # document edges
            doc_type = extract_doc_type(record)
            if doc_type:
                doc_id = f"doc:{doc_type}"
                add_node(doc_id, label=doc_type, type="document", val=10)
                add_link(func_id, doc_id, "touches")

            # error nodes
            if level_name in ("ERROR", "CRITICAL"):
                err_id = f"err:{func_id}:{timestamp}"
                add_node(err_id, label=message[:60], type="error", val=8, full_message=message)
                add_link(func_id, err_id, "raises")

    links = list(link_counts.values())
    return {"nodes": list(nodes.values()), "links": links}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python logs_to_graph.py <path_to.jsonl>", file=sys.stderr)
        sys.exit(1)

    graph = build_graph(sys.argv[1])
    print(json.dumps(graph, indent=2))