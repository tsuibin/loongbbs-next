"""End-to-end smoke test for LoongBBS Next.

Runs the whole flow against a throwaway SQLite database, so it needs no server:

    python3 tests/test_smoke.py

Exercises: signup -> new thread -> reply with image attachment -> search ->
private message -> admin settings -> thumbnail/original switch -> ban.
"""
from __future__ import annotations

import io
import os
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from loongbbs import create_app  # noqa: E402
from loongbbs.extensions import db  # noqa: E402
from loongbbs.models import Category, Forum, Post, Thread, User  # noqa: E402

CSRF_RE = re.compile(r'name="_csrf" value="([^"]+)"')

# 1×1 PNG
PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06"
    b"\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00"
    b"\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)

checks: list[str] = []


def ok(label: str) -> None:
    checks.append(label)
    print(f"  ✓ {label}")


def token(client) -> str:
    page = client.get("/login").get_data(as_text=True)
    match = CSRF_RE.search(page)
    assert match, "no csrf token in login page"
    return match.group(1)


def fresh_token(client, path: str) -> str:
    page = client.get(path).get_data(as_text=True)
    match = CSRF_RE.search(page)
    assert match, f"no csrf token on {path}"
    return match.group(1)


def main() -> int:
    workdir = tempfile.mkdtemp(prefix="loongbbs-smoke-")
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{workdir}/test.db",
            "UPLOAD_DIR": f"{workdir}/uploads",
            "POSTS_PER_PAGE": 10,
            "THREADS_PER_PAGE": 25,
        }
    )

    with app.app_context():
        db.create_all()
        cat = Category(name="测试分类", position=1)
        forum = Forum(category_id=1, name="测试版块", description="smoke", position=1)
        db.session.add(cat)
        db.session.flush()
        forum.category_id = cat.id
        db.session.add(forum)
        admin = User(username="root", email="root@test.local", is_admin=True)
        admin.set_password("root12345")
        db.session.add(admin)
        db.session.commit()
        forum_id = forum.id

    client = app.test_client()

    # ---- register ---------------------------------------------------------
    tok = fresh_token(client, "/register")
    response = client.post(
        "/register",
        data={
            "_csrf": tok,
            "username": "tester",
            "email": "tester@test.local",
            "password": "pass12345",
            "password2": "pass12345",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302, response.status_code
    ok("注册成功并跳转")

    # ---- new thread -------------------------------------------------------
    tok = fresh_token(client, f"/f/{forum_id}/new")
    response = client.post(
        f"/f/{forum_id}/new",
        data={"_csrf": tok, "title": "冒烟测试主题", "body": "正文来了 [b]加粗[/b]"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    thread_id = int(response.headers["Location"].rstrip("/").split("/")[-1])
    page = client.get(f"/t/{thread_id}").get_data(as_text=True)
    assert "冒烟测试主题" in page
    assert "<b>加粗</b>" in page, "BBCode 没有被渲染"
    ok("发主题并渲染 BBCode")

    # ---- reply with an image attachment -----------------------------------
    tok = fresh_token(client, f"/t/{thread_id}/reply")
    response = client.post(
        f"/t/{thread_id}/reply",
        data={
            "_csrf": tok,
            "body": "带图回复",
            "files": (io.BytesIO(PNG), "shot.png"),
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    page = response.get_data(as_text=True)
    assert "attachment-image" in page, "附件图片没有内联渲染"
    assert "attachment-thumb" in page, "缩略图模式没有生效"
    ok("上传附件并按缩略图模式内联显示")

    # 附件直链可下载
    match = re.search(r'/attachment/(\d+)', page)
    assert match
    attachment_id = match.group(1)
    file_response = client.get(f"/attachment/{attachment_id}?inline=1")
    assert file_response.status_code == 200
    assert file_response.mimetype == "image/png"
    assert file_response.data == PNG
    ok("附件下载字节一致（image/png）")

    # ---- search -----------------------------------------------------------
    page = client.get("/search?q=冒烟").get_data(as_text=True)
    assert "冒烟测试主题" in page
    ok("搜索命中主题")

    # ---- private message --------------------------------------------------
    tok = fresh_token(client, "/pm/new")
    response = client.post(
        "/pm/new",
        data={"_csrf": tok, "to": "root", "subject": "测试私信", "body": "你好"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    page = client.get("/pm/sent").get_data(as_text=True)
    assert "测试私信" in page
    ok("发送私信")

    # ---- admin ------------------------------------------------------------
    admin_client = app.test_client()
    tok = token(admin_client)
    response = admin_client.post(
        "/login",
        data={"_csrf": tok, "username": "root", "password": "root12345"},
        follow_redirects=False,
    )
    assert response.status_code == 302

    for path in ("/admin/", "/admin/settings", "/admin/forums", "/admin/users"):
        assert admin_client.get(path).status_code == 200, path
    ok("后台四个页面可访问")

    # 关闭缩略图 -> 附件不再包缩略图容器
    tok = fresh_token(admin_client, "/admin/settings")
    response = admin_client.post(
        "/admin/settings",
        data={
            "_csrf": tok,
            "site_name": "LoongBBS Next",
            "site_tagline": "测试环境",
            "posts_per_page": "10",
            "threads_per_page": "25",
            "allowregistration": "1",
            "attachthumbmode": "0",
            "attachthumbwidth": "480",
            "attachthumbheight": "360",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    page = client.get(f"/t/{thread_id}").get_data(as_text=True)
    assert "attachment-thumb" not in page, "关闭缩略图后仍然包了缩略图容器"
    assert "attachment-image" in page, "关闭缩略图后图片不应消失"
    ok("后台关闭缩略图后按原图显示")

    # 重新打开
    tok = fresh_token(admin_client, "/admin/settings")
    admin_client.post(
        "/admin/settings",
        data={
            "_csrf": tok,
            "site_name": "LoongBBS Next",
            "site_tagline": "测试环境",
            "posts_per_page": "10",
            "threads_per_page": "25",
            "allowregistration": "1",
            "attachthumbmode": "1",
            "attachthumbwidth": "480",
            "attachthumbheight": "360",
        },
        follow_redirects=True,
    )
    page = client.get(f"/t/{thread_id}").get_data(as_text=True)
    assert "attachment-thumb" in page
    ok("后台重新打开缩略图后恢复")

    # ---- ban --------------------------------------------------------------
    with app.app_context():
        tester_id = db.session.execute(db.select(User).where(User.username == "tester")).scalar_one().id
    tok = fresh_token(admin_client, "/admin/users")
    admin_client.post(f"/admin/users/{tester_id}/ban", data={"_csrf": tok}, follow_redirects=True)
    page = admin_client.get("/admin/users").get_data(as_text=True)
    assert "已封禁" in page
    ok("后台封禁用户")

    banned_client = app.test_client()
    tok = token(banned_client)
    response = banned_client.post(
        "/login",
        data={"_csrf": tok, "username": "tester", "password": "pass12345"},
        follow_redirects=True,
    )
    assert "已被封禁" in response.get_data(as_text=True)
    ok("被封禁账号无法登录")

    # ---- csrf -------------------------------------------------------------
    response = client.post(f"/f/{forum_id}/new", data={"title": "x", "body": "y"})
    assert response.status_code == 400
    ok("缺少 CSRF token 的写请求被拒绝")

    print(f"\n全部通过：{len(checks)} 项检查")
    return 0


if __name__ == "__main__":
    sys.exit(main())
