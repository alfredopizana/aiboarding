"""AIboarding — end-user Streamlit SPA.

A single-page app for new hires: chat over company knowledge, generate a
90-day success plan, find the right people, and inspect the audit trail.

It is a thin front-end over the exact same core the Slack bot and REST API
use — `build_services()` + `svc.agent.run()` — so behaviour is identical
across channels and works fully offline (LLM_PROVIDER=fake).

Run it with:  streamlit run src/aiboarding/ui/streamlit_app.py
      or:     aiboarding ui
"""

from __future__ import annotations

import streamlit as st

from aiboarding import __version__
from aiboarding.connectors import build_connectors
from aiboarding.container import Services, build_services
from aiboarding.ingestion.pipeline import run_ingestion
from aiboarding.models import UserProfile


@st.cache_resource(show_spinner="Cargando el asistente…")
def get_services() -> Services:
    """Build the service container once per Streamlit process."""
    return build_services()


def refresh_services() -> None:
    """Drop the cached container so on-disk changes (new ingests) are picked up."""
    get_services.clear()


def current_user() -> UserProfile:
    p = st.session_state.get("profile", {})
    return UserProfile(
        name=p.get("name") or "New Hire",
        role=p.get("role") or "",  # empty = let the generator pick from team
        team=p.get("team") or "",
        start_date=p.get("start_date") or None,
    )


def current_email() -> str:
    return (st.session_state.get("profile", {}).get("email") or "").strip()


def render_citations(citations: list) -> None:
    if not citations:
        return
    with st.expander(f"📄 Fuentes ({len(citations)})"):
        for c in citations:
            score = f" · score {c.score:.2f}" if getattr(c, "score", None) is not None else ""
            if c.uri:
                st.markdown(f"- [{c.title}]({c.uri}) — `{c.source}`{score}")
            else:
                st.markdown(f"- **{c.title}** — `{c.source}`{score}")


def render_people(matches: list) -> None:
    if not matches:
        return
    with st.expander(f"🤝 Personas sugeridas ({len(matches)})"):
        for m in matches:
            person = m.person
            contact = " · ".join(x for x in [person.slack, person.email] if x)
            st.markdown(
                f"**{person.name}** — {person.role} ({person.team})  \n"
                f"_{m.reason}_"
                + (f"  \n{contact}" if contact else "")
            )


# ─────────────────────────────────────────────────────────────────────────────
# Page config + sidebar
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="AIboarding", page_icon="🚀", layout="wide")

svc = get_services()

with st.sidebar:
    st.title("🚀 AIboarding")
    st.caption(f"Asistente de onboarding · v{__version__}")

    st.subheader("Tu perfil")
    st.session_state.setdefault("profile", {})
    prof = st.session_state["profile"]

    # Roles come from the plan templates; teams from the people directory.
    plan_roles = list(svc.plan_generator.templates["roles"].keys())
    teams = sorted({p.team for p in svc.people.people if p.team})

    prof["name"] = st.text_input("Nombre", value=prof.get("name", ""), placeholder="Ada Lovelace")
    prof["email"] = st.text_input(
        "Email (identidad para guardar tu progreso)",
        value=prof.get("email", ""),
        placeholder="ada@empresa.com",
    )
    _team_opts = ["—"] + teams
    prof["team"] = st.selectbox(
        "Equipo",
        _team_opts,
        index=_team_opts.index(prof["team"]) if prof.get("team") in _team_opts else 0,
    )
    prof["team"] = "" if prof["team"] == "—" else prof["team"]
    _role_opts = ["(auto por equipo)"] + plan_roles
    prof["role"] = st.selectbox(
        "Rol (para el plan)",
        _role_opts,
        index=_role_opts.index(prof["role"]) if prof.get("role") in _role_opts else 0,
    )
    prof["role"] = "" if prof["role"] == "(auto por equipo)" else prof["role"]
    prof["start_date"] = st.text_input(
        "Fecha de inicio", value=prof.get("start_date", ""), placeholder="2026-08-01"
    )

    st.divider()
    st.subheader("Estado del sistema")
    st.metric("Docs indexados", svc.store.count_documents())
    st.metric("Chunks", svc.store.count_chunks())
    col_a, col_b = st.columns(2)
    col_a.metric("Personas", len(svc.people.people))
    col_b.metric("LLM", svc.settings.llm_provider)
    if svc.settings.llm_provider == "fake":
        st.info("Modo offline: recupera y cita docs, sin síntesis en lenguaje natural.", icon="🔌")
    if svc.settings.langsmith_tracing:
        st.caption(f"🔍 LangSmith activo · proyecto `{svc.settings.langsmith_project}`")

    if st.button("🔄 Recargar índice", use_container_width=True):
        refresh_services()
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# Tabs
# ─────────────────────────────────────────────────────────────────────────────
tab_chat, tab_plan, tab_people, tab_admin = st.tabs(
    ["💬 Asistente", "🎯 Plan 90 días", "👥 Personas", "⚙️ Admin / Auditoría"]
)

# ── Chat ─────────────────────────────────────────────────────────────────────
with tab_chat:
    st.subheader("Pregúntale al asistente de onboarding")
    st.session_state.setdefault("messages", [])

    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            render_citations(msg.get("citations", []))
            render_people(msg.get("people", []))

    if prompt := st.chat_input("¿Cómo configuro mi entorno de desarrollo?"):
        st.session_state["messages"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Pensando…"):
                try:
                    result = svc.agent.run(prompt, user=current_user())
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Error del agente: {exc}")
                    result = None
            if result is not None:
                answer = result.get("answer", "") or "_(sin respuesta)_"
                citations = result.get("citations", [])
                people = result.get("people_matches", [])
                st.markdown(answer)
                render_citations(citations)
                render_people(people)
                st.caption(
                    f"intent: `{result.get('intent', '—')}` · thread: `{result.get('thread_id', '—')}`"
                )
                st.session_state["messages"].append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "citations": citations,
                        "people": people,
                    }
                )

    if st.session_state["messages"] and st.button("🗑️ Limpiar conversación"):
        st.session_state["messages"] = []
        st.rerun()

# ── Plan ─────────────────────────────────────────────────────────────────────
CATEGORY_ICON = {"learning": "📘", "relationships": "🤝", "delivery": "🚀", "process": "⚙️"}


def render_plan_checklist(stored) -> None:
    """Render a persisted plan grouped by phase, with checkboxes that save progress."""
    st.progress(
        stored.progress,
        text=f"Progreso: {stored.done_count}/{stored.total} ({stored.progress:.0%})",
    )
    # Group items by phase, preserving order.
    phases: dict[str, list] = {}
    for it in stored.items:
        phases.setdefault(it.phase, []).append(it)
    for phase, items in phases.items():
        st.markdown(f"### {phase}")
        if items and items[0].objective:
            st.caption(items[0].objective)
        for it in items:
            icon = CATEGORY_ICON.get(it.category, "•")
            checked = st.checkbox(
                f"{icon} **{it.title}** — {it.description}",
                value=it.done,
                key=f"item_{it.id}",
            )
            if checked != it.done:
                svc.progress.set_item_done(it.id, checked)
                st.rerun()
            meta = []
            if it.suggested_contacts:
                meta.append("🤝 " + ", ".join(it.suggested_contacts))
            if it.suggested_docs:
                meta.append(f"📄 {len(it.suggested_docs)} doc(s)")
            if meta:
                st.caption("   ".join(meta))


with tab_plan:
    st.subheader("Plan de éxito a 90 días")
    user = current_user()
    email = current_email()

    if not email:
        st.info("Ingresa tu **email** en la barra lateral para generar y guardar tu plan.", icon="✉️")
    else:
        role_label = user.role or f"auto → {svc.plan_generator._resolve_role_key(user)}"
        st.write(
            f"**{user.name}** · rol **{role_label}** · equipo **{user.team or '—'}** · `{email}`"
        )
        stored_user = svc.progress.upsert_user(user, email)
        stored_plan = svc.progress.get_active_plan(stored_user.id)

        col1, col2 = st.columns(2)
        if stored_plan is None:
            if col1.button("✨ Generar mi plan", type="primary"):
                with st.spinner("Generando plan…"):
                    plan = svc.plan_generator.generate(user)
                    stored_plan = svc.progress.save_plan(stored_user.id, plan)
                st.rerun()
        else:
            if col1.button("♻️ Regenerar plan"):
                with st.spinner("Regenerando…"):
                    plan = svc.plan_generator.generate(user)
                    svc.progress.save_plan(stored_user.id, plan)
                st.rerun()

        if stored_plan is not None:
            if stored_plan.summary:
                st.write(stored_plan.summary)
            render_plan_checklist(stored_plan)

# ── People ───────────────────────────────────────────────────────────────────
with tab_people:
    st.subheader("Encuentra a la persona adecuada")
    col1, col2 = st.columns([3, 1])
    topic = col1.text_input("Tema o expertise", placeholder="kubernetes, incident response…")
    team = col2.text_input("Equipo (opcional)", placeholder="devops")
    if topic:
        matches = svc.people.match(topic, team=team, limit=5)
        if not matches:
            st.warning("Sin coincidencias. Prueba otro término.")
        for m in matches:
            person = m.person
            with st.container(border=True):
                st.markdown(f"### {person.name}  ·  _{m.score:.2f}_")
                st.markdown(f"{person.role} — **{person.team}**")
                if person.expertise:
                    st.markdown("🏷️ " + ", ".join(person.expertise))
                contact = " · ".join(x for x in [person.slack, person.email] if x)
                if contact:
                    st.caption(contact)
                st.caption(m.reason)

# ── Admin / Audit ────────────────────────────────────────────────────────────
with tab_admin:
    st.subheader("Ingesta de documentos")
    src = st.selectbox("Fuente", ["local", "confluence", "gdrive", "github", "all"])
    path = st.text_input(
        "Ruta (solo para 'local')", value="data/sample_docs", placeholder="data/sample_docs"
    )
    if st.button("📥 Ingerir"):
        with st.spinner("Ingiriendo…"):
            connectors = build_connectors(svc.settings, local_path=path or None)
            selected = (
                list(connectors.values()) if src == "all" else [connectors.get(src)]
            )
            selected = [c for c in selected if c]
            if not selected:
                st.error(f"Fuente desconocida: {src}")
            else:
                results = run_ingestion(selected, svc.store)
                for r in results:
                    status = "skipped (not configured)" if r.skipped else "ok"
                    st.write(f"**{r.connector}**: {r.documents} docs / {r.chunks} chunks — {status}")
                st.success(
                    f"Índice: {svc.store.count_documents()} docs / {svc.store.count_chunks()} chunks."
                )

    st.divider()
    st.subheader("Auditoría por thread")
    thread_id = st.text_input("thread_id", placeholder="thr_xxxxxxxx")
    if thread_id:
        events = svc.audit.read(thread_id)
        if not events:
            st.warning("Sin eventos para ese thread_id.")
        else:
            st.dataframe(
                [
                    {
                        "ts": e.ts,
                        "node": e.node,
                        "status": e.status,
                        "latency_ms": e.latency_ms,
                        "model": e.model,
                        "sources": ", ".join(e.sources),
                    }
                    for e in events
                ],
                use_container_width=True,
            )
