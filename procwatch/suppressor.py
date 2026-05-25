"""Alert suppression rules — skip alerts matching user-defined conditions."""

from __future__ import annotations

from dataclasses import dataclass, field
from fnmatch import fnmatch
from typing import List, Optional

from procwatch.notifier import Alert


@dataclass
class SuppressionRule:
    """A single suppression rule.  All non-None fields must match."""

    name_glob: Optional[str] = None   # e.g. "python*"
    pid: Optional[int] = None
    max_cpu: Optional[float] = None   # suppress when cpu BELOW this value
    max_mem: Optional[float] = None   # suppress when mem BELOW this value


@dataclass
class SuppressorState:
    rules: List[SuppressionRule] = field(default_factory=list)


_state: SuppressorState = SuppressorState()


def reset_suppressor() -> None:
    """Clear all suppression rules (useful in tests)."""
    global _state
    _state = SuppressorState()


def add_rule(rule: SuppressionRule) -> None:
    """Register a suppression rule."""
    _state.rules.append(rule)


def _rule_matches(rule: SuppressionRule, alert: Alert) -> bool:
    if rule.pid is not None and rule.pid != alert.pid:
        return False
    if rule.name_glob is not None and not fnmatch(alert.name, rule.name_glob):
        return False
    if rule.max_cpu is not None and alert.cpu_percent >= rule.max_cpu:
        return False
    if rule.max_mem is not None and alert.mem_mb >= rule.max_mem:
        return False
    return True


def is_suppressed(alert: Alert) -> bool:
    """Return True if *any* registered rule matches the alert."""
    return any(_rule_matches(r, alert) for r in _state.rules)


def rules_from_config(cfg_suppression: List[dict]) -> None:
    """Populate suppressor from a list of raw config dicts."""
    for entry in cfg_suppression:
        add_rule(
            SuppressionRule(
                name_glob=entry.get("name"),
                pid=entry.get("pid"),
                max_cpu=entry.get("max_cpu"),
                max_mem=entry.get("max_mem"),
            )
        )
