import hashlib
import json
from dataclasses import asdict, dataclass

from event import Event


SCENARIO_NAME = "optimization_stress_v2"
FROZEN_SCENARIO_SHA256 = "50f6096e173f9e2c1a4e3a11a1944cd15a2704958fec162fa2e8b025bd193ef6"


@dataclass(frozen=True)
class EventSpec:
    name: str
    duration: int
    freq: int
    priority: int
    time_window: tuple[tuple[int, int, int], ...]
    preferred_start: tuple[tuple[int, int], ...]
    hard_flag: bool
    min_gap_days: int = 0
    pref_gap_days: int = 0


# Windows are declared independently. They intentionally mix fixed, narrow,
# broad, multi-window, and directly competing availability patterns.
EVENT_SPECS = (
    EventSpec("Workout", 4, 3, 2, ((0, 600, 800), (2, 600, 800), (5, 600, 800)), ((0, 700), (2, 700), (5, 700)), True, 1, 2),
    EventSpec("Study", 6, 3, 1, ((0, 1800, 2345), (2, 1800, 2345), (5, 1800, 2345)), ((0, 2000), (2, 2000), (5, 2000)), True, 1, 2),
    EventSpec("Medical Appointment", 8, 1, 0, ((2, 1300, 1500),), ((2, 1300),), True),
    EventSpec("Meal Preparation", 6, 3, 2, ((1, 1600, 2000), (3, 1600, 2000), (5, 1600, 2000)), ((1, 1700), (3, 1700), (5, 1700)), False, 1, 2),
    EventSpec("Language Practice", 3, 4, 1, ((0, 600, 900), (1, 600, 900), (3, 600, 900), (4, 600, 900)), ((0, 700), (1, 700), (3, 700), (4, 700)), False, 0, 1),
    EventSpec("Focus Block", 8, 1, 10, ((0, 900, 1100), (0, 1400, 1600)), ((0, 900),), True),
    EventSpec("Reading", 8, 1, 6, ((0, 900, 1100), (0, 1400, 1600)), ((0, 1400),), False),
    EventSpec("Project Lab", 12, 1, 9, ((1, 800, 1100), (1, 1500, 1800)), ((1, 800),), True),
    EventSpec("Personal Project", 12, 1, 7, ((1, 800, 1100), (1, 1500, 1800)), ((1, 1500),), False),
    EventSpec("Administration", 4, 1, 5, ((3, 1000, 1100), (3, 1700, 1800)), ((3, 1000),), True),
    EventSpec("Music Practice", 4, 1, 4, ((3, 1000, 1100), (3, 1700, 1800)), ((3, 1700),), False),
    EventSpec("Client Review", 6, 1, 8, ((4, 900, 1030), (4, 1800, 1930)), ((4, 900),), True),
    EventSpec("Social Event", 6, 1, 3, ((4, 900, 1030), (4, 1800, 1930)), ((4, 1800),), False),
)


def scenario_payload() -> list[dict]:
    return [asdict(spec) for spec in EVENT_SPECS]


def scenario_checksum() -> str:
    encoded = json.dumps(scenario_payload(), sort_keys=True).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def assert_scenario_frozen() -> None:
    actual = scenario_checksum()
    if actual != FROZEN_SCENARIO_SHA256:
        raise RuntimeError(
            f"{SCENARIO_NAME} changed without a version bump: {actual}"
        )


def build_events() -> list[Event]:
    assert_scenario_frozen()
    events = []
    for index, spec in enumerate(EVENT_SPECS):
        event = Event.__new__(Event)
        event.event_id = 3000 + index
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
    assert_scenario_frozen()
    return {
        "name": SCENARIO_NAME,
        "checksum": scenario_checksum(),
        "events": len(EVENT_SPECS),
        "required_events": sum(spec.hard_flag for spec in EVENT_SPECS),
        "optional_events": sum(not spec.hard_flag for spec in EVENT_SPECS),
        "requested_occurrences": sum(spec.freq for spec in EVENT_SPECS),
        "requested_slots": sum(spec.duration * spec.freq for spec in EVENT_SPECS),
    }
