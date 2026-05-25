"""Tests for procwatch.suppressor_reporter."""

from procwatch.suppressor import SuppressionRule
from procwatch.suppressor_reporter import (
    format_suppressed_line,
    format_suppression_table,
)


def test_format_table_empty():
    result = format_suppression_table([])
    assert "No suppression rules" in result


def test_format_table_shows_header():
    rules = [SuppressionRule(name_glob="python*")]
    result = format_suppression_table(rules)
    assert "Active suppression rules" in result


def test_format_table_shows_name_glob():
    rules = [SuppressionRule(name_glob="java*")]
    result = format_suppression_table(rules)
    assert "java*" in result


def test_format_table_shows_pid():
    rules = [SuppressionRule(pid=1234)]
    result = format_suppression_table(rules)
    assert "1234" in result


def test_format_table_shows_max_cpu():
    rules = [SuppressionRule(max_cpu=75.0)]
    result = format_suppression_table(rules)
    assert "75.0" in result


def test_format_table_shows_max_mem():
    rules = [SuppressionRule(max_mem=512.0)]
    result = format_suppression_table(rules)
    assert "512.0" in result


def test_format_table_multiple_rules():
    rules = [
        SuppressionRule(pid=1),
        SuppressionRule(name_glob="node*"),
    ]
    result = format_suppression_table(rules)
    assert "[0]" in result
    assert "[1]" in result


def test_format_suppressed_line_contains_fields():
    line = format_suppressed_line(name="bash", pid=42, reason="pid match")
    assert "bash" in line
    assert "42" in line
    assert "pid match" in line
    assert "SUPPRESSED" in line
