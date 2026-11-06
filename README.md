# LoongBBS Next

一个用 Python / Flask 重写的论坛系统，目标是把 vBulletin 2.3.11 的功能逐步对齐，
同时去掉那套「把 SQL 拼成字符串、方言靠翻译」的历史包袱：

- SQLAlchemy 建模，PostgreSQL 为一等公民（SQLite 也能直接跑起来）
- 模板 + 表单全部走参数化查询，不再有 MySQL/PG 方言翻译层
- 帖内附件图片带细边框，后台可选「缩略图 / 原图」
- 后台可管版块、用户、站点设置

本仓库当前状态见下方 **功能进度**，这是按「先能真跑，再逐项对齐 2.3.11」推进的第一轮。

## 快速开始

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt

# 默认用同目录下的 SQLite；接 PostgreSQL 用环境变量指定
export LOONG_BBS_DATABASE_URL="postgresql+psycopg2://user@/loongbbs?host=/tmp&port=5433"

flask --app run.py init-db
flask --app run.py seed            # 建分类/版块 + 管理员 + 演示数据
flask --app run.py run --debug     # http://127.0.0.1:5000
```

`seed` 默认创建管理员 `admin / admin12345`，可用 `--admin-name`、`--admin-password` 覆盖。

环境变量：

| 变量 | 默认 | 说明 |
| --- | --- | --- |
| `LOONG_BBS_DATABASE_URL` | 仓库目录下 `loongbbs.db` | SQLAlchemy 连接串 |
| `LOONG_BBS_SECRET` | `dev-change-me` | 会话密钥，生产必须改 |
| `LOONG_BBS_UPLOAD_DIR` | 仓库目录下 `uploads` | 附件落盘目录 |
| `LOONG_BBS_MAX_UPLOAD` | `8388608` | 单个请求上传上限（字节） |
| `LOONG_BBS_TIMEZONE` | `Asia/Shanghai` | 展示用站点时区（库里统一存 UTC） |

## 功能进度

已实现（第一轮）：

- 用户：注册、登录、登出、个人主页、封禁状态、管理员标记
- 版块：分类 → 版块，版块列表显示主题数/帖数/最后发帖
- 主题：发主题、回复、置顶、关闭、分页、浏览量、编辑自己的帖子
- 附件：图片/文件上传，图片在帖内内联显示（细边框 + 圆角 + 轻阴影），
  缩略图模式与尺寸在后台可调，点击打开原图，非图片走下载
- 搜索：按关键词搜主题标题与帖子正文
- 私信：收件箱、发信、阅读、回复（对话式列表）
- 后台：站点设置（含缩略图开关）、版块/分类增删改、用户封禁与提权、站点统计

尚未对齐 2.3.11 的部分（按计划逐批补）：

- 投票、日历、主题评分、用户组权限矩阵
- 审核队列、批量删帖/移动主题、附件管理后台
- 头像上传、个性签名渲染、用户资料字段
- 2.3.11 数据导入器（`word`/`searchindex` 那套搜索表结构）
- 全文检索（现在是 `ILIKE` 扫描，数据量上来要换 `tsvector`）

## 目录结构

```
run.py                 # 开发/WSGI 入口
loongbbs/
  __init__.py          # 应用工厂、CLI 命令（init-db / seed）
  extensions.py        # db / login_manager
  models.py            # User Category Forum Thread Post Attachment PrivateMessage Setting
  settings.py          # 运行期设置读取（带请求内缓存）
  auth.py              # 注册/登录/登出/个人主页
  forums.py            # 版块/主题/发帖/回复/编辑
  attachments.py       # 上传与下载
  search.py            # 搜索
  pm.py                # 私信
  admin.py             # 后台
  utils.py             # BBCode 渲染、CSRF、分页、时间格式化
  templates/           # Jinja2 模板
  static/style.css     # 全站样式
scripts/seed.py        # 演示数据
```

## 安全说明

- 所有 SQL 由 SQLAlchemy 生成，不存在拼接注入面
- 发帖正文先转义再解析受限 BBCode（`b i u s url code quote`），不允许原始 HTML
- 所有写操作表单带会话级 CSRF token，`before_request` 统一校验
- 上传文件按内容嗅探决定是否可内联显示，落盘名与用户提交的文件名无关
- 密码用 `werkzeug.security` 哈希，不存明文

## 许可

MIT
