"""Tests for procwatch.tag."""

import pytest
from procwatch.monitor import ProcessSnapshot
from procwatch import tag as tag_mod
from procwatch.tag import (
    reset_tagger,
    add_rule,
    get_tags,
    tag_snapshot,
    rules_from_config,
)


def _snap(pid: int = 1, name: str = "proc", cpu: float = 0.0, mem: float = 0.0) -> ProcessSnapshot:
    return ProcessSnapshot(pid=pid, name=name, cpu=cpu, mem=mem)


@pytest.fixture(autouse=True)
def clean():
    reset_tagger()
    yield
    reset_tagger()


def test_no_rules_returns_empty_tags():
    snap = _snap(name="python")
    assert get_tags(snap) == []


def test_tag_by_exact_name_glob():
    add_rule("scripting", name_glob="python")
    snap = _snap(name="python")
    assert "scripting" in get_tags(snap)


def test_tag_by_wildcard_glob():
    add_rule("web", name_glob="nginx*")
    assert "web" in get_tags(_snap(name="nginx"))
    assert "web" in get_tags(_snap(name="nginx-worker"))
    assert "web" not in get_tags(_snap(name="apache"))


def test_tag_by_pid():
    add_rule("special", pid=42)
    assert "special" in get_tags(_snap(pid=42))
    assert "special" not in get_tags(_snap(pid=99))


def test_multiple_tags_returned():
    add_rule("web", name_glob="nginx*")
    add_rule("monitored", name_glob="nginx*")
    tags = get_tags(_snap(name="nginx"))
    assert "web" in tags
    assert "monitored" in tags


def test_tags_deduplicated():
    add_rule("web", name_glob="nginx*")
    add_rule("web", pid=10)
    snap = _snap(pid=10, name="nginx")
    assert get_tags(snap).count("web") == 1


def test_tag_snapshot_includes_tags_field():
    add_rule("db", name_glob="postgres*")
    info = tag_snapshot(_snap(name="postgres"))
    assert "tags" in info
    assert "db" in info["tags"]


def test_add_rule_requires_at_least_one_matcher():
    with pytest.raises(ValueError):
        add_rule("oops")


def test_rules_from_config_name_glob():
    rules_from_config([{"tag": "system", "name_glob": "sys*"}])
    assert "system" in get_tags(_snap(name="syslog"))


def test_rules_from_config_pid():
    rules_from_config([{"tag": "init", "pid": 1}])
    assert "init" in get_tags(_snap(pid=1))


def test_rules_from_config_ignores_empty_name_glob():
    # name_glob present but empty string should be treated as None (pid used)
    rules_from_config([{"tag": "root", "name_glob": "", "pid": 1}])
    assert "root" in get_tags(_snap(pid=1))
