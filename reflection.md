# PawPal+ Project Reflection

## 1. System Design

**Core user actions**

Before drafting the UML, I identified three core actions a user of PawPal+ should be able to perform:

1. **Add a pet and owner profile** — The user can enter basic owner info (name, preferences) and pet info (name, species) so the system knows who and what it's planning care for.
2. **Add a pet care task** — The user can add a task (e.g., morning walk, feeding, meds) with a duration and priority, building up the list of things that need to happen that day.
3. **Generate and view today's plan** — The user can trigger the scheduler to turn the list of tasks into an ordered daily plan that fits the available time and respects priorities, and see the resulting schedule along with the reasoning behind it.

**a. Initial design**

My initial UML (see `diagrams/uml.mmd`) is organized around the three core actions above, with each class owning one responsibility:

- **Owner** — holds the owner's name and preferences, and the list of pets they manage (`add_pet`).
- **Pet** — holds the pet's name and species, and the list of care tasks for that pet (`add_task`, `get_tasks`).
- **Priority** — an enum (`LOW`, `MEDIUM`, `HIGH`) so priority is a constrained value instead of a free-text string, which keeps sorting/comparison logic simple later.
- **Task** — a plain data holder for one piece of care (title, duration in minutes, priority). It doesn't know about scheduling — it just describes "what needs to happen."
- **Scheduler** — the only class that contains scheduling logic. It takes a list of tasks and the available minutes in the day, sorts by priority, and decides what fits (`generate_plan`, `sort_by_priority`, `fits_in_remaining_time`).
- **DailyPlan** — the output of the scheduler: an ordered list of `ScheduledTask`s plus any tasks that didn't fit, with an `explain()` method that produces the human-readable reasoning ("why each task was chosen and when it happens").
- **ScheduledTask** — pairs a `Task` with its assigned start time and a short reasoning string, so the plan can explain itself without the `DailyPlan` needing to re-derive that info.

The split between `Task` (data) and `Scheduler` (behavior) was intentional: it keeps the scheduling algorithm in one place and testable in isolation, rather than scattering "if priority is high, do X" logic across the `Task` or `Pet` classes.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

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
