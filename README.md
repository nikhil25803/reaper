# Reaper

> A language-agnostic tool for dead code detection and analysis.

[![CI](https://github.com/nikhil25803/reaper/actions/workflows/ci.yml/badge.svg)](https://github.com/nikhil25803/reaper/actions/workflows/ci.yml)
[![Test](https://github.com/nikhil25803/reaper/actions/workflows/test.yml/badge.svg)](https://github.com/nikhil25803/reaper/actions/workflows/test.yml)
[![Downloads](https://img.shields.io/github/downloads/nikhil25803/reaper/total)](https://github.com/nikhil25803/reaper/releases)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/github/license/nikhil25803/reaper)](LICENSE)
![Graphify](https://img.shields.io/badge/Graphify-graph_analysis-6f42c1)
![llama.cpp](https://img.shields.io/badge/llama.cpp-local_AI-5c4033)

```text
 _ __ ___  __ _ _ __   ___ _ __
| '__/ _ \/ _` | '_ \ / _ \ '__|
| | |  __/ (_| | |_) |  __/ |
|_|  \___|\__,_| .__/ \___|_|
               |_|
```

## About

Reaper is an early-stage developer CLI for finding potentially unused and
unreachable code. Dead-code analysis is not implemented yet; future versions
will use dependency graphs and may use local llama.cpp models to classify
ambiguous findings without a cloud service.

## Available flags

| Flag | Description |
| --- | --- |
| `--help` | Show command help and exit. |
| `--version` | Show the installed version and exit. |

## Development

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```console
uv sync --locked
uv run reaper --help
uv run pytest
uv run ruff check .
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
