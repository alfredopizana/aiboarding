"""Phase 2 — Slack bot (SPEC-006 §3).

Complete implementation behind is_configured(); requires `pip install aiboarding[slack]`
plus SLACK_BOT_TOKEN (xoxb-) and SLACK_APP_TOKEN (xapp-, Socket Mode).
"""

from __future__ import annotations

import logging
import re

from aiboarding.container import Services, build_services
from aiboarding.models import UserProfile

logger = logging.getLogger(__name__)

_DONE_RE = re.compile(r"^(?:done|hecho|complete|completar)\s+(\d+)\b", re.IGNORECASE)
_MENTION_RE = re.compile(r"^<@[^>]+>\s*")


def _section(text: str) -> dict:
    return {"type": "section", "text": {"type": "mrkdwn", "text": text}}


class SlackBot:
    def __init__(self, services: Services | None = None):
        self.svc = services or build_services()

    def is_configured(self) -> bool:
        s = self.svc.settings
        if not (s.slack_bot_token and s.slack_app_token):
            return False
        try:
            import slack_sdk  # noqa: F401

            return True
        except ImportError:
            logger.warning("slack-sdk not installed; run: pip install 'aiboarding[slack]'")
            return False

    def handle_message(self, text: str, slack_user: str, channel: str, ts: str) -> dict:
        """Core handler, transport-agnostic (also used by tests).

        Routes plan/progress commands to the ProgressStore; everything else is
        Q&A over the knowledge base. The Q&A path only touches svc.agent so it
        works even with a minimal service container.
        """
        thread_id = f"slack_{channel}_{ts}".replace(".", "_")
        cmd = _MENTION_RE.sub("", text.strip())
        low = cmd.lower()

        done_match = _DONE_RE.match(low)
        if done_match:
            return self._handle_done(slack_user, int(done_match.group(1)), thread_id)
        if low in ("plan", "mi plan", "my plan") or low.startswith(("plan ", "genera")):
            return self._handle_plan(slack_user, thread_id, generate=True)
        if low in ("progreso", "progress", "mi progreso", "my progress"):
            return self._handle_plan(slack_user, thread_id, generate=False)

        # Default: Q&A over the knowledge base.
        result = self.svc.agent.run(
            text, user=UserProfile(name=slack_user), thread_id=thread_id
        )
        blocks = [
            {"type": "section", "text": {"type": "mrkdwn", "text": result.get("answer", "")[:2900]}}
        ]
        citations = result.get("citations", [])
        if citations:
            links = "\n".join(f"• <{c.uri}|{c.title}>" for c in citations[:5])
            blocks.append(
                {"type": "context", "elements": [{"type": "mrkdwn", "text": f"*Sources:*\n{links}"}]}
            )
        return {"thread_id": thread_id, "text": result.get("answer", ""), "blocks": blocks}

    # ── plan / progress commands ────────────────────────────────────────────
    def _identity(self, slack_user: str) -> tuple[str, str]:
        """Resolve (identity, display_name). Prefer real email so the Slack user
        shares plan/progress with the web UI; fall back to a slack: id."""
        web = getattr(self, "_web", None)
        if web is not None:
            try:
                info = web.users_info(user=slack_user)["user"]
                name = info.get("real_name") or info.get("name") or slack_user
                email = (info.get("profile") or {}).get("email")
                return (email or f"slack:{slack_user}", name)
            except Exception as exc:  # noqa: BLE001
                logger.warning("users.info failed (%s); using slack id as identity", exc)
        return (f"slack:{slack_user}", slack_user)

    def _profile_for(self, identity: str, name: str) -> UserProfile:
        saved = self.svc.progress.get_user(identity)
        if saved:
            return UserProfile(
                name=saved.name or name, role=saved.role, team=saved.team,
                start_date=saved.start_date,
            )
        return UserProfile(name=name)

    def _handle_plan(self, slack_user: str, thread_id: str, generate: bool) -> dict:
        identity, name = self._identity(slack_user)
        profile = self._profile_for(identity, name)
        user = self.svc.progress.upsert_user(profile, identity)
        plan = self.svc.progress.get_active_plan(user.id)
        if plan is None and generate:
            plan = self.svc.progress.save_plan(user.id, self.svc.plan_generator.generate(profile))
        if plan is None:
            text = "Aún no tienes un plan. Escribe *plan* para generarlo."
            return {"thread_id": thread_id, "text": text, "blocks": [_section(text)]}
        return {"thread_id": thread_id, "text": self._plan_text(plan), "blocks": self._plan_blocks(plan)}

    def _handle_done(self, slack_user: str, n: int, thread_id: str) -> dict:
        identity, name = self._identity(slack_user)
        user = self.svc.progress.get_user(identity)
        plan = self.svc.progress.get_active_plan(user.id) if user else None
        if plan is None:
            text = "No tienes un plan. Escribe *plan* primero."
            return {"thread_id": thread_id, "text": text, "blocks": [_section(text)]}
        if not 1 <= n <= len(plan.items):
            text = f"Número fuera de rango (1-{len(plan.items)})."
            return {"thread_id": thread_id, "text": text, "blocks": [_section(text)]}
        item = plan.items[n - 1]
        self.svc.progress.set_item_done(item.id, not item.done)
        plan = self.svc.progress.get_active_plan(user.id)
        return {"thread_id": thread_id, "text": self._plan_text(plan), "blocks": self._plan_blocks(plan)}

    @staticmethod
    def _plan_text(plan) -> str:
        return f"Plan de 90 días — progreso {plan.done_count}/{plan.total} ({plan.progress:.0%})"

    def _plan_blocks(self, plan) -> list[dict]:
        lines = [f"*{self._plan_text(plan)}*"]
        current_phase = None
        for i, it in enumerate(plan.items, 1):
            if it.phase != current_phase:
                current_phase = it.phase
                lines.append(f"\n*{it.phase}*")
            lines.append(f"{'✅' if it.done else '⬜'} `{i}` {it.title}")
        lines.append("\n_Marca completado con_ `done <n>`")
        return [_section("\n".join(lines)[:2900])]

    def start(self) -> None:
        """Start Socket Mode listener (blocking)."""
        if not self.is_configured():
            logger.error("Slack not configured (SLACK_BOT_TOKEN / SLACK_APP_TOKEN). No-op.")
            return
        from slack_sdk import WebClient
        from slack_sdk.socket_mode import SocketModeClient
        from slack_sdk.socket_mode.request import SocketModeRequest
        from slack_sdk.socket_mode.response import SocketModeResponse

        web = WebClient(token=self.svc.settings.slack_bot_token)
        self._web = web  # used by _identity to resolve the user's email
        socket = SocketModeClient(app_token=self.svc.settings.slack_app_token, web_client=web)

        def handle(client: SocketModeClient, req: SocketModeRequest) -> None:
            if req.type != "events_api":
                return
            client.send_socket_mode_response(SocketModeResponse(envelope_id=req.envelope_id))
            event = req.payload.get("event", {})
            if event.get("type") not in ("app_mention", "message") or event.get("bot_id"):
                return
            out = self.handle_message(
                text=event.get("text", ""),
                slack_user=event.get("user", "unknown"),
                channel=event.get("channel", ""),
                ts=event.get("ts", ""),
            )
            web.chat_postMessage(
                channel=event["channel"],
                thread_ts=event.get("thread_ts", event.get("ts")),
                text=out["text"][:3000],
                blocks=out["blocks"],
            )

        socket.socket_mode_request_listeners.append(handle)
        logger.info("Slack bot connected (Socket Mode). Ctrl+C to stop.")
        socket.connect()
        import signal

        signal.pause()
