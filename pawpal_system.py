"""PawPal+ logic layer: backend classes translated from diagrams/uml.mmd.

This is a skeleton only — attributes and method signatures match the UML,
but method bodies are not implemented yet.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str  # one of: "low", "medium", "high"

    def __repr__(self) -> str:
        raise NotImplementedError


@dataclass
class Pet:
    name: str
    species: str
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        raise NotImplementedError

    def get_tasks(self) -> List[Task]:
        raise NotImplementedError


@dataclass
class Owner:
    name: str
    preferences: dict = field(default_factory=dict)
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        raise NotImplementedError

    def get_preferences(self) -> dict:
        raise NotImplementedError


@dataclass
class ScheduledTask:
    task: Task
    start_time: str
    reasoning: str


@dataclass
class DailyPlan:
    scheduled_items: List[ScheduledTask] = field(default_factory=list)
    skipped_tasks: List[Task] = field(default_factory=list)
    total_minutes_used: int = 0

    def explain(self) -> str:
        raise NotImplementedError

    def add_scheduled_task(self, item: ScheduledTask) -> None:
        raise NotImplementedError

    def add_skipped_task(self, task: Task, reason: str) -> None:
        raise NotImplementedError


class Scheduler:
    def __init__(self, available_minutes: int):
        self.available_minutes = available_minutes

    def generate_plan(self, tasks: List[Task]) -> DailyPlan:
        raise NotImplementedError

    def _sort_by_priority(self, tasks: List[Task]) -> List[Task]:
        raise NotImplementedError

    def _fits_in_remaining_time(self, task: Task, remaining: int) -> bool:
        raise NotImplementedError
