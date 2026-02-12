from app.main import slack_events
from app.models import SlackEvent


def test_slack_uc1_route():
    payload = SlackEvent(
        user_id="U1",
        text="/uc1 Summarize handover risks for payments",
        channel="C1",
        role="Ops",
    )
    body = slack_events(payload)
    assert "Architecture Summary" in body["text"]


def test_slack_unknown_command():
    payload = SlackEvent(
        user_id="U2",
        text="hello",
        channel="C2",
        role="Employee",
    )
    body = slack_events(payload)
    assert "Usage" in body["text"]
