---
name: utcp-forge
description: Inspects any backend application or OpenAPI spec and generates a production-ready, agent-friendly UTCP v1.0 manual (utcp.json) with zero runtime proxy overhead.
---

# UTCP-Forge Skill

Use this skill when you or the user wants to expose an existing backend project, microservice, or API to AI coding agents via the **Universal Tool Calling Protocol (UTCP v1.0)**.

Unlike MCP, UTCP eliminates proxy wrappers, allowing agents to directly call native endpoints. This skill automates the extraction, semantic curation, and namespacing required for agent tool calling.

---

## When to Invoke This Skill

- The user asks to "make this API agent-ready", "generate a UTCP manual", "create utcp.json", or "connect this service to UTCP/MCP".
- The user wants their agent to call their local or deployed backend endpoints directly without building an intermediate wrapper.
- The user needs to prune noisy routes (like `/health` or `/metrics`) and produce high-context parameter descriptions for LLMs.

---

## Execution Workflow for Coding Agents

### Step 1: Verify Installation or CLI Availability

Check if `utcp-forge` is installed in the current environment or run it via Python:

```bash
which utcp-forge || echo "Run via python -m utcp_forge.cli"
```

If not installed globally, execute directly from its repository or environment:

```bash
python -m utcp_forge.cli --help
```

---

### Step 2: Determine Manual Namespace & Base URL

1. **Namespace**: Ask or infer a clean snake_case namespace for the manual:
   - For an order service: `order_service`
   - For a user service: `user_service`
2. **Base URL**:
   - `utcp-forge` automatically detects base URLs from `.env`, `docker-compose.yml`, and `config.py`.
   - If the app runs on a custom port, pass `--base-url http://localhost:<port>`.

---

### Step 3: Run the Scan & Agentification

Run `utcp-forge` against the target codebase or OpenAPI spec:

```bash
# Scan a Python/FastAPI codebase
utcp-forge scan ./backend \
  --manual-name my_service \
  --output ./public/utcp.json

# Scan an existing OpenAPI JSON/YAML
utcp-forge scan ./docs/openapi.json \
  --manual-name my_service \
  --output ./utcp.json
```

If using a local or proxy LLM endpoint (e.g. at `127.0.0.1:20128/v1`):

```bash
utcp-forge scan ./backend \
  --manual-name my_service \
  --llm-base-url http://127.0.0.1:20128/v1 \
  --model free \
  --output ./utcp.json
```

---

### Step 4: Validate Output Quality

Open and inspect the generated `utcp.json`:
1. Verify `manual_version: "1.0.0"` and `utcp_version: "1.0.2"`.
2. Check that all tools are prefixed with `<manual_name>.<resource>_<action>` (e.g. `my_service.users_create`).
3. Ensure auth tokens are namespaced with `${<manual_name>__<VAR_NAME>}`.
4. Verify non-business routes (`/health`, `/metrics`, `/docs`) were omitted.

---

### Step 5: (Optional) Expose `/utcp` Route in Target Framework

To allow agents to discover tools at runtime directly from the service:

#### FastAPI:
```python
from fastapi import FastAPI
from fastapi.responses import FileResponse

app = FastAPI()

@app.get("/utcp")
def get_utcp_manual():
    return FileResponse("utcp.json")
```

#### Express.js:
```javascript
app.get('/utcp', (req, res) => {
  res.sendFile(path.join(__dirname, 'utcp.json'));
});
```
