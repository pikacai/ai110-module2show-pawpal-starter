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

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

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

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
