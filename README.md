# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## ✨ Features

- **Priority-fitted daily plan** — `generate_plan()` sorts pending tasks
  high → medium → low and greedily places what fits the day's minute budget,
  skipping (with a reason) anything that doesn't.
- **Sorting by time** — `sort_by_time()` orders tasks chronologically by their
  `"HH:MM"` time (numeric, not string, comparison); untimed tasks sort last.
- **Filtering** — `filter_by_pet()` (case-insensitive) and `filter_by_status()`
  (done vs. to-do) return focused task subsets.
- **Conflict warnings** — `detect_conflicts()` flags any two tasks booked at the
  same clock time, returning warnings instead of raising.
- **Daily / weekly recurrence** — completing a recurring task auto-creates its
  next occurrence with the due date advanced by one day/week; one-off tasks
  don't recur.
- **Explainable output** — every scheduled task carries a `reasoning` string and
  `DailyPlan.explain()` prints a full human-readable summary.

## 📐 Smarter Scheduling

Each feature is a small, single-purpose method on `Scheduler` (see
`pawpal_system.py`):

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()` | Sorts by "HH:MM" time using a `lambda` key that converts each time to minutes-past-midnight (numeric, not string, comparison). Untimed tasks sort last; stable within a time slot. (`generate_plan` also uses `_sort_by_priority` to place high→medium→low.) |
| Filtering | `Scheduler.filter_by_pet()`, `Scheduler.filter_by_status()` | Return a task subset by pet name (case-insensitive) or by completion status (done vs. to-do). |
| Conflict detection | `Scheduler.detect_conflicts()` | Groups tasks by exact `time` and returns a list of warning strings for any shared slot. Lightweight: it warns instead of raising, so the program keeps running. |
| Recurring tasks | `Task.next_occurrence()`, `Scheduler.mark_task_complete()` | When a "daily"/"weekly" task is completed, a fresh copy is auto-created with `due_date` advanced by `timedelta(days=1)` / `timedelta(weeks=1)`. One-off tasks don't recur. |

Run `python main.py` to see all four exercised in the terminal.

## 🧪 Testing PawPal+

Run the full automated suite from the project root:

```bash
python -m pytest
```

The suite in `tests/test_pawpal.py` covers both the happy paths and the edge
cases that matter for a scheduler:

- **Data model** — `mark_complete()` flips a task's status; `Pet.add_task()`
  grows the task list.
- **Sorting correctness** — tasks come back in chronological order and untimed
  tasks sort last; `generate_plan()` places high-priority tasks first.
- **Filtering** — by pet (case-insensitive) and by completion status.
- **Conflict detection** — two tasks at the same time produce exactly one
  warning; distinct/untimed times produce none.
- **Recurrence logic** — completing a daily task queues a fresh one due the next
  day, a weekly task advances seven days, and one-off tasks don't recur.
- **Budget edge cases** — an empty task list yields a valid empty plan, a task
  larger than the whole day's budget is skipped (not scheduled), and already
  completed tasks are dropped before planning.

Successful run:

```
============================= test session starts ==============================
platform darwin -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/pikaka/ai110-module2show-pawpal-starter
plugins: anyio-4.14.1
collected 13 items

tests/test_pawpal.py::test_mark_complete_changes_status PASSED           [  7%]
tests/test_pawpal.py::test_add_task_increases_pet_task_count PASSED      [ 15%]
tests/test_pawpal.py::test_sort_by_time_orders_by_clock_and_pushes_untimed_last PASSED [ 23%]
tests/test_pawpal.py::test_filter_by_status_and_pet PASSED               [ 30%]
tests/test_pawpal.py::test_detect_conflicts_flags_same_time_slot PASSED  [ 38%]
tests/test_pawpal.py::test_mark_task_complete_spawns_next_daily_occurrence PASSED [ 46%]
tests/test_pawpal.py::test_one_off_task_does_not_recur PASSED            [ 53%]
tests/test_pawpal.py::test_weekly_recurrence_advances_seven_days PASSED  [ 61%]
tests/test_pawpal.py::test_empty_task_list_yields_empty_plan PASSED      [ 69%]
tests/test_pawpal.py::test_generate_plan_places_tasks_high_priority_first PASSED [ 76%]
tests/test_pawpal.py::test_generate_plan_skips_task_larger_than_daily_budget PASSED [ 84%]
tests/test_pawpal.py::test_generate_plan_ignores_already_completed_tasks PASSED [ 92%]
tests/test_pawpal.py::test_detect_conflicts_returns_empty_when_all_times_distinct PASSED [100%]

============================== 13 passed in 0.02s ==============================
```

**Confidence level: ★★★★☆ (4 / 5).** All 13 tests pass and cover the core
algorithms plus the tricky edges (empty input, over-budget tasks, recurrence
rollover, conflict boundaries). I hold back the fifth star because conflict
detection only compares exact start times, not overlapping durations, and time
inputs aren't yet validated in the UI — both are known, documented tradeoffs
rather than untested behavior.

## 📸 Demo Walkthrough

### The UI (`streamlit run app.py`)

The app is a single scrollable page backed by the `Scheduler` logic layer. A pet
owner can:

1. **Set up their profile** — enter an owner name and a preferred day-start time.
2. **Add pets** — name + species; the app confirms with `st.success` and lists
   each pet with its task count.
3. **Add tasks** — pick a pet, then enter a title, duration, priority, and an
   optional `HH:MM` time. Every task appears in an "All tasks" table.
4. **Generate a schedule** — set the day's available minutes and click
   **Generate schedule**. The app then shows:
   - **Conflict warnings** (`st.warning`) for any two tasks at the same time, or
     a green "no conflicts" message.
   - **Today at a glance** — every task sorted chronologically (`sort_by_time`).
   - **The fitted plan** — a table of what was scheduled, when, and *why*, plus a
     warning for each task skipped for lack of time. The full text summary from
     `plan.explain()` is tucked into an expander.

### Example workflow

> Add owner **Sam** → add pet **Rex** (dog) → add task "Morning walk" (30 min,
> high, 07:30) and "Long afternoon hike" (90 min, low, 16:00) → add pet **Milo**
> (cat) with "Play session" (20 min, low, 08:00) → set the budget to 75 minutes →
> **Generate schedule**. Rex's walk and the shorter tasks are placed high-priority
> first, the 90-minute hike is flagged as skipped (it exceeds the 75-minute day),
> and any same-time clash is called out as a conflict warning.

### Sample CLI output (`python main.py`)

The demo script exercises all four algorithms against an owner (Sam) with two
pets and five tasks on a 75-minute budget:

```
========================================================
Tasks sorted by time (Scheduler.sort_by_time)
========================================================
  07:30  Morning walk (Rex)
  08:00  Feed breakfast (Rex)
  08:00  Play session (Milo)
  09:00  Clean litter box (Milo)
  16:00  Long afternoon hike (Rex)

========================================================
Conflict detection (Scheduler.detect_conflicts)
========================================================
  ⚠️  Conflict at 08:00: Feed breakfast (Rex), Play session (Milo)

========================================================
Recurring tasks (Scheduler.mark_task_complete)
========================================================
  Completing: Morning walk (due None, daily)
  Auto-created next occurrence due 2026-07-05

========================================================
Today's Schedule for Sam
========================================================
Daily Plan — 4 scheduled, 1 skipped, 70 min used

Scheduled:
  07:30  Feed breakfast (Rex) [10min] — high priority; placed at 07:30 with 75 min free
  07:40  Morning walk (Rex) [30min] — high priority; placed at 07:40 with 65 min free
  08:10  Clean litter box (Milo) [10min] — medium priority; placed at 08:10 with 35 min free
  08:20  Play session (Milo) [20min] — low priority; placed at 08:20 with 25 min free

Skipped:
  Long afternoon hike (Rex) — needs 90 min but the day only has 75 min total
```

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
