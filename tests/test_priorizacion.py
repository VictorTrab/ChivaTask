from __future__ import annotations

import unittest

from domain.modelos import Task
from domain.priorizacion import academic_alerts, is_possible_exam, recommend_tasks


NOW = 1_800_000_000


def task(
    assignment_id: int,
    name: str,
    due_offset_days: int | None,
    status: str = "new",
    course_id: int = 1,
    snoozed_until: int | None = None,
) -> Task:
    due_at = None if due_offset_days is None else NOW + due_offset_days * 86400
    return Task(
        assignment_id,
        course_id,
        f"C{course_id}",
        f"Curso {course_id}",
        name,
        due_at,
        "https://campus.uph.edu.hn/mod/assign/view.php?id=1",
        status,
        snoozed_until=snoozed_until,
    )


class PrioritizationTests(unittest.TestCase):
    def test_overdue_before_upcoming_and_undated(self):
        recommendations = recommend_tasks(
            [
                task(1, "Sin fecha", None),
                task(2, "Vence en siete", 7),
                task(3, "Vencida", -5),
            ],
            NOW,
        )

        self.assertEqual([item.task.assignment_id for item in recommendations], [3, 2, 1])
        self.assertIn("vencio hace 5 dias", recommendations[0].primary_reason)

    def test_tomorrow_before_seven_days_and_submitted_snoozed_excluded(self):
        recommendations = recommend_tasks(
            [
                task(1, "Vence manana", 1),
                task(2, "Vence en siete", 7),
                task(3, "Entregada", -10, status="submitted"),
                task(4, "Pospuesta", -20, snoozed_until=NOW + 86400),
            ],
            NOW,
        )

        self.assertEqual([item.task.assignment_id for item in recommendations], [1, 2])
        self.assertIn("manana", recommendations[0].primary_reason)

    def test_possible_exam_increases_priority_and_is_explained(self):
        recommendations = recommend_tasks(
            [
                task(1, "Reporte normal", 7),
                task(2, "Evaluación II", 7),
            ],
            NOW,
        )

        self.assertEqual(recommendations[0].task.assignment_id, 2)
        self.assertTrue(recommendations[0].is_possible_exam)
        self.assertIn("Posible evaluacion", recommendations[0].secondary_reason or "")

    def test_overdue_is_not_displaced_by_possible_exam_upcoming(self):
        recommendations = recommend_tasks(
            [
                task(1, "Tarea vencida", -1),
                task(2, "EXAMEN FINAL", 0),
            ],
            NOW,
        )

        self.assertEqual(recommendations[0].task.assignment_id, 1)

    def test_exam_detection_normalizes_case_and_accents(self):
        self.assertTrue(is_possible_exam("EXAMEN FINAL"))
        self.assertTrue(is_possible_exam("Evaluación II"))
        self.assertTrue(is_possible_exam("quiz unidad 3"))
        self.assertFalse(is_possible_exam("Reporte de laboratorio"))

    def test_deterministic_tie_by_date_then_name(self):
        recommendations = recommend_tasks(
            [
                task(2, "Beta", 2),
                task(1, "Alpha", 2),
            ],
            NOW,
        )

        self.assertEqual([item.task.name for item in recommendations], ["Alpha", "Beta"])

    def test_alerts_are_based_on_real_conditions(self):
        alerts = academic_alerts(
            [
                task(1, "Tarea vencida", -1),
                task(2, "Quiz unidad", 2),
                task(3, "Actividad sin fecha", None),
            ],
            NOW,
        )

        joined = " ".join(alerts)
        self.assertIn("vencida", joined)
        self.assertIn("proximos 3 dias", joined)
        self.assertIn("sin fecha", joined)
        self.assertIn("Posible evaluacion", joined)


if __name__ == "__main__":
    unittest.main()
