# LoongBBS Next 本地部署说明

本机已部署可运行的 LoongBBS Next（Flask + SQLAlchemy 论坛，界面按 vBulletin 2.3.11 风格复刻）。
本文只记录本机实际部署结果，仓库原有的 `README.md` 保持不动。

## 当前状态

| 项目 | 值 |
|---|---|
| 访问地址 | http://127.0.0.1:5000/ （仅本机可访问） |
| 运行方式 | Waitress WSGI（`serve.py`，8 线程），后台进程 |
| Python | `C:\Python314\python.exe` 3.14.0，虚拟环境在仓库内 `.venv` |
| 数据库 | SQLite：`loongbbs.db`（86 KB，含演示数据） |
| 附件目录 | `uploads\` |
| 日志 | `logs\server.out.log`、`logs\server.err.log` |
| 进程号文件 | `.server.pid` |
| 会话密钥 | `.env.local` 中的 `LOONG_BBS_SECRET` |

已灌入的演示数据：4 个版块（站务公告、闲聊灌水、龙架构移植、数据库与运维）、3 个主题、4 个帖子、2 个会员。

## 账号

| 角色 | 用户名 | 密码 |
|---|---|---|
| 管理员 | `admin` | `admin12345` |
| 演示会员 | `loongfan` | `loongfan123` |

> 这两个密码是仓库 `seed` 命令的默认值，仅供本地试用。要对外提供服务前必须改掉，并同时更换 `LOONG_BBS_SECRET`。

## 日常操作

启动（已在运行时脚本会拒绝重复启动）：

```powershell
cd C:\Users\tsuibin\Doubao\chats\2026-11-06\new-chat-1\loongbbs-next
.\start-server.ps1
```

停止：

```powershell
.\stop-server.ps1
```

看日志：

```powershell
Get-Content .\logs\server.err.log -Tail 30
```

开发模式（带自动重载，改模板/代码即时生效，用于调试，不要长期开着）：

```powershell
.\.venv\Scripts\python.exe -m flask --app run.py run --debug
```

## 改监听端口 / 允许局域网访问

默认只绑 `127.0.0.1`。需要同一局域网的其他机器访问时，在 `.env.local` 里追加：

```
LOONG_BBS_HOST=0.0.0.0
LOONG_BBS_PORT=5000
LOONG_BBS_THREADS=8
```

改完执行 `.\stop-server.ps1` 再 `.\start-server.ps1`。绑定 `0.0.0.0` 前请先确认 Windows 防火墙放行该端口，并改掉默认管理员密码。

## 换成 PostgreSQL

SQLite 足以支撑本地试用；数据量或并发上来后可切 PostgreSQL（依赖 `psycopg2-binary` 已装好）：

```powershell
$env:LOONG_BBS_DATABASE_URL="postgresql+psycopg2://user:pass@127.0.0.1:5432/loongbbs"
.\.venv\Scripts\python.exe -m flask --app run.py init-db
```

切换是换库而不是迁移数据，原有 SQLite 数据需要另行导出导入。

## 重建数据库

```powershell
Remove-Item .\loongbbs.db -Force
.\.venv\Scripts\python.exe -m flask --app run.py init-db
.\.venv\Scripts\python.exe -m flask --app run.py seed
```

`seed` 支持 `--admin-name`、`--admin-password` 覆盖默认管理员。

## 界面按 vBulletin 2.3.11 复刻（1:1）

参考仓库：`https://git.loongfans.cn/tsuibin/vbulletin-2.3.11-php8`。

### 差异根因

旧实现是「CSS 类仿制」：`.tborder` / `.thead` / `.tcat` / `.alt1` / `.alt2` / `.smallfont` 一套自定义类，外加自绘的文字 logo。而 vB 2.3.11 原版模板根本不用 CSS 类，而是：

- `<body bgcolor="#666696" text="#000000" leftmargin="10">`
- 表格靠 `bgcolor` 属性 + 固定 `cellpadding="4" cellspacing="1"` 形成 1px 深色网格
- 字体靠嵌套 `<font face="verdana, arial, helvetica" size="1|2">`（normalfont = size 2，smallfont = size 1）
- logo 用真实的 `vBulletin_logo.gif`，顶部按钮用 `top_*.gif`

所以调 CSS 不可能对齐，必须按原始模板重建标记。

### 模板来源

参考仓库 `admin/vbulletin.style`（425 KB）是 vB 的样式导出文件，`|||` 分隔：前段是样式设置项，`|||forumhome|||` 之后是「模板名 / 模板正文」成对出现。按该锚点严格两两配对，导出 **484 个原始模板** 到 `_vb2ref\templates\*.html`（脚本 `_vb2ref\dump_tpl2.py`），样式设置项导出到 `_vb2ref\style_vars.json`（31 项）。

### 前台模板对应关系

| 本项目模板 | vB 原版模板 |
|---|---|
| `templates/base.html` | `header` + `headinclude` + `footer` |
| `templates/index.html` | `forumhome` + `forumhome_forumbit_level1_nopost` |
| `templates/forum.html` | `forumdisplay` + `forumdisplaybit` |
| `templates/thread.html` | `showthread` + `postbit` |
| `templates/post_form.html` | `newthread` / `newreply` |
| `templates/auth/login.html` | `standarderror` 同源的提示框版式 |
| `templates/auth/register.html` | `signupadult` |
| `templates/auth/profile.html` | `getinfo` |
| `templates/search.html` | `searchresults` |
| `templates/pm/*.html` | `privfolder_messages` / `privmessage` / `newreply`（私信版） |
| `templates/error.html` | `standarderror` |
| `templates/admin/*.html` | 后台按 `cp.css`（`/cp.css`）配色 |

### 必须一致的常量

| 用途 | 值 |
|---|---|
| 页面底色 | `#666696` |
| 内容区底色 | `#FFFFFF` |
| 表格外框 | `#555576` |
| 表头 | 底 `#8080A6`、文字 `#EEEEFF` |
| 分类条 | 底 `#606096`、文字 `#FFF788` |
| 交替行 | `#F1F1F1` / `#DFDFDF` |
| 链接 / 悬停 | `#000020` / `#FF4400` |
| 时间文字 | `#666686` |
| 输入框底 | `#CFCFCF` |
| 后台页面底 / 正文 | `#BBBBBB` / `#3F3849` |
| 后台表头 | 底 `#40364D`、文字 `#F5D300` |
| 后台表框 / 交替行 | `#51485F` / `#D0D0D0`、`#C5C5C5` |

### 图片素材

从参考仓库 `images\`（100 个文件）补齐本项目缺失的 41 个：`vBulletin_logo.gif`、`menu_background.gif`、6 个 `top_*.gif`、`multipage.gif`、`lastpost.gif`、`newpm.gif`、`pm.gif`、`sendpm.gif`、`1stars~4stars.gif`、`bbtitle.jpg`、`trashcan.gif`、`announcement.gif` 等，现共 99 个文件。

> 注意：`vBulletin_logo.gif` 是 Jelsoft 的原版商标素材，仅用于本地对照演示。对外发布前建议换成本站自制 logo（同名替换 `loongbbs\static\images\vBulletin_logo.gif` 即可，模板不用改）。

### 后台（Control Panel）的 1:1 还原

- **结构**：入口 `/admin/` 是真实的 `<frameset cols="180,*">` —— 左 frame `/admin/nav`（宽 180px，`#51485F` 底、`cp_logo.gif` 160×49、Control Panel Home），右上 `/admin/head`（高 20px 的三列状态条），右下主区（`/admin/home` 及各功能页）。与原版 `index.php?action=frames` 一致。
- **版式**：主区 `<body leftmargin="10" topmargin="10">` + 原版 `cp.css`（从参考仓库根目录直接拷进 `static/cp.css`，未做改写）；表单是 `<table class="tblborder" cellpadding="1" cellspacing="0" width="90%" align="center">` 包内层 `cellpadding="4"`，表头 `<tr class="tblhead">`（`#40364D` 底 / `#F5D300` 字），数据行 `firstalt` / `secondalt` 交替，提交按钮 `<tr id="submitrow">`（`#40364D` 底 + `#F5D300` 字）。
- **左侧导航**：18 个分组、条目顺序逐个照抄 `admin/index.php?action=nav`（Options / Announcements / Forums & Moderators / Threads & Posts / Moderation / Users / User Titles / User Profile Fields / User Groups / Avatars / Post Icons / Smilies / Custom vB Codes / Import & Maintenance / Statistics & Logs / Styles / Replacements / Templates）。

已移植的功能（点进去真能用）：

| 原版模块 | 本项目路由 |
|---|---|
| Options → vBulletin Options | `/admin/settings` |
| Forums & Moderators → Modify | `/admin/forums`（加分类、加版块、开关、删除） |
| Threads & Posts → Mass Move / Mass Prune | `/admin/threads`（勾选后批量移动、批量删除含全部回复） |
| Users → Find | `/admin/users`（按用户名查找、封禁/解封、授予/撤销管理员） |
| Avatars → Add / Modify / Upload | `/admin/avatars`（按最少帖子数分组的 5 列网格）、`/admin/avatars/add`（单条 + 按目录批量）、`/admin/avatars/upload` |
| Statistics & Logs → Statistics | `/admin/home` |

**头像**：数据表新增 `avatars`（`id / title / minimumposts / avatarpath`，字段与原版 `avatar` 表一致），`users` 表加 `avatar_id`、`custom_avatar` 两列。后台 Modify 页按 `minimumposts` 分段、每行 5 个，条目带 edit / remove；Add 页支持单条与「按目录批量」（扫描 `static/images/avatars` 里尚未入库的图片，逐个填名称与最少帖数）；Upload 页把文件存进 `static/images/avatars` 并入库。删除头像时按原版行为把使用它的会员 `avatar_id` 归零。

前台 `/avatar` 对应 `member.php?action=editavatar`：可从库里选一个（校验最少帖子数）、上传自定义图片、或填图片网址，也能选「不使用」；postbit 与会员资料页都显示真实头像。`seed_avatars.py` 生成了 8 个默认头像（纯 Python 写 PNG，不依赖 Pillow）。

老库升级：在仓库根执行 `upgrade_avatars.py`（补两列 + 建表，可重复执行）。新库直接 `flask --app run.py init-db` 就会建全。

未移植的条目（Announcements、Permissions、User Groups、Post Icons、Smilies、Styles、Templates 等）点击后进入 `/admin/not-port?module=...`，页面上写明「尚未移植」，不会假装成功。

### 活基准：原版 vBulletin 2.3.11 已在本地跑起来

为了逐页对照，参考仓库 `vbulletin-2.3.11-php8` 已在本机部署成可访问的服务：

| 项目 | 值 |
|---|---|
| 原版地址 | http://127.0.0.1:8080/ （后台 `/admin/index.php`） |
| 账号 | `admin` / `admin12345`（前台与后台同一套） |
| PHP | 8.5.12（NTS，解压在 `_vb2ref\runtime\php`，内置服务器 + `router.php` 解决 vB 的相对路径依赖） |
| 数据库 | MariaDB 11.8.9，`127.0.0.1:3307`，库 `vbulletin`，root 空密码，数据目录 `_vb2ref\runtime\mariadb-data` |
| 仓库副本 | `_vb2ref\vbulletin-2.3.11-php8` |
| 装库结果 | 487 个模板、174 项设置、管理员 `admin` |
| 对照数据 | 已播种成与本项目同构的 6 版块 / 4 主题 / 5 帖（`_vb2ref\runtime\seed.sql`） |

启动原版（两条命令，缺一不可）：

```powershell
$rt = "C:\Users\tsuibin\Doubao\chats\2026-11-06\new-chat-1\_vb2ref\runtime"
Start-Process "$rt\mariadb\mariadb-11.8.9-winx64\bin\mariadbd.exe" -ArgumentList @("--defaults-file=$rt\mariadb-data\my.ini","--basedir=$rt\mariadb\mariadb-11.8.9-winx64","--character-set-server=utf8mb4","--collation-server=utf8mb4_general_ci")
Start-Process "$rt\php\php.exe" -ArgumentList @("-c","$rt\php\php.ini","-S","127.0.0.1:8080","-t","$rt\..\vbulletin-2.3.11-php8","$rt\router.php") -WorkingDirectory $rt
```

> 数据目录已初始化、库已装好。**不要**再跑 `mysql_install_db.exe`，也**不要**再访问安装器的 `?step=4&resetdatabase=yes`，那会清库重建。

原版安装时的三个坑（已绕过，重装时注意）：`mariadb-install-db.exe` 不认 `--defaults-file/--basedir`，要用 `mysql_install_db.exe`；
`admin\db_mysql.php` 的 `connect()` 不把 `$port` 传给 `mysqli_connect`，只能在 `$servername` 里写 `host:port`；
安装器写配置必须 `POST ?step=writeconfig`（`step` 要放在 query string 里）。

逐页对照的结论写在 `_vb2ref\compare\DIFF-REPORT.md`，截图两两成对放在仓库上一级目录。

本轮据此修掉的结构差异（详见 `DIFF-REPORT.md` 第一节）：

- 版块页补上第 6 列「评分」（`clear.gif` 空评分）、`Last Post` 表头的反向排序箭头、`(正在浏览此版块的会员: …)` 行；
  数据行恢复成原版 8 格结构（`folder.gif` / 空单元格 / 标题 70% / 发起人 30% / 回复 / 查看 / 评分 / 最后发表）；
  `Forum Rules` 从一行说明改成原版的两列小表格（权限四项 + `HTML/vB/表情/[IMG]` 四项），筛选行 `colspan` 改 8。
- 首页分类条合并回单格 `colspan=6`（原版标题与描述同格），删掉原版没有的「悄悄话」分组块；
  版块 on/off 图标改为按「最后发表晚于上次访问」判断，游客统一 `off.gif`（原来按有帖数判断，永远是「有新帖」）。
- 主题页按 `showthread.html` / `postbit.html` 逐块复刻：面包屑补分类层、`◀ 上一个主题 / 下一个主题 ▶`（
  新增 `prev_thread`/`next_thread`）、表头只写「主题」、作者栏 `注册于 / 位置 / 帖子数`、
  `向版主举报本帖 | IP: 已登录`、`profile`/`pm`/`find`/`buddy` 图标行、论坛跳转首项 `-- 版块名 --`、
  右侧「评价本主题」与「管理选项」两个下拉（含 GO），并删掉原版 2.3.11 没有的快速回复块；
  回复统一走新页 `GET /t/<id>/reply`（`post_form.html` 的 `mode='reply'`）。
- 时间基准回到 GMT：`utils.LOCAL_TZ` 默认 `UTC`，页脚统一 `All times are GMT. The time now is …`；
  seed 里按本地时刻写入的时间戳已减 8 小时，post 2 显示 `11-05-2026 01:06 AM` 与参考站一致。
- 用户头衔改为按 `usergroups.usertitle` 取（新增 `usergroups` 表与 `users.usergroupid/usertitle`），
  admin 显示 `Administrator`、注册会员显示空 —— 取代原来写死的「管理员 / 注册会员 / 楼主」。
- 每条帖子有自己的标题（`posts.title`），回复页「主题:」默认 `Re: <主题标题>`。

`DIFF-REPORT.md` 第二、七、八节记录了逐页对照结果与仍然存在的差异（版权行、语言切换、
`移动/复制 / 合并 / 拆分主题` 仅占位），以及**还没取基准的页面清单**（newthread / newreply / editpost / member /
private / search / memberlist / misc / online / calendar / poll / printthread / showgroups / report / sendtofriend /
attachment / avatar / 注册页 / 错误页，后台除 home 外全部模块页）。

### 用户控制面板（UCP）的 1:1 还原

- 导航条 `auth/_cpnav.html` 对应原版 `usercpnav.html`，共 7 格：我的首页 / 编辑个人资料 / 编辑选项 / 修改密码 /
  编辑好友列表 / 编辑忽略列表 / 私信；`cpnav_current` 决定当前格用 `#8080A6` 高亮，其余 `#DFDFDF`。
  编辑头像页（`member.php?action=editavatar`）按原版习惯不高亮任何格。
- `/usercp/options` ← `member.php?action=editoptions`：照 `modifyoptions.html` 的五段分组表（登录、Cookie 与隐私 /
  私信与通知 / 主题浏览选项 / 日期与时间选项 / 其他选项），18 个选项全部可存；时区用 vB 原值列表（含 `-3.5`、`+5.5`
  半小时档），库里存分钟数（`+8` → 480）。
- `/usercp/password` ← `member.php?action=editpassword`（当前密码校验 + 新密码两次一致）。
- `/usercp/buddy`、`/usercp/ignore` ← `member2.php?action=viewlist&userlist=buddy|ignore`，按逗号串存
  `users.buddylist` / `users.ignorelist`，输入框补到 6 个与原版一致。
- 老库升级：在仓库根执行 `upgrade_options.py`（补 20 个 `users` 列，可重复执行）；新库 `flask init-db` 直接建全。

### 仍未做成 1:1 的部分

- 上表之外的后台模块，以及它们依赖的数据表（用户组、表情、样式表、模板管理）。
- 前台少量链接指向同一页（打印版、邮件推荐、订阅、标记已读等功能未实现），按钮与位置已按原版摆好。

## 已验证

- 仓库自带 `tests\test_smoke.py`：注册、发主题、BBCode 渲染、图片附件上传与缩略图、附件下载字节一致、搜索、私信、后台四个页面、缩略图开关、封禁与登录拦截、CSRF 拦截，共 12 项全部通过（`python tests\test_smoke.py`）。
- 逐路由渲染检查（登录态覆盖 `/`、`/f/*`、`/t/*`、`/f/*/new`、`/post/*/edit`、`/login`、`/register`、`/search`、`/u/*`、`/pm/*`、`/admin/*`，含 404 分支）全部正常，无模板异常。
- 后台专项：`/admin/`（frameset）、`/admin/nav`、`/admin/head`、`/admin/home`、`/admin/settings`、`/admin/forums`、`/admin/users`、`/admin/threads`、`/admin/not-port` 全部 200；Mass Move 与 Mass Prune 在一次性数据库上实测通过（移动后 `forum_id` 变化、删除后主题与其 1 条回复均归零）。
- 页面截图（在仓库上一级目录）：`loongbbs-home-v2.png`（首页）、`shot-login.png`、`shot-home-auth.png`、`shot-forum-auth.png`、`shot-thread-auth.png`、`shot-newthread.png`、`shot-pm.png`、`shot-search.png`、`shot-profile.png`、`shot-admin-frameset.png`（后台三栏整体）、`shot-admin-home.png`、`shot-admin-threads.png`、`shot-admin-avatars.png`（头像库网格）、`shot-avatar.png`（前台编辑头像）、`shot-thread-avatar.png`（帖子里显示头像）。
- 原生对照截图（两两成对，1280×960，与上一条同一窗口）：`vb-orig-home2.png` / `lb-home-compare2.png`、`vb-orig-forum.png` / `lb-forum-compare2.png`、`vb-orig-thread.png` / `lb-thread-compare2.png`；原版后台 `vb-orig-admin-login.png`、`vb-orig-admin.png`。
- 头像链路实测（一次性数据库 + 真实 static）：后台上传落库、单条添加、前台选库头像 → `users.avatar_id` 生效 → 帖子页出现该图 → 自定义上传 → 选「不使用」→ 后台 remove 后会员归零，逐项断言通过；服务重启后 12 项冒烟全过。

## 尚未对齐 vBulletin 2.3.11 的功能

投票、日历、主题评分、用户组权限矩阵、审核队列、附件管理后台、个性签名渲染、2.3.11 数据导入器、全文检索（当前是 `ILIKE` 扫描）。后台除「已移植的功能」表以外的模块（见上）。

UCP 里还差的三个入口：编辑个人资料表单（`member.php?action=editprofile`，现在「编辑个人资料」指向只读资料页）、
找回密码（`member.php?action=lostpw`）、会员列表（`memberlist.php`，好友/忽略列表页的「完整会员列表」链接暂时指到资料页）。

## 与远端仓库的同步状态（2026-11-06 核对）

远端 `https://git.loongfans.cn/tsuibin/loongbbs-next` 只有 3 个提交，`main` 头指针是 `58b2425`（2026-11-06 16:27:41，「界面：补齐 vB2 首页结构细节」）。
把 `archive/main.zip` 快照下来与本地逐文件做 SHA256 比对（比对范围 `loongbbs/`、`tests/` 及根目录 `.py`/`.txt`/`.md`/`.gitignore`/`.ps1`）：

- **远端有、本地没有的文件：0 个** —— 本地已经是最新基线，不需要再拉取。
- 本地比远端多：`static/images/` 整套 vBulletin 图标与 logo（含 8 个头像、后台 `cp_logo.gif`、`1stars~4stars`、`pm_*` 系列）、
  新增模板 `admin/{frameset,nav,head,avatars,avatars_add,avatars_edit,avatars_multiple,avatars_remove,avatars_upload,threads,not_port}.html`、
  `auth/{_cpnav,usercp}.html`、部署脚本 `serve.py` / `start-server.ps1` / `stop-server.ps1`、`seed_avatars.py` / `upgrade_avatars.py`、本文件。
- 本地已改、远端还是旧版：27 个文件（`base/index/forum/thread/profile/avatar/login/register/search/pm/admin_*` 等模板，以及 `__init__.py`、`admin.py`、`auth.py`、`models.py`、`settings.py`、`utils.py`）。
- 结论：这几轮的 1:1 复原改动只存在于本地，**远端仓库尚未包含**；要对外发布得先推送（本机没有 git，gitea 也需要登录态）。

本机没有 `git`，也没有 `.git` 目录（仓库是下载的源码副本），所以「更新到最新」只能是两种做法：
① 远端有新提交时下载 `archive/main.zip` 覆盖受影响的文件（本次不需要，远端无新内容）；
② 把本地改动推回远端 —— 需要先装 git 或在 gitea 网页上逐文件操作，并且要过 Anubis 挑战 + 登录。

运行环境核对：`pip check` 通过（`Flask 3.1.3` / `Flask-SQLAlchemy 3.1.1` / `Flask-Login 0.6.3` / `SQLAlchemy 2.1.8` / `waitress 3.0.2`），
`logs\server.err.log` 为空；登录态巡检 29 条路由全部 200，唯一 404 是 `/f/5` —— 本地库里只有 4 个版块（id 1~4），
原版的 6 条 `forum` 记录里有 2 条是分类，属数据差异而非代码缺陷。


