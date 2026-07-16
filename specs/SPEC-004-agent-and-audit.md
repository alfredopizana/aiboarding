# SPEC-004 — Agente LangGraph y Auditabilidad

**Estado:** Aprobado · **Versión:** 1.0

## 1. Estado del grafo

```python
class AgentState(TypedDict):
    thread_id: str
    user: UserProfile          # name, role, team, start_date
    query: str
    intent: Literal["question","connect","plan","docs"] | None
    retrieved: list[RetrievedChunk]
    people_matches: list[PersonMatch]
    plan: SuccessPlan | None
    answer: str
    citations: list[Citation]
```

## 2. Grafo

```
START → classify_intent ─┬→ answer_question ─┐
                         ├→ suggest_people ──┤
                         ├→ generate_plan ───┼→ finalize → END
                         └→ refer_docs ──────┘
```

Routing con `add_conditional_edges(classify_intent, route_by_intent)`.

## 3. Clasificación de intención

1. Heurística determinista primero (keywords ES/EN: "plan", "90", "quién/who",
   "contact", "doc", "dónde encuentro"...).
2. Fallback a LLM si es ambiguo. En provider `fake`, solo heurística.

## 4. Auditoría (requisito duro)

- Toda ejecución del grafo genera eventos JSONL en `data/audit/{thread_id}.jsonl`.
- Evento por nodo: `{ts, thread_id, node, status, latency_ms, input_digest, output_digest, sources[], model, detail}`.
- Digests = sha256 truncado (no se guarda PII cruda del prompt, sólo digest + longitud;
  el `detail` guarda resumen no sensible: intent, #chunks, ids de fuentes).
- Evento inicial `graph_start` (query digest) y final `graph_end` (answer digest).
- Lectura: `aiboarding audit <thread_id>` y `GET /audit/{thread_id}`.

## 5. Citas obligatorias

`answer_question` y `refer_docs` DEBEN adjuntar `citations[]` con `{title, uri, source, chunk_id, score}`.
Si no hay contexto recuperado (score bajo o store vacío) el agente lo declara y
sugiere personas del directorio en su lugar.

## 6. Proveedores LLM

| Provider | Uso |
|---|---|
| `openai` | Producción (`AIBOARDING_LLM_MODEL`) |
| `fake` | Determinista, offline, para tests/demo: plantillas basadas en contexto |

Interfaz: `LLMClient.complete(system: str, user: str) -> str`.
