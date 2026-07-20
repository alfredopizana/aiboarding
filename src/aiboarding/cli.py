"""Typer CLI (SPEC-006 §2)."""

from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

from aiboarding.config import get_settings
from aiboarding.connectors import build_connectors
from aiboarding.container import build_services
from aiboarding.ingestion.pipeline import ingest_text, run_ingestion
from aiboarding.models import Person, UserProfile

app = typer.Typer(help="AIboarding — AI onboarding assistant (auditable LangGraph agent).")
console = Console()


@app.command()
def ingest(
    source: str = typer.Option("all", help="local | confluence | gdrive | github | all"),
    path: str | None = typer.Option(None, help="Docs dir for the local connector"),
):
    """Ingest documents into the knowledge base."""
    svc = build_services()
    connectors = build_connectors(svc.settings, local_path=path)
    selected = list(connectors.values()) if source == "all" else [connectors[source]]
    results = run_ingestion(selected, svc.store)
    table = Table(title="Ingestion results")
    table.add_column("Connector")
    table.add_column("Docs", justify="right")
    table.add_column("Chunks", justify="right")
    table.add_column("Status")
    for r in results:
        table.add_row(r.connector, str(r.documents), str(r.chunks), "skipped (not configured)" if r.skipped else "ok")
    console.print(table)
    console.print(f"Store now holds [bold]{svc.store.count_documents()}[/] docs / [bold]{svc.store.count_chunks()}[/] chunks.")


@app.command(name="add-doc")
def add_doc(
    title: str = typer.Option(..., help="Document title"),
    file: str | None = typer.Option(None, help="Read content from this file (.md/.txt)"),
    content: str | None = typer.Option(None, help="Inline content (alternative to --file)"),
    uri: str = typer.Option("", help="Stable URI; pushing the same URI again updates the doc"),
):
    """Push a single document into the knowledge base (no connector needed)."""
    if (file is None) == (content is None):
        console.print("[red]Provide exactly one of --file or --content.[/]")
        raise typer.Exit(2)
    if file is not None:
        from pathlib import Path

        path = Path(file).expanduser()
        if not path.is_file():
            console.print(f"[red]File not found: {path}[/]")
            raise typer.Exit(2)
        content = path.read_text(encoding="utf-8", errors="replace")
        uri = uri or str(path.resolve())
    if not content or not content.strip():
        console.print("[red]Content is empty.[/]")
        raise typer.Exit(2)
    svc = build_services()
    doc, n_chunks = ingest_text(svc.store, title=title, content=content, uri=uri)
    console.print(
        f"Ingested [bold]{doc.title}[/] as {doc.doc_id} ({n_chunks} chunks). "
        f"Store: {svc.store.count_documents()} docs / {svc.store.count_chunks()} chunks."
    )


@app.command(name="add-person")
def add_person(
    person_id: str = typer.Option(..., "--id", help="Unique id, e.g. jane.doe"),
    name: str = typer.Option(..., help="Full name"),
    role: str = typer.Option(..., help="Job title"),
    team: str = typer.Option(..., help="Team id, e.g. devops"),
    email: str = typer.Option("", help="Email address"),
    slack: str = typer.Option("", help="Slack handle, e.g. @jane"),
    expertise: str = typer.Option("", help="Comma-separated topics"),
    buddy: bool = typer.Option(False, "--buddy", help="Mark as onboarding buddy"),
    timezone: str = typer.Option("", help="IANA timezone, e.g. America/Mexico_City"),
):
    """Add or update a person in the directory (persisted to people.yaml)."""
    svc = build_services()
    person = Person(
        id=person_id,
        name=name,
        role=role,
        team=team,
        email=email,
        slack=slack,
        expertise=[t.strip() for t in expertise.split(",") if t.strip()],
        onboarding_buddy=buddy,
        timezone=timezone,
    )
    created = svc.people.upsert(person)
    svc.people.save(svc.settings.people_file)
    verb = "Added" if created else "Updated"
    console.print(
        f"{verb} [bold]{person.name}[/] ({person.team}) — directory now has "
        f"{len(svc.people.people)} people in {svc.settings.people_file}."
    )


@app.command()
def diagram(
    output: str | None = typer.Option(None, help="Write a Markdown file with the Mermaid diagram"),
):
    """Generate the agent's architecture diagram (Mermaid) from the live LangGraph graph."""
    svc = build_services()
    mermaid = svc.agent.graph.get_graph().draw_mermaid()
    md = "# AIboarding agent graph\n\n```mermaid\n" + mermaid + "\n```\n"
    if output:
        with open(output, "w") as fh:
            fh.write(md)
        console.print(f"Diagram written to [bold]{output}[/] — renders on GitHub or https://mermaid.live")
    else:
        console.print(mermaid)


@app.command()
def ask(
    query: str,
    name: str = typer.Option("New Hire", help="Your name"),
    role: str = typer.Option("default", help="Your role"),
    team: str = typer.Option("", help="Your team"),
):
    """Ask the onboarding agent anything."""
    svc = build_services()
    result = svc.agent.run(query, user=UserProfile(name=name, role=role, team=team))
    console.print(f"[dim]thread: {result['thread_id']} · intent: {result.get('intent')}[/]")
    console.print(Markdown(result.get("answer", "")))
    citations = result.get("citations", [])
    if citations:
        console.print("\n[bold]Sources:[/]")
        for c in citations:
            console.print(f"  • {c.title} ({c.source}) — {c.uri} [dim]score={c.score}[/]")


@app.command()
def plan(
    name: str = typer.Option(..., help="New hire name"),
    role: str = typer.Option("default", help="engineer | product | default"),
    team: str = typer.Option("", help="Team name"),
    start_date: str | None = typer.Option(None, help="YYYY-MM-DD"),
    output: str | None = typer.Option(None, help="Write markdown to this file"),
):
    """Generate a 90-day success plan."""
    svc = build_services()
    user = UserProfile(name=name, role=role, team=team, start_date=start_date)
    result = svc.agent.run(f"Generate my 90 day success plan for {role}", user=user)
    plan_obj = result.get("plan") or svc.plan_generator.generate(user)
    md = plan_obj.to_markdown()
    if output:
        with open(output, "w") as fh:
            fh.write(md)
        console.print(f"Plan written to [bold]{output}[/] (thread {result['thread_id']})")
    else:
        console.print(Markdown(md))
        console.print(f"[dim]thread: {result['thread_id']}[/]")


@app.command()
def people(topic: str, team: str = typer.Option("", help="Boost matches from this team")):
    """Find who to connect with about a topic."""
    svc = build_services()
    matches = svc.people.match(topic, team=team, limit=5)
    if not matches:
        console.print("No matches — check data/people.yaml")
        raise typer.Exit(1)
    table = Table(title=f"Who to talk to about: {topic}")
    table.add_column("Name")
    table.add_column("Role")
    table.add_column("Team")
    table.add_column("Contact")
    table.add_column("Why")
    for m in matches:
        table.add_row(m.person.name, m.person.role, m.person.team, m.person.slack or m.person.email, m.reason)
    console.print(table)


@app.command()
def audit(thread_id: str, as_json: bool = typer.Option(False, "--json")):
    """Show the audit trail of a thread."""
    svc = build_services()
    events = svc.audit.read(thread_id)
    if not events:
        console.print(f"No audit trail for {thread_id}")
        raise typer.Exit(1)
    if as_json:
        console.print_json(json.dumps([e.model_dump() for e in events]))
        return
    table = Table(title=f"Audit trail — {thread_id}")
    table.add_column("ts")
    table.add_column("node")
    table.add_column("status")
    table.add_column("ms", justify="right")
    table.add_column("sources", justify="right")
    table.add_column("detail")
    for e in events:
        table.add_row(e.ts.split("T")[1][:12], e.node, e.status, str(e.latency_ms), str(len(e.sources)), json.dumps(e.detail)[:60])
    console.print(table)


@app.command()
def serve(host: str = "127.0.0.1", port: int = 8000):
    """Run the REST API."""
    import uvicorn

    from aiboarding.api.server import create_app

    uvicorn.run(create_app(), host=host, port=port)


@app.command()
def ui(host: str = "127.0.0.1", port: int = 8501):
    """Launch the Streamlit SPA (end-user app, alternative to Slack)."""
    import subprocess
    import sys
    from pathlib import Path

    app_path = Path(__file__).parent / "ui" / "streamlit_app.py"
    try:
        import streamlit  # noqa: F401
    except ImportError:
        console.print("[red]Streamlit not installed. Run:[/] pip install 'aiboarding[ui]'")
        raise typer.Exit(1) from None
    cmd = [
        sys.executable, "-m", "streamlit", "run", str(app_path),
        "--server.address", host, "--server.port", str(port),
    ]
    raise typer.Exit(subprocess.call(cmd))


@app.command()
def slack():
    """Start the Slack bot (Socket Mode). Requires pip install 'aiboarding[slack]'."""
    from aiboarding.integrations.slack_bot import SlackBot

    bot = SlackBot()
    if not bot.is_configured():
        console.print(
            "[red]Slack not configured.[/] Set SLACK_BOT_TOKEN (xoxb-) and "
            "SLACK_APP_TOKEN (xapp-) in .env and run: pip install 'aiboarding[slack]'"
        )
        raise typer.Exit(1)
    console.print("[green]Starting Slack bot (Socket Mode). Ctrl+C to stop.[/]")
    bot.start()


@app.command()
def info():
    """Show current configuration and store stats."""
    svc = build_services()
    s = get_settings()
    console.print_json(
        json.dumps(
            {
                "llm_provider": s.llm_provider,
                "embeddings_provider": s.embeddings_provider,
                "vectorstore_dir": str(s.vectorstore_dir),
                "docs_indexed": svc.store.count_documents(),
                "chunks": svc.store.count_chunks(),
                "people": len(svc.people.people),
            }
        )
    )


if __name__ == "__main__":
    app()
