import copy

import pytest

import scoring
from event import Event
from schedule import Placement, Schedule
from time_rep import to_slot


EXPECTED_COMPONENTS = {
    "required_event",
    "occurances",
    "optional_events",
    "priority",
    "preferred_day",
    "pref_time",
    "event_spacing",
    "idle_gap",
    "fragmentation",
    "late_night",
    "consecutive_workload",
    "daily_balance",
    "weekly_balance",
}


def make_event(
    name="Work",
    *,
    duration=4,
    freq=1,
    priority=5,
    preferred_start=(),
    hard_flag=True,
    pref_gap_days=0,
):
    event = Event.__new__(Event)
    event.event_id = Event._next_id
    Event._next_id += 1
    event.name = name
    event.duration = duration
    event.freq = freq
    event.period = "weekly"
    event.priority = priority
    event.hard_flag = hard_flag
    event.time_window = tuple((day, 0, 2359) for day in range(7))
    event.preferred_start = preferred_start
    event.min_gap_days = 0
    event.pref_gap_days = pref_gap_days
    return event


def make_schedule(*event_starts):
    schedule = Schedule()
    for event, start in event_starts:
        assert schedule.place(Placement(event, start)) is True
    return schedule


def score(schedule, events, weights=None):
    if weights is None:
        scorer = scoring.SimonCowell()
    else:
        scorer = scoring.SimonCowell(weights=weights)
    result = scorer.score(schedule, set(events))
    assert isinstance(result, scoring.ScoreBreakdown)
    return result


def assert_scores_higher(better, worse, events, component):
    better_score = score(better, events)
    worse_score = score(worse, events)
    assert better_score.components[component] > worse_score.components[component]
    assert better_score.total > worse_score.total


def test_score_breakdown_contains_total_and_all_independent_components():
    event = make_event(preferred_start=((0, 900),))
    result = score(make_schedule((event, to_slot(0, 9, 0))), [event])

    assert isinstance(result.total, (int, float))
    assert EXPECTED_COMPONENTS <= result.components.keys()
    assert result.total == pytest.approx(sum(result.components.values()))


def test_scoring_does_not_modify_schedule():
    event = make_event()
    schedule = make_schedule((event, to_slot(0, 9, 0)))
    slots_before = schedule.slots.copy()
    placements_before = copy.copy(schedule.placements)

    score(schedule, [event])

    assert schedule.slots == slots_before
    assert schedule.placements == placements_before


def test_better_spacing_scores_higher():
    event = make_event(freq=3, pref_gap_days=2)
    evenly_spaced = make_schedule(
        (event, to_slot(0, 9, 0)),
        (event, to_slot(2, 9, 0)),
        (event, to_slot(4, 9, 0)),
    )
    clustered = make_schedule(
        (event, to_slot(0, 9, 0)),
        (event, to_slot(1, 9, 0)),
        (event, to_slot(2, 9, 0)),
    )

    assert_scores_higher(evenly_spaced, clustered, [event], "event_spacing")


def test_higher_priority_events_increase_score():
    high = make_event(name="High", priority=10)
    low = make_event(name="Low", priority=2)

    high_score = score(make_schedule((high, to_slot(0, 9, 0))), [high])
    low_score = score(make_schedule((low, to_slot(0, 9, 0))), [low])

    assert high_score.components["priority"] > low_score.components["priority"]
    assert high_score.total > low_score.total


def test_preferred_day_increases_score():
    event = make_event(preferred_start=((0, 900), (0, 1400)))
    preferred_day = make_schedule((event, to_slot(0, 11, 0)))
    other_day = make_schedule((event, to_slot(1, 11, 0)))

    assert_scores_higher(preferred_day, other_day, [event], "preferred_day")


def test_preferred_time_increases_score():
    event = make_event(preferred_start=((0, 900),))
    preferred = make_schedule((event, to_slot(0, 9, 0)))
    later = make_schedule((event, to_slot(0, 14, 0)))

    assert_scores_higher(preferred, later, [event], "pref_time")


def test_large_idle_gaps_reduce_score():
    events = [make_event(name=f"Event {index}") for index in range(3)]
    compact = make_schedule(
        *[(event, to_slot(0, 9 + index, 0)) for index, event in enumerate(events)]
    )
    gapped = make_schedule(
        *[(event, to_slot(0, 9 + index * 3, 0)) for index, event in enumerate(events)]
    )

    assert_scores_higher(compact, gapped, events, "idle_gap")


def test_fragmentation_reduces_score():
    events = [make_event(name=f"Event {index}") for index in range(3)]
    continuous = make_schedule(
        *[(event, to_slot(0, 9, 0) + index * 4) for index, event in enumerate(events)]
    )
    fragmented = make_schedule(
        *[(event, to_slot(0, 9, 0) + index * 6) for index, event in enumerate(events)]
    )

    assert_scores_higher(continuous, fragmented, events, "fragmentation")


def test_late_night_placement_reduces_score():
    event = make_event()
    daytime = make_schedule((event, to_slot(0, 10, 0)))
    late_night = make_schedule((event, to_slot(0, 2, 0)))

    assert_scores_higher(daytime, late_night, [event], "late_night")


def test_long_consecutive_workload_reduces_score():
    events = [make_event(name=f"Work {index}", duration=16) for index in range(2)]
    with_break = make_schedule(
        (events[0], to_slot(0, 8, 0)),
        (events[1], to_slot(0, 13, 0)),
    )
    continuous = make_schedule(
        (events[0], to_slot(0, 8, 0)),
        (events[1], to_slot(0, 12, 0)),
    )

    assert_scores_higher(with_break, continuous, events, "consecutive_workload")


def test_balanced_daily_workload_scores_higher():
    events = [make_event(name=f"Task {index}") for index in range(4)]
    balanced = make_schedule(
        *[(event, to_slot(index, 9, 0)) for index, event in enumerate(events)]
    )
    overloaded_day = make_schedule(
        *[(event, to_slot(0, 9 + index, 0)) for index, event in enumerate(events)]
    )

    assert_scores_higher(balanced, overloaded_day, events, "daily_balance")


def test_balanced_week_distribution_scores_higher():
    events = [make_event(name=f"Task {index}") for index in range(4)]
    distributed = make_schedule(
        *[(event, to_slot(index * 2, 9, 0)) for index, event in enumerate(events)]
    )
    front_loaded = make_schedule(
        *[(event, to_slot(index // 2, 9 + index % 2, 0)) for index, event in enumerate(events)]
    )

    assert_scores_higher(distributed, front_loaded, events, "weekly_balance")


def test_missing_required_event_receives_heavy_penalty():
    required = make_event(hard_flag=True)
    complete = score(make_schedule((required, to_slot(0, 9, 0))), [required])
    missing = score(Schedule(), [required])

    assert missing.components["required_event"] <= -1000
    assert complete.total - missing.total >= 1000


def test_changing_weights_changes_only_the_expected_contribution():
    assert hasattr(scoring, "ScoringWeights"), "scoring.py must define ScoringWeights"
    event = make_event(priority=10)
    schedule = make_schedule((event, to_slot(0, 9, 0)))
    default = scoring.ScoringWeights()
    priority_weight = default.priority
    heavier = scoring.ScoringWeights(priority=priority_weight * 2)

    default_score = score(schedule, [event], default)
    heavier_score = score(schedule, [event], heavier)

    assert heavier_score.components["priority"] == pytest.approx(
        default_score.components["priority"] * 2
    )
    assert heavier_score.total > default_score.total


def test_detailed_report_lists_components_and_total():
    event = make_event(preferred_start=((0, 900),))
    result = score(make_schedule((event, to_slot(0, 9, 0))), [event])

    report = result.report()

    assert isinstance(report, str)
    assert "Schedule Score" in report
    assert "Priority" in report
    assert "Spacing" in report
    assert "Fragmentation" in report
    assert "Idle Gap" in report
    assert "Late Night" in report
    assert "Total" in report
