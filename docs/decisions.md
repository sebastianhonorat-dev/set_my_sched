1.  `can_place` will be used in the algo itself. If `True`, then `scoring.score()`. So this means only valid schedules are scored.
2. `AC-3` I will only remove a value if it can prove it can never work. `can_place()` will determine whether a specific placement is legal given the current schedule.
3. `has_all_occurrences()` only evaluates events that were placed at least once. Completely missing events are handled separately by the required/optional event completion components to avoid double-penalizing the same scheduling failure.


### Priority Weighting

Priority is applied only during final schedule evaluation and is intentionally excluded from search order. This keeps the objective function independent of the optimization algorithm while allowing higher-priority events to have greater influence on the final score.

Priority is mapped to a multiplier using `(priority + 1) / 6`, making priority 5 the baseline (≈1.0×), lower priorities contribute less, and higher priorities contribute proportionally more.

### on_pref_day exponent

Exponent 2.46 was tuned so a 2-hour deviation scores about 0.8

### Preferred Gap Scoring

Preferred spacing is intentionally scored as a soft preference rather than a strict penalty. Since minimum spacing is already enforced as a hard constraint, schedules that deviate by one or two days remain acceptable and receive only a moderate reduction in score. The nonlinear decay rewards ideal spacing while avoiding excessive penalties for small deviations.
