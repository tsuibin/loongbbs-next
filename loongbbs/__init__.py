"""LoongBBS Next — Flask application factory."""
from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, render_template

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
    from .utils import format_dt, human_size, render_body, time_ago

    app.jinja_env.filters.update(
        dt=format_dt, ago=time_ago, size=human_size, body=render_body
    )

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
