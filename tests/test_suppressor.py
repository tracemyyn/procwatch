"""Tests for procwatch.suppressor."""

import pytest

from procwatch.notifier import Alert
from procwatch.suppressor import (
    SuppressionRule,
    add_rule,
    is_suppressed,
    reset_suppressor,
    rules_from_config,
)


@pytest.fixture(autouse=True)
def clean():
    reset_suppressor()
    yield
    reset_suppressor()


def _alert(name="bash", pid=100, cpu=50.0, mem=200.0) -> Alert:
    return Alert(pid=pid, name=name, cpu_percent=cpu, mem_mb=mem, message="")


def test_no_rules_never_suppresses():
    assert is_suppressed(_alert()) is False


def test_suppress_by_exact_pid():
    add_rule(SuppressionRule(pid=100))
    assert is_suppressed(_alert(pid=100)) is True


def test_pid_rule_does_not_match_other_pid():
    add_rule(SuppressionRule(pid=999))
    assert is_suppressed(_alert(pid=100)) is False


def test_suppress_by_name_glob():
    add_rule(SuppressionRule(name_glob="py*"))
    assert is_suppressed(_alert(name="python3")) is True


def test_name_glob_no_match():
    add_rule(SuppressionRule(name_glob="java*"))
    assert is_suppressed(_alert(name="python3")) is False


def test_suppress_when_cpu_below_threshold():
    # max_cpu=60 means suppress when cpu < 60
    add_rule(SuppressionRule(max_cpu=60.0))
    assert is_suppressed(_alert(cpu=30.0)) is True


def test_no_suppress_when_cpu_at_or_above_threshold():
    add_rule(SuppressionRule(max_cpu=60.0))
    assert is_suppressed(_alert(cpu=60.0)) is False


def test_suppress_when_mem_below_threshold():
    add_rule(SuppressionRule(max_mem=500.0))
    assert is_suppressed(_alert(mem=100.0)) is True


def test_combined_rule_all_fields_must_match():
    add_rule(SuppressionRule(name_glob="bash", pid=100))
    # wrong pid — should NOT be suppressed
    assert is_suppressed(_alert(name="bash", pid=200)) is False
    # correct pid and name — suppressed
    assert is_suppressed(_alert(name="bash", pid=100)) is True


def test_first_matching_rule_is_sufficient():
    add_rule(SuppressionRule(pid=1))
    add_rule(SuppressionRule(name_glob="bash"))
    assert is_suppressed(_alert(name="bash", pid=999)) is True


def test_rules_from_config_populates_rules():
    cfg = [
        {"name": "chrome*", "max_cpu": 80.0},
        {"pid": 42},
    ]
    rules_from_config(cfg)
    assert is_suppressed(_alert(name="chrome_helper", cpu=20.0)) is True
    assert is_suppressed(_alert(pid=42)) is True


def test_reset_clears_rules():
    add_rule(SuppressionRule(pid=100))
    reset_suppressor()
    assert is_suppressed(_alert(pid=100)) is False
