import argparse
import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from algo.greedy_boy import GreedyScheduler
from schedule import Schedule
from scoring import Judge
from time_rep import to_slot, weekly_slots

from benchmarks.challenging_week import SCENARIO_NAME, build_events, scenario_summary


ROOT = Path(__file__).parents[1]
REPORT_DIR = ROOT / "docs" / "benchmark_reports"


@dataclass
class BenchmarkResult:
    scenario: str
    algorithm: str
    generated_at_utc: str
    status: str
    valid: bool
    runtime_seconds: float
    candidate_placements_evaluated: int
    events_requested: int
    events_scheduled: int
    events_failed: int
    required_events_completed: int
    optional_events_completed: int
    occurrences_requested: int
    occurrences_scheduled: int
    occupancy_percent: float
    final_schedule_score: float
    failures: list[str]
    validation_failures: list[str]


class TrackingGreedyScheduler(GreedyScheduler):
    def __init__(self, schedule, events):
        super().__init__(schedule, events)
        self.candidates_evaluated = 0

    def return_rank_candidates(self, event, candidate_slot):
        self.candidates_evaluated += len(candidate_slot)
        return super().return_rank_candidates(event, candidate_slot)


def validate_schedule(schedule: Schedule) -> list[str]:
    failures = []
    seen_slots = set()
    for event, placements in schedule.placements.items():
        if len(placements) > event.freq:
            failures.append(f"{event.name}: frequency exceeded")

        ordered = sorted(placements, key=lambda placement: placement.start)
        for placement in ordered:
            occupied = set(range(placement.start, placement.end + 1))
            if seen_slots.intersection(occupied):
                failures.append(f"{event.name}: placement overlaps another event")
            seen_slots.update(occupied)

            inside_window = any(
                placement.start >= to_slot(day, start // 100, start % 100)
                and placement.end <= to_slot(day, end // 100, end % 100)
                for day, start, end in event.time_window
            )
            if not inside_window:
                failures.append(f"{event.name}: placement is outside its allowed window")

        for earlier, later in zip(ordered, ordered[1:]):
            gap_days = (later.start - earlier.start) // 96
            if gap_days < event.min_gap_days:
                failures.append(
                    f"{event.name}: {gap_days}-day gap is below minimum "
                    f"{event.min_gap_days}"
                )
    return failures


def run_greedy(events) -> tuple[Schedule, str, list[str], float, int]:
    scheduler = TrackingGreedyScheduler(Schedule(), events)
    failures = []
    status = "success"
    started = time.perf_counter()

    for event in sorted(events, key=lambda item: item.priority, reverse=True):
        placement_result = scheduler.place(event)
        if placement_result.status == "success":
            continue
        failures.append(f"{event.name}: " + "; ".join(placement_result.reasons))
        status = placement_result.status
        if event.hard_flag or placement_result.status == "corrupt":
            break

    runtime = time.perf_counter() - started
    return scheduler.schedule, status, failures, runtime, scheduler.candidates_evaluated


ALGORITHMS = {"greedy": run_greedy}


def benchmark(algorithm: str) -> BenchmarkResult:
    events = build_events()
    schedule, status, failures, runtime, candidates = ALGORITHMS[algorithm](events)
    validation_failures = validate_schedule(schedule)
    scheduled_events = set(schedule.placements)
    score = Judge().score(schedule, set(events)).total
    summary = scenario_summary()

    return BenchmarkResult(
        scenario=SCENARIO_NAME,
        algorithm=algorithm,
        generated_at_utc=datetime.now(timezone.utc).isoformat(),
        status=status,
        valid=not validation_failures,
        runtime_seconds=runtime,
        candidate_placements_evaluated=candidates,
        events_requested=len(events),
        events_scheduled=len(scheduled_events),
        events_failed=len(events) - len(scheduled_events),
        required_events_completed=sum(event.hard_flag for event in scheduled_events),
        optional_events_completed=sum(not event.hard_flag for event in scheduled_events),
        occurrences_requested=int(summary["requested_occurrences"]),
        occurrences_scheduled=sum(len(items) for items in schedule.placements.values()),
        occupancy_percent=schedule.occupancy() * 100,
        final_schedule_score=score,
        failures=failures,
        validation_failures=validation_failures,
    )


def write_report(result: BenchmarkResult) -> tuple[Path, Path]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stem = f"{result.algorithm}_{result.scenario}"
    json_path = REPORT_DIR / f"{stem}.json"
    markdown_path = REPORT_DIR / f"{stem}.md"
    json_path.write_text(json.dumps(asdict(result), indent=2) + "\n", encoding="ascii")

    failures = "\n".join(f"- {reason}" for reason in result.failures) or "- None"
    validation = (
        "\n".join(f"- {reason}" for reason in result.validation_failures) or "- None"
    )
    markdown_path.write_text(
        f"""# Benchmark Report: {result.algorithm}

## Scenario

- Name: `{result.scenario}`
- Status: `{result.status}`
- Valid schedule: `{result.valid}`
- Generated: `{result.generated_at_utc}`

## Results

| Metric | Value |
| --- | ---: |
| Runtime (seconds) | {result.runtime_seconds:.6f} |
| Candidate placements evaluated | {result.candidate_placements_evaluated} |
| Events requested | {result.events_requested} |
| Events scheduled | {result.events_scheduled} |
| Events failed | {result.events_failed} |
| Required events completed | {result.required_events_completed} |
| Optional events completed | {result.optional_events_completed} |
| Occurrences requested | {result.occurrences_requested} |
| Occurrences scheduled | {result.occurrences_scheduled} |
| Occupancy | {result.occupancy_percent:.2f}% |
| Final schedule score | {result.final_schedule_score:.6f} |

## Scheduling Failures

{failures}

## Validation Failures

{validation}
""",
        encoding="ascii",
    )
    return json_path, markdown_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run shared scheduling benchmarks")
    parser.add_argument(
        "--algorithm", choices=sorted(ALGORITHMS), default="greedy"
    )
    args = parser.parse_args()
    result = benchmark(args.algorithm)
    json_path, markdown_path = write_report(result)
    print(json_path)
    print(markdown_path)


if __name__ == "__main__":
    main()
