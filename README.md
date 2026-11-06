# UTCP-Forge

### Stop writing wrapper servers for your AI agents.
**Turn any existing FastAPI, Flask, or Express backend into production-ready [UTCP v1.0](https://github.com/universal-tool-calling-protocol) tools in 5 seconds flat.**

---

## Why Developers & AI Engineers Care

Anthropic's Model Context Protocol (MCP) started a revolution in agent tooling. But it introduced an agonizing tax for engineering teams: **the wrapper tax**.

To let an agent use your internal APIs, you had to write, containerize, and host separate MCP proxy servers over stdio or SSE. More moving parts, more memory leaks, more latency.

**UTCP (Universal Tool Calling Protocol)** threw away the wrapper servers. It proved that AI agents can call native HTTP, WebSocket, and CLI endpoints directly—if they have a clean tool manual.

### The Catch with Raw APIs
Try feeding an existing Swagger or OpenAPI file to an agent today:
- **Context window explosion**: Hundreds of internal health checks (`/healthz`, `/metrics`), debug routes, and telemetry spam your prompt and inflate token bills.
- **Agent blindness**: Endpoints like `POST /v1/claims` lack semantic context explaining *when*, *why*, and under what *pre-conditions* an agent should trigger them.
- **Missing documentation**: Most internal microservices don't even have an up-to-date OpenAPI spec.

**UTCP-Forge solves this at the source.** It inspects your actual application source code, maps routes and Pydantic schemas deterministically via an AST symbol table, uses an LLM to enrich semantic instructions, and outputs a strict UTCP v1.0 manual.

Zero runtime wrappers. Zero extra infrastructure. Instant agent connectivity.

---

## Key Highlights

- **Codebase-First AST Extraction**: Points straight at your code repository (FastAPI, Starlette, Flask). Discovers decorators, schemas, and auth guards without executing your code.
- **Deterministic SymbolTable (90%+ Token Savings)**: Slices only the essential signatures and Pydantic schemas. Avoids dumping whole files into the LLM, keeping costs at pennies per service.
- **Intelligent Noise Pruning**: Automatically drops non-agent endpoints (`/health`, `/metrics`, `/docs`) so your agent context stays lean and focused.
- **Enterprise Namespacing (UTCP v1.0 Standard)**: Guarantees collision-free tool identifiers (`<manual_name>.<resource>_<action>`) and isolated credential variables (`${<manual_name>__<VAR_NAME>}`).
- **Drop-In Agent Skill Included**: Packaged with a native `skills/utcp-forge/` definition ready for Claude Code, Cursor, and OpenCode.

---

## Architecture at a Glance

```
  [ Your Backend Codebase ]
             │
             ▼ (Zero-Cost AST Walk)
  [ Deterministic SymbolTable ]
     ├── Routes & Handlers
     └── Pydantic / TypedDict Schemas
             │
             ▼ (Micro-Prompt Synthesis ~350 tokens)
  [ LLM Semantic Curation Engine ]
     ├── Prunes /health, /metrics
     ├── Generates intent & side-effect warnings
     └── Maps auth to isolated env placeholders
             │
             ▼
  [ Production UTCP v1.0 Manual (`utcp.json`) ]
     └── Ready for any UTCP or MCP-compatible agent!
```

---

## Quickstart

### 1. Installation

```bash
git clone https://github.com/muhamadtalebi/utcp-forge.git
cd utcp-forge
uv venv
source .venv/bin/activate
uv pip install -e .
```

### 2. Scan Your Application

Point `utcp-forge` at your backend folder. It auto-detects your base URL, discovers routes, and compiles `utcp.json`:

```bash
utcp-forge scan ./backend \
  --manual-name billing_service \
  --output ./public/utcp.json
```

### 3. Use with Custom / Local LLMs

Works with any OpenAI-compatible API (including local models, vLLM, Ollama, or proxies):

```bash
utcp-forge scan ./backend \
  --manual-name billing_service \
  --llm-base-url http://127.0.0.1:20128/v1 \
  --model free \
  --output ./utcp.json
```

### 4. Scan from OpenAPI / Swagger (Fallback)

Have an existing OpenAPI spec? UTCP-Forge enriches it just as easily:

```bash
utcp-forge scan https://api.mycompany.com/openapi.json \
  --manual-name external_gateway \
  --output ./utcp.json
```

---

## Output Example: Clean, Namespaced UTCP v1.0

Here is what UTCP-Forge generates from your raw code:

```json
{
  "manual_version": "1.0.0",
  "utcp_version": "1.0.2",
  "tools": [
    {
      "name": "billing_service.orders_create",
      "description": "Places a customer order. Charges credit card and reserves warehouse stock. Call only after validating cart items.",
      "tags": ["orders"],
      "inputs": {
        "type": "object",
        "properties": {
          "body": {
            "type": "object",
            "title": "OrderPayload",
            "properties": {
              "item_id": { "type": "string" },
              "quantity": { "type": "number" }
            },
            "required": ["item_id", "quantity"]
          }
        },
        "required": ["body"]
      },
      "outputs": {
        "type": "object",
        "description": "JSON response from endpoint"
      },
      "tool_call_template": {
        "name": "billing_service.orders_create",
        "call_template_type": "http",
        "url": "https://api.mycompany.com/api/v1/orders",
        "http_method": "POST",
        "content_type": "application/json",
        "allowed_communication_protocols": ["http"],
        "auth": {
          "auth_type": "api_key",
          "api_key": "Bearer ${billing_service__API_KEY}",
          "var_name": "Authorization",
          "location": "header"
        }
      }
    }
  ]
}
```

---

## Coding Agent Skill Integration

UTCP-Forge includes an official Agent Skill in `skills/utcp-forge/` conforming to Anthropic and Claude Code specifications. 

To give your AI coding agent the superpower of making any project agent-ready on command:

```bash
# Link or copy the skill into your agent's skills directory
cp -r skills/utcp-forge ~/.agents/skills/
```

Now, simply prompt your coding agent:
> *"Make this backend agent-ready with UTCP."*

---

## Technical Specifications & CLI Flags

| Option | Flag | Description | Default |
|---|---|---|---|
| `target` | Positional | Path to codebase directory, or OpenAPI JSON/YAML URL/file | Required |
| `--manual-name` | `-n` | Namespace prefix for tools and credentials | `app_service` |
| `--output` | `-o` | Destination file path for generated manual | `utcp.json` |
| `--base-url` | `-u` | Base URL prepended to route paths (auto-detected if omitted) | Auto-detected |
| `--llm-base-url` | N/A | Base URL for custom OpenAI-compatible server | Environment / None |
| `--llm-api-key` | N/A | API key for LLM provider | Environment / None |
| `--model` | `-m` | LLM model identifier | `free` |
| `--quiet` | `-q` | Suppress interactive terminal rendering | `False` |

---

## Verification & Testing

Run unit test suite:

```bash
PYTHONPATH=src .venv/bin/python -m unittest discover tests
```

---

## License

Apache License 2.0. See [LICENSE](LICENSE) for details.
