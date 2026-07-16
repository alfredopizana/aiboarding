# SPEC-001 — AIboarding: Visión y Alcance

**Estado:** Aprobado · **Versión:** 1.0 · **Fecha:** 2026-07-15

## 1. Problema

Los nuevos empleados tardan semanas en volverse productivos porque el conocimiento
está disperso (Confluence, Drive, GitHub, PDFs, tribal knowledge) y no saben:

1. Qué deben lograr en sus primeros 90 días.
2. A quién preguntar cada tema.
3. Dónde está la documentación relevante.

## 2. Solución

**AIboarding**: asistente de onboarding con agente LangGraph auditable que:

- **Genera planes "90-Day Success"** personalizados por rol/equipo (30/60/90).
- **Responde dudas** con RAG sobre el conocimiento ingerido, citando fuentes.
- **Conecta personas**: sugiere con quién hablar según tema y rol.
- **Refiere documentación**: enlaza a la fuente original (Confluence/Drive/GitHub/PDF).

## 3. Alcance

### Fase 1 (este repo)
- Conectores de ingesta: archivos locales (md/txt/pdf), Confluence, Google Drive, GitHub.
- Pipeline de ingesta → chunking → embeddings → vector store persistente.
- Directorio de personas (people.yaml) con expertise y disponibilidad.
- Agente LangGraph con router de intenciones y auditoría completa (JSONL).
- Generador de plan 90 días (Markdown + JSON estructurado).
- API REST (FastAPI) y CLI (Typer).

### Fase 2 (interfaces preparadas, integración diferida)
- Bot de Slack (Socket Mode) — módulo `integrations/slack_bot.py`.
- Notificaciones/digest por correo (SMTP) — módulo `integrations/email_sender.py`.

### Fuera de alcance
- SSO/permisos por documento (se asume corpus ya autorizado).
- UI web propia (se consume vía API/CLI/Slack).

## 4. Usuarios

| Usuario | Necesidad |
|---|---|
| Nuevo empleado | Plan 90 días, respuestas, contactos, docs |
| Manager / Buddy | Generar y ajustar el plan, ver progreso |
| People Ops | Mantener corpus y directorio de personas |

## 5. Criterios de éxito

- Un nuevo empleado obtiene un plan 90 días en < 1 min.
- Toda respuesta del agente incluye citas de fuente o contactos sugeridos.
- Cada interacción queda auditada (quién, qué, qué nodos corrieron, qué fuentes se usaron).
- El sistema funciona en modo offline determinista (`fake` provider) para tests/demo.
