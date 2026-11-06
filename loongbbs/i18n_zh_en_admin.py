"""后台管理页文案的中英对照。

来源分三类：
1. 参考站 `admin/lang_zh.php` 与 `admin/lang_en.php` 对齐得到的中英短语（术语表）；
2. vBulletin 2.3.11 后台原本就是英文的界面骨架（导航、表头、按钮），本站模板里存的是中文，
   这里给出对应的原版英文措辞；
3. 设置项（Options）的名字与描述。参考站的 settingdesc 在数据库里是中文，
   英文版安装包里才是原文，但那份 SQL 不在手上，所以这里的英文按原文语义直译，
   措辞贴近 vB 后台的习惯（祈使句 + 括号补充）。

注意：分类名、版块名、主题标题这类数据库内容不在这里翻译——参考站英文模式下它们也保持原样。
"""

MAP = {
    # —— 变量名前缀（后面跟动态变量名，靠前缀匹配）——
    "变量名：": "Variable Name: ",

    # —— 导航与页面骨架 ——
    "进入控制面板": "Enter Control Panel",
    "返回控制面板": "Return to Control Panel",
    "控制面板": "Control Panel",
    "模块尚未移植": "Module Not Yet Ported",
    "版本信息": "Version Info",
    "界面按 vBulletin 2.3.11 后台复刻": "Admin interface rebuilt after vBulletin 2.3.11",
    "左侧导航照原版保留了完整的分组与条目，已经移植的条目会直接打开对应页面；没有移植的条目会打开本页说明，不会假装成功。": (
        "The left navigation keeps the complete original groups and entries. Ported entries open "
        "their page directly; entries that are not ported open this explanation page instead of "
        "pretending to succeed."
    ),
    "从这里可以管理站点的一切。左侧导航是原版后台的分组与条目：已经移植的功能直接可用，未移植的条目会打开说明页。": (
        "Everything on the site is managed from here. The left navigation lists the groups and "
        "entries of the original control panel: ported features work directly, entries that are "
        "not ported open an explanation page."
    ),
    "已移植的后台功能：站点选项（Options）、版块与分类（Forums &amp; Moderators → Modify）、主题批量移动与删除（Threads &amp; Posts → Mass Move / Mass Prune）、会员查找与封禁（Users → Find）、统计（Statistics &amp; Logs → Statistics）。": (
        "Admin features already ported: site Options; Forums &amp; Moderators → Modify; "
        "Threads &amp; Posts → Mass Move / Mass Prune; Users → Find; Statistics &amp; Logs → Statistics."
    ),
    "「moderators」是 vBulletin 2.3.11 后台的一个模块，LoongBBS Next 还没有对应的实现。": (
        "\"moderators\" is a module of the vBulletin 2.3.11 control panel. LoongBBS Next has no "
        "equivalent implementation yet."
    ),
    "「templates」是 vBulletin 2.3.11 后台的一个模块，LoongBBS Next 还没有对应的实现。": (
        "\"templates\" is a module of the vBulletin 2.3.11 control panel. LoongBBS Next has no "
        "equivalent implementation yet."
    ),
    "「calendar」是 vBulletin 2.3.11 后台的一个模块，LoongBBS Next 还没有对应的实现。": (
        "\"calendar\" is a module of the vBulletin 2.3.11 control panel. LoongBBS Next has no "
        "equivalent implementation yet."
    ),
    "「phpinfo」是 vBulletin 2.3.11 后台的一个模块，LoongBBS Next 还没有对应的实现。": (
        "\"phpinfo\" is a module of the vBulletin 2.3.11 control panel. LoongBBS Next has no "
        "equivalent implementation yet."
    ),
    "「smilies」是 vBulletin 2.3.11 后台的一个模块，LoongBBS Next 还没有对应的实现。": (
        "\"smilies\" is a module of the vBulletin 2.3.11 control panel. LoongBBS Next has no "
        "equivalent implementation yet."
    ),
    "「backup」是 vBulletin 2.3.11 后台的一个模块，LoongBBS Next 还没有对应的实现。": (
        "\"backup\" is a module of the vBulletin 2.3.11 control panel. LoongBBS Next has no "
        "equivalent implementation yet."
    ),
    "「styles」是 vBulletin 2.3.11 后台的一个模块，LoongBBS Next 还没有对应的实现。": (
        "\"styles\" is a module of the vBulletin 2.3.11 control panel. LoongBBS Next has no "
        "equivalent implementation yet."
    ),
    "「ranks」是 vBulletin 2.3.11 后台的一个模块，LoongBBS Next 还没有对应的实现。": (
        "\"ranks\" is a module of the vBulletin 2.3.11 control panel. LoongBBS Next has no "
        "equivalent implementation yet."
    ),
    "「icons」是 vBulletin 2.3.11 后台的一个模块，LoongBBS Next 还没有对应的实现。": (
        "\"icons\" is a module of the vBulletin 2.3.11 control panel. LoongBBS Next has no "
        "equivalent implementation yet."
    ),
    "「cron」是 vBulletin 2.3.11 后台的一个模块，LoongBBS Next 还没有对应的实现。": (
        "\"cron\" is a module of the vBulletin 2.3.11 control panel. LoongBBS Next has no "
        "equivalent implementation yet."
    ),
    "「css」是 vBulletin 2.3.11 后台的一个模块，LoongBBS Next 还没有对应的实现。": (
        "\"css\" is a module of the vBulletin 2.3.11 control panel. LoongBBS Next has no "
        "equivalent implementation yet."
    ),
    "「faq」是 vBulletin 2.3.11 后台的一个模块，LoongBBS Next 还没有对应的实现。": (
        "\"faq\" is a module of the vBulletin 2.3.11 control panel. LoongBBS Next has no "
        "equivalent implementation yet."
    ),
    "返回 Avatars &rsaquo; Add": "Back to Avatars &rsaquo; Add",
    "当前浏览器不支持框架。": "Your browser does not support frames.",

    # —— 统计块 ——
    "会员总数": "Total Members",
    "主题总数": "Total Threads",
    "帖子总数": "Total Posts",
    "最近注册的会员": "Newest Members",
    "最近发布的帖子": "Latest Posts",
    "注册时间": "Join Date",

    # —— 版块与分类管理 ——
    "版块与分类": "Forums &amp; Categories",
    "版块 / 分类": "Forums / Categories",
    "添加分类": "Add Category",
    "分类名称": "Category Name",
    "添加版块": "Add Forum",
    "所属分类": "Parent Category",
    "版块名称": "Forum Name",
    "全部版块": "All Forums",
    "版块层级": "Forum Depth",
    "开放": "Open",
    "关闭": "Closed",
    "版块下仍有主题时不允许删除；关闭的版块前台不能再发新主题。": (
        "A forum that still contains threads cannot be deleted; a closed forum accepts no new threads "
        "on the front end."
    ),

    # —— 主题管理 ——
    "主题管理": "Thread Management",
    "对选中的主题：": "For the selected threads:",
    "勾选主题后可批量移动到另一个版块，或连同其全部回复一起删除。": (
        "Select threads to move them to another forum in bulk, or delete them together with all "
        "their replies."
    ),
    "（选择目标版块）": "(Select destination forum)",
    "[置顶]": "[Sticky]",
    "主题显示选项": "Thread Display Options",
    "最新在前": "Newest First",
    "最早在前": "Oldest First",
    "每页主题数": "Threads per page",
    "版块列表中提供多页主题的分页链接？": "Provide paged links for multi-page threads in the forum list?",
    "版块页面分页前每页显示的主题数。": "Number of threads shown per page before paging on the forum page.",
    "主题内帖子排序": "Post order in threads",
    "推荐的主题显示顺序是按时间从原帖到最新回复。也可以改为反向显示，即从最新帖到最早帖。": (
        "Threads are normally shown in chronological order, from the original post to the newest "
        "reply. You can show them in reverse order, from the newest post to the oldest."
    ),

    # —— 会员管理 ——
    "用户管理": "User Management",
    "查找会员": "Find User",
    "按版块筛选": "Filter by forum",
    "会员": "Member",
    "会员列表选项": "Member List Options",
    "启用会员列表": "Enable member list",
    "启用会员列表功能？用户可查看注册用户列表，并（可选）在其中搜索。": (
        "Enable the member list? Users can browse the registered user list and, optionally, "
        "search it."
    ),
    "允许高级搜索": "Allow advanced search",
    "允许在会员列表中使用高级搜索。": "Allow advanced search in the member list.",
    "每页会员数": "Members per page",
    "会员列表每页默认显示的记录数。": "Default number of records shown per page in the member list.",
    "限制列表显示范围": "Limit list display range",
    "显示的发帖排行人数": "Number of top posters shown",
    "「显示发帖排行前 x」中的 x 值。": "The x in \"show the top x posters\".",
    "用户名最短长度": "Minimum user name length",
    "用户名最长长度": "Maximum user name length",
    "用户名允许的最小长度。": "Minimum length allowed for user names.",
    "用户名允许的最大长度。": "Maximum length allowed for user names.",
    "非法用户名": "Illegal user names",
    "输入不允许注册的用户名。若用户名包含其中任意一项，将提示错误。多个名字用空格分隔。": (
        "Enter user names that may not be registered. If a name contains any of these, an error is "
        "shown. Separate several names with spaces."
    ),
    "允许同一用户重复注册": "Allow multiple registrations per user",
    "默认情况下，vBulletin 会通过 cookie 阻止同一用户注册多个账号。若要允许注册多个用户名，请选择「是」。": (
        "By default vBulletin uses a cookie to stop one person from registering several accounts. "
        "Choose \"Yes\" to allow several user names per person."
    ),
    "允许新用户注册": "Allow new registrations",
    "如需临时（或永久）禁止新用户注册，可在此设置。REGISTER 按钮仍会显示，但尝试注册的人会被告知当前不接受新注册。": (
        "Use this to disable new registrations temporarily or permanently. The REGISTER button is "
        "still shown, but anyone trying to register is told that registrations are not being "
        "accepted at the moment."
    ),
    "注册时校验邮箱地址": "Verify email address at registration",
    "要求邮箱地址唯一": "Require unique email addresses",
    "默认要求每个注册用户的邮箱唯一，即两个用户不能使用同一邮箱。取消勾选「不要求唯一邮箱」可关闭此限制。": (
        "Each registered user is required to have a unique email address, so two users cannot share "
        "one address. Uncheck \"do not require a unique email\" to lift this restriction."
    ),
    "允许忽略版主": "Allow ignoring moderators",
    "允许用户将版主和管理员加入忽略列表吗？": "May users add moderators and administrators to their ignore list?",
    "新会员需审核": "Moderate new members",
    "允许你在新会员成为正式注册会员并获得发帖权限之前进行审核。": (
        "Lets you approve new members before they become full registered members with posting "
        "rights."
    ),
    "新会员通知": "New member notification",
    "有新用户注册时接收通知的邮箱。留空则不发送。": (
        "Email address that receives a notification when a new user registers. Leave empty to send "
        "nothing."
    ),
    "自定义用户头衔": "Custom User Titles",
    "用户与注册选项": "User and Registration Options",
    "用户权限区域": "User Permissions",
    "高亮显示管理员": "Highlight admins",
    "启用后，在「已登录用户」和「在线用户」中，管理员名字以粗斜体显示，版主名字以粗体显示。": (
        "When enabled, administrators are shown in bold italic and moderators in bold in the "
        "logged-in users and Who's Online listings."
    ),

    # —— 举报 ——
    "举报帖子": "Reported Posts",
    "目前没有举报记录。会员在主题页点「向版主举报本帖」后，记录会出现在这里。": (
        "There are no reported posts yet. Records appear here after a member clicks \"report this "
        "post to a moderator\" on a thread page."
    ),
    "状态": "Status",
    "说明": "Details",
    "操作": "Actions",
    "时间": "Time",
    "角色": "Role",
    "附件": "Attachments",

    # —— 头像管理 ——
    "「images/avatars」下面没有可加入的图片。": "There are no images under \"images/avatars\" that can be added.",
    "附件图片的缩略图上限怎么定？": "How is the thumbnail limit for attachment images set?",
    "上传选项": "Upload Options",
    "支持 gif / jpg / png / bmp / webp": "Supports gif / jpg / png / bmp / webp",

    # —— 站点设置：分组名 ——
    "全部设置": "All Settings",
    "常规设置": "General Settings",
    "联系方式": "Contact Details",
    "邮件选项": "Email Options",
    "封禁选项": "Banning Options",
    "语言选项": "Language Options",
    "私信选项": "Private Messaging Options",
    "拼写检查": "Spell Check",
    "首页版块选项": "Forum Home Options",
    "刷屏检查选项": "Flood Check Options",
    "负载限制选项": "Load Limit Options",
    "敏感词过滤选项": "Word Censor Options",
    "IP 记录选项": "IP Logging Options",
    "日期 / 时间选项": "Date / Time Options",
    "HTTP 头与输出": "HTTP Headers and Output",
    "论坛开关": "Forum Open/Closed",
    "论坛是否开放": "Forum Open/Closed",
    "版块显示选项": "Forum Display Options",
    "这些值保存在 settings 表，保存后前台即时生效。分组与字段照原版 vB 后台的 Options 页面。": (
        "These values are stored in the settings table and take effect on the front end as soon as "
        "they are saved. Groups and fields follow the Options pages of the original vB control panel."
    ),

    # —— 站点设置：字段名 ——
    "论坛名称": "Forum Name",
    "首页名称": "Home Name",
    "论坛 URL": "Forum URL",
    "首页 URL": "Home URL",
    "版权信息": "Copyright Text",
    "站长邮箱": "Webmaster Email",
    "传真号码": "Fax Number",
    "公司名称": "Company Name",
    "公司地址": "Company Address",
    "隐私声明 URL": "Privacy Statement URL",
    "「联系我们」链接": "\"Contact Us\" link",
    "GD 版本": "GD Version",
    "时区偏移": "Time Offset",
    "日期格式": "Date Format",
    "时间格式": "Time Format",
    "生日格式": "Birthday Format",
    "生日格式 #2": "Birthday Format #2",
    "注册日期格式": "Registered Date Format",
    "显示邮箱地址": "Display email addresses",
    "允许公开查看邮箱地址。": "Allow email addresses to be visible to everyone.",
    "隐藏私密版块": "Hide private forums",
    "允许使用签名": "Allow signatures",
    "允许签名中使用表情？": "Allow smilies in signatures?",
    "允许签名中使用 [img] 代码？": "Allow [img] code in signatures?",
    "允许签名中使用 vB 代码？": "Allow vB code in signatures?",
    "允许签名中使用 HTML？": "Allow HTML in signatures?",
    "允许注册用户使用签名。别忘了同步修改这些模板：newtopic newreply editpost modifyprofile register": (
        "Allow registered users to use signatures. Remember to update these templates as well: "
        "newtopic newreply editpost modifyprofile register"
    ),
    "每帖/签名最多图片数": "Maximum images per post/signature",
    "帖子/签名中允许的最大图片数。设为 0 表示不限制。": (
        "Maximum number of images allowed in a post or signature. Set to 0 for no limit."
    ),
    "每帖最大字符数": "Maximum characters per post",
    "每帖允许的最大字符数。设为 0 表示不限制。": (
        "Maximum number of characters allowed in a post. Set to 0 for no limit."
    ),
    "允许用户自设每页帖子数": "Allow users to set posts per page",
    "如果允许用户自行设置每帖最多显示多少楼，请用逗号分隔各选项。留空则强制使用上方的 MAXPOSTS 设置。例如 10,20,30,40": (
        "If users may choose how many posts to show per page, list the options separated by commas. "
        "Leave empty to force the MAXPOSTS setting above. For example 10,20,30,40"
    ),
    "每页帖子数": "Posts per page",
    "单页最多帖子数（超出则分页）": "Maximum posts per page (paging starts beyond this)",
    "显示默认图标": "Show default icon",
    "当用户未选择帖子图标或受版块设置限制无法选择时，是否显示默认图标？将使用 {imagesfolder}/icons/icon1.gif。": (
        "Should a default icon be shown when a user picked no post icon, or cannot pick one because "
        "of the forum settings? {imagesfolder}/icons/icon1.gif is used."
    ),
    "允许使用消息图标": "Allow message icons",
    "全局开关：完全禁用 vB 代码按钮和可点击表情。": (
        "Global switch: disable the vB code buttons and clickable smilies completely."
    ),
    "显示 vB 代码按钮与可点表情？": "Show vB code buttons and clickable smilies?",
    "发帖代码权限（vB 代码 / HTML 等）": "Posting code permissions (vB code / HTML and so on)",

    # —— 搜索 ——
    "启用搜索？": "Enable search?",
    "允许在论坛内搜索帖子。该功能较耗服务器资源，可考虑关闭。": (
        "Allow posts to be searched inside the forum. This feature is server intensive; consider "
        "turning it off."
    ),
    "搜索词最短长度": "Minimum search word length",
    "搜索词最长长度": "Maximum search word length",
    "搜索引擎建立索引的最小词长。数值越小，搜索索引和数据库越大。": (
        "Shortest word length indexed by the search engine. The smaller the value, the larger the "
        "search index and the database."
    ),
    "搜索引擎建立索引的最大词长。数值越大，搜索索引和数据库越大。": (
        "Longest word length indexed by the search engine. The larger the value, the larger the "
        "search index and the database."
    ),
    "搜索结果每页显示的条目数。": "Number of results shown per page.",
    "允许通配符？": "Allow wildcards?",
    "允许用户在搜索中使用星号（*）匹配部分单词？": "May users use an asterisk (*) to match partial words in searches?",
    "若要完全禁用所有版块的搜索，请删除 searchintro 模板中的相应选项。": (
        "To disable searching in all forums entirely, remove the corresponding option from the "
        "searchintro template."
    ),
    "用户两次搜索之间必须间隔的最短时间（秒）。设为 0 表示不限制。": (
        "Minimum time in seconds between two searches by one user. Set to 0 for no limit."
    ),
    "刷屏检查 - 两次搜索的最短间隔": "Flood Check - minimum time between two searches",

    # —— 邮件 ——
    "启用邮件功能？": "Enable email features?",
    "启用邮件功能：发送给朋友，以及给发帖人和版主的邮件通知。别忘了从": (
        "Enable email features: send to friend, plus email notification to posters and moderators. "
        "Remember to remove"
    ),
    "模板中删除对应链接": "the corresponding links from the templates",
    "为个别用户组关闭「发送给朋友」。": "Turn off \"send to friend\" for individual user groups.",
    "使用邮件表单？": "Use email form?",
    "当「显示邮箱地址」为「是」时，邮箱如何显示？设为「是」则必须填写在线表单才能发信，从而隐藏收件地址；设为「否」则直接显示邮箱地址。": (
        "How are email addresses shown when \"display email addresses\" is \"Yes\"? Choose \"Yes\" to "
        "require the online form before mail can be sent, hiding the recipient address; choose "
        "\"No\" to show the address directly."
    ),
    "站长的邮箱地址。": "Webmaster email address.",
    "论坛标题，会显示在每个页面的标题栏。": "Forum title, shown in the title bar of every page.",
    "首页名称，会显示在每个页面底部。": "Home name, shown at the bottom of every page.",
    "首页网址，会显示在每个页面底部。": "Home URL, shown at the bottom of every page.",
    "论坛网址（结尾不要带「/」），也不要包含「/index.php」。例如：http://www.example.com/forum": (
        "Forum URL (no trailing \"/\"), and do not include \"/index.php\". For example: "
        "http://www.example.com/forum"
    ),
    "联系本站的链接，可以直接是 mailto:webmaster@example.com，也可以是你自己的表单。显示在每个页面底部。": (
        "The contact link can be a plain mailto:webmaster@example.com or your own form. It is shown "
        "at the bottom of every page."
    ),
    "插入到页面页脚的版权文字。": "Copyright text inserted into the page footer.",
    "隐私声明网址（如果有）。": "Privacy statement URL (if any).",

    # —— 封禁 ——
    "启用封禁选项？": "Enable banning options?",
    "封禁功能可阻止特定 IP 和邮箱注册及发帖。": (
        "Banning stops specific IP addresses and email addresses from registering and posting."
    ),
    "记录 IP 地址？": "Log IP addresses?",
    "不记录 IP": "Do not log IPs",
    "记录，仅管理员/版主可见": "Log, visible to admins/moderators only",
    "记录并公开显示": "Log and display publicly",
    "出于安全考虑，可显示发帖人的 IP。默认关闭。可选择仅记录到文件（论坛上不可见），或记录并在论坛公开显示。": (
        "For security reasons the poster's IP can be shown. Off by default. You may log it to the "
        "files only (not visible on the forum), or log and display it publicly on the forum."
    ),
    "待封禁的 IP：": "IPs to ban:",
    "待封禁的邮箱地址": "Email addresses to ban",
    "IP 封禁列表：可禁止指定 IP 注册和发帖。填写完整 IP（如 243.21.31.7）或部分 IP（如 243.21.31）。系统会从 IP 开头匹配：填 243.21.31 时，IP 为 243.21.31.5 的人无法注册；填 243.21 时，IP 为 243.21.3.44 的人也无法注册。因此请尽量精确。多个 IP 用空格分隔。": (
        "IP ban list: stops the listed IPs from registering and posting. Enter a full IP (such as "
        "243.21.31.7) or part of one (such as 243.21.31). Matching runs from the start of the IP: "
        "entering 243.21.31 blocks 243.21.31.5, while entering 243.21 also blocks 243.21.3.44. So be "
        "as precise as you can. Separate several IPs with spaces."
    ),
    "邮箱封禁列表：可禁止特定邮箱注册。封禁某个邮箱请填完整地址（如 waldo@whereiswaldo.com）；封禁整个域名（如 hotmail）只填域名（如 hotmail.com）即可。多个邮箱用空格分隔。": (
        "Email ban list: stops the listed email addresses from registering. To ban one address, "
        "enter it in full (such as waldo@whereiswaldo.com); to ban a whole domain (such as hotmail), "
        "enter just the domain (such as hotmail.com). Separate several addresses with spaces."
    ),
    "允许用户保留被封禁的邮箱": "Allow users to keep banned email addresses",
    "如果你封禁了某邮箱而用户正在使用它，可在此设置：用户下次修改邮箱时必须换成新地址，还是可以继续保留这个被封禁的邮箱。": (
        "If you ban an address that a user is already using, decide here whether the user must "
        "switch to a new address on the next email change, or may keep the banned address."
    ),

    # —— 私信 ——
    "悄悄话": "Private Messages",
    "启用私信支持": "Enable private messaging",
    "私信支持 - 检查新私信": "Private Messaging - Check for new PMs",
    "选择「是」后，每次用户打开页面都会检查私信库，并显示新私信提示。": (
        "With \"Yes\", the private message store is checked every time a user opens a page, and new "
        "message notices are shown."
    ),
    "收件箱名称": "Inbox name",
    "收件箱文件夹的名称。": "Name of the Inbox folder.",
    "已发送箱名称": "Sent Items name",
    "已发送文件夹的名称。": "Name of the Sent Items folder.",
    "每条私信的最大字符数": "Maximum characters per private message",
    "私信允许的最大字符数。设为 0 表示不限制。": (
        "Maximum characters allowed in a private message. Set to 0 for no limit."
    ),
    "最多保存的消息数": "Maximum saved messages",
    "用户最多可保存的私信数量。0 表示不限制。": (
        "Maximum number of private messages a user may keep. 0 means no limit."
    ),
    "允许私信中使用表情？": "Allow smilies in private messages?",
    "允许私信中使用 [img] 代码？": "Allow [img] code in private messages?",
    "允许私信中使用 vB 代码？": "Allow vB code in private messages?",
    "允许私信中使用 HTML？": "Allow HTML in private messages?",
    "允许私信使用标准消息图标。": "Allow the standard message icons in private messages.",
    "标记已取消消息的用词": "Word used to mark cancelled messages",
    "删除「已取消」的消息？": "Delete cancelled messages?",
    "当用户在消息跟踪中「取消」消息时，是否彻底删除该消息？警告：选择「是」可能会让已收到邮件通知的用户困惑。": (
        "When a user cancels a message in message tracking, should the message be deleted "
        "completely? Warning: choosing \"Yes\" may confuse users who already received the email "
        "notification."
    ),
    "私信防灌水：两次发送私信之间的最短间隔，防止单个用户快速大量发信。设为 0 表示不限制。": (
        "Private message flood check: minimum time between two private messages, to stop one user "
        "from sending large numbers of messages quickly. Set to 0 for no limit."
    ),
    "刷屏检查 - 两条私信的最短间隔": "Flood Check - minimum time between two private messages",

    # —— 刷屏检查 ——
    "启用发帖刷屏检查？": "Enable flood check?",
    "防灌水检查的时间（秒）。建议 60。只填数字。": (
        "Length of the flood check in seconds. 60 is recommended. Numbers only."
    ),
    "两次发帖的最短间隔": "Minimum time between posts",
    "启用后可防止用户连续灌水：限制两次发帖的最小间隔。例如设为 60 秒，则用户发帖后 60 秒内不能再次发帖。管理员和版主不受限制。": (
        "When enabled this stops users from flooding: it limits the minimum interval between two "
        "posts. With 60 seconds, a user cannot post again within 60 seconds of a post. Administrators "
        "and moderators are not restricted."
    ),
    "帖子可编辑时限": "Post edit time limit",
    "允许编辑帖子的时限（分钟）。超过后只有版主能编辑或删除。1 天为 1440 分钟。设为 0 表示不限制。": (
        "Time limit in minutes for editing a post. After that only moderators may edit or delete it. "
        "One day is 1440 minutes. Set to 0 for no limit."
    ),
    "主题标题可编辑时限": "Thread title edit time limit",
    "主题作者可以编辑主题标题的时限（分钟）。": (
        "Time limit in minutes for a thread author to edit the thread title."
    ),
    "对管理员也显示「已编辑」？": "Show \"edited by\" for administrators too?",
    "若希望管理员编辑帖子时显示 [edited by xxx]，请选择「是」。版主和其他用户默认会显示，此选项可单独关闭管理员的提示。": (
        "Choose \"Yes\" if [edited by xxx] should be shown when an administrator edits a post. "
        "Moderators and other users always show it; this option turns the note off for "
        "administrators only."
    ),
    "帖子被编辑后显示「由 xxx 于 yyy 编辑」？": "Show \"edited by xxx on yyy\" after a post is edited?",
    "多久后才开始显示「已编辑…」": "How long before the \"edited\" note starts appearing",
    "用户在多少分钟（以内）编辑帖子时不显示 [edited by xxx]。": (
        "Minutes within which an edit by the user does not show [edited by xxx]."
    ),
    "禁止标题全大写「吼叫」": "Stop shouting in thread titles",
    "把全大写标题改为仅首字母大写，防止用户在标题中「大喊」。使用不同字符集的国际论坛建议关闭，可能引发问题。": (
        "Change all-capital thread titles to initial capitals only, so users cannot \"shout\" in "
        "titles. International forums using other character sets should turn this off; it may cause "
        "problems there."
    ),

    # —— 敏感词 ——
    "启用敏感词过滤？": "Enable word censor?",
    "待过滤的词": "Words to censor",
    "可以对论坛中的某些词进行屏蔽，被屏蔽的词会替换成星号，影响所有标题和内容。": (
        "Certain words can be censored across the forum; censored words are replaced by asterisks in "
        "all titles and content."
    ),
    "替换敏感词所用的字符：": "Character used to replace censored words:",
    "在此填写要屏蔽的词。用空格分隔，不要用逗号。例如填「dog cat boy」而不是「dog, cat, boy」。填「dog」会屏蔽所有包含「dog」的词（如 dogma 会显示为「***ma」）。若要更精确，可以只屏蔽完整单词：把词放进花括号，如 {dog}，此时 dogma 保持原样而 dog 显示为「***」。因此列表可以写成：cat {dog} {barn} barn": (
        "Enter the words to censor, separated by spaces — not commas. For example \"dog cat boy\", "
        "not \"dog, cat, boy\". Entering \"dog\" censors every word containing it (dogma shows as "
        "\"***ma\"). To be more precise, censor whole words only: put the word in curly braces, as "
        "in {dog}; then dogma stays intact while dog shows as \"***\". The list can therefore read: "
        "cat {dog} {barn} barn"
    ),
    "不要使用引号，精确匹配必须用花括号而不是圆括号。": (
        "Do not use quotes; exact matching must use curly braces rather than parentheses."
    ),

    # —— 表情 ——
    "可点表情总数": "Total smilies shown",
    "每行可点表情数": "Smilies per row",
    "启用可点击表情后，屏幕上先显示多少个表情，用户再点击「更多」查看其余。": (
        "How many smilies are shown first when clickable smilies are enabled, before the user clicks "
        "\"more\" for the rest."
    ),
    "启用可点击表情后，每行显示多少个表情？": "How many smilies are shown per row with clickable smilies enabled?",

    # —— 首页 / 在线 ——
    "首页显示版块简介。": "Show forum descriptions on forum home.",
    "首页显示今日生日？": "Show today's birthdays on forum home?",
    "首页显示已登录用户": "Show logged-in users on forum home",
    "是否在首页显示已登录的活跃会员？显示最近 {cookie 超时时间} 秒内活跃的用户。": (
        "Show active logged-in members on forum home? Users active within the last "
        "{cookie timeout} seconds are shown."
    ),
    "首页显示的版块层级深度。出于性能考虑，不要设得太大。": (
        "Forum depth shown on forum home. Do not set this too high, for performance reasons."
    ),
    "启用后会给首页带来一定性能开销，也可能并不是你想要的功能。": (
        "This adds some load to forum home and may not be the feature you want."
    ),
    "显示正在浏览版块的用户？": "Show users browsing forums?",
    "启用后会在 forumdisplay.php 显示当前浏览该版块的用户，并增加一次查询，通常不影响性能。": (
        "When enabled, forumdisplay.php lists the users currently browsing that forum and adds one "
        "query; performance is usually unaffected."
    ),
    "版块页显示子版块时的层级深度。出于性能考虑不要设得太大。": (
        "Depth shown when listing sub-forums on a forum page. Do not set this too high, for "
        "performance reasons."
    ),
    "使用「热门」图标": "Use \"hot\" icons",
    "热门图标表示活动频繁的主题，图标会显示为着火的文件夹动画。": (
        "The hot icon marks heavily active threads; the icon appears as a burning folder animation."
    ),
    "判定热门主题所需的查看数": "Views needed for a hot thread",
    "判定热门主题所需的回复数": "Replies needed for a hot thread",
    "整体开关": "Global switch",
    "显示已锁定版块？": "Show locked forums?",
    "启用「版块跳转」？": "Enable forum jump?",
    "是否在页面使用「版块跳转」下拉菜单？若 MySQL 已优化但仍有效能问题，可关闭此选项以减少查询。": (
        "Use the \"forum jump\" drop-down on pages? If MySQL is tuned but performance is still an "
        "issue, turn this off to save queries."
    ),

    # —— 用户组 / 权限 ——
    "启用访问权限掩码？": "Enable access masks?",
    "访问权限掩码是管理版块权限的简便方式，但会在多数页面增加查询。若不使用，建议关闭。": (
        "Access masks are a convenient way to manage forum permissions, but they add queries on "
        "most pages. If you do not use them, turning this off is recommended."
    ),
    "选择「是」可对无权访问的用户隐藏私密版块；即使有权限，也需要登录后才能在首页和「跳转到…」框中看到。": (
        "Choose \"Yes\" to hide private forums from users without access; even with access they "
        "need to log in before the forum appears on forum home and in the \"jump to...\" box."
    ),
    "选择「是」可让「等待确认」「等待 COPPA」「未注册/未登录」用户组的会员不出现在会员列表中。": (
        "Choose \"Yes\" to keep members of the \"awaiting confirmation\", \"awaiting COPPA\" and "
        "\"unregistered/not logged in\" groups out of the member list."
    ),
    "使用「圆点」图标？": "Use the \"dot\" icon?",
    "启用后，已登录用户会在自己参与过的主题旁看到文件夹图标上的「圆点」（或你选择的图形）。": (
        "When enabled, logged-in users see a \"dot\" (or the image you chose) on the folder icon "
        "next to threads they have posted in."
    ),
    "使用「圆点」图标": "Use the \"dot\" icon",

    # —— 开关文字 / 日期时间 ——
    "「开」的显示文字": "Text for \"on\"",
    "「关」的显示文字": "Text for \"off\"",
    "表示「开启」的文字，用于让代码与语言无关。用于帖子中的 vB 代码 / HTML 代码 开/关 显示。": (
        "Text that means \"on\", so the code stays language independent. Used for the on/off display "
        "of vB code and HTML code in posts."
    ),
    "表示「关闭」的文字，用于让代码与语言无关。用于帖子中的 vB 代码 / HTML 代码 开/关 显示。": (
        "Text that means \"off\", so the code stays language independent. Used for the on/off display "
        "of vB code and HTML code in posts."
    ),
    "页面日期的显示格式。": "Display format for the date.",
    "页面时间的显示格式。": "Display format for the time.",
    "用于格式化帖子中显示的注册日期。主题列表左侧、用户名和头衔下方会显示注册时间。": (
        "Formats the registered date shown in posts. The join date appears on the left of the thread "
        "list, under the user name and title."
    ),
    "服务器相对 GMT 的时差（小时）。请选择最合适的一项。": (
        "Server offset from GMT in hours. Pick the most appropriate one."
    ),
    "用户未填写出生年份时，资料中显示的生日格式。不要包含年份代码。": (
        "Birthday format shown in profiles when the user gave no birth year. Do not include the year "
        "code."
    ),
    "用户填写出生年份时，资料中显示的日期格式。": (
        "Date format shown in profiles when the user gave a birth year."
    ),
    "美式全称（如 April 25th, 1998）- F jS, Y": "US full (such as April 25th, 1998) - F jS, Y",
    "欧式全称（如 25th April 1998）- jS F Y": "European full (such as 25th April 1998) - jS F Y",
    "美式（如 04-25-98）- m-d-y": "US (such as 04-25-98) - m-d-y",
    "欧式（如 25-04-98）- d-m-Y": "European (such as 25-04-98) - d-m-Y",
    "12 小时制（如 11:15 PM）- h:i A": "12 hour (such as 11:15 PM) - h:i A",
    "24 小时制（如 23:15）- H:i": "24 hour (such as 23:15) - H:i",

    # —— 负载 / 分页 / 其他 ——
    "分页链接的最大数量": "Maximum number of page links",
    "在主题（或版块）的分页链接中，当前页两侧各显示多少页。设为 0 表示显示全部页码。": (
        "In thread or forum paging links, how many pages are shown either side of the current page. "
        "Set to 0 to show every page number."
    ),
    "导航栏显示的页数": "Pages shown in the nav bar",
    "版块列表分页链接中，超过多少个页码后不再继续列出，而用「更多…」代替。": (
        "In the forum list paging links, after how many page numbers the list stops and shows "
        "\"more...\" instead."
    ),
    "自动换行的字符数": "Characters before automatic word wrap",
    "若希望自动在长单词中插入空格按固定字符数换行，请填写字符数；不需要则填 0。": (
        "To break long words automatically by inserting a space every fixed number of characters, "
        "enter that number; enter 0 to turn this off."
    ),
    "移动主题的标题前缀": "Prefix for moved thread titles",
    "被移动到其他版块的主题标题前缀（可使用 HTML）。": (
        "Prefix for the titles of threads moved to another forum (HTML allowed)."
    ),
    "置顶主题的标题前缀": "Prefix for sticky thread titles",
    "设为「置顶」的主题标题前缀，这类主题总显示在列表顶部（可使用 HTML）。": (
        "Prefix for the titles of threads set to sticky; such threads always show at the top of the "
        "list (HTML allowed)."
    ),
    "投票主题的标题前缀": "Prefix for poll thread titles",
    "投票主题标题的前缀（可使用 HTML）。": "Prefix for poll thread titles (HTML allowed).",
    "投票": "Poll",
    "模板": "Template",
    "显示票数": "Show Votes",
    "允许改票？": "Allow vote changes?",
    "是否允许用户修改对主题的评分？": "May users change their rating of a thread?",
    "主题需要多少票后才显示投票结果？": "How many votes before poll results are shown?",

    # —— 注册 / COPPA / 验证 ——
    "使用 COPPA 注册机制": "Use the COPPA registration system",
    "启用 COPPA 注册流程，符合 COPPA 法律：13 岁以下儿童发帖前须获得父母同意。关于该法律的更多说明见：": (
        "Enable the COPPA registration flow, as COPPA requires: children under 13 need parental "
        "consent before posting. More on the law:"
    ),
    "公司名称，COPPA 需要。": "Company name, required by COPPA.",
    "公司地址，COPPA 表单会寄往此处。": "Company address, the COPPA form is mailed here.",
    "公司传真号，COPPA 表单会传真到此号码。": "Company fax number, the COPPA form is faxed here.",
    "图片验证码": "Image verification",
    "启用后，注册时会向新用户显示随机验证码图片，用户需输入图中内容以确认不是自动程序。需要服务器启用 GD。": (
        "When enabled, registration shows new users a random verification image and they must type "
        "its contents to prove they are not a bot. GD must be enabled on the server."
    ),
    "服务器上安装的 GD 版本。若已启用 GD，可在 phpinfo() 中查看版本。": (
        "GD version installed on the server. If GD is enabled, check the version in phpinfo()."
    ),
    "新会员提交注册后，系统会把密码邮件发送给他，以确认身份和邮箱。若账号未激活，将一直留在「等待激活的用户」用户组。": (
        "After a new member registers, the password email is sent to confirm identity and address. "
        "Until the account is activated the user stays in the \"users awaiting activation\" group."
    ),
    "启用推荐系统？": "Enable the referral system?",
    "启用推荐系统？启用后，若用户通过含 referrerid=XXX 的链接访问并注册，推荐积分将记到该用户名下（XXX 为推荐人的 userid）。": (
        "Enable the referral system? When enabled, a user arriving through a link containing "
        "referrerid=XXX and registering credits the referral to that user (XXX is the referrer's "
        "userid)."
    ),
    "允许用户切换风格": "Allow users to change styles",
    "允许用户在注册或编辑选项时选择风格。设为「否」将禁用该选项，强制使用指定风格。": (
        "Allow users to choose a style when registering or editing options. \"No\" disables the "
        "option and forces the specified style."
    ),
    "在线用户": "Who's Online",
    "文件固定存到": "Files are stored in",

    # —— 补漏：整句 ——
    "关闭论坛时显示的原因": "Reason shown when the forum is closed",
    "论坛关闭时显示的文字。": "Text shown when the forum is closed.",
    "管理员仍可正常浏览论坛": " Admins can still browse the forums normally",
    "注意：即使对公众关闭，管理员仍可照常浏览论坛。": (
        "Note: even when closed to the public, administrators can still browse the forums as usual."
    ),
    "Cookie 有效期": "Cookie timeout",
    "允许 [img] 标签使用动态 URL？": "Allow dynamic URLs in [img] tags?",
    "用户多久（秒）不活动后，未读帖子会被重置为已读。": (
        "Seconds of inactivity after which unread threads are marked as read."
    ),
    "本字段最多 250 个字符。": "This field allows at most 250 characters.",
    "搜索选项": "Search Options",
    "消息跟踪": "Message Tracking",
    "推荐人": "Referrer",
    "参见：": "See also:",
    "示例：": "Example:",
    "可参考": "See",
    "也可在": "you can also",
    "），也可以直接贴完整网址。": "), or paste the full URL.",
    "是": "Yes",
    "否": "No",

    # —— 补漏：后台页头 / 页脚 / 说明句 ——
    "（Flask + SQLAlchemy 重制）": " (Flask + SQLAlchemy rebuild)",
    "LoongBBS Next（Flask + SQLAlchemy 重制）": "LoongBBS Next (Flask + SQLAlchemy rebuild)",
    "界面参照 vBulletin 2.3.11（2.3.11-php8 移植版）": (
        "Interface based on vBulletin 2.3.11 (2.3.11-php8 port)"
    ),
    "从这里可以管理站点的一切。左侧导航是原版后台的分组与条目：已经移植的功能直接可用，未移植的条目会打开说明页。": (
        "Everything on the site is managed from here. The left navigation lists the groups and "
        "entries of the original control panel: ported features work directly, entries that are not "
        "ported open an explanation page."
    ),
    "版块下仍有主题时不允许删除；关闭的版块前台不能再发新主题。": (
        "A forum that still holds threads cannot be deleted; a closed forum accepts no new threads "
        "on the board."
    ),
    "勾选主题后可批量移动到另一个版块，或连同其全部回复一起删除。": (
        "Select threads to mass move them to another forum, or delete them together with all their "
        "replies."
    ),
    "目前没有举报记录。会员在主题页点「向版主举报本帖」后，记录会出现在这里。": (
        "No reports yet. Once a member clicks \"Report this post to a moderator\" on a thread page, "
        "the report shows up here."
    ),
    "这个分类下还没有版块。": "No forums in this category yet.",
    "没有匹配的会员。": "No matching members.",
    "确定删除版块": "Delete forum",

    # —— 补漏：description 里被标签/变量切开的片段 ——
    "「Path to image」填相对论坛根目录的路径（例如": (
        "\"Path to image\" is a path relative to the forum root (for example"
    ),
    "中，被「取消」的消息标题前会加上这个词（可使用 HTML）。": (
        ", this word is added before the title of a cancelled message (HTML allowed)."
    ),
    "，体积上限按 Options 里的「自定义头像最大体积」。": (
        "; the size limit follows \"Maximum Custom Avatar Size\" in Options."
    ),
    "这是论坛的总开关；各用户组的权限可在用户权限区域单独设置。": (
        "This is the master switch of the board; per-usergroup permissions are set separately in "
        "the User Permissions area."
    ),
    "有时你可能需要在维护、升级等期间关闭论坛。关闭后访客会看到「论坛暂时不可用」的提示。": (
        "You may need to close the board during maintenance or upgrades. Visitors then see the "
        "\"board temporarily unavailable\" notice."
    ),
    "首页的新帖指示图标（on.gif / off.gif）是否对访客和无发帖权限的会员显示锁形标记？": (
        "Should the new-post indicator icons (on.gif / off.gif) be shown with a lock mark to guests "
        "and to members without posting permission?"
    ),
    "设为「否」时，如果图片路径包含 ? 或 & 等动态字符，则不显示 [img] 标签，可防止该标签被恶意利用。": (
        "With \"No\", if the image path contains dynamic characters such as ? or &, the [img] tag is "
        "not displayed, which keeps the tag from being abused."
    ),
}
