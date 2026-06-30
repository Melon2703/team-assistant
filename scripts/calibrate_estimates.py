#!/usr/bin/env python3
"""
Estimate calibration baseline для PM-команды.

Читает raw_tasks.json (объединённый snapshot задач команды), фильтрует шум,
вычисляет три метрики на (исполнитель × сегмент):

    1. Velocity        — distribution длительности задачи (created → completed)
                         в днях. Грубая, но всегда есть.
    2. Deadline slip   — distribution отклонения completed_at от due_on
                         (только для задач где due_on заполнен на момент закрытия).
    3. QA return rate  — доля задач с "Отправлялось на доработку" = Да.

Сегментация: assignee × Issue Type × дисциплина (TS. Команда).

Ограничения (см. canon/estimates/README.md):
    — История изменений due_date через MCP-коннектор недоступна → considered "promised"
      то значение, что лежит на момент чтения.
    — Estimate-поля почти всегда null → метрика "estimate accuracy" НЕ вычислима.
    — Не учитываем парковку (статусы Ждет/Приостановлено) — данные недоступны.

Вывод: calibration-YYYY-MM.json (по текущему месяцу) и summary в stdout.
"""

from __future__ import annotations

import json
import re
import statistics as stats
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "canon" / "estimates" / "raw_tasks.json"
OUT_JSON = ROOT / "canon" / "estimates" / f"calibration-{datetime.now(timezone.utc):%Y-%m}.json"

# --- Фильтры шума ---
NOISE_NAME_PATTERNS = [
    re.compile(r"^Ревью #"),               # CI auto PR review tasks
    re.compile(r"^История перемещения$"),  # Asana auto-generated
    re.compile(r"^TS\. Pull Requests$"),
]
# Минимальная длительность жизни — отсекаем same-second auto-tasks
MIN_LIFETIME_SECONDS = 60
# Минимум задач на (assignee × segment) для устойчивой статистики
MIN_SAMPLE = 5


def parse_iso(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def to_date_utc(s: Optional[str]) -> Optional[datetime]:
    """due_on — дата без времени, конец дня в UTC."""
    if not s:
        return None
    return datetime.fromisoformat(s).replace(
        hour=23, minute=59, second=59, tzinfo=timezone.utc
    )


def is_noise(t: dict) -> bool:
    name = t.get("name") or ""
    if any(p.match(name) for p in NOISE_NAME_PATTERNS):
        return True
    if not t.get("assignee_gid"):
        return True
    if not t.get("completed_at") or not t.get("created_at"):
        return True
    c1 = parse_iso(t["created_at"])
    c2 = parse_iso(t["completed_at"])
    if (c2 - c1).total_seconds() < MIN_LIFETIME_SECONDS:
        return True
    return False


def discipline(t: dict) -> str:
    """Дисциплина (TS. Команда) — берём первое не-null."""
    cf = t.get("custom_fields") or {}
    return cf.get("TS. Команда") or "—unknown—"


def issue_type(t: dict) -> str:
    cf = t.get("custom_fields") or {}
    return cf.get("Issue Type") or "—unspecified—"


def lifetime_days(t: dict) -> float:
    c1 = parse_iso(t["created_at"])
    c2 = parse_iso(t["completed_at"])
    return (c2 - c1).total_seconds() / 86400.0


def slip_days(t: dict) -> Optional[float]:
    """completed_at − due_on в днях. None если due_on не задан."""
    due = to_date_utc(t.get("due_on"))
    if due is None:
        return None
    completed = parse_iso(t["completed_at"])
    return (completed - due).total_seconds() / 86400.0


def percentile(xs: list[float], p: float) -> Optional[float]:
    if not xs:
        return None
    xs = sorted(xs)
    if len(xs) == 1:
        return xs[0]
    k = (len(xs) - 1) * p
    f = int(k)
    c = min(f + 1, len(xs) - 1)
    if f == c:
        return xs[f]
    return xs[f] + (xs[c] - xs[f]) * (k - f)


@dataclass
class Bucket:
    sample_size: int = 0
    velocity_days: dict = field(default_factory=dict)
    deadline: dict = field(default_factory=dict)
    qa_returns: dict = field(default_factory=dict)


def bucket_metrics(tasks: list[dict]) -> dict:
    n = len(tasks)
    velocities = [lifetime_days(t) for t in tasks]
    velocities = [v for v in velocities if v >= 0]

    slips_all: list[float] = []
    slips_with_due = 0
    on_time = 0
    late = 0
    for t in tasks:
        s = slip_days(t)
        if s is None:
            continue
        slips_with_due += 1
        slips_all.append(s)
        if -1 <= s <= 1:
            on_time += 1
        elif s > 1:
            late += 1

    qa_yes = sum(
        1
        for t in tasks
        if (t.get("custom_fields") or {}).get("Отправлялось на доработку") == "Да"
    )

    return {
        "sample_size": n,
        "velocity_days": {
            "p50": percentile(velocities, 0.5),
            "p80": percentile(velocities, 0.8),
            "p95": percentile(velocities, 0.95),
            "mean": stats.fmean(velocities) if velocities else None,
            "max": max(velocities) if velocities else None,
        },
        "deadline": {
            "tasks_with_due": slips_with_due,
            "due_coverage_pct": round(100.0 * slips_with_due / n, 1) if n else 0,
            "on_time_pct": (
                round(100.0 * on_time / slips_with_due, 1) if slips_with_due else None
            ),
            "late_pct": (
                round(100.0 * late / slips_with_due, 1) if slips_with_due else None
            ),
            "slip_p50": percentile(slips_all, 0.5),
            "slip_p80": percentile(slips_all, 0.8),
            "slip_max": max(slips_all) if slips_all else None,
        },
        "qa_returns": {
            "returned_pct": round(100.0 * qa_yes / n, 1) if n else 0,
            "returned": qa_yes,
        },
    }


def main() -> None:
    raw = json.loads(SRC.read_text(encoding="utf-8"))
    print(f"=== Loaded raw tasks: {len(raw)}")

    clean = [t for t in raw if not is_noise(t)]
    print(f"=== After noise filter: {len(clean)}  (removed {len(raw) - len(clean)})")

    snapshot_meta = {
        "snapshot_date": datetime.now(timezone.utc).isoformat(),
        "window": {
            "earliest_completed": min(t["completed_at"] for t in clean),
            "latest_completed": max(t["completed_at"] for t in clean),
        },
        "raw_count": len(raw),
        "clean_count": len(clean),
        "filters": {
            "noise_name_patterns": [p.pattern for p in NOISE_NAME_PATTERNS],
            "min_lifetime_seconds": MIN_LIFETIME_SECONDS,
            "min_sample": MIN_SAMPLE,
        },
        "data_limitations": [
            "MCP Asana коннектор не отдаёт stories → не различаем committed-due и retroactively-changed-due.",
            "Estimate-поля почти всегда null → метрика actual/estimated ratio не вычислима.",
            "Не учитываем парковку (Приостановлено / Ждет фидбека) — данные истории статуса недоступны.",
        ],
    }

    by_full: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    by_assignee: dict[str, list[dict]] = defaultdict(list)
    by_assignee_discipline: dict[tuple[str, str], list[dict]] = defaultdict(list)
    by_discipline: dict[str, list[dict]] = defaultdict(list)
    overall: list[dict] = clean

    for t in clean:
        aname = t["assignee_name"]
        d = discipline(t)
        it = issue_type(t)
        by_full[(aname, d, it)].append(t)
        by_assignee[aname].append(t)
        by_assignee_discipline[(aname, d)].append(t)
        by_discipline[d].append(t)

    out: dict[str, Any] = {
        "meta": snapshot_meta,
        "overall": bucket_metrics(overall),
        "by_discipline": {
            d: bucket_metrics(ts) for d, ts in sorted(by_discipline.items())
        },
        "by_assignee": {
            a: bucket_metrics(ts)
            for a, ts in sorted(by_assignee.items(), key=lambda x: -len(x[1]))
            if a
        },
        "by_assignee_discipline": [
            {"assignee": a, "discipline": d, **bucket_metrics(ts)}
            for (a, d), ts in sorted(
                by_assignee_discipline.items(), key=lambda x: -len(x[1])
            )
            if a and len(ts) >= MIN_SAMPLE
        ],
        "by_assignee_discipline_issue": [
            {"assignee": a, "discipline": d, "issue_type": it, **bucket_metrics(ts)}
            for (a, d, it), ts in sorted(by_full.items(), key=lambda x: -len(x[1]))
            if a and len(ts) >= MIN_SAMPLE
        ],
    }

    OUT_JSON.write_text(
        json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    print(f"\n=== Wrote {OUT_JSON}")

    print("\n=== OVERALL ===")
    o = out["overall"]
    print(
        f"sample={o['sample_size']}  velocity P50={o['velocity_days']['p50']:.1f}d "
        f"P80={o['velocity_days']['p80']:.1f}d  due_coverage={o['deadline']['due_coverage_pct']}%  "
        f"on_time={o['deadline']['on_time_pct']}%  qa_returns={o['qa_returns']['returned_pct']}%"
    )

    print("\n=== TOP ASSIGNEES (sample >= 5) ===")
    print(
        f"{'name':30s}  {'n':>3s}  {'P50':>5s}  {'P80':>5s}  "
        f"{'due%':>5s}  {'ontime%':>7s}  {'late%':>5s}  {'qaret%':>6s}"
    )
    for a, b in out["by_assignee"].items():
        if b["sample_size"] < MIN_SAMPLE:
            continue
        v = b["velocity_days"]
        d = b["deadline"]
        q = b["qa_returns"]
        ontime = d["on_time_pct"] if d["on_time_pct"] is not None else float("nan")
        late = d["late_pct"] if d["late_pct"] is not None else float("nan")
        print(
            f"{a[:30]:30s}  {b['sample_size']:>3d}  {v['p50']:>5.1f}  {v['p80']:>5.1f}  "
            f"{d['due_coverage_pct']:>5.1f}  {ontime:>7.1f}  {late:>5.1f}  {q['returned_pct']:>6.1f}"
        )


if __name__ == "__main__":
    main()
