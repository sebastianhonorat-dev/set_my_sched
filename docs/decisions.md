# Design Decisions

## Constraint Validation

**Scoring only valid schedules**

The search algorithm is responsible for calling `can_place()` before evaluating a placement. Only schedules that satisfy all hard constraints are passed to `SchedulerScorer`, making the scoring system responsible solely for measuring schedule quality.

**AC-3 and `can_place()`**

`AC-3` removes a value only when it can prove that the value can never participate in a valid solution. `can_place()` performs the final legality check for a specific placement using the current schedule state.

**Occurrence Scoring**

`has_all_occurrences()` evaluates only events that have been placed at least once. Events that are never scheduled are handled separately by the required and optional event completion components to avoid double-penalizing the same failure.

## Priority Weighting

Priority is applied only during final schedule evaluation and is intentionally excluded from search order. This keeps the objective function independent of the optimization algorithm while allowing higher-priority events to contribute more heavily to the final score.

Priority is mapped to a multiplier using `(priority + 1) / 6`, making priority `5` the baseline (≈1.0×), lower priorities contribute less, and higher priorities contribute proportionally more.

## Preferred Time Scoring

The preferred-time scoring curve uses an exponent of `2.46`, tuned so that a placement approximately two hours from the preferred start time still receives a score of about `0.8`. Small deviations are treated leniently while larger deviations decay more rapidly.

## Preferred Gap Scoring

Preferred spacing is treated as a soft preference rather than a strict penalty. Minimum spacing is already enforced as a hard constraint, so schedules that deviate by one or two days remain acceptable and receive only a moderate reduction in score. A nonlinear decay rewards ideal spacing without excessively penalizing small deviations.

### Completed Schedule Validation

For now, scoring validation reuses the existing placement constraint logic and ignores a placement colliding with itself. This is a temporary compatibility fix. A separate completed-schedule validation function should be added later so `can_place()` can remain focused on validating new candidate placements before insertion.

### Deferred Scoring Features

The initial scoring system will remain intentionally minimal. Generic idle-gap, fragmentation, late-night, consecutive-workload, daily-balance, and weekly-balance penalties are deferred until actual scheduler output demonstrates a need for them.

Generic even-spacing is also not assumed. Recurring-event spacing is currently evaluated using the event's explicit `pref_gap_days` preference.

Configurable scoring weights and detailed score-report generation are deferred for now. `ScoreBreakdown` provides the underlying component data without automatically generating reports.

The goal is to first observe what schedules emerge from the core constraints and explicit user preferences before introducing additional assumptions about what constitutes a "good" schedule.
