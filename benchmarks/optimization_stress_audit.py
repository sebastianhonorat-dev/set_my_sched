import json
from dataclasses import asdict, dataclass
from itertools import combinations
from pathlib import Path

from schedule import Placement, Schedule
from scoring import Judge
from time_rep import to_slot

from benchmarks.optimization_stress import (
    SCENARIO_NAME,
    build_events,
    scenario_checksum,
)


ROOT = Path(__file__).parents[1]
AUDIT_DIR = ROOT / "docs" / "benchmark_reports" / "audit"


SWAP_CODES = (
    (0, 0, 0, 0),
    (1, 1, 1, 1),
    (1, 1, 0, 0),
    (0, 0, 1, 1),
    (1, 0, 1, 0),
    (0, 1, 0, 1),
    (1, 0, 0, 1),
    (0, 1, 1, 0),
    (1, 1, 1, 0),
    (0, 0, 0, 1),
)

WORKOUT_HOURS = (700, 630, 700, 630, 700, 630, 700, 630, 700, 630)
STUDY_HOURS = (2000, 1800, 2200, 1900, 2100, 1800, 2200, 2000, 1900, 2100)
LANGUAGE_HOURS = (700, 600, 700, 600, 700, 600, 700, 600, 700, 600)

PAIR_LAYOUTS = (
    ("Focus Block", "Reading", (0, 900), (0, 1400)),
    ("Project Lab", "Personal Project", (1, 800), (1, 1500)),
    ("Administration", "Music Practice", (3, 1000), (3, 1700)),
    ("Client Review", "Social Event", (4, 900), (4, 1800)),
)


@dataclass(frozen=True)
class AuditedSchedule:
    audit_id: str
    score: float
    placements: dict[str, list[int]]


@dataclass(frozen=True)
class AuditResult:
    scenario: str
    checksum: str
    schedules_verified: int
    minimum_changed_occurrences: int
    minimum_displacement_slots: int
    lowest_score: float
    highest_score: float
    score_spread_percent: float
    schedules: tuple[AuditedSchedule, ...]


def _clock_to_parts(clock: int) -> tuple[int, int]:
    return clock // 100, clock % 100


def _add(schedule: Schedule, event, day: int, clock: int) -> None:
    hour, minute = _clock_to_parts(clock)
    if not schedule.place(Placement(event, to_slot(day, hour, minute))):
        raise RuntimeError(f"Audit placement failed for {event.name}")


def build_audit_schedule(index: int) -> tuple[Schedule, list]:
    events = build_events()
    by_name = {event.name: event for event in events}
    schedule = Schedule()

    for day in (0, 2, 5):
        _add(schedule, by_name["Workout"], day, WORKOUT_HOURS[index])
        _add(schedule, by_name["Study"], day, STUDY_HOURS[index])
    _add(schedule, by_name["Medical Appointment"], 2, 1300)
    for day in (1, 3, 5):
        _add(schedule, by_name["Meal Preparation"], day, 1600 if day == 5 else 1800)
    for day in (0, 1, 3, 4):
        language_start = 815 if day == 0 else LANGUAGE_HOURS[index]
        _add(schedule, by_name["Language Practice"], day, language_start)

    for bit, (first_name, second_name, first_slot, second_slot) in zip(
        SWAP_CODES[index], PAIR_LAYOUTS
    ):
        first_target, second_target = (
            (first_slot, second_slot) if bit == 0 else (second_slot, first_slot)
        )
        _add(schedule, by_name[first_name], *first_target)
        _add(schedule, by_name[second_name], *second_target)
    return schedule, events


def placement_map(schedule: Schedule) -> dict[str, list[int]]:
    return {
        event.name: sorted(placement.start for placement in placements)
        for event, placements in sorted(
            schedule.placements.items(), key=lambda item: item[0].event_id
        )
    }


def layout_distance(first: dict[str, list[int]], second: dict[str, list[int]]) -> tuple[int, int]:
    changed = 0
    displacement = 0
    for name in first:
        for first_slot, second_slot in zip(first[name], second[name]):
            if first_slot != second_slot:
                changed += 1
                displacement += abs(first_slot - second_slot)
    return changed, displacement


def run_audit(validate_schedule) -> AuditResult:
    audited = []
    for index in range(len(SWAP_CODES)):
        schedule, events = build_audit_schedule(index)
        failures = validate_schedule(schedule)
        if failures:
            raise RuntimeError(f"audit-{index + 1:02d} invalid: " + "; ".join(failures))
        if sum(len(items) for items in schedule.placements.values()) != sum(
            event.freq for event in events
        ):
            raise RuntimeError(f"audit-{index + 1:02d} is incomplete")
        audited.append(
            AuditedSchedule(
                audit_id=f"audit-{index + 1:02d}",
                score=Judge().score(schedule, set(events)).total,
                placements=placement_map(schedule),
            )
        )

    distances = [
        layout_distance(first.placements, second.placements)
        for first, second in combinations(audited, 2)
    ]
    minimum_changed = min(changed for changed, _ in distances)
    minimum_displacement = min(displacement for _, displacement in distances)
    if minimum_changed < 2 or minimum_displacement < 32:
        raise RuntimeError("Audited schedules are not meaningfully distinct")

    scores = [item.score for item in audited]
    low, high = min(scores), max(scores)
    spread = (high - low) / high * 100
    if spread < 20:
        raise RuntimeError(f"Score spread {spread:.2f}% is below the 20% gate")

    return AuditResult(
        scenario=SCENARIO_NAME,
        checksum=scenario_checksum(),
        schedules_verified=len(audited),
        minimum_changed_occurrences=minimum_changed,
        minimum_displacement_slots=minimum_displacement,
        lowest_score=low,
        highest_score=high,
        score_spread_percent=spread,
        schedules=tuple(audited),
    )


def write_audit_report(result: AuditResult) -> tuple[Path, Path]:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = AUDIT_DIR / f"{result.scenario}_audit.json"
    markdown_path = AUDIT_DIR / f"{result.scenario}_audit.md"
    json_path.write_text(json.dumps(asdict(result), indent=2) + "\n", encoding="ascii")

    sections = []
    for schedule in result.schedules:
        placements = "\n".join(
            f"- {name}: {', '.join(map(str, starts))}"
            for name, starts in schedule.placements.items()
        )
        sections.append(
            f"### {schedule.audit_id}\n\nScore: `{schedule.score:.6f}`\n\n{placements}"
        )
    markdown_path.write_text(
        f"""# Optimization Stress Audit

- Scenario: `{result.scenario}`
- SHA-256: `{result.checksum}`
- Complete valid schedules: {result.schedules_verified}
- Minimum changed occurrences between any pair: {result.minimum_changed_occurrences}
- Minimum aggregate displacement: {result.minimum_displacement_slots} slots
- Lowest score: {result.lowest_score:.6f}
- Highest score: {result.highest_score:.6f}
- Score spread: {result.score_spread_percent:.2f}%

## Verified Schedules

{chr(10).join(sections)}
""",
        encoding="ascii",
    )
    return json_path, markdown_path
