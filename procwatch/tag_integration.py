"""Integration helpers: apply tags during a scan and emit tagged alerts."""

from __future__ import annotations

from typing import List, Optional

from procwatch.config import Config
from procwatch.monitor import ProcessSnapshot
from procwatch.tag import get_tags, rules_from_config, reset_tagger
from procwatch.notifier import Alert


def init_tags_from_config(cfg: Config) -> None:
    """Populate tagger rules from the Config object if a 'tags' key is present."""
    reset_tagger()
    tag_defs = getattr(cfg, "tags", None)
    if tag_defs and isinstance(tag_defs, list):
        rules_from_config(tag_defs)  # type: ignore[arg-type]


def enrich_alert_with_tags(alert: Alert, snap: ProcessSnapshot) -> Alert:
    """Return a new Alert whose message is prefixed with the process tags."""
    tags = get_tags(snap)
    if not tags:
        return alert
    tag_str = "[" + ", ".join(tags) + "] "
    return Alert(
        pid=alert.pid,
        name=alert.name,
        cpu=alert.cpu,
        mem=alert.mem,
        message=tag_str + alert.message,
    )


def tagged_snapshots(snaps: List[ProcessSnapshot]) -> List[dict]:
    """Return a list of dicts enriching each snapshot with its tags."""
    result = []
    for snap in snaps:
        result.append(
            {
                "pid": snap.pid,
                "name": snap.name,
                "cpu": snap.cpu,
                "mem": snap.mem,
                "tags": get_tags(snap),
            }
        )
    return result


def filter_by_tag(snaps: List[ProcessSnapshot], tag: str) -> List[ProcessSnapshot]:
    """Return only snapshots that carry the given tag."""
    return [s for s in snaps if tag in get_tags(s)]
