# 功能差距清单：loongbbs-next vs vBulletin 2.3.11（本地参考站）

对照基准：`_vb2ref/vbulletin-2.3.11-php8`（前台 28 个 `*.php` 入口、后台 `admin/` 下 20+ 模块）与
`_vb2ref/templates/*.html`（484 个原版模板）；本项目侧取 `flask url_map` 的 58 条路由、后台导航 18 组共 57 个条目。
统计时间：2026-11-06，对应提交 `633d881`。

结论先说：**界面层面的"页面骨架"基本齐了，缺的主要是"页面里的第二层功能"和"后台模块"。**
前台 13 个整页缺失、7 处入口点了没反应；后台 57 个菜单条目里只有 7 个是真页面，其余 50 个是占位。

---

## 一、前台整页缺失（13 项）

| 功能 | 参考站入口 | 本项目现状 | 影响 |
|---|---|---|---|
| 会员列表 | `memberlist.php` | 无路由 | 顶栏「会员列表」图标点了回首页，用户看不到会员 |
| 常见问题 | `misc.php?action=faq` | 无路由 | 顶栏「常见问题」、首页「请先看看 FAQ」都回首页 |
| 谁在线 | `online.php` | 无路由 | 首页「当前在线用户」只是个数字，点进去回首页；没有在线列表/所在页面/IP |
| 日历 | `calendar.php` | 无路由 | 顶栏「日历」回首页，无事件/公共日历 |
| 打印主题 | `printthread.php` | 无路由 | 帖子页「显示可打印版本」链接指回本页 |
| 邮件推荐 | `sendtofriend.php` | 无路由 | 「用邮件推荐这个页面」指回本页 |
| 举报帖子 | `report.php` | 借用私信表单 | 能提交，但落到 PM 而不是举报队列，后台也没有待处理举报页 |
| 主题投票 | `poll.php` | 无（无投票模型） | 主题不能带投票；后台缺 Strip Poll / Who Voted |
| 主题评分 | `threadrate.php` | 只有下拉框 | 表单 GET `?vote=` 到 `/t/<id>`，后端**不读取**，评分不落库、页面也不显示评分 |
| 会员组 / 版主列表 | `showgroups.php` | 无路由 | 无从查看有哪些用户组、谁是版主 |
| 公告 | `announcement.php` | 无 | 版块页顶部不会有公告块 |
| 找回密码 | `member.php?action=lostpw` | 无 | 登录页没有「忘记密码」，密码丢了只能找站长 |
| 编辑个人资料 | `member.php?action=editprofile` | 无（`/u/<用户名>` 只读） | 用户改不了邮箱、生日、来自、兴趣等资料 |

## 二、入口在、点了没用（7 处，属"假链接"）

1. 顶栏 `calendar` / `members` / `faq` 三个图标：全部 `url_for('forums.index')`。
2. 首页「请先看看 **FAQ**」与「当前在线用户」标题：同样回首页。
3. 帖子页「显示可打印版本 / 用邮件推荐这个页面 / 订阅这个主题」：三条都指回主题页自身；没有主题订阅表。
4. 版块页「标记这个版块为已读」：指回版块页，没有 mark-read 动作（`grep markread` 无实现，也没有"全部版块标记已读"）。
5. 「评价本主题」下拉 + GO：`?vote=` 被丢弃（见上表）。
6. 版块页「搜索这个版块」：表单带了 `forum=<id>`，但 `search()` 只读 `q`/`page`，**版块内搜索实际是全站搜索**。
7. 帖子页「向版主举报本帖」：跳私信撰写页（借位实现）。

## 三、后台模块缺失（18 组 57 条，真页面 7 条）

已移植：vBulletin Options（`/admin/settings`）、Forums Modify（`/admin/forums`，含分类/版块新增删除开关）、
Threads Mass Move（`/admin/threads`，移动/删除）、Users Find（`/admin/users`，封禁/设为管理员）、
Avatars Add/Modify/Upload（`/admin/avatars` 全套）、Statistics（`/admin/home`）。

其余 50 条走 `/admin/not-port` 占位页。按组分别是：

- **Announcements**：Add、Modify
- **Forums & Moderators**：Add（能力其实在 Modify 页里）、Permissions（版块权限，完全缺）
- **Threads & Posts**：Mass Prune、Unsubscribe Thread、Strip Poll、Who Voted
- **Moderation**：Moderate New Posts、Moderate New Attachments
- **Users**：Add、Move/Prune、PM Statistics、IP Addresses、Referrals、Email Users、Build Mailing List
- **User Titles**：Add、Modify（前台头衔已取 usergroup，但自定义头衔梯度还没做）
- **User Profile Fields**：Add、Modify（对应前台那 7 行空字段）
- **User Groups**：Add、Modify、Forum Permissions
- **Post Icons** / **Smilies**：Add、Modify、Upload（表情目前只有静态图）
- **Custom vB Codes**：Add、Modify
- **Import & Maintenance**：Back-up Database、Database Settings、BB Import Systems、Update Counters
- **Statistics & Logs**：Admin Log（没有操作日志表）
- **Styles** / **Templates** / **Replacements**：三组 10 条全缺（现在是代码里的 Jinja 模板，不是库内模板）

## 四、数据模型缺口（决定了上面很多页面做不出来）

现有表：categories / forums / threads / posts / users / attachments / settings / avatars / usergroups / pm。
缺：`poll`、`announcement`、`event`（日历）、`threadrate`、`subscription`（主题订阅）、`report`（举报）、
`profilefield`（资料字段定义）、`smilie`、`style` / `template`、`adminlog`、`forumpermission`（版块级权限）、`badwords`。

另外 `users` 表没有原版的 `homepage / icq / aim / yahoo / location / interests / occupation` 列，
所以 `/u/<用户名>` 那 7 行永远是空值 —— 这跟"缺 editprofile"是同一个根因。

## 五、细节与体验差异

- 注册**没有验证码**（参考站用 `regimage.php` 出图，可防机器人）。
- 页脚仍没有 `中文 | English` 语言切换；版权行还是自述文案，不是 `Powered by: vBulletin Version 2.3.11` + Jelsoft 版权。
- 私信只有收件箱/阅读/撰写/已发送，缺追踪、阅读回执、自定义文件夹、导出。
- 附件没有每帖/每日配额，后台也没有附件统计与批量清理页。
- 主题工具：置顶/关闭/编辑/删除可用；**移动、复制、合并、拆分**只有下拉占位（无后端）。
- 搜索缺按作者、按日期范围、按版块三种筛选。
- 版块页筛选行时间范围默认「从最开始」，原版是 `last 30 days` selected。

## 六、建议的处理顺序

**P0（用户一用就撞到）**
1. 编辑个人资料 `editprofile` + 补 `users` 那 7 个资料列（一次改完，顺带修掉 `/u/` 的空行）
2. 找回密码 `lostpw`（邮箱重置令牌）
3. 会员列表 `memberlist`（顶栏 members 图标落地）
4. 版块内搜索（`search()` 读 `forum` 参数，一行改动起效）
5. 标记已读 / 全部标记已读（「标记这个版块为已读」落地）
6. 打印主题 `printthread`（纯模板，成本最低）

**P1（社区感强烈依赖）**
7. 主题评分 `threadrate`（下拉已经在页面上，只缺一张票表和聚合显示）
8. 举报 `report` + 后台举报队列（替掉现在借私信的写法）
9. 公告 `announcement`（前台版块页公告块 + 后台增改）
10. 谁在线 `online`（sessions 表 + 首页链接）

**P2（原版有、用得少）**
11. 投票 `poll`、日历 `calendar`、邮件推荐 `sendtofriend`、会员组页 `showgroups`
12. 语言切换 + 真版权行

**P3（后台 1:1）**
13. 先做前台依赖的三组：User Groups、Forum Permissions、User Profile Fields
14. 再做维护类：Back-up Database、Admin Log、Sensitive Words(Replacements)、Smilies
15. Styles / Templates 是"把模板搬进库"的架构级改造，建议单独立项，不要和功能补齐混在一起

---

### 一句话对照
参考站前台 28 个入口，本项目**真能用的**是 13 个（index / forumdisplay / showthread / newthread / newreply / editpost /
private / usercp / member(仅 getinfo+editoptions+editpassword+好友忽略) / search / attachment / avatar / register），
另有 2 个只有界面（threadrate 下拉、printthread 链接）；后台 20+ 模块，本项目覆盖 6 个。
缺的不是"页面长得不一样"，而是这些页面背后的第二层功能。
