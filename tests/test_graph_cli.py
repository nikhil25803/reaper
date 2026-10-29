import json

from typer.testing import CliRunner

from reaper.cli import app

runner = CliRunner()


def write_graph(project, nodes: list[dict], edges: list[dict]) -> None:
    graph_dir = project / "reaper-analysis" / "graphify-out"
    graph_dir.mkdir(parents=True, exist_ok=True)
    (graph_dir / "graph.json").write_text(
        json.dumps({"nodes": nodes, "links": edges}), encoding="utf-8"
    )


def callable_node(node_id: str, label: str, source: str, line: str) -> dict:
    return {
        "id": node_id,
        "label": label,
        "norm_label": label,
        "_origin": "ast",
        "_callable": True,
        "file_type": "code",
        "source_file": source,
        "source_location": line,
        "community": 1,
    }


def test_candidates_filter_and_sort_nodes(tmp_path) -> None:
    nodes = [
        callable_node("dead_a", "dead_a()", "src/c.py", "L20"),
        callable_node("dead_b", "dead_b()", "src/a.py", "L10"),
        callable_node("recursive", "recursive()", "src/b.py", "L5"),
        callable_node("used", "used()", "src/used.py", "L1"),
        callable_node("test_caller", "test_caller()", "tests/test_app.py", "L1"),
        callable_node("external", "external()", "src/external.py", "L1")
        | {"external": True},
        {
            "id": "data",
            "label": "data",
            "_origin": "ast",
            "file_type": "code",
            "source_file": "src/data.py",
        },
    ]
    edges = [
        {"source": "module", "target": "dead_b", "relation": "contains"},
        {"source": "recursive", "target": "recursive", "relation": "calls"},
        {"source": "dead_a", "target": "dependency", "relation": "calls"},
        {"source": "test_caller", "target": "used", "relation": "calls"},
    ]
    write_graph(tmp_path, nodes, edges)

    result = runner.invoke(app, ["graph", "candidates", str(tmp_path)])

    assert result.exit_code == 0
    assert "Review candidates only" in result.output
    assert "dead_a()" in result.output
    assert "dead_b()" in result.output
    assert "recursive()" in result.output
    assert "used()" not in result.output
    assert "test_caller()" not in result.output
    assert "external()" not in result.output
    assert result.output.index("dead_b()") < result.output.index("dead_a()")


def test_candidates_limit_and_empty_result(tmp_path) -> None:
    nodes = [
        callable_node("first", "first()", "src/a.py", "L1"),
        callable_node("second", "second()", "src/b.py", "L1"),
    ]
    write_graph(tmp_path, nodes, [])

    limited = runner.invoke(app, ["graph", "candidates", str(tmp_path), "--limit", "1"])

    assert limited.exit_code == 0
    assert "first()" in limited.output
    assert "second()" not in limited.output

    write_graph(
        tmp_path,
        [callable_node("used", "used()", "src/used.py", "L1")],
        [{"source": "caller", "target": "used", "relation": "calls"}],
    )
    empty = runner.invoke(app, ["graph", "candidates", str(tmp_path)])

    assert empty.exit_code == 0
    assert "No zero-inbound callable candidates found" in empty.output


def test_inspect_node_by_id_and_label(tmp_path) -> None:
    nodes = [
        callable_node("alpha_id", "alpha()", "src/a.py", "L2"),
        callable_node("beta_id", "beta()", "src/b.py", "L4"),
    ]
    edges = [
        {"source": "alpha_id", "target": "beta_id", "relation": "calls"},
        {"source": "external", "target": "alpha_id", "relation": "references"},
    ]
    write_graph(tmp_path, nodes, edges)

    by_id = runner.invoke(app, ["graph", "inspect", str(tmp_path), "alpha_id"])
    by_label = runner.invoke(app, ["graph", "inspect", str(tmp_path), "alpha"])

    for result in (by_id, by_label):
        assert result.exit_code == 0
        assert "Graph Node" in result.output
        assert "alpha_id" in result.output
        assert "calls" in result.output
        assert "references" in result.output
        assert "out" in result.output
        assert "in" in result.output


def test_inspect_rejects_ambiguous_or_missing_node(tmp_path) -> None:
    nodes = [
        callable_node("one", "main()", "src/one.py", "L1"),
        callable_node("two", "main()", "src/two.py", "L1"),
    ]
    write_graph(tmp_path, nodes, [])

    ambiguous = runner.invoke(app, ["graph", "inspect", str(tmp_path), "main"])
    missing = runner.invoke(app, ["graph", "inspect", str(tmp_path), "missing"])

    assert ambiguous.exit_code == 2
    assert "one" in ambiguous.output
    assert "two" in ambiguous.output
    assert missing.exit_code == 1
    assert "Node not found" in missing.output


def test_graph_command_handles_missing_and_invalid_graph(tmp_path) -> None:
    missing = runner.invoke(app, ["graph", "candidates", str(tmp_path)])
    assert missing.exit_code == 1
    assert "Run reaper --scan first" in missing.output

    graph_dir = tmp_path / "reaper-analysis" / "graphify-out"
    graph_dir.mkdir(parents=True)
    (graph_dir / "graph.json").write_text("not json", encoding="utf-8")
    invalid = runner.invoke(app, ["graph", "candidates", str(tmp_path)])

    assert invalid.exit_code == 1
    assert "Unable to read graph" in invalid.output
