"""Demo script for PawPal+ — a temporary testing ground.

Builds an owner with two pets and several care tasks, then exercises the
smarter-scheduling algorithms (sorting, filtering, conflict detection, and
recurring tasks) and prints today's plan to the terminal.

Run with:  python main.py
"""

from pawpal_system import Owner, Pet, Scheduler, Task


def main() -> None:
    # An owner with a preferred start time for the day.
    owner = Owner(name="Sam", preferences={"day_start": "07:30"})

    # Two pets with care tasks. Tasks are added intentionally OUT OF ORDER (by
    # time) and one pair shares a time slot, so the sorting and conflict-
    # detection algorithms have something real to do.
    rex = Pet(name="Rex", species="dog")
    rex.add_task(Task("Long afternoon hike", 90, priority="low", time="16:00"))
    rex.add_task(Task("Morning walk", 30, priority="high", time="07:30"))
    rex.add_task(Task("Feed breakfast", 10, priority="high", time="08:00"))

    milo = Pet(name="Milo", species="cat")
    milo.add_task(Task("Clean litter box", 10, priority="medium", time="09:00"))
    # Same time as Rex's breakfast → an intentional scheduling conflict.
    milo.add_task(Task("Play session", 20, priority="low", time="08:00"))

    owner.add_pet(rex)
    owner.add_pet(milo)

    scheduler = Scheduler(available_minutes=75)
    tasks = owner.get_all_tasks()

    # --- Sorting by time --------------------------------------------------
    print("=" * 56)
    print("Tasks sorted by time (Scheduler.sort_by_time)")
    print("=" * 56)
    for task in scheduler.sort_by_time(tasks):
        print(f"  {task.time or '  ?  '}  {task.title} ({task.pet_name})")

    # --- Filtering --------------------------------------------------------
    print("\n" + "=" * 56)
    print("Filtering (Scheduler.filter_by_pet / filter_by_status)")
    print("=" * 56)
    print("Rex's tasks:")
    for task in scheduler.filter_by_pet(tasks, "Rex"):
        print(f"  - {task.title}")
    print("Still to do (not completed):")
    for task in scheduler.filter_by_status(tasks, completed=False):
        print(f"  - {task.title} ({task.pet_name})")

    # --- Conflict detection ----------------------------------------------
    print("\n" + "=" * 56)
    print("Conflict detection (Scheduler.detect_conflicts)")
    print("=" * 56)
    conflicts = scheduler.detect_conflicts(tasks)
    if conflicts:
        for warning in conflicts:
            print(f"  ⚠️  {warning}")
    else:
        print("  No conflicts found.")

    # --- Recurring tasks --------------------------------------------------
    print("\n" + "=" * 56)
    print("Recurring tasks (Scheduler.mark_task_complete)")
    print("=" * 56)
    walk = rex.get_tasks()[1]  # "Morning walk", frequency defaults to "daily"
    print(f"  Completing: {walk.title} (due {walk.due_date}, {walk.frequency})")
    follow_up = scheduler.mark_task_complete(walk, tasks)
    if follow_up:
        print(f"  Auto-created next occurrence due {follow_up.due_date}")

    # --- Priority-based daily plan ---------------------------------------
    print("\n" + "=" * 56)
    print(f"Today's Schedule for {owner.name}")
    print("=" * 56)
    plan = scheduler.generate_plan(tasks, owner.get_preferences())
    print(plan.explain())


if __name__ == "__main__":
    main()
