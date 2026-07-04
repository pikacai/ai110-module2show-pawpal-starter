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

## 🖥️ Sample Output

Terminal output from running the demo script (`python main.py`). An owner (Sam)
with two pets and five tasks, scheduled against a 75-minute daily budget:

```
================================================
Today's Schedule for Sam
================================================
Daily Plan — 4 scheduled, 1 skipped, 70 min used

Scheduled:
  07:30  Morning walk (Rex) [30min] — high priority; placed at 07:30 with 75 min free
  08:00  Feed breakfast (Rex) [10min] — high priority; placed at 08:00 with 45 min free
  08:10  Clean litter box (Milo) [10min] — medium priority; placed at 08:10 with 35 min free
  08:20  Play session (Milo) [20min] — low priority; placed at 08:20 with 25 min free

Skipped:
  Long afternoon hike (Rex) — needs 90 min but the day only has 75 min total
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
============================= test session starts ==============================
collected 2 items

tests/test_pawpal.py::test_mark_complete_changes_status PASSED           [ 50%]
tests/test_pawpal.py::test_add_task_increases_pet_task_count PASSED      [100%]

============================== 2 passed in 0.01s ===============================
```

## 📐 Smarter Scheduling

The scheduler goes beyond a flat task list with four algorithmic features. Each
is a small, single-purpose method on `Scheduler` (see `pawpal_system.py`):

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()` | Sorts by "HH:MM" time using a `lambda` key that converts each time to minutes-past-midnight (numeric, not string, comparison). Untimed tasks sort last; stable within a time slot. (`generate_plan` also uses `_sort_by_priority` to place high→medium→low.) |
| Filtering | `Scheduler.filter_by_pet()`, `Scheduler.filter_by_status()` | Return a task subset by pet name (case-insensitive) or by completion status (done vs. to-do). |
| Conflict detection | `Scheduler.detect_conflicts()` | Groups tasks by exact `time` and returns a list of warning strings for any shared slot. Lightweight: it warns instead of raising, so the program keeps running. |
| Recurring tasks | `Task.next_occurrence()`, `Scheduler.mark_task_complete()` | When a "daily"/"weekly" task is completed, a fresh copy is auto-created with `due_date` advanced by `timedelta(days=1)` / `timedelta(weeks=1)`. One-off tasks don't recur. |

Run `python main.py` to see all four exercised in the terminal.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
