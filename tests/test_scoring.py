import copy
import inspect

import pytest

import scoring
from event import Event
from schedule import Placement, Schedule
from time_rep import to_slot


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


def score(schedule, events, scorer=None):
    scorer = scorer or scoring.SimonCowell()
    result = scorer.score(schedule, set(events))
    assert isinstance(result, scoring.ScoreBreakdown)
    return result


def assert_scores_higher(better, worse, events):
    better_score = score(better, events)
    worse_score = score(worse, events)
    assert better_score.total > worse_score.total


def test_score_breakdown_contains_total_and_named_components():
    event = make_event(preferred_start=((0, 900),))
    result = score(make_schedule((event, to_slot(0, 9, 0))), [event])

    assert isinstance(result.total, (int, float))
    assert isinstance(result.components, dict)
    assert "required_event" in result.components
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

    assert_scores_higher(evenly_spaced, clustered, [event])


def test_higher_priority_events_increase_score():
    high = make_event(name="High", priority=10)
    low = make_event(name="Low", priority=2)

    high_score = score(make_schedule((high, to_slot(0, 9, 0))), [high])
    low_score = score(make_schedule((low, to_slot(0, 9, 0))), [low])

    assert high_score.total > low_score.total


def test_preferred_day_increases_score():
    event = make_event(preferred_start=((0, 900), (0, 1400)))
    preferred_day = make_schedule((event, to_slot(0, 11, 0)))
    other_day = make_schedule((event, to_slot(1, 11, 0)))

    assert_scores_higher(preferred_day, other_day, [event])


def test_preferred_time_increases_score():
    event = make_event(preferred_start=((0, 900),))
    preferred = make_schedule((event, to_slot(0, 9, 0)))
    later = make_schedule((event, to_slot(0, 14, 0)))

    assert_scores_higher(preferred, later, [event])


def test_large_idle_gaps_reduce_score():
    events = [make_event(name=f"Event {index}") for index in range(3)]
    compact = make_schedule(
        *[(event, to_slot(0, 9 + index, 0)) for index, event in enumerate(events)]
    )
    gapped = make_schedule(
        *[(event, to_slot(0, 9 + index * 3, 0)) for index, event in enumerate(events)]
    )

    assert_scores_higher(compact, gapped, events)


def test_fragmentation_reduces_score():
    events = [make_event(name=f"Event {index}") for index in range(3)]
    continuous = make_schedule(
        *[(event, to_slot(0, 9, 0) + index * 4) for index, event in enumerate(events)]
    )
    fragmented = make_schedule(
        *[(event, to_slot(0, 9, 0) + index * 6) for index, event in enumerate(events)]
    )

    assert_scores_higher(continuous, fragmented, events)


def test_late_night_placement_reduces_score():
    event = make_event()
    daytime = make_schedule((event, to_slot(0, 10, 0)))
    late_night = make_schedule((event, to_slot(0, 2, 0)))

    assert_scores_higher(daytime, late_night, [event])


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

    assert_scores_higher(with_break, continuous, events)


def test_balanced_daily_workload_scores_higher():
    events = [make_event(name=f"Task {index}") for index in range(4)]
    balanced = make_schedule(
        *[(event, to_slot(index, 9, 0)) for index, event in enumerate(events)]
    )
    overloaded_day = make_schedule(
        *[(event, to_slot(0, 9 + index, 0)) for index, event in enumerate(events)]
    )

    assert_scores_higher(balanced, overloaded_day, events)


def test_balanced_week_distribution_scores_higher():
    events = [make_event(name=f"Task {index}") for index in range(4)]
    distributed = make_schedule(
        *[(event, to_slot(index * 2, 9, 0)) for index, event in enumerate(events)]
    )
    front_loaded = make_schedule(
        *[(event, to_slot(index // 2, 9 + index % 2, 0)) for index, event in enumerate(events)]
    )

    assert_scores_higher(distributed, front_loaded, events)


def make_required_event_set(count=4):
    return [make_event(name=f"Required {index}", hard_flag=True) for index in range(count)]


def schedule_first_events(events, count):
    return make_schedule(
        *[(event, to_slot(index, 9, 0)) for index, event in enumerate(events[:count])]
    )


def test_more_required_events_placed_increases_required_event_component():
    required = make_required_event_set()
    one_placed = score(schedule_first_events(required, 1), required)
    two_placed = score(schedule_first_events(required, 2), required)

    assert two_placed.components["required_event"] > one_placed.components["required_event"]


def test_all_required_events_placed_has_full_completion():
    required = make_required_event_set()
    result = score(schedule_first_events(required, 4), required)

    assert result.components["required_event"] == pytest.approx(1.0)


def test_partial_required_event_completion_is_fractional():
    required = make_required_event_set()
    result = score(schedule_first_events(required, 2), required)

    assert result.components["required_event"] == pytest.approx(0.5)


def test_missing_required_events_does_not_make_schedule_invalid():
    required = make_required_event_set()

    result = score(Schedule(), required)

    assert result.components["required_event"] == pytest.approx(0.0)


def test_no_required_events_requested_has_full_completion():
    optional = make_event(hard_flag=False)
    result = score(Schedule(), [optional])

    assert result.components["required_event"] == pytest.approx(1.0)


def test_changing_weights_changes_the_final_score():
    assert hasattr(scoring, "ScoringWeights"), "scoring.py must define ScoringWeights"
    event = make_event(priority=10)
    schedule = make_schedule((event, to_slot(0, 9, 0)))
    default = scoring.ScoringWeights()
    priority_weight = default.priority
    heavier = scoring.ScoringWeights(priority=priority_weight * 2)

    scorer_parameters = inspect.signature(scoring.SimonCowell).parameters
    if "weights" in scorer_parameters:
        default_scorer = scoring.SimonCowell(weights=default)
        heavier_scorer = scoring.SimonCowell(weights=heavier)
    else:
        default_scorer = scoring.SimonCowell()
        heavier_scorer = scoring.SimonCowell()
        default_scorer.weights = default
        heavier_scorer.weights = heavier

    default_score = score(schedule, [event], default_scorer)
    heavier_score = score(schedule, [event], heavier_scorer)

    assert heavier_score.total > default_score.total


def test_detailed_report_lists_components_and_total():
    event = make_event(preferred_start=((0, 900),))
    scorer = scoring.SimonCowell()
    result = score(make_schedule((event, to_slot(0, 9, 0))), [event], scorer)

    if callable(getattr(result, "report", None)):
        report = result.report()
    elif callable(getattr(scorer, "report", None)):
        report = scorer.report(result)
    elif callable(getattr(scoring, "format_score_report", None)):
        report = scoring.format_score_report(result)
    else:
        pytest.fail("scoring.py must expose a detailed score-report function or method")

    assert isinstance(report, str)
    assert "Schedule Score" in report
    assert "Priority" in report
    assert "Spacing" in report
    assert "Fragmentation" in report
    assert "Idle Gap" in report
    assert "Late Night" in report
    assert "Total" in report
