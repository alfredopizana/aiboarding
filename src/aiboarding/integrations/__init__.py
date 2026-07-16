"""Phase 2 integrations: Slack bot and email sender."""

from aiboarding.integrations.email_sender import EmailSender
from aiboarding.integrations.slack_bot import SlackBot

__all__ = ["EmailSender", "SlackBot"]
