"""Tests for procwatch.payload_builder."""

from __future__ import annotations

import platform

import pytest

from procwatch.notifier import Alert
from procwatch.payload_builder import (
    build_base_payload,
    build_rich_payload,
    payload_to_slack,
)


@pytest.fixture()
def alert() -> Alert:
    return Alert(pid=42, name="myapp", cpu_percent=55.0, mem_percent=30.0, message="cpu spike")


def test_base_payload_contains_pid(alert: Alert) -> None:
    p = build_base_payload(alert)
    assert p["pid"] == 42


def test_base_payload_contains_name(alert: Alert) -> None:
    p = build_base_payload(alert)
    assert p["name"] == "myapp"


def test_base_payload_contains_cpu(alert: Alert) -> None:
    p = build_base_payload(alert)
    assert p["cpu_percent"] == 55.0


def test_base_payload_contains_mem(alert: Alert) -> None:
    p = build_base_payload(alert)
    assert p["mem_percent"] == 30.0


def test_base_payload_contains_message(alert: Alert) -> None:
    p = build_base_payload(alert)
    assert p["message"] == "cpu spike"


def test_base_payload_has_host(alert: Alert) -> None:
    p = build_base_payload(alert)
    assert p["host"] == platform.node()


def test_base_payload_has_timestamp(alert: Alert) -> None:
    p = build_base_payload(alert)
    assert "timestamp" in p and "T" in p["timestamp"]


def test_base_payload_has_version(alert: Alert) -> None:
    p = build_base_payload(alert)
    assert p["version"] == "1.0"


def test_rich_payload_default_severity(alert: Alert) -> None:
    p = build_rich_payload(alert)
    assert p["severity"] == "info"


def test_rich_payload_custom_severity(alert: Alert) -> None:
    p = build_rich_payload(alert, severity="critical")
    assert p["severity"] == "critical"


def test_rich_payload_tags_empty_by_default(alert: Alert) -> None:
    p = build_rich_payload(alert)
    assert p["tags"] == []


def test_rich_payload_tags_included(alert: Alert) -> None:
    p = build_rich_payload(alert, tags=["web", "prod"])
    assert p["tags"] == ["web", "prod"]


def test_rich_payload_extra_merged(alert: Alert) -> None:
    p = build_rich_payload(alert, extra={"env": "staging"})
    assert p["env"] == "staging"


def test_slack_payload_has_attachments(alert: Alert) -> None:
    p = payload_to_slack(alert)
    assert "attachments" in p and len(p["attachments"]) == 1


def test_slack_payload_severity_info_for_low_values(alert: Alert) -> None:
    p = payload_to_slack(alert)
    assert p["attachments"][0]["color"] == "#36a64f"


def test_slack_payload_severity_critical_for_high_cpu() -> None:
    a = Alert(pid=1, name="hog", cpu_percent=95.0, mem_percent=10.0, message="high")
    p = payload_to_slack(a)
    assert p["attachments"][0]["color"] == "#ff0000"


def test_slack_payload_tags_shown(alert: Alert) -> None:
    p = payload_to_slack(alert, tags=["db"])
    fields = {f["title"]: f["value"] for f in p["attachments"][0]["fields"]}
    assert fields["Tags"] == "db"
