# SPEC-006 — API, CLI e Integraciones Fase 2

**Estado:** Aprobado · **Versión:** 1.0

## 1. API REST (FastAPI)

| Método | Ruta | Body | Respuesta |
|---|---|---|---|
| GET | `/health` | — | `{status, docs_indexed, people}` |
| POST | `/ask` | `{query, user?}` | `{thread_id, intent, answer, citations[], people[]}` |
| POST | `/plan` | `UserProfile` | `{thread_id, plan, markdown}` |
| GET | `/people?topic=` | — | `[PersonMatch]` |
| POST | `/ingest` | `{source, path?}` | `{ingested_docs, chunks}` |
| GET | `/audit/{thread_id}` | — | `[AuditEvent]` |

Errores: 422 validación, 502 fallo LLM, 404 audit inexistente.

## 2. CLI (Typer)

`ingest`, `ask`, `plan`, `people`, `audit`, `serve` (uvicorn).

## 3. Fase 2 — Slack

- `integrations/slack_bot.py`: Socket Mode (`slack-sdk`, extra `[slack]`).
- Eventos: `app_mention` y DM → `run_agent(query, user=slack_profile)`.
- Respuesta con bloques: answer + citas + botón "¿Con quién hablo?".
- Mismo pipeline de auditoría (`thread_id = slack_{channel}_{ts}`).
- Fase 1 entrega la clase completa con `is_configured()`; sin tokens hace no-op.

## 4. Fase 2 — Email

- `integrations/email_sender.py`: SMTP (stdlib `smtplib`, sin deps).
- Casos: enviar plan 90 días al empleado+manager, digest semanal de progreso.
- `send_plan(plan, to)` renderiza el Markdown a texto/HTML simple.

## 5. Seguridad

- Secretos sólo por env vars; nunca en repo.
- Auditoría guarda digests, no prompts crudos.
- API pensada para red interna; auth (API key header) queda como TODO Fase 2.
