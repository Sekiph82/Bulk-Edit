"""
Schedule calculator for ScheduledJob.

Rules:
- All next_run_at values are stored in UTC.
- Input timezone must be a valid IANA timezone string.
- Interval minimum: 60 minutes.
- Monthly day_of_month: 1–28 only (avoids month-end edge cases).
- one_time jobs: run_at must be future; become completed after single run.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any

try:
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
except ImportError:
    from backports.zoneinfo import ZoneInfo, ZoneInfoNotFoundError  # type: ignore

VALID_INTERVAL_UNITS = {"minutes", "hours", "days"}
MIN_INTERVAL_MINUTES = 60
VALID_WEEKDAYS = {"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}
WEEKDAY_MAP = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6}


class ScheduleError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def _parse_tz(timezone_str: str) -> ZoneInfo:
    try:
        return ZoneInfo(timezone_str)
    except (ZoneInfoNotFoundError, KeyError):
        raise ScheduleError(f"Invalid timezone: {timezone_str!r}", 400)


def _parse_time(time_str: str) -> tuple[int, int]:
    try:
        parts = time_str.split(":")
        h, m = int(parts[0]), int(parts[1])
        if not (0 <= h <= 23 and 0 <= m <= 59):
            raise ValueError
        return h, m
    except Exception:
        raise ScheduleError(f"Invalid time format: {time_str!r}. Use HH:MM (e.g. '09:00')", 400)


def validate_schedule(schedule_type: str, schedule_payload: dict[str, Any]) -> None:
    if schedule_type == "one_time":
        run_at = schedule_payload.get("run_at")
        if not run_at:
            raise ScheduleError("one_time schedule requires 'run_at' field", 400)
        try:
            datetime.fromisoformat(str(run_at))
        except ValueError:
            raise ScheduleError(f"Invalid run_at datetime: {run_at!r}", 400)

    elif schedule_type == "interval":
        every = schedule_payload.get("every")
        unit = schedule_payload.get("unit")
        if every is None or unit is None:
            raise ScheduleError("interval schedule requires 'every' and 'unit' fields", 400)
        if unit not in VALID_INTERVAL_UNITS:
            raise ScheduleError(f"Invalid interval unit: {unit!r}. Must be one of: {sorted(VALID_INTERVAL_UNITS)}", 400)
        try:
            every = int(every)
        except (TypeError, ValueError):
            raise ScheduleError("'every' must be an integer", 400)
        if every <= 0:
            raise ScheduleError("'every' must be positive", 400)
        minutes = every if unit == "minutes" else (every * 60 if unit == "hours" else every * 1440)
        if minutes < MIN_INTERVAL_MINUTES:
            raise ScheduleError(f"Minimum interval is {MIN_INTERVAL_MINUTES} minutes", 400)

    elif schedule_type == "daily":
        time_str = schedule_payload.get("time")
        if not time_str:
            raise ScheduleError("daily schedule requires 'time' field (HH:MM)", 400)
        _parse_time(time_str)

    elif schedule_type == "weekly":
        day = schedule_payload.get("day_of_week")
        time_str = schedule_payload.get("time")
        if not day or not time_str:
            raise ScheduleError("weekly schedule requires 'day_of_week' and 'time' fields", 400)
        if day.lower() not in VALID_WEEKDAYS:
            raise ScheduleError(f"Invalid day_of_week: {day!r}. Must be one of: {sorted(VALID_WEEKDAYS)}", 400)
        _parse_time(time_str)

    elif schedule_type == "monthly":
        dom = schedule_payload.get("day_of_month")
        time_str = schedule_payload.get("time")
        if dom is None or not time_str:
            raise ScheduleError("monthly schedule requires 'day_of_month' and 'time' fields", 400)
        try:
            dom = int(dom)
        except (TypeError, ValueError):
            raise ScheduleError("'day_of_month' must be an integer", 400)
        if not (1 <= dom <= 28):
            raise ScheduleError("'day_of_month' must be between 1 and 28", 400)
        _parse_time(time_str)

    else:
        raise ScheduleError(f"Invalid schedule_type: {schedule_type!r}", 400)


def calculate_next_run(
    schedule_type: str,
    schedule_payload: dict[str, Any],
    timezone_str: str,
    after: datetime | None = None,
) -> datetime | None:
    tz = _parse_tz(timezone_str)
    now_utc = after if after is not None else datetime.now(timezone.utc)
    now_local = now_utc.astimezone(tz)

    if schedule_type == "one_time":
        run_at_str = schedule_payload["run_at"]
        run_at = datetime.fromisoformat(str(run_at_str))
        if run_at.tzinfo is None:
            run_at = run_at.replace(tzinfo=tz)
        return run_at.astimezone(timezone.utc)

    elif schedule_type == "interval":
        every = int(schedule_payload["every"])
        unit = schedule_payload["unit"]
        if unit == "minutes":
            delta = timedelta(minutes=every)
        elif unit == "hours":
            delta = timedelta(hours=every)
        else:
            delta = timedelta(days=every)
        return now_utc + delta

    elif schedule_type == "daily":
        h, m = _parse_time(schedule_payload["time"])
        candidate = now_local.replace(hour=h, minute=m, second=0, microsecond=0)
        if candidate <= now_local:
            candidate = candidate + timedelta(days=1)
        return candidate.astimezone(timezone.utc)

    elif schedule_type == "weekly":
        h, m = _parse_time(schedule_payload["time"])
        target_weekday = WEEKDAY_MAP[schedule_payload["day_of_week"].lower()]
        current_weekday = now_local.weekday()
        days_ahead = (target_weekday - current_weekday) % 7
        candidate = now_local.replace(hour=h, minute=m, second=0, microsecond=0)
        if days_ahead == 0 and candidate <= now_local:
            days_ahead = 7
        candidate = candidate + timedelta(days=days_ahead)
        return candidate.astimezone(timezone.utc)

    elif schedule_type == "monthly":
        h, m = _parse_time(schedule_payload["time"])
        dom = int(schedule_payload["day_of_month"])
        candidate = now_local.replace(day=dom, hour=h, minute=m, second=0, microsecond=0)
        if candidate <= now_local:
            # advance one month
            if now_local.month == 12:
                candidate = candidate.replace(year=now_local.year + 1, month=1)
            else:
                candidate = candidate.replace(month=now_local.month + 1)
        return candidate.astimezone(timezone.utc)

    return None


def should_run_now(job: Any, now: datetime | None = None) -> bool:
    if now is None:
        now = datetime.now(timezone.utc)
    if job.status != "active":
        return False
    if job.next_run_at is None:
        return False
    next_run = job.next_run_at
    if next_run.tzinfo is None:
        next_run = next_run.replace(tzinfo=timezone.utc)
    if job.starts_at is not None:
        starts = job.starts_at
        if starts.tzinfo is None:
            starts = starts.replace(tzinfo=timezone.utc)
        if now < starts:
            return False
    if job.ends_at is not None:
        ends = job.ends_at
        if ends.tzinfo is None:
            ends = ends.replace(tzinfo=timezone.utc)
        if now >= ends:
            return False
    if job.max_runs is not None and job.run_count >= job.max_runs:
        return False
    return now >= next_run
