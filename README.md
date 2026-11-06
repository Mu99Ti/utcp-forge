# UTCP-Forge

> Zero-overhead agentification for backend APIs.
> Turn any existing codebase or OpenAPI specification into production-grade, agent-ready Universal Tool Calling Protocol (UTCP v1.0) manuals in seconds.

---

## Executive Summary & Value Proposition

Anthropic's Model Context Protocol (MCP) introduced an industry-standard interface for agent tooling, but it imposed a steep "wrapper tax": developers must deploy, run, and maintain dedicated proxy server processes for every internal service.

**UTCP (Universal Tool Calling Protocol)** eliminates this wrapper tax by allowing autonomous AI agents to invoke native HTTP, WebSocket, and CLI endpoints directly.

However, adopting UTCP presents critical engineering hurdles:
1. **The Context Window Poisoning Problem**: Naive OpenAPI ingestion dumps hundreds of administrative, telemetry, and health check endpoints into the agent prompt, driving up latency and token costs.
2. **Ambiguous Tool Descriptions**: Bare API specs lack semantic instructions explaining *when*, *why*, and under what *pre-conditions* an agent should trigger an action.
3. **Outdated or Missing Documentation**: Many production services lack up-to-date Swagger/OpenAPI files altogether.

**UTCP-Forge solves these challenges at the source.** It statically scans application codebases, resolves schemas deterministically via an AST symbol table, uses an LLM to enrich semantic tool descriptions, and emits strict UTCP v1.0 manuals adhering to expert namespacing rules.

---

## Key Architecture & Cost-Efficiency Innovations

### 1. Codebase-First AST Extraction
Unlike naive tools that require manual OpenAPI generation, UTCP-Forge reads Python AST trees directly (FastAPI, Starlette, Flask). It maps route decorators, HTTP verbs, URL path parameters, and authentication dependencies without executing target code.

### 2. Deterministic SymbolTable (90%+ Token Reduction)
Rather than passing entire codebases into expensive LLM context windows, UTCP-Forge constructs an in-memory `SymbolTable` that:
- Indexes all Pydantic models, TypedDicts, and dataclasses locally.
- Resolves request and response schemas deterministically ($0.00 token cost).
- Slices only minimal handler skeletons and docstrings, keeping per-route LLM consumption under 400 tokens.

### 3. Expert Namespacing Standards (UTCP v1.0 Compliance)
UTCP-Forge strictly enforces official UTCP v1.0 namespacing rules:
- **Tool Identifiers**: Formatted as `<manual_name>.<resource>_<action>` (e.g. `billing_service.invoices_create`), preventing symbol collisions in multi-manual agent runtimes.
- **Credential Isolation**: Environment variable placeholders are namespaced with duplicate underscores: `${<manual_name>__<VAR_NAME>}` (e.g. `${billing_service__API_KEY}`).
- **Protocol Restraints**: Enforces `allowed_communication_protocols: ["http"]` to block unauthorized protocol escalation.

---

## Getting Started

### Prerequisites
- Python 3.9 or higher
- `uv` (recommended) or `pip`

### Installation

```bash
git clone https://github.com/muhamadtalebi/utcp-forge.git
cd utcp-forge
uv venv
source .venv/bin/activate
uv pip install -e .
```

### Basic Usage

#### Scan a FastAPI / Python Codebase
Point UTCP-Forge at your project root to scan AST symbols, prune internal endpoints, and compile `utcp.json`:

```bash
utcp-forge scan ./my_backend_app \
  --manual-name order_service \
  --output ./public/utcp.json \
  --base-url https://api.mycompany.com
```

#### Scan with a Custom LLM Endpoint (e.g., Local or Proxy)
UTCP-Forge supports any OpenAI-compatible API endpoint:

```bash
utcp-forge scan ./my_backend_app \
  --manual-name order_service \
  --llm-base-url http://127.0.0.1:20128/v1 \
  --model free \
  --output ./utcp.json
```

#### Scan an Existing OpenAPI / Swagger Spec
If an OpenAPI spec is already available, UTCP-Forge can ingest and enrich it:

```bash
utcp-forge scan https://api.mycompany.com/openapi.json \
  --manual-name external_gateway \
  --output ./utcp.json
```

---

## Technical Specifications

### CLI Reference

| Option | Flag | Description | Default |
|---|---|---|---|
| `target` | Positional | Path to codebase directory, or OpenAPI JSON/YAML URL/file | Required |
| `--manual-name` | `-n` | Namespace prefix for tools and credentials | `app_service` |
| `--output` | `-o` | Destination file path for generated manual | `utcp.json` |
| `--base-url` | `-u` | Base URL prepended to route paths | `https://api.example.com` |
| `--llm-base-url` | N/A | Base URL for custom OpenAI-compatible server | Environment / None |
| `--llm-api-key` | N/A | API key for LLM provider | Environment / None |
| `--model` | `-m` | LLM model identifier | `free` |
| `--quiet` | `-q` | Suppress interactive terminal rendering | `False` |

---

## Development and Testing

Run test suite:

```bash
PYTHONPATH=src .venv/bin/python -m unittest discover tests
```

---

## License

Apache License 2.0. See LICENSE for details.
