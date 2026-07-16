"""Phase 2 — Email sender via SMTP (SPEC-006 §4). Stdlib only."""

from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from aiboarding.config import Settings, get_settings
from aiboarding.models import SuccessPlan

logger = logging.getLogger(__name__)


def _markdown_to_basic_html(md: str) -> str:
    lines = []
    for line in md.splitlines():
        if line.startswith("# "):
            lines.append(f"<h1>{line[2:]}</h1>")
        elif line.startswith("## "):
            lines.append(f"<h2>{line[3:]}</h2>")
        elif line.startswith("- "):
            lines.append(f"<li>{line[2:]}</li>")
        elif line.strip():
            lines.append(f"<p>{line}</p>")
    return f"<html><body>{''.join(lines)}</body></html>"


class EmailSender:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def is_configured(self) -> bool:
        s = self.settings
        return bool(s.smtp_host and s.smtp_user and s.smtp_password)

    def send(self, to: list[str], subject: str, body_md: str) -> bool:
        if not self.is_configured():
            logger.warning("SMTP not configured — email not sent (no-op).")
            return False
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.settings.email_from
        msg["To"] = ", ".join(to)
        msg.attach(MIMEText(body_md, "plain"))
        msg.attach(MIMEText(_markdown_to_basic_html(body_md), "html"))
        with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port) as server:
            server.starttls()
            server.login(self.settings.smtp_user, self.settings.smtp_password)
            server.sendmail(self.settings.email_from, to, msg.as_string())
        logger.info("Email sent to %s: %s", to, subject)
        return True

    def send_plan(self, plan: SuccessPlan, to: list[str]) -> bool:
        subject = f"90-Day Success Plan — {plan.user.name}"
        return self.send(to, subject, plan.to_markdown())
