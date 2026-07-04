"""Demo script for PawPal+ — a temporary testing ground.

Builds an owner with two pets and several care tasks, runs the scheduler,
and prints today's schedule to the terminal.

Run with:  python main.py
"""

from pawpal_system import Owner, Pet, Scheduler, Task


def main() -> None:
    # An owner with a preferred start time for the day.
    owner = Owner(name="Sam", preferences={"day_start": "07:30"})

    # Two pets, each with their own care tasks (different durations).
    rex = Pet(name="Rex", species="dog")
    rex.add_task(Task("Morning walk", duration_minutes=30, priority="high"))
    rex.add_task(Task("Feed breakfast", duration_minutes=10, priority="high"))
    rex.add_task(Task("Long afternoon hike", duration_minutes=90, priority="low"))

    milo = Pet(name="Milo", species="cat")
    milo.add_task(Task("Clean litter box", duration_minutes=10, priority="medium"))
    milo.add_task(Task("Play session", duration_minutes=20, priority="low"))

    owner.add_pet(rex)
    owner.add_pet(milo)

    # The scheduler has a 75-minute budget for the day. It reads the flattened
    # task list and the owner's preferences.
    scheduler = Scheduler(available_minutes=75)
    plan = scheduler.generate_plan(owner.get_all_tasks(), owner.get_preferences())

    print("=" * 48)
    print(f"Today's Schedule for {owner.name}")
    print("=" * 48)
    print(plan.explain())


if __name__ == "__main__":
    main()
