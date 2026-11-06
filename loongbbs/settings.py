"""Runtime site settings, cached per request."""
from __future__ import annotations

from flask import g
from flask import current_app

from .admin_settings import SETTING_DEFAULTS as SETTING_DEFAULTS_SRC
from .extensions import db
from .models import Setting

LOCAL_DEFAULTS = {
    "site_name": "LoongBBS Next",
    "site_tagline": "龙芯社区论坛 · Python 重制版",
    "posts_per_page": "10",
    "threads_per_page": "25",
    "allow_registration": "1",
    "thumb_mode": "1",
    "thumb_width": "480",
    "thumb_height": "360",
    "avatarenabled": "1",
    "avatarmaxdimension": "100",
    "avatarmaxsize": "1024",
    "avatarcustomposts": "0",
}

# vB 后台 Options 的默认值打底，本站自有键覆盖同名项
DEFAULTS = {**SETTING_DEFAULTS_SRC, **LOCAL_DEFAULTS}


def get_settings() -> dict[str, str]:
    """Return the settings dict for the current request (cached on ``g``)."""
    cached = getattr(g, "_loongbbs_settings", None)
    if cached is not None:
        return cached

    values: dict[str, str] = dict(DEFAULTS)
    try:
        for row in db.session.execute(db.select(Setting)).scalars():
            values[row.key] = row.value
    except Exception:  # tables not created yet (e.g. before init-db)
        current_app.logger.debug("settings table not ready", exc_info=True)
    g._loongbbs_settings = values
    return values


def get_setting(key: str, default: str | None = None) -> str:
    return get_settings().get(key, DEFAULTS.get(key, default or ""))


def set_setting(key: str, value: str) -> None:
    row = db.session.get(Setting, key)
    if row is None:
        row = Setting(key=key, value=value)
        db.session.add(row)
    else:
        row.value = value
    getattr(g, "_loongbbs_settings", {}).pop(key, None)
