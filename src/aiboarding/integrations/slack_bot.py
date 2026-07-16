"""Phase 2 — Slack bot (SPEC-006 §3).

Complete implementation behind is_configured(); requires `pip install aiboarding[slack]`
plus SLACK_BOT_TOKEN (xoxb-) and SLACK_APP_TOKEN (xapp-, Socket Mode).
"""

from __future__ import annotations

import logging

from aiboarding.container import Services, build_services
from aiboarding.models import UserProfile

logger = logging.getLogger(__name__)


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
        """Core handler, transport-agnostic (also used by tests)."""
        thread_id = f"slack_{channel}_{ts}".replace(".", "_")
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
