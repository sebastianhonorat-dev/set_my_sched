from types import SimpleNamespace

import pytest

from constraints import (
    ConstraintResult,
    SchedulerConfig,
    check_gap,
    cross_midnight,
    day_from_slot,
    get_end_slot,
    time_from_slot,
    validate_placement,
)
from schedule import Schedule
from time_rep import to_slot, weekly_slots


def make_event(**overrides):
    values = {
        "event_id": 100,
        "name": "Workout",
        "duration": 4,
        "freq": 2,
        "period": "weekly",
        "priority": 5,
        "time_window": tuple((day, 800, 1800) for day in range(5)),
        "preferred_start": ((0, 900), (2, 900)),
        "min_gap_days": 1,
        "pref_gap_days": 2,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def add_existing(schedule, event, start_slot):
    placement = SimpleNamespace(
        placement_id=len(schedule.placements) + 1,
        event_id=event.event_id,
        name=event.name,
        start=start_slot,
        end=start_slot + event.duration - 1,
        duration=event.duration,
    )
    schedule.placements[placement.placement_id] = placement
    for slot in range(placement.start, placement.end + 1):
        schedule.slots[slot] = placement
    return placement


def assert_reason_contains(reasons, *terms):
    combined = " ".join(reasons).lower()
    assert all(term.lower() in combined for term in terms), reasons


def test_constraint_result_holds_pass_state_and_reasons():
    result = ConstraintResult(
        passed=False,
        reasons=["Event starts before allowed time", "Slot already occupied"],
    )

    assert result.passed is False
    assert result.reasons == [
        "Event starts before allowed time",
        "Slot already occupied",
    ]


def test_scheduler_config_has_simple_global_defaults():
    config = SchedulerConfig()

    assert config.avoid_hours == range(0, 6)
    assert config.default_min_gap_slots == 96
    assert config.allow_cross_midnight is False


def test_slot_helpers_report_start_end_and_midnight_crossing():
    event = make_event(duration=8)
    start = to_slot(1, 23, 0)

    assert day_from_slot(start) == 1
    assert time_from_slot(start) == 2300
    assert get_end_slot(event, start) == start + 7
    assert cross_midnight(event, start) is True


def test_gap_helper_measures_days_between_same_event_occurrences():
    schedule = Schedule()
    event = make_event()
    add_existing(schedule, event, to_slot(0, 9, 0))

    gaps = check_gap(schedule, event, to_slot(2, 9, 0))

    assert gaps == [2]


def test_valid_placement_passes_without_hard_failures():
    result = validate_placement(make_event(), Schedule(), to_slot(0, 9, 0))

    assert result["valid"] is True
    assert result["hard_failures"] == []
    assert result["soft_warnings"] == []


def test_overlapping_placement_fails():
    schedule = Schedule()
    event = make_event()
    add_existing(schedule, make_event(event_id=200, name="Meeting"), to_slot(0, 9, 0))

    result = validate_placement(event, schedule, to_slot(0, 9, 15))

    assert result["valid"] is False
    assert_reason_contains(result["hard_failures"], "slots", "occupied")


@pytest.mark.parametrize("start_slot", [-1, weekly_slots - 2])
def test_placement_outside_week_fails(start_slot):
    result = validate_placement(make_event(duration=4), Schedule(), start_slot)

    assert result["valid"] is False
    assert_reason_contains(result["hard_failures"], "week")


def test_disallowed_day_fails():
    event = make_event(
        time_window=((0, 800, 1800), (2, 800, 1800), (4, 800, 1800))
    )

    result = validate_placement(event, Schedule(), to_slot(1, 9, 0))

    assert result["valid"] is False
    assert_reason_contains(result["hard_failures"], "outside", "requested", "slots")


def test_placement_before_earliest_allowed_start_fails():
    result = validate_placement(make_event(), Schedule(), to_slot(0, 7, 45))

    assert result["valid"] is False
    assert_reason_contains(result["hard_failures"], "outside", "requested", "slots")


def test_placement_ending_after_latest_allowed_end_fails():
    event = make_event(duration=8)

    result = validate_placement(event, Schedule(), to_slot(0, 17, 0))

    assert result["valid"] is False
    assert_reason_contains(result["hard_failures"], "outside", "requested", "slots")


def test_frequency_exceeded_fails():
    schedule = Schedule()
    event = make_event(freq=2, min_gap_days=0)
    add_existing(schedule, event, to_slot(0, 9, 0))
    add_existing(schedule, event, to_slot(2, 9, 0))

    result = validate_placement(event, schedule, to_slot(4, 9, 0))

    assert result["valid"] is False
    assert_reason_contains(result["hard_failures"], "frequency")


def test_minimum_gap_violation_fails_for_two_occurrences_on_same_day():
    schedule = Schedule()
    event = make_event(min_gap_days=1)
    add_existing(schedule, event, to_slot(0, 8, 0))

    result = validate_placement(event, schedule, to_slot(0, 14, 0))

    assert result["valid"] is False
    assert_reason_contains(result["hard_failures"], "minimum", "gap")


def test_soft_warning_is_detected_without_failing_placement():
    event = make_event(preferred_start=((0, 900),))

    result = validate_placement(event, Schedule(), to_slot(2, 10, 0))

    assert result["valid"] is True
    assert result["hard_failures"] == []
    assert result["soft_warnings"]
    assert_reason_contains(result["soft_warnings"], "preferred")
