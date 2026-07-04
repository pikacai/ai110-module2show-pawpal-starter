import streamlit as st

# Step 1: Establish the Connection
# Bring the logic-layer classes into the UI so buttons can call real methods.
from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ app. The UI below is wired to the logic layer in
`pawpal_system.py` — adding a pet or a task creates real `Pet`/`Task` objects
that persist in memory while you use the app.
"""
)

# Step 2: Manage the Application "Memory"
# Streamlit re-runs this whole script top-to-bottom on every interaction, so an
# Owner created here would be "reborn" empty each time. We stash a single Owner
# in st.session_state (a dict that survives re-runs) and only create it once.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", preferences={"day_start": "08:00"})

owner = st.session_state.owner

st.divider()

# ---------------------------------------------------------------------------
# Owner settings
# ---------------------------------------------------------------------------
st.subheader("Owner")
owner.name = st.text_input("Owner name", value=owner.name)
day_start = st.text_input(
    "Preferred day start (HH:MM)",
    value=owner.preferences.get("day_start", "08:00"),
)
owner.preferences["day_start"] = day_start

st.divider()

# ---------------------------------------------------------------------------
# Step 3: Wiring UI Actions to Logic — Add a Pet
# ---------------------------------------------------------------------------
st.subheader("Add a Pet")
with st.form("add_pet_form", clear_on_submit=True):
    new_pet_name = st.text_input("Pet name", value="Mochi")
    new_species = st.selectbox("Species", ["dog", "cat", "other"])
    add_pet_submitted = st.form_submit_button("Add pet")

if add_pet_submitted:
    if new_pet_name.strip():
        # Create a real Pet object and register it on the persisted Owner.
        owner.add_pet(Pet(name=new_pet_name.strip(), species=new_species))
        st.success(f"Added {new_pet_name} ({new_species}) to {owner.name}'s pets.")
    else:
        st.error("Please enter a pet name.")

# Show the pets currently in memory.
if owner.pets:
    st.write("**Your pets:**")
    for pet in owner.pets:
        st.write(f"- {pet.name} ({pet.species}) — {len(pet.get_tasks())} task(s)")
else:
    st.info("No pets yet. Add one above.")

st.divider()

# ---------------------------------------------------------------------------
# Step 3 (cont.): Wiring UI Actions to Logic — Add a Task to a Pet
# ---------------------------------------------------------------------------
st.subheader("Add a Task")

if not owner.pets:
    st.info("Add a pet first, then you can schedule tasks for it.")
else:
    with st.form("add_task_form", clear_on_submit=True):
        pet_names = [pet.name for pet in owner.pets]
        selected_pet_name = st.selectbox("For which pet?", pet_names)

        task_title = st.text_input("Task title", value="Morning walk")
        col1, col2, col3 = st.columns(3)
        with col1:
            duration = st.number_input(
                "Duration (minutes)", min_value=1, max_value=240, value=20
            )
        with col2:
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
        with col3:
            # Optional "HH:MM" preferred time — feeds sort_by_time and
            # detect_conflicts below. Blank means "no fixed time".
            task_time = st.text_input("Preferred time (HH:MM, optional)", value="")

        add_task_submitted = st.form_submit_button("Add task")

    if add_task_submitted:
        # Find the selected Pet object and let IT own the new Task via add_task,
        # which stamps the task with the pet's name.
        pet = next(p for p in owner.pets if p.name == selected_pet_name)
        pet.add_task(
            Task(
                title=task_title,
                duration_minutes=int(duration),
                priority=priority,
                time=task_time.strip(),
            )
        )
        st.success(f"Added '{task_title}' for {selected_pet_name}.")

# Show every task currently in memory, gathered through the Owner.
all_tasks = owner.get_all_tasks()
if all_tasks:
    st.write("**All tasks:**")
    st.table(
        [
            {
                "Pet": task.pet_name,
                "Task": task.title,
                "Time": task.time or "—",
                "Minutes": task.duration_minutes,
                "Priority": task.priority,
            }
            for task in all_tasks
        ]
    )

st.divider()

# ---------------------------------------------------------------------------
# Build Schedule — call the Scheduler with the Owner's tasks + preferences
# ---------------------------------------------------------------------------
st.subheader("Build Schedule")
available_minutes = st.number_input(
    "Available minutes for the day", min_value=1, max_value=1440, value=75
)

if st.button("Generate schedule"):
    tasks = owner.get_all_tasks()
    if not tasks:
        st.warning("No tasks to schedule yet. Add a pet and some tasks first.")
    else:
        scheduler = Scheduler(available_minutes=int(available_minutes))

        # --- Conflict warnings (Scheduler.detect_conflicts) --------------
        # Surface any two tasks booked at the same clock time BEFORE the plan
        # so the owner can spot the clash and adjust. One st.warning per slot
        # keeps each conflict visually distinct.
        conflicts = scheduler.detect_conflicts(tasks)
        if conflicts:
            for warning in conflicts:
                st.warning(f"⚠️ {warning}")
        else:
            st.success("No time conflicts detected. 🎉")

        # --- Today at a glance (Scheduler.sort_by_time) ------------------
        # Show every task in chronological order (untimed tasks sort last) so
        # the owner sees the shape of their day independent of the budget.
        st.markdown("**Today at a glance** (sorted by time)")
        st.table(
            [
                {
                    "Time": task.time or "—",
                    "Task": task.title,
                    "Pet": task.pet_name,
                    "Priority": task.priority,
                    "Minutes": task.duration_minutes,
                }
                for task in scheduler.sort_by_time(tasks)
            ]
        )

        # --- The priority-fitted plan (Scheduler.generate_plan) ----------
        plan = scheduler.generate_plan(tasks, owner.get_preferences())
        st.success(
            f"Scheduled {len(plan.scheduled_items)} task(s) using "
            f"{plan.total_minutes_used} of {int(available_minutes)} available minutes."
        )
        if plan.scheduled_items:
            st.table(
                [
                    {
                        "Start": item.start_time,
                        "Task": item.task.title,
                        "Pet": item.task.pet_name,
                        "Minutes": item.task.duration_minutes,
                        "Why": item.reasoning,
                    }
                    for item in plan.scheduled_items
                ]
            )
        # Tasks that didn't fit the budget: flag each so nothing silently vanishes.
        for task, reason in zip(plan.skipped_tasks, plan.skip_reasons):
            st.warning(f"Skipped **{task.title}** ({task.pet_name}) — {reason}")

        # Keep the plain-text reasoning available for anyone who wants the
        # full explanation in one copyable block.
        with st.expander("Full text summary (plan.explain())"):
            st.text(plan.explain())
