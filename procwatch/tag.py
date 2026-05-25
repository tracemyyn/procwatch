"""Process tagging: assign user-defined labels to processes by name glob or pid."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from procwatch.monitor import ProcessSnapshot


@dataclass
class TagRule:
    tag: str
    name_glob: Optional[str] = None
    pid: Optional[int] = None


@dataclass
class TaggerState:
    rules: List[TagRule] = field(default_factory=list)


_state: TaggerState = TaggerState()


def reset_tagger() -> None:
    """Clear all tag rules (useful in tests)."""
    _state.rules.clear()


def add_rule(tag: str, *, name_glob: Optional[str] = None, pid: Optional[int] = None) -> TagRule:
    """Register a new tagging rule. At least one of name_glob or pid must be set."""
    if name_glob is None and pid is None:
        raise ValueError("TagRule requires at least one of name_glob or pid")
    rule = TagRule(tag=tag, name_glob=name_glob, pid=pid)
    _state.rules.append(rule)
    return rule


def _rule_matches(rule: TagRule, snap: ProcessSnapshot) -> bool:
    if rule.pid is not None and rule.pid == snap.pid:
        return True
    if rule.name_glob is not None and fnmatch.fnmatch(snap.name, rule.name_glob):
        return True
    return False


def get_tags(snap: ProcessSnapshot) -> List[str]:
    """Return all tags that match a snapshot, preserving insertion order, deduped."""
    seen: Dict[str, None] = {}
    for rule in _state.rules:
        if _rule_matches(rule, snap):
            seen[rule.tag] = None
    return list(seen.keys())


def tag_snapshot(snap: ProcessSnapshot) -> Dict[str, object]:
    """Return a dict with snapshot fields plus a 'tags' list."""
    return {
        "pid": snap.pid,
        "name": snap.name,
        "cpu": snap.cpu,
        "mem": snap.mem,
        "tags": get_tags(snap),
    }


def rules_from_config(cfg_tags: List[Dict[str, object]]) -> None:
    """Populate tagger rules from a list of config dicts."""
    for entry in cfg_tags:
        add_rule(
            str(entry["tag"]),
            name_glob=entry.get("name_glob") or None,  # type: ignore[arg-type]
            pid=int(entry["pid"]) if "pid" in entry else None,
        )
