```text
 _ __ ___  __ _ _ __   ___ _ __
| '__/ _ \/ _` | '_ \ / _ \ '__|
| | |  __/ (_| | |_) |  __/ |
|_|  \___|\__,_| .__/ \___|_|
               |_|
```

> A language-agnostic tool for dead code detection and analysis.

[![CI](https://github.com/nikhil25803/reaper/actions/workflows/ci.yml/badge.svg)](https://github.com/nikhil25803/reaper/actions/workflows/ci.yml)
[![Test](https://github.com/nikhil25803/reaper/actions/workflows/test.yml/badge.svg)](https://github.com/nikhil25803/reaper/actions/workflows/test.yml)
[![Downloads](https://img.shields.io/github/downloads/nikhil25803/reaper/total)](https://github.com/nikhil25803/reaper/releases)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/github/license/nikhil25803/reaper)](LICENSE)
[![Graphify](https://github.com/nikhil25803/reaper/actions/workflows/graphify.yml/badge.svg)](https://github.com/nikhil25803/reaper/actions/workflows/graphify.yml)
![llama.cpp](https://img.shields.io/badge/llama.cpp-local_AI-5c4033)

## About

Reaper is an early-stage developer CLI that uses an externally installed
Graphify executable to generate local code graphs. It does not identify dead
code yet; interpreting those graphs and classifying findings comes later.

## Available flags

| Flag               | Description                               |
| ------------------ | ----------------------------------------- |
| `--help`           | Show command help and exit.               |
| `--version`        | Show the installed version and exit.      |
| `--check graphify` | Check whether Graphify is installed.      |
| `--scan PATH`      | Generate a code-only graph for a project. |
| `graph`            | Explore an existing generated graph.      |

## Graphify

Reaper does not bundle Graphify. Install its `graphify` command separately:

```console
uv tool install graphifyy
```

> Installs Graphify as an isolated uv tool.

```console
reaper --check graphify
```

> Confirms Graphify is available and prints its version.

```console
reaper --scan .
```

> Scans the current project in code-only mode and writes the generated graph
> under `reaper-analysis/graphify-out`.

A scan runs locally without a graph database, API key, or LLM and writes its
files to `<project>/reaper-analysis/graphify-out`. Code-only mode skips
documentation, PDFs, images, and other semantic inputs. Existing analysis files
are updated by Graphify and are not deleted by Reaper. Successful scans print a
compact table containing the node, edge, and community counts.

## Explore the graph

```console
reaper graph candidates .
```

> Lists callable nodes with no incoming usage connections. These are review
> candidates, not confirmed dead code: entry points, public APIs, decorators,
> reflection, and framework hooks can appear unused.

```console
reaper graph candidates . --limit 10
```

> Limits the candidate table to ten results.

```console
reaper graph inspect . "main()"
```

> Shows a node's metadata and incoming and outgoing relationships. Use an exact
> node ID when a label matches more than one node.

## Development

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```console
uv sync --locked
```

```console
uv run reaper --help
```

```console
uv run pytest
```

```console
uv run ruff check .
```

```console
uv run ruff format --check .
```

The same tasks are available through the convenience `Makefile`; run
`make help` to list them.

## Docker

```console
docker build -t reaper .
docker run --rm reaper --help
```

## License

Reaper is available under the [MIT License](LICENSE).
