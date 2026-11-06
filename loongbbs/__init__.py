"""LoongBBS Next — Flask application factory."""
from __future__ import annotations

import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from flask import Flask, g, render_template, request
from flask_login import current_user

BASE_DIR = Path(__file__).resolve().parent.parent


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=False)

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("LOONG_BBS_SECRET", "dev-change-me"),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "LOONG_BBS_DATABASE_URL", f"sqlite:///{BASE_DIR / 'loongbbs.db'}"
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_DIR=os.environ.get("LOONG_BBS_UPLOAD_DIR", str(BASE_DIR / "uploads")),
        MAX_CONTENT_LENGTH=int(os.environ.get("LOONG_BBS_MAX_UPLOAD", 8 * 1024 * 1024)),
        POSTS_PER_PAGE=10,
        THREADS_PER_PAGE=25,
    )
    if test_config:
        app.config.update(test_config)

    Path(app.config["UPLOAD_DIR"]).mkdir(parents=True, exist_ok=True)

    from .extensions import db, login_manager

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "请先登录。"

    from .auth import bp as auth_bp
    from .forums import bp as forums_bp
    from .attachments import bp as attachments_bp
    from .search import bp as search_bp
    from .pm import bp as pm_bp
    from .admin import bp as admin_bp
    from .members import bp as members_bp
    from .misc import bp as misc_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(forums_bp)
    app.register_blueprint(attachments_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(pm_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(members_bp)
    app.register_blueprint(misc_bp)

    from .utils import csrf_protect, current_user_or_none

    app.before_request(csrf_protect)

    from .attachments import attachment_css, thumb_limits
    from .utils import (
        avatar_src,
        dowordwrap,
        format_date,
        format_datetime,
        format_dt,
        format_joined,
        format_time,
        human_size,
        now_gmt,
        render_body,
        time_ago,
    )

    app.jinja_env.filters.update(
        dt=format_dt,
        ago=time_ago,
        size=human_size,
        body=render_body,
        wordwrap=dowordwrap,
        datefmt=format_date,
        timefmt=format_time,
        datetimefmt=format_datetime,
        joinedfmt=format_joined,
    )
    app.jinja_env.globals["avatar_src"] = avatar_src
    app.jinja_env.globals["now_gmt"] = now_gmt

    @app.before_request
    def _mark_request_start():
        g._t0 = time.perf_counter()

    @app.before_request
    def _board_closed_guard():
        """vB 的 bbactive：关站时只有管理员还能浏览，其余人看到关闭说明。"""
        from .settings import get_settings

        current = get_settings()
        if current.get("bbactive", "1") != "0":
            return None
        path = request.path or "/"
        if (
            path.startswith("/static")
            or path.startswith("/admin")
            or path in ("/login", "/logout")
        ):
            return None
        if current_user.is_authenticated and getattr(current_user, "is_admin", False):
            return None
        reason = (current.get("bbclosedreason") or "论坛暂时关闭，请稍后再来。").strip()
        return render_template("board_closed.html", reason=reason), 503

    @app.before_request
    def _ip_ban_guard():
        """vB 组 17 的 checkipban()：enablebanning 打开时按 banip 前缀封禁来访 IP。"""
        from .settings import get_settings

        current = get_settings()
        if current.get("enablebanning", "0") != "1":
            return None
        banlist = (current.get("banip") or "").strip()
        if not banlist:
            return None
        path = request.path or "/"
        if path.startswith("/static"):
            return None
        ip = (request.remote_addr or "").strip()
        if not ip:
            return None
        # 原版 `strstr(" ".$ipaddress, " ".$val)`：从 IP 开头匹配，支持部分 IP
        for entry in banlist.split():
            if entry and ip.startswith(entry):
                return render_template("ban_ip.html"), 403
        return None

    @app.before_request
    def _apply_cookie_timeout():
        """vB 组 6 的 cookietimeout（秒）：会话 cookie 的有效期。"""
        from flask import session

        from .settings import get_setting

        try:
            timeout = int(get_setting("cookietimeout") or 900)
        except ValueError:
            timeout = 900
        timeout = max(60, timeout)
        session.permanent = True
        app.permanent_session_lifetime = timedelta(seconds=timeout)

        # 组 20 cookiepath / cookiedomain：会话 cookie 的路径与域名（原版
        # functions.php 的 setcookie($name,$value,$expire,$cookiepath,$cookiedomain,...)）
        app.config["SESSION_COOKIE_PATH"] = (get_setting("cookiepath") or "/").strip() or "/"
        domain = (get_setting("cookiedomain") or "").strip()
        app.config["SESSION_COOKIE_DOMAIN"] = domain or None

    @app.after_request
    def _http_header_options(response):
        """vB 组 20：addheaders / nocacheheaders / gzipoutput / gziplevel。

        原版在 global.php 里按开关直接 header()；这里同样按开关往响应上加，
        只在 HTML 页面上生效（图片、附件下载等二进制响应不改）。
        """
        import gzip

        from .settings import get_setting

        if request.path.startswith("/static"):
            return response

        is_html = (response.mimetype or "") == "text/html"

        # addheaders：显式发 200 OK 的文本类型（原版 header("Content-type: text/html; charset=UTF-8")）
        if is_html and get_setting("addheaders") == "1":
            response.headers["Content-Type"] = "text/html; charset=UTF-8"

        # nocacheheaders：四个禁缓存头，值照抄原版
        if get_setting("nocacheheaders") == "1":
            response.headers["Expires"] = "Mon, 26 Jul 1997 05:00:00 GMT"
            response.headers["Last-Modified"] = format_datetime(datetime.now(timezone.utc))
            response.headers["Cache-Control"] = "no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"

        # gzipoutput：Accept-Encoding 里带 gzip 才压，gziplevel=0 表示不压
        if is_html and get_setting("gzipoutput") == "1":
            try:
                level = int(get_setting("gziplevel") or 1)
            except ValueError:
                level = 1
            level = max(0, min(level, 9))
            accepts = (request.headers.get("Accept-Encoding") or "").lower()
            if level > 0 and "gzip" in accepts and response.status_code == 200:
                data = response.get_data()
                if data:
                    response.set_data(gzip.compress(data, compresslevel=level, mtime=0))
                    response.headers["Content-Encoding"] = "gzip"
                    response.headers["Vary"] = "Accept-Encoding"
        return response

    @app.before_request
    def _touch_last_seen():
        if current_user.is_authenticated:
            from .models import utcnow

            seen = current_user.last_seen
            if seen is not None and seen.tzinfo is None:
                seen = seen.replace(tzinfo=timezone.utc)
            if seen is None or (utcnow() - seen).total_seconds() > 300:
                if seen is not None:
                    # 新会话开始时，把上一次的在线时间记为 last_visit（未读判断的基准）
                    current_user.last_visit = seen
                current_user.last_seen = utcnow()
                db.session.commit()

    @app.context_processor
    def inject_globals():
        from .settings import get_settings
        from .utils import csrf_token

        return {
            "settings": get_settings(),
            "csrf_token": csrf_token,
            "nav_user": current_user_or_none(),
            "attachment_css": attachment_css,
            "thumb_limits": thumb_limits(),
            "server_time": format_datetime(datetime.now(timezone.utc)),
            "generation_time": "%.4f" % (time.perf_counter() - g.get("_t0", time.perf_counter())),
        }

    @app.errorhandler(403)
    def forbidden(error):
        return render_template("error.html", code=403, message="没有权限访问这个页面。"), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template("error.html", code=404, message="页面不存在。"), 404

    @app.cli.command("init-db")
    def init_db():
        """Create all tables."""
        from .extensions import db

        db.create_all()
        print("已创建数据表：", app.config["SQLALCHEMY_DATABASE_URI"])

    @app.cli.command("seed")
    def seed_command():
        """Populate demo categories, forums, an admin user and sample threads."""
        from .seed import seed

        seed()

    return app
