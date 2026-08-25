from pathlib import Path

import yaml


WORKFLOW_PATH = Path(".github/workflows/send-daily-digest.yml")


def load_workflow() -> dict[str, object]:
    return yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))


def test_digest_workflow_is_daily_and_manually_previewable() -> None:
    workflow = load_workflow()
    triggers = workflow["on"]

    assert triggers["schedule"] == [
        {"cron": "23 8 * * *", "timezone": "America/Lima"}
    ]
    assert triggers["workflow_dispatch"]["inputs"]["dry_run"]["default"] is True


def test_digest_workflow_uses_secrets_and_prevents_parallel_sends() -> None:
    workflow = load_workflow()
    job = workflow["jobs"]["daily-digest"]

    assert workflow["permissions"] == {"contents": "read"}
    assert workflow["concurrency"]["group"] == "daily-event-digest"
    assert job["env"]["GMAIL_APP_PASSWORD"] == "${{ secrets.GMAIL_APP_PASSWORD }}"
    assert job["env"]["DIGEST_RECIPIENT_EMAILS"] == (
        "${{ secrets.DIGEST_RECIPIENT_EMAILS }}"
    )
    commands = "\n".join(str(step.get("run", "")) for step in job["steps"])
    assert "send_daily_digest --dry-run" in commands
    assert "send_daily_digest --preview" in commands

