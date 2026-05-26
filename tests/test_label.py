"""Tests for procwatch.label and procwatch.label_reporter."""

import pytest

from procwatch.label import (
    reset_label_config,
    configure_labels,
    get_label,
    label_for_cpu,
    label_for_mem,
    annotate,
)
from procwatch.label_reporter import (
    format_label_line,
    format_label_table,
    format_label_summary,
)


@pytest.fixture(autouse=True)
def clean():
    reset_label_config()
    yield
    reset_label_config()


# ---------------------------------------------------------------------------
# get_label
# ---------------------------------------------------------------------------

def test_get_label_info():
    assert get_label("info") == "INFO"


def test_get_label_warning():
    assert get_label("warning") == "WARNING"


def test_get_label_critical():
    assert get_label("critical") == "CRITICAL"


def test_get_label_unknown_returns_unknown():
    assert get_label("banana") == "UNKNOWN"


def test_get_label_case_insensitive():
    assert get_label("WARNING") == "WARNING"
    assert get_label("Critical") == "CRITICAL"


# ---------------------------------------------------------------------------
# configure_labels
# ---------------------------------------------------------------------------

def test_configure_labels_overrides_mapping():
    configure_labels({"info": "LOW", "critical": "HIGH"})
    assert get_label("info") == "LOW"
    assert get_label("critical") == "HIGH"
    assert get_label("warning") == "WARNING"  # unchanged


def test_configure_labels_custom_unknown():
    configure_labels({}, unknown_label="N/A")
    assert get_label("nope") == "N/A"


def test_reset_restores_defaults():
    configure_labels({"info": "FINE"})
    reset_label_config()
    assert get_label("info") == "INFO"


# ---------------------------------------------------------------------------
# label_for_cpu / label_for_mem
# ---------------------------------------------------------------------------

def test_label_for_cpu_below_warn():
    assert label_for_cpu(30.0) == "INFO"


def test_label_for_cpu_at_warn():
    assert label_for_cpu(70.0) == "WARNING"


def test_label_for_cpu_at_crit():
    assert label_for_cpu(90.0) == "CRITICAL"


def test_label_for_mem_below_warn():
    assert label_for_mem(100.0) == "INFO"


def test_label_for_mem_warn_range():
    assert label_for_mem(800.0) == "WARNING"


def test_label_for_mem_critical():
    assert label_for_mem(2000.0) == "CRITICAL"


# ---------------------------------------------------------------------------
# annotate
# ---------------------------------------------------------------------------

def test_annotate_uses_provided_level():
    result = annotate({"pid": 1}, level="critical")
    assert result["label"] == "CRITICAL"
    assert result["pid"] == 1


def test_annotate_reads_level_from_dict():
    result = annotate({"level": "warning", "name": "proc"})
    assert result["label"] == "WARNING"


def test_annotate_does_not_mutate_original():
    original = {"level": "info"}
    annotate(original)
    assert "label" not in original


# ---------------------------------------------------------------------------
# label_reporter
# ---------------------------------------------------------------------------

def test_format_label_line_contains_pid_and_label():
    line = format_label_line(42, "myproc", "warning")
    assert "42" in line
    assert "myproc" in line
    assert "WARNING" in line


def test_format_label_table_shows_header():
    table = format_label_table([])
    assert "PID" in table
    assert "LABEL" in table


def test_format_label_table_empty_shows_placeholder():
    table = format_label_table([])
    assert "no entries" in table


def test_format_label_table_lists_entries():
    entries = [
        {"pid": 1, "name": "alpha", "level": "info"},
        {"pid": 2, "name": "beta", "level": "critical"},
    ]
    table = format_label_table(entries)
    assert "alpha" in table
    assert "CRITICAL" in table


def test_format_label_summary_counts_labels():
    entries = [
        {"pid": 1, "name": "a", "level": "info"},
        {"pid": 2, "name": "b", "level": "info"},
        {"pid": 3, "name": "c", "level": "critical"},
    ]
    summary = format_label_summary(entries)
    assert "INFO: 2" in summary
    assert "CRITICAL: 1" in summary


def test_format_label_summary_empty():
    assert format_label_summary([]) == "No labelled alerts."
