"""Mediciones reproducibles para rendimiento de sincronizacion."""

import time
import unittest
from contextlib import nullcontext

from application.caso_uso_sincronizacion import SyncUseCase
from application.consultas_tareas import TaskQueries
from domain.modelos import Course, StoredCredentials, Task
from infrastructure.persistence import SQLiteTaskRepository


class MeasurementCredentials:
    def load(self):
        return StoredCredentials("user", "pass", "token")

    def save_credentials(self, username, password):
        pass

    def save_token(self, token):
        pass

    def clear_token(self):
        pass


class MeasurementCampusBase:
    def __init__(self, courses: int = 3, assignments_per_course: int = 20, latency_seconds: float = 0.0) -> None:
        self.course_count = courses
        self.assignments_per_course = assignments_per_course
        self.latency_seconds = latency_seconds
        self.site_calls = 0
        self.course_calls = 0
        self.assignment_calls = 0
        self.status_calls = 0
        self.status_bulk_calls = 0

    def login(self, username, password):
        return "token"

    def site_info(self, token):
        self.site_calls += 1
        return {"userid": 7}

    def courses(self, token, user_id):
        self.course_calls += 1
        return [
            {"id": course_id, "shortname": f"C{course_id}", "fullname": f"Curso {course_id}", "visible": 1}
            for course_id in range(1, self.course_count + 1)
        ]

    def assignments(self, token):
        self.assignment_calls += 1
        next_id = 1
        payload = []
        for course_id in range(1, self.course_count + 1):
            assignments = []
            for _index in range(self.assignments_per_course):
                assignments.append({"id": next_id, "name": f"Tarea {next_id}", "duedate": 0, "url": None})
                next_id += 1
            payload.append({"id": course_id, "assignments": assignments})
        return payload

    def _status_payload(self):
        if self.latency_seconds:
            time.sleep(self.latency_seconds)
        return {"lastattempt": {"submission": {"status": "new"}}}


class LegacyMeasurementCampus(MeasurementCampusBase):
    def submission_status(self, token, assignment_id):
        self.status_calls += 1
        return self._status_payload()


class BulkMeasurementCampus(MeasurementCampusBase):
    def submission_status(self, token, assignment_id):
        self.status_calls += 1
        return self._status_payload()

    def submission_statuses(self, token, assignment_ids):
        self.status_bulk_calls += 1
        status = self._status_payload()
        return {assignment_id: status for assignment_id in assignment_ids}


class NoTransactionRepository(SQLiteTaskRepository):
    def transaction(self):
        return nullcontext()


class SyncPerformanceMeasurementTests(unittest.TestCase):
    def _run_sync(self, campus, repo_cls=SQLiteTaskRepository):
        repo = repo_cls(":memory:")
        start = time.perf_counter()
        result = SyncUseCase(repo, MeasurementCredentials(), campus).execute()
        elapsed = time.perf_counter() - start
        repo.close()
        return result, elapsed

    def test_moodle_status_lookup_reduces_request_shape_with_fixture(self):
        legacy = LegacyMeasurementCampus(courses=3, assignments_per_course=20)
        bulk = BulkMeasurementCampus(courses=3, assignments_per_course=20)

        legacy_result, _legacy_elapsed = self._run_sync(legacy)
        bulk_result, _bulk_elapsed = self._run_sync(bulk)

        self.assertTrue(legacy_result.ok)
        self.assertTrue(bulk_result.ok)
        self.assertEqual(legacy.status_calls, 60)
        self.assertEqual(legacy.status_bulk_calls, 0)
        self.assertEqual(bulk.status_calls, 0)
        self.assertEqual(bulk.status_bulk_calls, 1)
        self.assertEqual(bulk.assignment_calls, 1)

    def test_bulk_status_lookup_is_faster_with_latency_fixture(self):
        legacy = LegacyMeasurementCampus(courses=2, assignments_per_course=15, latency_seconds=0.001)
        bulk = BulkMeasurementCampus(courses=2, assignments_per_course=15, latency_seconds=0.001)

        _legacy_result, legacy_elapsed = self._run_sync(legacy)
        _bulk_result, bulk_elapsed = self._run_sync(bulk)

        self.assertLess(bulk_elapsed, legacy_elapsed)

    def _run_sync_with_trace(self, repo_cls):
        repo = repo_cls(":memory:")
        campus = BulkMeasurementCampus(courses=2, assignments_per_course=5)
        statements = []
        repo.conn.set_trace_callback(statements.append)

        result = SyncUseCase(repo, MeasurementCredentials(), campus).execute()

        repo.conn.set_trace_callback(None)
        repo.close()
        return result, statements

    def test_sync_transaction_reduces_sqlite_commits_for_successful_write_set(self):
        result, statements = self._run_sync_with_trace(SQLiteTaskRepository)
        baseline_result, baseline_statements = self._run_sync_with_trace(NoTransactionRepository)

        commits = len([statement for statement in statements if statement == "COMMIT"])
        baseline_commits = len([statement for statement in baseline_statements if statement == "COMMIT"])

        self.assertTrue(result.ok)
        self.assertTrue(baseline_result.ok)
        self.assertLess(commits, baseline_commits)

    def test_sync_uses_single_notification_state_select_for_changed_tasks(self):
        repo = SQLiteTaskRepository(":memory:")
        campus = BulkMeasurementCampus(courses=2, assignments_per_course=5)
        statements = []
        repo.conn.set_trace_callback(statements.append)

        result = SyncUseCase(repo, MeasurementCredentials(), campus).execute()

        repo.conn.set_trace_callback(None)
        self.assertTrue(result.ok)
        notification_selects = [
            statement
            for statement in statements
            if "FROM notification_state" in statement and "SELECT" in statement
        ]
        self.assertEqual(len(notification_selects), 1)
        repo.close()

    def test_task_filtering_many_tasks_stays_under_budget(self):
        repo = SQLiteTaskRepository(":memory:")
        repo.upsert_courses([Course(1, "IS", "Ingenieria", True)])
        repo.upsert_tasks(
            [
                Task(index, 1, "IS", "Ingenieria", f"Proyecto {index}", 1_800_000_000 + index, None, "new")
                for index in range(1, 1001)
            ]
        )
        queries = TaskQueries(repo)

        start = time.perf_counter()
        filtered = queries.pending_filtered(search="Proyecto 99")
        elapsed = time.perf_counter() - start

        self.assertGreaterEqual(len(filtered), 1)
        self.assertLess(elapsed, 0.2)
        repo.close()


if __name__ == "__main__":
    unittest.main()
