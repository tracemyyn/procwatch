"""Tests for procwatch.filter."""

import pytest

from procwatch.filter import (
    FilterRules,
    apply_filters,
    rules_from_config,
    should_include,
)
from procwatch.monitor import ProcessSnapshot


def _snap(
    name="python",
    pid=100,
    cpu=5.0,
    mem=50.0,
    user="alice",
) -> ProcessSnapshot:
    return ProcessSnapshot(
        pid=pid,
        name=name,
        cpu_percent=cpu,
        memory_mb=mem,
        username=user,
    )


# ---------------------------------------------------------------------------
# should_include
# ---------------------------------------------------------------------------

def test_empty_rules_accepts_everything():
    assert should_include(_snap(), FilterRules()) is True


def test_exclude_pid_blocks_process():
    rules = FilterRules(exclude_pids=[100])
    assert should_include(_snap(pid=100), rules) is False


def test_include_names_glob_match():
    rules = FilterRules(include_names=["py*"])
    assert should_include(_snap(name="python"), rules) is True
    assert should_include(_snap(name="nginx"), rules) is False


def test_exclude_names_glob_match():
    rules = FilterRules(exclude_names=["nginx*"])
    assert should_include(_snap(name="nginx"), rules) is False
    assert should_include(_snap(name="python"), rules) is True


def test_include_users_filter():
    rules = FilterRules(include_users=["alice"])
    assert should_include(_snap(user="alice"), rules) is True
    assert should_include(_snap(user="bob"), rules) is False


def test_min_cpu_filter():
    rules = FilterRules(min_cpu=10.0)
    assert should_include(_snap(cpu=5.0), rules) is False
    assert should_include(_snap(cpu=15.0), rules) is True


def test_min_memory_filter():
    rules = FilterRules(min_memory=100.0)
    assert should_include(_snap(mem=50.0), rules) is False
    assert should_include(_snap(mem=200.0), rules) is True


# ---------------------------------------------------------------------------
# apply_filters
# ---------------------------------------------------------------------------

def test_apply_filters_returns_matching_subset():
    snaps = [_snap(name="python"), _snap(name="nginx", pid=200)]
    rules = FilterRules(include_names=["py*"])
    result = apply_filters(snaps, rules)
    assert len(result) == 1
    assert result[0].name == "python"


def test_apply_filters_none_rules_returns_all():
    snaps = [_snap(), _snap(pid=200, name="nginx")]
    assert apply_filters(snaps, None) == snaps


# ---------------------------------------------------------------------------
# rules_from_config
# ---------------------------------------------------------------------------

def test_rules_from_config_empty_section():
    rules = rules_from_config({})
    assert rules.include_names == []
    assert rules.min_cpu == 0.0


def test_rules_from_config_full_section():
    cfg = {
        "filter": {
            "include_names": ["py*"],
            "exclude_names": ["idle"],
            "include_users": ["root"],
            "exclude_pids": [1],
            "min_cpu": 2.5,
            "min_memory": 10.0,
        }
    }
    rules = rules_from_config(cfg)
    assert rules.include_names == ["py*"]
    assert rules.exclude_names == ["idle"]
    assert rules.include_users == ["root"]
    assert rules.exclude_pids == [1]
    assert rules.min_cpu == 2.5
    assert rules.min_memory == 10.0
