from app.main import jira_ticket
from app.models import JiraTicket


def test_jira_ticket_integration():
    payload = JiraTicket(
        ticket_id="PAY-1",
        title="Timeouts in payments",
        description="ERROR Timeout while calling payments API",
        priority="P1",
        reporter="sre.user",
        role="Ops",
    )
    body = jira_ticket(payload)
    assert body["ticket_id"] == "PAY-1"
    assert "Summary" in body["comment"]
