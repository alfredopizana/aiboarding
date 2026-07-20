"""Phase 2 integrations: no-op safety without credentials + core handlers."""

from aiboarding.agent.llm import FakeLLM
from aiboarding.config import Settings
from aiboarding.integrations.email_sender import EmailSender, _markdown_to_basic_html
from aiboarding.models import UserProfile
from aiboarding.plans.generator import PlanGenerator


def test_email_not_configured_is_noop():
    sender = EmailSender(Settings(smtp_host="", smtp_user="", smtp_password=""))
    assert sender.is_configured() is False
    assert sender.send(["a@b.com"], "hi", "body") is False


def test_markdown_to_html():
    html = _markdown_to_basic_html("# Title\n\n- item one\n\nparagraph")
    assert "<h1>Title</h1>" in html
    assert "<li>item one</li>" in html


def test_email_send_plan_renders_markdown(populated_store, people, monkeypatch):
    sender = EmailSender(
        Settings(smtp_host="smtp.test", smtp_user="u", smtp_password="p")
    )
    sent = {}

    def fake_send(to, subject, body_md):
        sent.update(to=to, subject=subject, body=body_md)
        return True

    monkeypatch.setattr(sender, "send", fake_send)
    plan = PlanGenerator(populated_store, people, FakeLLM()).generate(
        UserProfile(name="Ana", role="engineer")
    )
    assert sender.send_plan(plan, ["ana@company.com"])
    assert "90-Day Success Plan" in sent["subject"]


def test_slack_handle_message_uses_agent(agent, monkeypatch):
    from aiboarding.integrations.slack_bot import SlackBot

    bot = SlackBot.__new__(SlackBot)
    bot.svc = type("S", (), {"agent": agent})()
    out = bot.handle_message("Who knows about kubernetes?", "U123", "C42", "1700.001")
    assert out["thread_id"] == "slack_C42_1700_001"
    assert out["text"]
    assert out["blocks"]
    # audit trail exists under the slack thread id
    assert agent.audit.read("slack_C42_1700_001")


def _plan_bot(agent, populated_store, people, tmp_path):
    from aiboarding.integrations.slack_bot import SlackBot
    from aiboarding.persistence import get_progress_store

    bot = SlackBot.__new__(SlackBot)
    bot.svc = type(
        "S",
        (),
        {
            "agent": agent,
            "progress": get_progress_store("sqlite", tmp_path / "slack.db"),
            "plan_generator": PlanGenerator(populated_store, people, FakeLLM()),
        },
    )()
    return bot


def test_slack_plan_command_generates_and_persists(agent, populated_store, people, tmp_path):
    bot = _plan_bot(agent, populated_store, people, tmp_path)
    out = bot.handle_message("plan", "U9", "C1", "1.1")
    assert "progreso 0/" in out["text"]
    # user + active plan now exist keyed by the slack identity
    user = bot.svc.progress.get_user("slack:U9")
    assert user is not None
    assert bot.svc.progress.get_active_plan(user.id).total > 0


def test_slack_done_command_marks_progress(agent, populated_store, people, tmp_path):
    bot = _plan_bot(agent, populated_store, people, tmp_path)
    bot.handle_message("plan", "U9", "C1", "1.1")
    out = bot.handle_message("done 1", "U9", "C1", "1.2")
    user = bot.svc.progress.get_user("slack:U9")
    assert bot.svc.progress.get_active_plan(user.id).done_count == 1
    assert "progreso 1/" in out["text"]


def test_slack_progress_without_plan_prompts(agent, populated_store, people, tmp_path):
    bot = _plan_bot(agent, populated_store, people, tmp_path)
    out = bot.handle_message("progreso", "Unew", "C1", "1.1")
    assert "plan" in out["text"].lower()
