# SPEC-002 — Arquitectura

**Estado:** Aprobado · **Versión:** 1.0

## 1. Diagrama

```
┌──────────────── Sources ────────────────┐
│ Local (md/txt/pdf) · Confluence · Drive │
│              · GitHub                   │
└───────────────┬─────────────────────────┘
                │ connectors/*  (Document)
                ▼
        ingestion/pipeline ── chunker ──► knowledge/vectorstore (JSON persist)
                                              ▲
                                              │ retrieve(k)
┌──────────── Interfaces ─────────┐     ┌─────┴──────────────────────────┐
│  CLI (Typer)   API (FastAPI)    │────►│   agent/graph  (LangGraph)     │
│  Slack (F2)    Email (F2)       │     │  ingest→router→{qa|connect|    │
└─────────────────────────────────┘     │   plan|docs}→cite→respond      │
                                        └─────┬──────────────────────────┘
                                              │ every node
                                              ▼
                                     audit/ (JSONL por thread)
```

## 2. Módulos

| Módulo | Responsabilidad |
|---|---|
| `config.py` | Settings vía pydantic-settings + `.env` |
| `models.py` | Entidades Pydantic: `SourceDocument`, `Chunk`, `Person`, `SuccessPlan`, `AuditEvent` |
| `connectors/` | `base.Connector` (ABC) + `local`, `confluence`, `gdrive`, `github` |
| `ingestion/` | `chunker.py` (split por párrafos con overlap), `pipeline.py` (orquesta) |
| `knowledge/` | `embeddings.py` (openai/hashing), `vectorstore.py`, `people.py` |
| `agent/` | `state.py`, `llm.py`, `nodes.py`, `graph.py` (LangGraph), `audit.py` |
| `plans/` | `generator.py` — plan 90 días desde plantilla de rol + contexto RAG |
| `api/` | FastAPI: `/ask`, `/plan`, `/people`, `/health`, `/audit/{thread_id}` |
| `cli.py` | `ingest`, `ask`, `plan`, `people`, `serve`, `audit` |
| `integrations/` | Fase 2: `slack_bot.py`, `email_sender.py` |

## 3. Decisiones (ADR resumido)

| # | Decisión | Razón |
|---|---|---|
| 1 | LangGraph `StateGraph` con nodos puros | Auditabilidad: cada transición se registra |
| 2 | Vector store propio (JSON + coseno) por defecto | Cero deps nativas; Chroma opcional después |
| 3 | Proveedor LLM/embeddings intercambiable, con modo `fake`/`hashing` determinista | Tests offline, CI sin API keys |
| 4 | Auditoría JSONL append-only por `thread_id` | Trazabilidad simple, greppable, exportable |
| 5 | Personas en `people.yaml` versionado | Fuente de verdad simple para Fase 1 |

## 4. Flujo del agente (LangGraph)

Nodos: `classify_intent → (answer_question | suggest_people | generate_plan | refer_docs) → finalize`.

- `classify_intent`: clasifica en `{question, connect, plan, docs}`.
- `answer_question`: retrieve top-k → LLM con contexto → respuesta con citas.
- `suggest_people`: matching de expertise contra people directory (+ razón).
- `generate_plan`: delega a `plans.generator`.
- `refer_docs`: retrieve → lista de fuentes con URL/ruta.
- `finalize`: ensambla respuesta, cierra evento de auditoría.

Cada nodo emite `AuditEvent{thread_id, node, ts, input_digest, output_digest, sources, latency_ms}`.

## 5. Errores

- Conector no configurado → se omite con warning, no rompe la ingesta.
- Vector store vacío → el agente responde honestamente y sugiere ingerir.
- LLM fallo → error explícito en API (502) y evento de auditoría `error`.
