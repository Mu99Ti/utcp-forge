---
name: utcp-forge
description: Inspects any backend application (FastAPI, Flask, Express) or OpenAPI specification and synthesizes production-ready, agent-friendly UTCP v1.0 manuals (utcp.json) with zero runtime proxy overhead. Triggers on "generate utcp", "create utcp.json", "make api agent-ready", or "utcp manual".
license: Apache-2.0
---

# UTCP-Forge

Autonomous skill that extracts, filters, and compiles production-ready Universal Tool Calling Protocol (UTCP v1.0) manuals directly from backend codebases.

Unlike Anthropic's MCP (which forces intermediate proxy servers), UTCP allows AI agents to directly call native HTTP/WebSocket endpoints. This skill ensures generated manuals have accurate descriptions, strict namespacing, and zero context-poisoning endpoints.

---

## Progressive Disclosure & Resources

- `references/utcp_spec_v1.md`: Strict UTCP 1.0.x JSON schema and namespacing rules.
- `references/framework_adapters.md`: AST extraction rules for FastAPI, Flask, and Express.
- `scripts/run_forge.py`: Standalone CLI wrapper executable without global installations.

---

## Workflow

### 1. Identify Target & Manual Namespace
Determine the project directory (e.g., `./backend`) or OpenAPI spec URL/file.
Select a clean snake_case namespace for the manual:
- E-commerce service: `ecommerce_api`
- Billing service: `billing_service`

### 2. Auto-Detect Base URL
`utcp-forge` automatically inspects:
- `.env`, `.env.local` for `BASE_URL`, `DOMAIN`, `PORT`
- `docker-compose.yml` for exposed host ports
- `config.py` / `settings.py` for server assignments

If unresolvable, default to `http://localhost:8000` or specify with `--base-url`.

### 3. Execute Scan & Synthesis
Invoke the bundled script or the `utcp-forge` command:

```bash
# Using python script directly
python skills/utcp-forge/scripts/run_forge.py scan ./backend \
  --manual-name my_service \
  --output ./public/utcp.json

# Or if using a local LLM endpoint (e.g. 127.0.0.1:20128)
python skills/utcp-forge/scripts/run_forge.py scan ./backend \
  --manual-name my_service \
  --llm-base-url http://127.0.0.1:20128/v1 \
  --model free \
  --output ./utcp.json
```

### 4. Quality Audit
Confirm the output `utcp.json` conforms to UTCP v1.0:
- All tools use `<manual_name>.<resource>_<action>` (e.g. `my_service.users_create`).
- Auth placeholders use double underscores: `${<manual_name>__<VAR_NAME>}`.
- Non-business routes (`/health`, `/metrics`, `/docs`) are excluded.
- Protocol restrictions enforce `allowed_communication_protocols: ["http"]`.

### 5. (Optional) Provide Runtime Route Snippet
If the user wants their app to serve its own manual at runtime, provide the one-line route handler:
- **FastAPI**: `app.get("/utcp")(lambda: FileResponse("utcp.json"))`
- **Express**: `app.get("/utcp", (req, res) => res.sendFile("utcp.json"))`
