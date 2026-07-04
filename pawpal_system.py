"""PawPal+ logic layer: backend classes translated from diagrams/uml.mmd.

Implements the four core classes (Task, Pet, Owner, Scheduler) plus the two
supporting data holders (ScheduledTask, DailyPlan) that make up a working
daily-planning engine for pet care.
"""

from dataclasses import dataclass, field
from typing import List, Optional

# Lower rank = scheduled earlier. Used by Scheduler._sort_by_priority so that
# priority is compared numerically instead of by the (nonsensical) alphabetical
# ordering of the strings "high"/"low"/"medium".
_PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}


@dataclass
class Task:
    """A single unit of pet care — what needs to happen and how long it takes.

    A plain data holder: it describes an activity but knows nothing about how
    it gets scheduled (that lives in Scheduler).
    """

    title: str
    duration_minutes: int
    priority: str = "medium"  # one of: "low", "medium", "high"
    pet_name: str = ""  # which pet this task belongs to, so the plan can identify it
    frequency: str = "daily"  # e.g. "daily", "weekly"
    completed: bool = False  # completion status

    def __repr__(self) -> str:
        status = "done" if self.completed else "todo"
        owner = f" for {self.pet_name}" if self.pet_name else ""
        return (
            f"Task({self.title!r}{owner}, {self.duration_minutes}min, "
            f"{self.priority}, {self.frequency}, {status})"
        )

    def mark_complete(self) -> None:
        """Mark this task as done so the scheduler stops planning it."""
        self.completed = True


@dataclass
class Pet:
    """Stores a pet's details and the list of care tasks it needs."""

    name: str
    species: str
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task to this pet, tagging it with the pet's name."""
        # Stamp the task with this pet's name so it stays identifiable once the
        # Scheduler flattens tasks from every pet into one list.
        task.pet_name = self.name
        self.tasks.append(task)

    def get_tasks(self) -> List[Task]:
        """Return this pet's list of care tasks."""
        return self.tasks


@dataclass
class Owner:
    """Manages multiple pets and exposes their tasks + scheduling preferences."""

    name: str
    preferences: dict = field(default_factory=dict)
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        self.pets.append(pet)

    def get_preferences(self) -> dict:
        """Return the owner's scheduling preferences."""
        return self.preferences

    def get_all_tasks(self) -> List[Task]:
        """Flatten every pet's tasks into one list for the scheduler."""
        all_tasks: List[Task] = []
        for pet in self.pets:
            all_tasks.extend(pet.get_tasks())
        return all_tasks


@dataclass
class ScheduledTask:
    """Pairs a Task with the time it was placed at and why."""

    task: Task
    start_time: str
    reasoning: str


@dataclass
class DailyPlan:
    """The scheduler's output: what got placed, what didn't, and why.

    `skipped_tasks[i]` corresponds to `skip_reasons[i]` — the two lists are
    kept in lockstep by `add_skipped_task`.
    """

    scheduled_items: List[ScheduledTask] = field(default_factory=list)
    skipped_tasks: List[Task] = field(default_factory=list)
    skip_reasons: List[str] = field(default_factory=list)
    total_minutes_used: int = 0

    def add_scheduled_task(self, item: ScheduledTask) -> None:
        """Record a placed task and add its duration to the running total."""
        self.scheduled_items.append(item)
        self.total_minutes_used += item.task.duration_minutes

    def add_skipped_task(self, task: Task, reason: str) -> None:
        """Record a task that didn't fit, along with the reason it was skipped."""
        self.skipped_tasks.append(task)
        self.skip_reasons.append(reason)

    def explain(self) -> str:
        """Produce a human-readable summary of the plan and its reasoning."""
        lines = [
            f"Daily Plan — {len(self.scheduled_items)} scheduled, "
            f"{len(self.skipped_tasks)} skipped, {self.total_minutes_used} min used"
        ]

        if self.scheduled_items:
            lines.append("")
            lines.append("Scheduled:")
            for item in self.scheduled_items:
                task = item.task
                owner = f" ({task.pet_name})" if task.pet_name else ""
                lines.append(
                    f"  {item.start_time}  {task.title}{owner} "
                    f"[{task.duration_minutes}min] — {item.reasoning}"
                )

        if self.skipped_tasks:
            lines.append("")
            lines.append("Skipped:")
            for task, reason in zip(self.skipped_tasks, self.skip_reasons):
                owner = f" ({task.pet_name})" if task.pet_name else ""
                lines.append(f"  {task.title}{owner} — {reason}")

        return "\n".join(lines)


class Scheduler:
    """The brain: retrieves, organizes, and places tasks into a daily plan.

    It deliberately consumes a flat ``List[Task]`` rather than reaching into an
    Owner. The caller wires the two together:

        plan = scheduler.generate_plan(owner.get_all_tasks(), owner.get_preferences())

    This keeps the scheduling algorithm decoupled from the Owner/Pet structure
    and easy to test in isolation.
    """

    def __init__(self, available_minutes: int):
        """Create a scheduler with a daily time budget in minutes."""
        self.available_minutes = available_minutes

    def generate_plan(
        self, tasks: List[Task], preferences: Optional[dict] = None
    ) -> DailyPlan:
        """Sort tasks by priority and greedily place what fits into the day."""
        preferences = preferences or {}
        clock = self._parse_time(preferences.get("day_start", "08:00"))

        plan = DailyPlan()

        # Already-completed tasks don't need planning; drop them up front.
        pending = [task for task in tasks if not task.completed]
        ordered = self._sort_by_priority(pending)

        remaining = self.available_minutes
        for task in ordered:
            if self._fits_in_remaining_time(task, remaining):
                start_str = self._format_time(clock)
                reasoning = (
                    f"{task.priority} priority; placed at {start_str} with "
                    f"{remaining} min free"
                )
                plan.add_scheduled_task(ScheduledTask(task, start_str, reasoning))
                clock += task.duration_minutes
                remaining -= task.duration_minutes
            else:
                if task.duration_minutes > self.available_minutes:
                    reason = (
                        f"needs {task.duration_minutes} min but the day only has "
                        f"{self.available_minutes} min total"
                    )
                else:
                    reason = (
                        f"needs {task.duration_minutes} min but only {remaining} min "
                        f"left after higher-priority tasks"
                    )
                plan.add_skipped_task(task, reason)

        return plan

    def _sort_by_priority(self, tasks: List[Task]) -> List[Task]:
        """Return tasks ordered high→medium→low, stable within a priority."""
        # Stable sort: high before medium before low; equal priorities keep
        # their insertion order so results are deterministic. Unknown priority
        # strings fall back to "medium" rank rather than crashing.
        return sorted(
            tasks, key=lambda task: _PRIORITY_RANK.get(task.priority.lower(), 1)
        )

    def _fits_in_remaining_time(self, task: Task, remaining: int) -> bool:
        """Return True if the task's duration fits in the remaining minutes."""
        return task.duration_minutes <= remaining

    @staticmethod
    def _parse_time(hhmm: str) -> int:
        """Convert an 'HH:MM' string into minutes past midnight."""
        try:
            hours, minutes = hhmm.split(":")
            return int(hours) * 60 + int(minutes)
        except (ValueError, AttributeError):
            return 8 * 60  # default to 08:00 on malformed input

    @staticmethod
    def _format_time(total_minutes: int) -> str:
        """Convert minutes past midnight back into an 'HH:MM' string."""
        total_minutes %= 24 * 60
        return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"
