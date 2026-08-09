# Shared Scheduler Benchmark

All scheduling algorithms should run against `challenging_week_v1` without
changing its event definitions. Each run must construct fresh events with
`build_events()` and begin with an empty `Schedule`.

The scenario contains required and optional events, recurring events, narrow
and overlapping windows, competing priorities, minimum gaps, preferred gaps,
and 15-minute slot boundaries. This makes completion, legality, placement
quality, and runtime comparable across algorithms.

Run the current baseline from the repository root:

```powershell
python -m benchmarks.run_benchmarks --algorithm greedy
```

Reports are written as both JSON and Markdown under
`docs/benchmark_reports/`. Add future algorithms to the `ALGORITHMS` registry
in `run_benchmarks.py`; adapters must return a schedule, status, failures,
runtime, and number of candidate placements evaluated.

Do not tune the scenario per algorithm. Version the scenario name and create a
new definition when benchmark inputs need to change so historical reports stay
comparable.
