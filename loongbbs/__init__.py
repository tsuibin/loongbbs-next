"""LoongBBS Next — Flask application factory."""
from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, g, render_template
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

    app.register_blueprint(auth_bp)
    app.register_blueprint(forums_bp)
    app.register_blueprint(attachments_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(pm_bp)
    app.register_blueprint(admin_bp)

    from .utils import csrf_protect, current_user_or_none

    app.before_request(csrf_protect)

    from .attachments import attachment_css, thumb_limits
    from .utils import avatar_src, format_dt, human_size, now_gmt, render_body, time_ago

    app.jinja_env.filters.update(
        dt=format_dt, ago=time_ago, size=human_size, body=render_body
    )
    app.jinja_env.globals["avatar_src"] = avatar_src
    app.jinja_env.globals["now_gmt"] = now_gmt

    @app.before_request
    def _mark_request_start():
        g._t0 = time.perf_counter()

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
            "server_time": format_dt(
                datetime.now(timezone.utc), "%m-%d-%Y %I:%M %p"
            ),
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
