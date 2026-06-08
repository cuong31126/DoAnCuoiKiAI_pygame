from core.map import build_demo_level
from core.robot import Robot


class GameManager:
    """Owns the active hospital level data and scoring helpers."""

    def __init__(self, level):
        self.level = level
        self.map = build_demo_level(level)
        self.robot = Robot(self.map.start, self.map.battery_limit)
        self.elapsed = 0.0
        self.replan_count = 0
        self.status_message = "Ready"

    def reset(self):
        self.map = build_demo_level(self.level)
        self.robot = Robot(self.map.start, self.map.battery_limit)
        self.elapsed = 0.0
        self.replan_count = 0
        self.status_message = "Ready"

    def mark_task_if_reached(self):
        completed = None
        for task in self.map.tasks:
            if not task.completed and task.target == self.robot.position:
                task.completed = True
                self.robot.completed_tasks.append(task.task_id)
                bonus = max(0, int((task.deadline or self.map.time_limit) - self.elapsed))
                late_penalty = 50 if task.urgent and task.deadline and self.elapsed > task.deadline else 0
                self.robot.score += task.reward + bonus - late_penalty
                completed = task
                break
        return completed

    def all_tasks_done(self):
        return all(task.completed for task in self.map.tasks)

    def current_task_label(self):
        remaining = self.map.remaining_tasks()
        if not remaining:
            return "All tasks complete"
        urgent = [task for task in remaining if task.urgent]
        task = min(urgent or remaining, key=lambda item: (item.deadline or 999, -item.priority))
        return task.display_name()

