"""SQL de esquema y migracion para el cache local."""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS courses (
    course_id INTEGER PRIMARY KEY,
    shortname TEXT NOT NULL,
    fullname TEXT NOT NULL,
    visible INTEGER NOT NULL,
    last_seen_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS tasks (
    assignment_id INTEGER PRIMARY KEY,
    course_id INTEGER NOT NULL,
    course_shortname TEXT NOT NULL,
    course_fullname TEXT NOT NULL,
    name TEXT NOT NULL,
    due_at INTEGER,
    url TEXT,
    submission_status TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    last_seen_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS notification_state (
    assignment_id INTEGER PRIMARY KEY,
    last_notified_hash TEXT,
    snoozed_until INTEGER
);
CREATE TABLE IF NOT EXISTS app_state (
    key TEXT PRIMARY KEY,
    value TEXT
);
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""

LEGACY_MIGRATION_SQL = """
INSERT OR IGNORE INTO tasks (
    assignment_id, course_id, course_shortname, course_fullname, name,
    due_at, url, submission_status, content_hash, last_seen_at
)
SELECT
    assignment_id, course_id, course_shortname, course_fullname, name,
    due_at, url, submission_status, content_hash, last_seen_at
FROM assignments
WHERE EXISTS (
    SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'assignments'
);
"""
