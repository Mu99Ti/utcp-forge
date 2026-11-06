# UTCP-Forge 🛠️

> **Zero-Overhead Agentification for Any Backend API**  
> Generate production-ready, agent-friendly [UTCP 1.0](https://github.com/universal-tool-calling-protocol) manuals (`utcp.json`) directly from your application's source code or OpenAPI specs using cost-efficient AST extraction and LLM semantic curation.

---

## ⚡ The Philosophy: Why UTCP-Forge?

Anthropic's Model Context Protocol (MCP) requires deploying and maintaining wrapper proxy servers for every internal API. **UTCP (Universal Tool Calling Protocol)** eliminates that wrapper tax by letting AI agents call native HTTP, WebSocket, and CLI endpoints directly.

However, crafting `utcp.json` manuals manually or relying on bare OpenAPI ingestion leads to:
1. **Context Bloat**: Ingesting hundreds of internal routes (`/healthz`, `/metrics`, `/debug`) into LLM prompts.
2. **Ambiguous Tool Descriptions**: Raw endpoints lack clear instructions explaining *when*, *why*, and with what *pre-conditions* an agent should call them.
3. **Missing Specs**: Many internal microservices have out-of-date or non-existent OpenAPI files.

**UTCP-Forge solves this by scanning codebases directly:**
- 🔍 **Codebase-First AST Scanning**: Extracts routes, methods, schemas, and auth guards directly from FastAPI, Starlette, Flask, and Express code.
- 💡 **Cost-Efficient LLM Curation**: Uses AST code skeletonization to feed only minimal signatures to the LLM, reducing token cost by over 80%.
- 🛡️ **Zero Runtime Overhead**: Emits static, validated UTCP 1.0 JSON manuals. No intermediary proxy server is required at runtime.

---

## 🚀 Quickstart

### 1. Installation

```bash
cd /Users/muhamadtalebi/Developer/utcp-forge
uv venv
source .venv/bin/activate
uv pip install -e .
```

### 2. Scan a Codebase

```bash
utcp-forge scan ./my_fastapi_app --output public/utcp.json --base-url https://api.mycompany.com
```

### 3. Scan an OpenAPI / Swagger Spec

```bash
utcp-forge scan https://api.mycompany.com/openapi.json --output utcp.json
```

---

## 🧪 Testing

```bash
PYTHONPATH=src .venv/bin/python -m unittest discover tests
```

---

## 📄 License
Apache-2.0
