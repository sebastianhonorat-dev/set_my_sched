from unittest.mock import mock_open

import pytest

from algo import greedy_boy
from algo.greedy_boy import GreedyScheduler, PlacementResults
from constraints import validate_placement
from event import Event
from schedule import Placement, Schedule
from time_rep import to_slot


def make_event(
    name="Event",
    *,
    duration=4,
    freq=1,
    priority=5,
    time_window=((0, 900, 1700),),
    preferred_start=((0, 900),),
    hard_flag=True,
    min_gap_days=0,
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
    event.time_window = time_window
    event.preferred_start = preferred_start
    event.min_gap_days = min_gap_days
    event.pref_gap_days = pref_gap_days
    return event


@pytest.fixture(autouse=True)
def prevent_report_file_writes(monkeypatch):
    report_file = mock_open()
    monkeypatch.setattr(greedy_boy, "open", report_file, raising=False)
    return report_file


def placements_for(schedule, event):
    return schedule.placements.get(event, [])


def assert_schedule_is_valid(schedule):
    rebuilt = Schedule()
    placements = sorted(
        (placement for group in schedule.placements.values() for placement in group),
        key=lambda placement: placement.start,
    )
    for placement in placements:
        validation = validate_placement(placement.event, rebuilt, placement.start)
        assert validation["valid"], validation["hard_failures"]
        assert rebuilt.place(Placement(placement.event, placement.start)) is True


def test_empty_event_list_returns_empty_successful_schedule():
    result = GreedyScheduler(Schedule(), []).generate()

    assert result.status == "success"
    assert result.schedule.placements == {}
    assert result.reasons == []
    assert result.runtime >= 0


def test_single_event_is_scheduled_in_its_allowed_window():
    event = make_event()

    result = GreedyScheduler(Schedule(), [event]).generate()

    assert result.status == "success"
    assert len(placements_for(result.schedule, event)) == 1
    placement = placements_for(result.schedule, event)[0]
    assert to_slot(0, 9, 0) <= placement.start
    assert placement.end <= to_slot(0, 17, 0)


def test_multiple_events_are_scheduled_without_overlap():
    events = [make_event(name=f"Event {index}") for index in range(3)]

    result = GreedyScheduler(Schedule(), events).generate()

    print(result.reasons)

    assert result.status == "success"
    assert all(len(placements_for(result.schedule, event)) == 1 for event in events)
    occupied_ranges = [
        set(range(placement.start, placement.end + 1))
        for event in events
        for placement in placements_for(result.schedule, event)
    ]
    assert all(
        first.isdisjoint(second)
        for index, first in enumerate(occupied_ranges)
        for second in occupied_ranges[index + 1 :]
    )


def test_recurring_event_places_every_occurrence_with_preferred_spacing():
    event = make_event(
        freq=3,
        time_window=((0, 900, 1700), (2, 900, 1700), (4, 900, 1700)),
        preferred_start=((0, 900), (2, 900), (4, 900)),
        min_gap_days=1,
        pref_gap_days=2,
    )

    result = GreedyScheduler(Schedule(), [event]).generate()

    print(result.reasons)

    placements = sorted(placements_for(result.schedule, event), key=lambda item: item.start)
    assert result.status == "success"
    assert len(placements) == event.freq
    assert all(
        (later.start - earlier.start) // 96 >= event.min_gap_days
        for earlier, later in zip(placements, placements[1:])
    )


def test_events_are_attempted_in_descending_priority_order(monkeypatch):
    low = make_event(name="Low", priority=1)
    high = make_event(name="High", priority=10)
    medium = make_event(name="Medium", priority=5)
    scheduler = GreedyScheduler(Schedule(), [low, high, medium])
    attempted = []

    def record_success(event):
        attempted.append(event)
        return PlacementResults("success", event.event_id, event.name, [])

    monkeypatch.setattr(scheduler, "place", record_success)

    scheduler.generate()

    assert attempted == [high, medium, low]


def test_event_with_no_valid_placement_is_documented_and_does_not_crash():
    impossible = make_event(name="Impossible", time_window=(), hard_flag=False)

    result = GreedyScheduler(Schedule(), [impossible]).generate()

    assert result.status != "corrupt"
    assert placements_for(result.schedule, impossible) == []
    reason_text = " ".join(result.reasons).lower()
    assert "impossible" in reason_text
    assert "no slots" in reason_text or "no available" in reason_text


def test_failed_required_event_stops_later_events(monkeypatch):
    impossible = make_event(name="Impossible", priority=10)
    schedulable = make_event(name="Schedulable", priority=1)
    scheduler = GreedyScheduler(Schedule(), [schedulable, impossible])
    attempted = []

    def controlled_place(event):
        attempted.append(event)
        if event is impossible:
            return PlacementResults(
                "fail", event.event_id, event.name, ["No valid placement"]
            )
        return PlacementResults("success", event.event_id, event.name, [])

    monkeypatch.setattr(scheduler, "place", controlled_place)

    result = scheduler.generate()

    assert attempted == [impossible]
    assert result.status == "fail"
    assert any("Impossible" in reason for reason in result.reasons)


def test_generated_schedule_satisfies_all_hard_constraints():
    recurring = make_event(
        name="Workout",
        freq=2,
        priority=10,
        time_window=((0, 800, 1200), (2, 800, 1200)),
        preferred_start=((0, 900), (2, 900)),
        min_gap_days=1,
        pref_gap_days=2,
    )
    meeting = make_event(
        name="Meeting",
        priority=7,
        time_window=((0, 800, 1200),),
        preferred_start=((0, 1000),),
    )

    result = GreedyScheduler(Schedule(), [meeting, recurring]).generate()

    print(result.reasons)

    assert result.status == "success"
    assert_schedule_is_valid(result.schedule)
