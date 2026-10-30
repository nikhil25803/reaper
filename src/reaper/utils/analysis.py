"""Evidence preparation and report generation for model-assisted analysis."""

import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from reaper.utils.graph import graph_path, usage_edges

VERDICT_ORDER = {"likely_dead": 0, "needs_review": 1, "likely_used": 2}


def candidate_evidence(
    project: Path,
    node: dict,
    edges: list[dict],
    nodes: list[dict],
    incoming: int,
    outgoing: int,
) -> dict:
    """Build bounded graph and source evidence for one candidate."""
    project = project.resolve()
    source = str(node["source_file"])
    source_path = (project / source).resolve()
    if not source_path.is_relative_to(project):
        raise ValueError(f"source path escapes project: {source}")

    labels = {item.get("id"): item.get("label") for item in nodes}
    node_id = node["id"]
    relationships: list[dict] = []
    for edge in usage_edges(edges):
        if edge.get("source") == node_id:
            neighbor = edge.get("target")
            relationships.append(
                {
                    "direction": "outgoing",
                    "relation": str(edge.get("relation") or "unknown"),
                    "node": str(labels.get(neighbor) or neighbor),
                }
            )
        elif edge.get("target") == node_id:
            neighbor = edge.get("source")
            relationships.append(
                {
                    "direction": "incoming",
                    "relation": str(edge.get("relation") or "unknown"),
                    "node": str(labels.get(neighbor) or neighbor),
                }
            )
    relationships.sort(key=lambda item: tuple(item.values()))

    return {
        "node_id": node_id,
        "symbol": str(node.get("label") or node_id),
        "source": source,
        "line": str(node.get("source_location") or "-"),
        "community": node.get("community"),
        "ecosystem": node.get("ecosystem"),
        "incoming_connections": incoming,
        "outgoing_connections": outgoing,
        "total_connections": incoming + outgoing,
        "relationships": relationships[:10],
        "source_excerpt": _source_excerpt(source_path, node.get("source_location")),
    }


def build_report(
    project: Path,
    model: str | None,
    findings: list[dict],
    reviewed: int,
    limit: int | None,
    low_connectivity: int | None,
) -> dict:
    """Build the stable JSON report contract."""
    ordered = sorted(
        findings,
        key=lambda item: (
            VERDICT_ORDER[item["verdict"]],
            -item["confidence"],
            item["total_connections"],
            item["source"],
            _line_number(item["line"]),
        ),
    )
    counts = {
        verdict: sum(item["verdict"] == verdict for item in ordered)
        for verdict in VERDICT_ORDER
    }
    return {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "project": str(project.resolve()),
        "graph": str(graph_path(project.resolve())),
        "model": model,
        "options": {
            "limit": limit,
            "low_connectivity": low_connectivity,
        },
        "summary": {"reviewed": reviewed, **counts},
        "findings": ordered,
    }


def write_reports(project: Path, report: dict) -> tuple[Path, Path]:
    """Atomically replace the machine-readable and human-readable reports."""
    output = project.resolve() / "reaper-analysis"
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "reaper-report.json"
    markdown_path = output / "reaper-report.md"
    replacements = (
        (json_path, json.dumps(report, indent=2, ensure_ascii=False) + "\n"),
        (markdown_path, markdown_report(report)),
    )
    temporary: list[tuple[Path, Path]] = []
    try:
        for destination, content in replacements:
            with tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=output,
                delete=False,
            ) as handle:
                handle.write(content)
                temporary.append((Path(handle.name), destination))
        for source, destination in temporary:
            os.replace(source, destination)
    finally:
        for source, _ in temporary:
            source.unlink(missing_ok=True)
    return json_path, markdown_path


def markdown_report(report: dict) -> str:
    """Render a concise report for human review."""
    summary = report["summary"]
    lines = [
        "# Reaper dead-code analysis",
        "",
        f"- Model: `{_markdown(report.get('model') or 'not run')}`",
        f"- Candidates reviewed: {summary['reviewed']}",
        f"- Likely dead: {summary['likely_dead']}",
        f"- Needs review: {summary['needs_review']}",
        f"- Likely used: {summary['likely_used']}",
        "",
        "> Model verdicts are review evidence, not proof that code is removable.",
    ]
    labels = {
        "likely_dead": "Likely dead",
        "needs_review": "Needs review",
        "likely_used": "Likely used",
    }
    for verdict in VERDICT_ORDER:
        lines.extend(["", f"## {labels[verdict]}", ""])
        findings = [item for item in report["findings"] if item["verdict"] == verdict]
        if not findings:
            lines.append("None.")
            continue
        for finding in findings:
            lines.extend(
                [
                    f"### `{_markdown(finding['symbol'])}`",
                    "",
                    f"- Node: `{_markdown(finding['node_id'])}`",
                    "- Source: "
                    f"`{_markdown(finding['source'])}:{_markdown(finding['line'])}`",
                    f"- Confidence: {finding['confidence']}%",
                    f"- Removal risk: {finding['removal_risk']}",
                    f"- Connections: {finding['total_connections']}",
                    f"- Reason: {_markdown(finding['reason'])}",
                ]
            )
            if finding["evidence"]:
                lines.append("- Evidence:")
                lines.extend(
                    f"  - {_markdown(evidence)}" for evidence in finding["evidence"]
                )
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def merge_findings(evidence: list[dict], verdicts: list[dict]) -> list[dict]:
    """Merge trusted graph metadata with validated model verdicts."""
    verdict_by_id = {item["node_id"]: item for item in verdicts}
    return [
        {
            key: candidate[key]
            for key in (
                "node_id",
                "symbol",
                "source",
                "line",
                "community",
                "incoming_connections",
                "outgoing_connections",
                "total_connections",
            )
        }
        | verdict_by_id[candidate["node_id"]]
        for candidate in evidence
    ]


def _source_excerpt(path: Path, location: object) -> str:
    """Return at most 31 numbered source lines around a graph location."""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return "Source unavailable."
    line = _line_number(location)
    if line < 1:
        return "Source location unavailable."
    start = max(0, line - 16)
    end = min(len(lines), line + 15)
    excerpt = "\n".join(
        f"{index + 1:>6} | {lines[index]}" for index in range(start, end)
    )
    return excerpt[:8000]


def _line_number(location: object) -> int:
    try:
        return int(str(location).removeprefix("L").split("-", 1)[0])
    except ValueError:
        return 0


def _markdown(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")
