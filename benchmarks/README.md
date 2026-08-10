# Shared Scheduler Benchmarks

All algorithms run against the frozen `optimization_stress_v2` event set from
`optimization_stress.py`. The event definitions use heterogeneous fixed,
narrow, broad, multi-window, and competing availability patterns. Required and
optional events deliberately have mixed priorities.

The scheduling algorithms receive only fresh events from `build_events()` and
an empty `Schedule`. Audit layouts are isolated in
`optimization_stress_audit.py` and are never passed to an algorithm.

Before every measured run, the audit must verify all of these gates:

- 10 complete hard-constraint-valid schedules.
- At least two changed occurrences and 32 slots of aggregate displacement
  between every pair of audited layouts.
- At least 20% spread between the lowest and highest Issue #5 scores.

The audit evidence, including every placement and score, is written to
`docs/benchmark_reports/audit/`. Its scenario checksum identifies the exact
frozen input used by algorithm reports.

Each algorithm is measured on two separate results:

- Feasibility: every requested occurrence is placed and the schedule is valid.
- Optimization: the Issue #5 score of the produced schedule.

Run the current baseline from the repository root:

```powershell
python -m benchmarks.run_benchmarks --algorithm greedy
```

Algorithm reports are timestamped under
`docs/benchmark_reports/<algorithm>/`; existing runs are never overwritten.
Future algorithm adapters belong in the `ALGORITHMS` registry in
`run_benchmarks.py` and must return a schedule, status, failures, runtime, and
number of candidate placements evaluated.

Do not edit a frozen scenario in response to algorithm performance. Create a
new scenario version and regenerate its audit if the benchmark itself changes.
