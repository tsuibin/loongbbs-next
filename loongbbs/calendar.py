"""Calendar month view — port of the reference calendar.php (action=getmonth)."""
from __future__ import annotations

import calendar as _pycal
from datetime import datetime, timedelta, timezone

from flask import Blueprint, render_template, request
from sqlalchemy import select

from .extensions import db
from .models import User, utcnow
from .settings import get_setting

bp = Blueprint("calendar", __name__)

# 参考站月历从「星期日」开始（calendar.php 的 $weekdaynames）
WEEKDAYS = ("星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六")
MONTHS_EN = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)
WEEKDAYS_EN = (
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
)

# 参考站年份下拉从 2000 起，到当前年 + 2
START_YEAR = 2000


def _offset_minutes() -> int:
    try:
        return int(get_setting("timeoffset", "8") or 8) * 60
    except (TypeError, ValueError):
        return 8 * 60


def _local_now() -> datetime:
    utc = utcnow()
    if utc.tzinfo is None:
        utc = utc.replace(tzinfo=timezone.utc)
    return utc.astimezone(timezone.utc).replace(tzinfo=None) + timedelta(minutes=_offset_minutes())


def _birthdays_for_month(month: int) -> dict[int, list[str]]:
    """calendar.php 的生日条目：由 calbirthday 控制是否显示，calshowbirthdays 控制是否带年龄。"""
    if get_setting("calbirthday", "1") != "1":
        return {}
    show_age = get_setting("calshowbirthdays", "1") == "1"
    year_now = _local_now().year
    rows = db.session.execute(
        select(User).where(User.birthday.isnot(None), User.birthday != "")
    ).scalars().all()
    by_day: dict[int, list[str]] = {}
    for user in rows:
        value = (user.birthday or "").strip()
        if len(value) < 10:
            continue
        try:
            y = int(value[:4])
            m = int(value[5:7])
            d = int(value[8:10])
        except ValueError:
            continue
        if m != month or not 1 <= d <= 31:
            continue
        text = user.username
        if show_age and 0 < y < year_now:
            text = f"{user.username} ({year_now - y})"
        by_day.setdefault(d, []).append(text)
    return by_day


def _clamp_int(raw: str | None, fallback: int, low: int, high: int) -> int:
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return fallback
    return max(low, min(high, value))


@bp.get("/calendar")
def calendar_view():
    now = _local_now()
    month = _clamp_int(request.args.get("month"), now.month, 1, 12)
    year = _clamp_int(request.args.get("year"), now.year, START_YEAR, 2100)

    first_weekday, days_in_month = _pycal.monthrange(year, month)
    # Python 的 monthrange 以周一为 0；原版日历以周日为第一列
    lead = (first_weekday + 1) % 7
    birthdays = _birthdays_for_month(month)

    cells: list[dict] = []
    for _ in range(lead):
        cells.append({"day": None, "birthdays": []})
    for day in range(1, days_in_month + 1):
        cells.append({"day": day, "birthdays": birthdays.get(day, [])})
    while len(cells) % 7:
        cells.append({"day": None, "birthdays": []})
    weeks = [cells[i : i + 7] for i in range(0, len(cells), 7)]

    prev_month, prev_year = (12, year - 1) if month == 1 else (month - 1, year)
    next_month, next_year = (1, year + 1) if month == 12 else (month + 1, year)

    return render_template(
        "calendar.html",
        month=month,
        year=year,
        weeks=weeks,
        weekday_names=WEEKDAYS,
        weekday_names_en=WEEKDAYS_EN,
        month_names=[(m, f"{m}月") for m in range(1, 13)],
        month_name_en=MONTHS_EN[month - 1],
        month_names_en=[(m, MONTHS_EN[m - 1]) for m in range(1, 13)],
        prev_month_en=MONTHS_EN[prev_month - 1],
        next_month_en=MONTHS_EN[next_month - 1],
        years=list(range(START_YEAR, max(now.year + 2, year) + 1)),
        prev_month=prev_month,
        prev_year=prev_year,
        next_month=next_month,
        next_year=next_year,
        today=(now.day if (now.year == year and now.month == month) else None),
    )
