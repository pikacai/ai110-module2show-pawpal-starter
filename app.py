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
        col1, col2 = st.columns(2)
        with col1:
            duration = st.number_input(
                "Duration (minutes)", min_value=1, max_value=240, value=20
            )
        with col2:
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

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
    if not owner.get_all_tasks():
        st.warning("No tasks to schedule yet. Add a pet and some tasks first.")
    else:
        scheduler = Scheduler(available_minutes=int(available_minutes))
        plan = scheduler.generate_plan(
            owner.get_all_tasks(), owner.get_preferences()
        )
        # plan.explain() returns a plain-text summary; show it in a code block.
        st.text(plan.explain())
