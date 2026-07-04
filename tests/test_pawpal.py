"""Quick tests for the PawPal+ logic layer."""

from datetime import date, timedelta

from pawpal_system import Pet, Scheduler, Task


def test_mark_complete_changes_status():
    """Calling mark_complete() flips a task from not-done to done."""
    task = Task("Evening walk", duration_minutes=20, priority="high")
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_add_task_increases_pet_task_count():
    """Adding a task to a pet grows that pet's task list by one."""
    pet = Pet(name="Rex", species="dog")
    assert len(pet.get_tasks()) == 0

    pet.add_task(Task("Morning walk", duration_minutes=30, priority="high"))

    assert len(pet.get_tasks()) == 1


def test_sort_by_time_orders_by_clock_and_pushes_untimed_last():
    """sort_by_time() orders "HH:MM" numerically; untimed tasks go last."""
    scheduler = Scheduler(available_minutes=60)
    tasks = [
        Task("Dinner", 10, time="18:00"),
        Task("Anytime brush", 5, time=""),
        Task("Breakfast", 10, time="08:00"),
    ]

    ordered = scheduler.sort_by_time(tasks)

    assert [t.title for t in ordered] == ["Breakfast", "Dinner", "Anytime brush"]


def test_filter_by_status_and_pet():
    """filter_by_status splits done/todo; filter_by_pet matches names."""
    scheduler = Scheduler(available_minutes=60)
    done = Task("Fed", 10, pet_name="Rex", completed=True)
    todo = Task("Walk", 30, pet_name="Rex")
    other = Task("Litter", 10, pet_name="Milo")
    tasks = [done, todo, other]

    assert scheduler.filter_by_status(tasks, completed=False) == [todo, other]
    assert scheduler.filter_by_status(tasks, completed=True) == [done]
    assert scheduler.filter_by_pet(tasks, "rex") == [done, todo]


def test_detect_conflicts_flags_same_time_slot():
    """Two tasks at the same time produce a warning; distinct times don't."""
    scheduler = Scheduler(available_minutes=60)
    tasks = [
        Task("Walk", 30, pet_name="Rex", time="08:00"),
        Task("Play", 20, pet_name="Milo", time="08:00"),
        Task("Nap", 15, pet_name="Milo", time="10:00"),
    ]

    warnings = scheduler.detect_conflicts(tasks)

    assert len(warnings) == 1
    assert "08:00" in warnings[0]


def test_mark_task_complete_spawns_next_daily_occurrence():
    """Completing a daily task queues a fresh one due the next day."""
    scheduler = Scheduler(available_minutes=60)
    task = Task("Walk", 30, frequency="daily", due_date=date(2026, 7, 4))
    tasks = [task]

    follow_up = scheduler.mark_task_complete(task, tasks)

    assert task.completed is True
    assert follow_up is not None
    assert follow_up.completed is False
    assert follow_up.due_date == date(2026, 7, 4) + timedelta(days=1)
    assert tasks == [task, follow_up]


def test_one_off_task_does_not_recur():
    """A non-recurring task returns no next occurrence."""
    scheduler = Scheduler(available_minutes=60)
    task = Task("Vet visit", 60, frequency="once")

    assert scheduler.mark_task_complete(task) is None


def test_weekly_recurrence_advances_seven_days():
    """Completing a weekly task queues one due exactly a week later."""
    scheduler = Scheduler(available_minutes=60)
    task = Task("Nail trim", 15, frequency="weekly", due_date=date(2026, 7, 4))

    follow_up = scheduler.mark_task_complete(task)

    assert follow_up is not None
    assert follow_up.due_date == date(2026, 7, 4) + timedelta(weeks=1)


# --- Edge cases: the scheduler under pressure --------------------------------


def test_empty_task_list_yields_empty_plan():
    """A pet/owner with no tasks produces a valid, empty plan (no crash)."""
    scheduler = Scheduler(available_minutes=60)

    plan = scheduler.generate_plan([])

    assert plan.scheduled_items == []
    assert plan.skipped_tasks == []
    assert plan.total_minutes_used == 0


def test_generate_plan_places_tasks_high_priority_first():
    """generate_plan schedules high before medium before low priority."""
    scheduler = Scheduler(available_minutes=120)
    tasks = [
        Task("Low job", 10, priority="low"),
        Task("High job", 10, priority="high"),
        Task("Medium job", 10, priority="medium"),
    ]

    plan = scheduler.generate_plan(tasks)

    titles = [item.task.title for item in plan.scheduled_items]
    assert titles == ["High job", "Medium job", "Low job"]


def test_generate_plan_skips_task_larger_than_daily_budget():
    """A task that can't fit the whole day is skipped, not scheduled."""
    scheduler = Scheduler(available_minutes=30)
    tasks = [Task("Marathon hike", 90, priority="high")]

    plan = scheduler.generate_plan(tasks)

    assert plan.scheduled_items == []
    assert len(plan.skipped_tasks) == 1
    assert plan.skipped_tasks[0].title == "Marathon hike"


def test_generate_plan_ignores_already_completed_tasks():
    """Completed tasks are dropped before planning — not scheduled or skipped."""
    scheduler = Scheduler(available_minutes=60)
    tasks = [
        Task("Done deal", 10, priority="high", completed=True),
        Task("Still pending", 10, priority="high"),
    ]

    plan = scheduler.generate_plan(tasks)

    scheduled_titles = [item.task.title for item in plan.scheduled_items]
    assert scheduled_titles == ["Still pending"]
    assert plan.skipped_tasks == []


def test_detect_conflicts_returns_empty_when_all_times_distinct():
    """No two tasks share a slot → no warnings; untimed tasks are ignored."""
    scheduler = Scheduler(available_minutes=60)
    tasks = [
        Task("Walk", 30, time="08:00"),
        Task("Feed", 10, time="09:00"),
        Task("Brush", 5, time=""),  # untimed — must not be flagged
    ]

    assert scheduler.detect_conflicts(tasks) == []
