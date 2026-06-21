"""Pruebas de politica de clasificacion de tareas."""

import unittest

from domain.modelos import Task, TaskBucket
from domain.politica_tareas import classify_task, sort_pending


def task(assignment_id: int, due_at, status="new") -> Task:
    return Task(
        assignment_id=assignment_id,
        course_id=1,
        course_shortname="IS-441",
        course_fullname="Traductores",
        name=f"Tarea {assignment_id}",
        due_at=due_at,
        url=None,
        submission_status=status,
    )


class ClassifierTests(unittest.TestCase):
    def test_new_without_due_date_is_undated(self):
        self.assertEqual(classify_task(task(1, None), current_ts=100), TaskBucket.UNDATED)

    def test_new_past_due_is_overdue(self):
        self.assertEqual(classify_task(task(1, 50), current_ts=100), TaskBucket.OVERDUE)

    def test_new_future_due_is_upcoming(self):
        self.assertEqual(classify_task(task(1, 150), current_ts=100), TaskBucket.UPCOMING)

    def test_submitted_is_not_pending(self):
        self.assertEqual(classify_task(task(1, 50, status="submitted"), current_ts=100), TaskBucket.SUBMITTED)

    def test_sort_orders_overdue_upcoming_undated(self):
        ordered = sort_pending([task(1, None), task(2, 150), task(3, 50)])
        self.assertEqual([item.assignment_id for item in ordered], [3, 2, 1])


if __name__ == "__main__":
    unittest.main()
