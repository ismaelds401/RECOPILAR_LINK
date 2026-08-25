from pathlib import Path

import yaml


WORKFLOW_PATH = Path(".github/workflows/update-events.yml")


def load_workflow() -> dict[str, object]:
    return yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))


def test_update_events_workflow_has_manual_and_six_hour_triggers() -> None:
    workflow = load_workflow()
    triggers = workflow["on"]

    assert "workflow_dispatch" in triggers
    assert triggers["schedule"] == [
        {"cron": "17 */6 * * *", "timezone": "America/Lima"}
    ]


def test_update_events_workflow_uses_minimum_permissions_and_secrets() -> None:
    workflow = load_workflow()
    job = workflow["jobs"]["update-events"]

    assert workflow["permissions"] == {"contents": "read"}
    assert job["timeout-minutes"] == 20
    assert job["env"]["SUPABASE_URL"] == "${{ secrets.SUPABASE_URL }}"
    assert job["env"]["SUPABASE_SECRET_KEY"] == (
        "${{ secrets.SUPABASE_SECRET_KEY }}"
    )
    commands = "\n".join(
        str(step.get("run", "")) for step in job["steps"]
    )
    assert "python -m pytest -p no:cacheprovider" in commands
    assert "python -m backend.main --preview 0" in commands
    assert "python -m backend.scripts.check_phase5" in commands
    assert "python -m backend.scripts.check_phase10" in commands

