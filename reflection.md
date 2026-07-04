# PawPal+ Project Reflection

## 1. System Design

**Core user actions**

Before drafting the UML, I identified three core actions a user of PawPal+ should be able to perform:

1. **Add a pet and owner profile** — The user can enter basic owner info (name, preferences) and pet info (name, species) so the system knows who and what it's planning care for.
2. **Add a pet care task** — The user can add a task (e.g., morning walk, feeding, meds) with a duration and priority, building up the list of things that need to happen that day.
3. **Generate and view today's plan** — The user can trigger the scheduler to turn the list of tasks into an ordered daily plan that fits the available time and respects priorities, and see the resulting schedule along with the reasoning behind it.

**a. Initial design**

My initial UML (see `diagrams/uml.mmd`) is organized around the three core actions above, with each class owning one responsibility:

- **Owner** — holds the owner's name and preferences (a `dict`) and the list of pets they manage. Its methods are `add_pet` (register a pet) and `get_preferences` (expose preferences to the scheduler later). It is the top of the ownership hierarchy: one owner has many pets.
- **Pet** — holds the pet's name and species and the list of care tasks belonging to that pet. `add_task` appends a task and `get_tasks` returns them. One pet has many tasks.
- **Task** — a plain data holder for one piece of care: `title`, `duration_minutes`, and `priority` (a string constrained by convention to `"low"`, `"medium"`, or `"high"`). It doesn't know about scheduling — it just describes "what needs to happen." Its only behavior is `__repr__` for readable output.
- **Scheduler** — the only class that contains scheduling logic. Constructed with `available_minutes` for the day, it takes a list of tasks, sorts them by priority, and decides what fits: `generate_plan` (the entry point), plus the private helpers `_sort_by_priority` and `_fits_in_remaining_time`.
- **DailyPlan** — the output of the scheduler: `scheduled_items` (an ordered list of `ScheduledTask`s), `skipped_tasks` (tasks that didn't fit), and `total_minutes_used`. `explain()` produces the human-readable reasoning ("why each task was chosen and when it happens"), while `add_scheduled_task` and `add_skipped_task` let the scheduler build the plan incrementally.
- **ScheduledTask** — pairs a `Task` with its assigned `start_time` and a short `reasoning` string, so the plan can explain itself without `DailyPlan` needing to re-derive that info.

The split between `Task` (data) and `Scheduler` (behavior) was intentional: it keeps the scheduling algorithm in one place and testable in isolation, rather than scattering "if priority is high, do X" logic across the `Task` or `Pet` classes. Keeping `priority` a simple string (rather than an enum) keeps the data classes lightweight; the tradeoff is that valid values are enforced by convention and by the `Scheduler`'s sorting logic rather than by the type system.

**b. Design changes**

Yes. I asked my AI coding assistant to review the `pawpal_system.py` skeleton for missing relationships and logic bottlenecks. Its feedback led to three changes that closed real gaps in the end-to-end "generate today's plan" workflow:

1. **Gave the `Scheduler` access to owner preferences.** *Problem the AI flagged:* `Owner` has a `preferences` dict and every `ScheduledTask` carries a `reasoning` string, which implies scheduling decisions should reflect preferences (e.g., "walk before breakfast") — but `generate_plan(tasks)` only received a flat task list, so the scheduler could never actually see or explain a preference-driven choice. *Change:* `generate_plan` now takes an optional `preferences: dict`, and I added a `Scheduler ..> Owner : reads preferences` dependency to the UML. *Why:* without this link the `reasoning` field was decorative; wiring preferences in makes the "why" in the plan honest.

2. **Added `Owner.get_all_tasks()` to aggregate tasks across pets.** *Problem the AI flagged:* nothing in the design actually produced the `List[Task]` that `generate_plan` consumes — the chain Owner → pets → tasks → scheduler was never closed, so the third core action had no home. *Change:* `Owner` now has `get_all_tasks()` that flattens every pet's tasks into one list. *Why:* it gives the "generate today's plan" action a clear entry point instead of leaving the flattening to ad-hoc calling code.

3. **Added `pet_name` to `Task`.** *Problem the AI flagged:* once tasks from multiple pets are flattened into one list, there's no back-reference to the owning pet, so `DailyPlan.explain()` could say "Walk at 9:00" but not "Walk **Rex** at 9:00." *Change:* `Task` now carries a `pet_name` field (defaulted, so existing construction still works). *Why:* the plan's whole purpose is a readable cross-pet schedule, and pet identity is needed for that.

**What I did *not* change:** the AI also suggested replacing `priority: str` with an enum and computing `start_time` from a real day-start clock. I kept `priority` as a string on purpose (documented in 1a — lightweight data classes, values enforced by the scheduler's sort logic) and left the `start_time` computation as an implementation detail for the scheduling logic rather than a structural change to the class design.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler weighs three constraints when building a `DailyPlan`:

1. **Available time (a hard budget).** `Scheduler(available_minutes=...)` sets a
   ceiling on the day. `generate_plan` tracks a `remaining` counter and only
   places a task if `_fits_in_remaining_time` — otherwise it's recorded in
   `skipped_tasks` with a reason. This is the one constraint that can never be
   violated, so it's checked on every placement.
2. **Priority (the ordering rule).** Before placing anything, `_sort_by_priority`
   orders pending tasks high → medium → low via a numeric `_PRIORITY_RANK` map
   (so "high" beats "low" numerically rather than alphabetically). Because the
   budget is greedy, ordering *is* the decision: whatever sorts first gets first
   claim on the remaining minutes.
3. **Owner preferences (the starting point).** `preferences["day_start"]` sets
   the clock the plan counts up from, so start times reflect when the owner
   actually begins their day.

I decided time mattered most because it's the constraint that makes the plan
*honest* — a schedule that promises more than the day holds is useless. Priority
came second as the fair way to resolve competition for that scarce time, and
preferences last because they shape presentation (when the day starts) rather
than what fits.

**b. Tradeoffs**

The clearest tradeoff is in **conflict detection** (`Scheduler.detect_conflicts`).
It only flags tasks that share the *exact same* `"HH:MM"` start time — it does
**not** account for overlapping durations. A 30-minute "Morning walk" at `08:00`
and a "Feed breakfast" at `08:15` genuinely collide in the real world, but the
detector stays silent because their start strings differ. I chose exact-match
grouping because it's O(n) with a single dictionary pass, trivial to read, and
returns plain warning strings instead of raising — the program keeps running and
the owner simply sees a heads-up.

That tradeoff is reasonable for this scenario: PawPal+ is a lightweight personal
planning aid, not an operating-room scheduler. Pet-care tasks are short and the
owner is a human who can eyeball a near-miss; the cost of a missed 15-minute
overlap is low, while the benefit of simple, crash-free, easily-understood code
is high. Interval-overlap detection (sort by start, compare each task's
`start + duration` against the next start) would be the natural next step if the
app ever needed hard, back-to-back time blocking.

---

## 3. AI Collaboration

**a. How you used AI**

I used my AI coding assistant at three distinct stages, and deliberately kept
them in **separate chat sessions** so each conversation stayed focused:

- **Design review.** After sketching the UML, I asked the assistant to critique
  the class skeleton for missing relationships and bottlenecks. This surfaced the
  three gaps documented in section 1b (preferences never reaching the scheduler,
  no `get_all_tasks()`, no `pet_name` back-reference).
- **Implementation.** I used it to draft the small single-purpose methods on
  `Scheduler` (sorting, filtering, conflict detection, recurrence) and to explain
  Python idioms I was unsure about — e.g. why a `lambda` sort key over
  minutes-past-midnight is safer than sorting `"HH:MM"` strings directly.
- **Testing.** In a fresh session, I asked "what are the most important edge
  cases for a pet scheduler with sorting and recurring tasks?" That produced the
  edge-case list I turned into tests (empty task list, over-budget task,
  completed-task exclusion, weekly rollover).

The most helpful prompts were **specific and grounded in my actual files** —
attaching `pawpal_system.py` and asking "what's missing to close the
Owner → Pet → Task → Scheduler chain?" got far better answers than open-ended
"how should I build a scheduler?" questions.

**b. Judgment and verification**

The clearest moment I *didn't* accept a suggestion: the assistant recommended
replacing `priority: str` with a proper `Enum` and computing start times from a
real clock object. I rejected the enum change on purpose — for a lightweight
personal planner, a plain string keeps the data classes trivial to construct in
tests and in the UI, and the valid values are already enforced by the
scheduler's sort logic (unknown priorities fall back to "medium" rank rather
than crashing). I kept the design decision and documented the tradeoff instead
of adding type-system ceremony.

I verified AI output two ways: by **reading it before saving** (I had the
assistant explain any test code I didn't fully understand, per the Phase 5
workflow) and by **running `python -m pytest` and `python main.py`** to confirm
behavior matched the explanation. When a suggested test and my logic disagreed,
I traced which side was actually wrong rather than blindly "fixing" the code to
match the test.

---

## 4. Testing and Verification

**a. What you tested**

The suite in `tests/test_pawpal.py` (13 tests, all passing) covers:

- **Data model** — `mark_complete()` flips status; `Pet.add_task()` grows the
  list. These are the primitives everything else depends on.
- **Sorting correctness** — `sort_by_time()` returns chronological order with
  untimed tasks last, and `generate_plan()` places high-priority tasks first.
  Sorting *is* the scheduling decision, so getting the order wrong silently
  produces a wrong plan.
- **Filtering** — by pet (case-insensitive) and by completion status.
- **Conflict detection** — two tasks at one time yield exactly one warning;
  distinct/untimed times yield none. This pins down the exact boundary of the
  lightweight algorithm.
- **Recurrence logic** — completing a daily task queues one due the next day, a
  weekly task advances seven days, and one-off tasks don't recur. Recurrence
  touches date math, which is easy to get subtly wrong.
- **Budget edge cases** — an empty task list yields a valid empty plan (no
  crash), a task larger than the whole day is skipped rather than scheduled, and
  already-completed tasks are dropped before planning.

These mattered because they target the places a scheduler *silently* misbehaves:
wrong order, off-by-one date rollovers, and empty/over-budget inputs that a
happy-path demo would never exercise.

**b. Confidence**

**★★★★☆ (4 / 5).** All 13 tests pass and exercise both the happy paths and the
edges most likely to hide bugs. I hold back the fifth star for two reasons, both
known and documented rather than untested: conflict detection compares only
exact start times (not overlapping durations), and the Streamlit UI doesn't yet
validate that a typed time is a well-formed `HH:MM`.

If I had more time I'd add tests for: malformed time strings reaching
`_parse_time`, back-to-back duration overlap (once interval-based conflict
detection exists), a task whose duration is exactly the remaining budget
(boundary), and multiple recurring tasks rolling forward together across several
"complete" cycles.

---

## 5. Reflection

**a. What went well**

I'm most satisfied with the clean split between **data** (`Task`, `Pet`,
`Owner`) and **behavior** (`Scheduler`). Because all the scheduling logic lives
in small, single-purpose methods that take plain lists and return plain values,
every algorithm was testable in isolation — I could verify sorting, conflict
detection, and recurrence without ever standing up the Streamlit UI. That
separation is also what let the UI stay thin: `app.py` just calls
`sort_by_time`, `detect_conflicts`, and `generate_plan` and renders the results.

**b. What you would improve**

The biggest redesign would be **interval-based conflict detection**: sort by
start time and compare each task's `start + duration` against the next start, so
a 30-minute walk at 08:00 correctly conflicts with a feeding at 08:15. I'd also
give the scheduler a smarter fallback than greedy-by-priority — for example,
trying to fit a lower-priority short task into leftover minutes that a skipped
high-priority long task can't use. Finally, I'd add input validation and a
"mark complete / show recurrence" control in the UI so the recurrence feature is
visible to the end user, not just the CLI demo.

**c. Key takeaway**

The most important thing I learned is that being the **lead architect** means
owning the boundaries and the tradeoffs, not the typing. The AI was excellent at
producing method bodies and spotting gaps, but the decisions that shaped the
system — keeping `priority` a string, making conflict detection deliberately
lightweight, treating time as a hard constraint and priority as the tiebreaker —
were mine to make and defend. AI accelerates the *how*; the human still owns the
*what* and *why*, and tests are how you hold both of you accountable.
