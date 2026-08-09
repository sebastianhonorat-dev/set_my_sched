from dataclasses import dataclass

from event import Event


SCENARIO_NAME = "challenging_week_v1"


@dataclass(frozen=True)
class EventSpec:
    name: str
    duration: int
    freq: int
    priority: int
    time_window: tuple[tuple[int, int, int], ...]
    preferred_start: tuple[tuple[int, int], ...] = ()
    hard_flag: bool = True
    min_gap_days: int = 0
    pref_gap_days: int = 0


EVENT_SPECS = (
    EventSpec(
        "Deep Work",
        8,
        4,
        10,
        tuple((day, 800, 1200) for day in range(5)),
        ((0, 900), (1, 900), (3, 900), (4, 900)),
        min_gap_days=1,
        pref_gap_days=1,
    ),
    EventSpec(
        "Project Lab",
        12,
        2,
        9,
        ((1, 1200, 1600), (3, 1200, 1600)),
        ((1, 1230), (3, 1230)),
        min_gap_days=1,
        pref_gap_days=2,
    ),
    EventSpec(
        "Course Seminar",
        6,
        3,
        9,
        ((0, 1000, 1300), (2, 1000, 1300), (4, 1000, 1300)),
        ((0, 1030), (2, 1030), (4, 1030)),
        min_gap_days=1,
        pref_gap_days=2,
    ),
    EventSpec(
        "Workout",
        4,
        4,
        8,
        tuple((day, 600, 900) for day in range(6))
        + tuple((day, 1700, 2000) for day in range(5)),
        ((0, 700), (2, 700), (4, 700), (5, 800)),
        min_gap_days=1,
        pref_gap_days=2,
    ),
    EventSpec(
        "Team Sync",
        4,
        3,
        8,
        ((0, 1300, 1500), (2, 1300, 1500), (4, 1300, 1500)),
        ((0, 1300), (2, 1300), (4, 1300)),
        min_gap_days=1,
        pref_gap_days=2,
    ),
    EventSpec(
        "Client Review",
        6,
        2,
        8,
        ((1, 1600, 1900), (3, 1600, 1900)),
        ((1, 1700), (3, 1700)),
        min_gap_days=1,
        pref_gap_days=2,
    ),
    EventSpec(
        "Exam Preparation",
        10,
        3,
        7,
        tuple((day, 1500, 2100) for day in range(5)),
        ((0, 1600), (2, 1600), (4, 1600)),
        min_gap_days=1,
        pref_gap_days=2,
    ),
    EventSpec(
        "Medical Appointment",
        8,
        1,
        10,
        ((2, 1500, 1730),),
        ((2, 1500),),
    ),
    EventSpec(
        "Weekly Planning",
        4,
        1,
        7,
        ((0, 800, 1000),),
        ((0, 800),),
    ),
    EventSpec(
        "Meal Preparation",
        6,
        3,
        6,
        ((1, 1900, 2130), (3, 1900, 2130), (5, 1900, 2130)),
        ((1, 1900), (3, 1900), (5, 1900)),
        min_gap_days=1,
        pref_gap_days=2,
    ),
    EventSpec(
        "Reading",
        4,
        4,
        5,
        tuple((day, 1900, 2200) for day in range(5)),
        ((0, 2000), (1, 2000), (3, 2000), (4, 2000)),
        hard_flag=False,
        pref_gap_days=1,
    ),
    EventSpec(
        "Language Practice",
        3,
        4,
        5,
        tuple((day, 700, 900) for day in range(5)),
        ((0, 730), (1, 730), (3, 730), (4, 730)),
        hard_flag=False,
        pref_gap_days=1,
    ),
    EventSpec(
        "Social Dinner",
        8,
        2,
        4,
        ((4, 1800, 2200), (5, 1800, 2200)),
        ((4, 1900), (5, 1900)),
        hard_flag=False,
        min_gap_days=1,
        pref_gap_days=1,
    ),
    EventSpec(
        "Personal Project",
        12,
        2,
        4,
        ((2, 1800, 2200), (5, 900, 1500)),
        ((2, 1830), (5, 1000)),
        hard_flag=False,
        min_gap_days=1,
        pref_gap_days=3,
    ),
    EventSpec(
        "Errands",
        8,
        1,
        3,
        ((5, 900, 1400),),
        ((5, 1100),),
        hard_flag=False,
    ),
    EventSpec(
        "Music Practice",
        4,
        3,
        3,
        tuple((day, 1600, 2000) for day in range(5)),
        ((1, 1700), (3, 1700), (4, 1700)),
        hard_flag=False,
        pref_gap_days=2,
    ),
    EventSpec(
        "Volunteer Shift",
        16,
        1,
        2,
        ((5, 900, 1700),),
        ((5, 1200),),
        hard_flag=False,
    ),
    EventSpec(
        "Creative Writing",
        6,
        2,
        2,
        ((1, 1800, 2200), (3, 1800, 2200), (5, 1400, 1800)),
        ((1, 1900), (3, 1900)),
        hard_flag=False,
        pref_gap_days=2,
    ),
)


def build_events() -> list[Event]:
    """Return fresh Event objects so every algorithm gets identical clean input."""
    events = []
    for index, spec in enumerate(EVENT_SPECS):
        event = Event.__new__(Event)
        event.event_id = 1000 + index
        event.name = spec.name
        event.duration = spec.duration
        event.freq = spec.freq
        event.period = "weekly"
        event.priority = spec.priority
        event.hard_flag = spec.hard_flag
        event.time_window = spec.time_window
        event.preferred_start = spec.preferred_start
        event.min_gap_days = spec.min_gap_days
        event.pref_gap_days = spec.pref_gap_days
        events.append(event)
    return events


def scenario_summary() -> dict[str, int | str]:
    return {
        "name": SCENARIO_NAME,
        "events": len(EVENT_SPECS),
        "required_events": sum(spec.hard_flag for spec in EVENT_SPECS),
        "optional_events": sum(not spec.hard_flag for spec in EVENT_SPECS),
        "requested_occurrences": sum(spec.freq for spec in EVENT_SPECS),
        "requested_slots": sum(spec.duration * spec.freq for spec in EVENT_SPECS),
    }
