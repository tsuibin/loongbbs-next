# 后台 31 组 Options 接线进度

对照基准：参考站 MariaDB（`127.0.0.1:3307` / `vbulletin` / `setting` 表，按
`settinggroupid` 分组）与 `_vb2ref/vbulletin-2.3.11-php8` 的原版用法。
每组的原值都是直接 dump 出来的，接线时按原版代码里的实际用法落到本项目的 Python/模板。

| 组 | 名称 | 状态 | 说明 |
|---|---|---|---|
| 0 | Version Info | 只读 | 版本信息展示用，无行为 |
| 1 | 开关 | 已接 | `bbactive` 关站页 |
| 2 | General | 已接 | 站点名/URL/联系邮箱等 |
| 3 | Contact | 已接 | 联系站长信息 |
| 4 | Posting Code | 已接 | BBCode / 表情 / IMG 开关 |
| 5 | Forums Home Page | 已接 | 版块描述、置顶/锁图标、深度、`displayloggedin` 等（生日块见文末缺口） |
| 6 | User and registration | 已接 | 注册开关、邮箱验证、签名、`cookietimeout` 等 |
| 7 | Memberlist | 已接 | 会员列表开关、每页条数、发帖榜 |
| 8 | Thread display | 已接 | 每页帖数、排序、分页、`wordwrap`、`stopshouting` |
| 9 | Forum Display | 已接 | 每版主题数、深度、版块内在线、排序默认值 |
| 10 | Search | 已接 | 搜索开关、每页、洪泛、最短/最长词、通配符 |
| 11 | Email | 已接 | `enableemail` |
| 12 | Date/Time | 已接 | 时区偏移、日期/时间/GMT 格式 |
| 14 | Edit | 已接 | 编辑痕迹、限时、标题改频 |
| 15 | IP Logging | 已接 | `logip` 与帖子 IP 显示三态 |
| 16 | Floodcheck | 已接 | `enablefloodcheck` / `floodchecktime` |
| 17 | Banning | 已接 | `enablebanning` / `banip` / `banemail` / `allowkeepbannedemail` |
| 18 | Language | 已接 | `ontext` / `offtext`（「是/否」文案） |
| 19 | Private Messaging | 已接（部分不接） | 接了 `enablepms`、`pmquota`、`pmfloodtime`、`pmmaxchars`、`inboxname`、`sentitemsname`、`checknewpm`、`privallowbbcode`、`privallowbbimagecode`、`privallowsmilies`；不接 `privallowhtml`（本站从不解析原始 HTML，与原值 0 一致）、`privallowicons`（PrivateMessage 无 iconid 字段）、`pmcancelledword` / `pmcancelkill`（本站没有撤回功能） |
| 20 | HTTP Headers | 已接 | `addheaders`、`nocacheheaders`、`gzipoutput` + `gziplevel`、`cookiedomain` / `cookiepath` |
| 22 | Spell Check | **不接** | 该组只有 `spellchecklang`。原版 `newthread` / `newreply` / `editpost` / `priv_sendprivmsg` 模板里的 Spell Check 按钮与 `spch.js` 全被 `<!-- -->` 整段注释掉，参考站界面上根本不存在该控件，且依赖第三方 spellchecker.net 在线服务。接上只会造出一个原版没有的开关 |
| 23 | Templates | 已接 | `addtemplatename` 打开时给页面加 `<!-- template: xxx -->`（Jinja 只能标最外层模板，原版是逐段 eval 拼接） |
| 24 | Load limiting | 已接 | `loadlimit` 读 `/proc/loadavg`（Windows 无此文件自然不生效）；`sessionlimit` 用 15 分钟内活跃会员数近似并发会话；管理员放行；`/login`、`/logout`、`/admin` 留出口（本站没有 vB 的 session 表，全拦会把管理员锁在外面） |
| 25 | Polls | 已接 | `maxpolloptions` 决定发帖页选项行数与落库上限；`updatelastpost=1` 时投票后顶帖 |
| 26 | Avatars | 已接 | `avatarmaxsize`（字节）、`avatarmaxdimension`、`avatarcustomposts` |
| 27 | Attachments | 已接 | `maxattachsize`（字节）、`attachextensions`、`attachthumbmode` / `attachthumbwidth` / `attachthumbheight` |
| 28 | Custom User Titles | 已接 | `ctEnable` 总开关；`ctAdmin` 让管理员无条件可用；`ctEitherOr` 决定「任一满足/两者都要」；`ctPosts` / `ctDays` 用发帖数与注册天数；`ctMaxChars` 截断；`ctCensorWords` + `ctCensorMod` 用 `customcensortext` 同一套规则屏蔽；`resettitle` 回到用户组头衔 |
| 29 | Calendar | **不接** | 11 项（`calendarenabled`、`calbirthday`、`calshowbirthdays`、`calallowhtml`、`calbbimagecode`、`calallowsmilies`、`calallowbbcode`、`caltitlelength`、`calStart` 等）全部服务于 `calendar.php` 的日历与事件系统（calendar 事件表、月历、事件的提交/编辑/删除）。本站没有日历功能，也没有事件数据模型，接成开关只会是没有落点的假开关。其中 `calbirthday` / `calshowbirthdays` 在原版里只决定日历页怎么列生日，首页的今日生日块用的是组 5 的 `showbirthdays`，不应拿日历组开关去替代 |
| 30 | Upload | 已接 | 同组 27 的附件上限与扩展名 |
| 31 | Who's Online | 已接 | `WOLenable` 总开关（关掉显示原版 error_whosonlinedisabled 文案）；`WOLguests` 控制游客行与 Guests 计数；`WOLresolve` 控制 IP 列反解主机名；`WOLrefresh` 控制 meta refresh 秒数。新增 `online_sessions` 表模拟 vB 的 session 表，`/online` 页面复刻 `whosonline.html` |

## 已知缺口（本轮未做，不在上述组内）

- 首页「今日生日」块：原版由组 5 的 `showbirthdays` 控制（`index.php:67-95`），本项目
  首页目前没有该块，`users.birthday` 只在资料页读写。
- 「Most users ever online was …」纪录行：原版由 `index.php` 的 `$loadmaxusers` 统计，
  本项目 `online_sessions` 已能算当前在线数，但没有历史峰值记录。
- 日历（`calendar.php`）整页与其后台模块未做，顶栏「日历」图标仍回到首页。
