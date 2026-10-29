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

Reaper transforms complex codebases into navigable graphs. It is built to
combine Graphify’s structural intelligence with local llama.cpp models for smart,
private dead-code analysis—giving models focused evidence instead of making them
spend tokens rediscovering the repository.

> **What’s left:** Graphify integration is ready. llama.cpp integration and
> Bash/PowerShell automation will complete the end-to-end workflow and generate
> token-efficient system prompts for local models.

## Quick Start

Pull the published image:

```console
docker pull ghcr.io/nikhil25803/reaper:latest
```

> The GHCR image becomes available after the first tagged release and may
> require authentication until the package is public. Until then, build it
> locally from this repository:

```console
docker build -t reaper .
```

The commands below use the GHCR image. Replace its name with `reaper` when using
the locally built image.

```console
docker run --rm ghcr.io/nikhil25803/reaper:latest --check graphify
```

> Confirms that the bundled Graphify executable is available.

```console
docker run --rm \
  --user "$(id -u):$(id -g)" \
  --env HOME=/tmp \
  --volume "$PWD:/workspace" \
  ghcr.io/nikhil25803/reaper:latest --scan /workspace
```

> Scans the current project and keeps generated files owned by your host user.

## Available flags

| Flag               | Description                               |
| ------------------ | ----------------------------------------- |
| `--help`           | Show command help and exit.               |
| `--version`        | Show the installed version and exit.      |
| `--check graphify` | Check whether Graphify is installed.      |
| `--scan PATH`      | Generate a code-only graph for a project. |
| `graph`            | Explore an existing generated graph.      |

## Graphify

Graphify is bundled in Reaper's Docker image and generates the local code graph
used by the exploration commands.

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
reaper graph projects .
```

> Discovers scan paths below the current directory that contain
> `reaper-analysis/graphify-out/graph.json`. Copy a project path from this table
> into the candidates or inspect command.

```console
reaper graph candidates .
```

> Counts callable nodes with no incoming usage connections and prints the next
> command for listing them.

```console
reaper graph candidates . --list --limit 10 --page 1
```

> Displays the first ten candidates with stable node IDs and pagination.

```console
reaper graph inspect . src_user_service_unused_legacy_handler
```

> Shows the selected node's metadata and incoming and outgoing relationships.

`PROJECT_PATH` in command help is a directory placeholder, not the literal word
`project`. When working in the scanned directory, it can be omitted:

```console
reaper graph candidates --list
```

Candidates are not confirmed dead code: entry points, public APIs, decorators,
reflection, and framework hooks can appear unused.

## Monorepo example

Consider an illustrative service monorepo:

```text
demo-monorepo/
├── Makefile
├── README.md
├── apps/
│   ├── api-gateway/
│   ├── user-service/
│   ├── admin-service/
│   ├── billing-service/
│   ├── notification-service/
│   └── reporting-service/
├── packages/
│   ├── database/
│   ├── shared/
│   ├── observability/
│   └── config/
├── docs/
│   ├── architecture.md
│   └── adr/
├── scripts/
│   ├── create-service.sh
│   └── init-database.sql
├── docker-compose.yml
├── package.json
├── pnpm-lock.yaml
├── pnpm-workspace.yaml
└── turbo.json
```

First, scan the monorepo root:

```console
reaper --scan .
```

> Generates `./reaper-analysis/graphify-out/graph.json` and prints a compact
> summary. Example counts are illustrative:

```text
 Reaper <> Graphify Scan Complete
┏━━━━━━━━━━━━━┳━━━━━━━┓
┃ Metric      ┃ Count ┃
┡━━━━━━━━━━━━━╇━━━━━━━┩
│ Nodes       │ 1,284 │
│ Edges       │ 2,047 │
│ Communities │    34 │
└─────────────┴───────┘
```

List the scan paths Reaper can analyze:

```console
reaper graph projects .
```

> A root scan produces one entry. Services scanned independently appear as
> additional projects. Example output:

```text
                         Analyzed Projects
┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Project       ┃ Project path                                        ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ demo-monorepo │ /workspace/demo-monorepo                            │
│ user-service  │ /workspace/demo-monorepo/apps/user-service          │
│ admin-service │ /workspace/demo-monorepo/apps/admin-service         │
└───────────────┴─────────────────────────────────────────────────────┘
Found 3 analyzed project(s).
```

Next, count possible candidates:

```console
reaper graph candidates .
```

> Reports the total and suggests the detailed listing command:

```text
Found 193 possible dead-code candidates.
Next: reaper graph candidates "." --list --limit 10 --page 1
```

List the first page:

```console
reaper graph candidates . --list --limit 10 --page 1
```

> Candidate names and counts below are illustrative.

> Review candidates only: entry points, public APIs, decorators, reflection,
> and framework hooks can appear unused.

| Node ID                                    | Symbol                   | Source                                        | Line | Outgoing |
| ------------------------------------------ | ------------------------ | --------------------------------------------- | ---- | -------: |
| `src_user_service_unused_legacy_handler`   | `unusedLegacyHandler()`  | `apps/user-service/src/legacy.ts`             | L42  |        0 |
| `src_admin_service_stale_permission_check` | `stalePermissionCheck()` | `apps/admin-service/src/permissions.ts`       | L88  |        1 |
| `src_billing_service_old_invoice_mapper`   | `oldInvoiceMapper()`     | `apps/billing-service/src/invoice/mapper.ts`  | L17  |        1 |

```text
Page 1/20 · Showing 1-10 of 193 candidates

Inspect: reaper graph inspect "." "src_user_service_unused_legacy_handler"
Next: reaper graph candidates "." --list --limit 10 --page 2
```

Finally, inspect a candidate by its stable node ID:

```console
reaper graph inspect . src_user_service_unused_legacy_handler
```

> Displays its source metadata and graph relationships before a human decides
> whether the code is actually unused.

## Development

Source setup is intended for contributors. End-user installation currently uses
Docker; PyPI publishing and direct `uv tool install reaper` support are planned.

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```console
uv sync --locked
```

```console
uv tool install graphifyy
```

> Installs the external Graphify executable for source-based development.

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

## License

Reaper is available under the [MIT License](LICENSE).
