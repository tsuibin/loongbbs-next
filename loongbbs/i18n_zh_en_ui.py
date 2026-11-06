"""手写补充词条：首页、版块页、主题页、发帖页、用户面板与通用页脚。

键是模板里的中文原文，值取 vBulletin 2.3.x 界面上的英文原文措辞。
这些条目优先于自动导出的 i18n_zh_en_common / ucp / admin。
"""

MAP = {
    # ---- 通用（页脚、顶栏、语言条）----
    "Powered by: LoongBBS Next — Flask + SQLAlchemy 重制版":
        "Powered by: LoongBBS Next — a Flask + SQLAlchemy rebuild",
    "界面参照 vBulletin 2.3.11 默认风格": "Interface follows the vBulletin 2.3.11 default style",
    "页面生成耗时 ": "Page generated in ",
    "联系站长": "Contact Us",
    "论坛提示": "vBulletin Message",
    "论坛首页": "Forum Home",
    "会员列表": "Members List",
    "免费注册": "Register",
    "常见问题": "FAQ",
    "搜索": "Search",
    "日历": "Calendar",
    "个人资料、悄悄话与设置": "Profile, private messages and settings",
    "中文": "中文",  # 语言条本身不翻，保留中文

    # ---- 首页 ----
    "欢迎回来，": "Welcome back, ",
    "你尚未登录": "You are not logged in",
    "你有 ": "You have ",
    " 条未读悄悄话": " unread private message(s)",
    "查看今日新帖": "View Today's Posts",
    "会员:": "Members:",
    ", 主题:": ", Threads:",
    ", 帖子:": ", Posts:",
    "欢迎最新会员,": "Welcome to our newest member,",
    "现在时间是 ": "The time now is ",
    "你上次访问:": "You last visited:",
    "版块": "Forum",
    "帖子": "Posts",
    "主题": "Threads",
    "最后发表": "Last Post",
    "版主": "Moderators",
    "（版块已关闭）": "(Forum is closed)",
    "从未": "Never",
    "有新帖": "New Posts",
    "无新帖": "No New Posts",
    "已关闭的版块": "Closed Forums",
    "当前在线用户": "Currently Active Users",
    "其中包含你自己。": "This includes you.",
    "登录后可以在这里看到自己的名字。": "Log in and you will see your name here.",
    "不想用 Cookie？": "Don't want to use cookies?",
    "用用户名和密码登录:": "Please log in using your user name and password:",
    "登录!": "Log in!",
    "退出登录": "Log Out",
    "查看新帖": "View New Posts",
    "标记全部版块为已读": "Mark All Forums Read",
    "论坛版主": "Forum Leaders",
    "前往最后一帖": "Go to last post",
    "注册": "Register",
    "登录": "Log in",
    "密码": "Password",
    "用户名": "User Name",
    "邮箱": "Email",
    "发送": "Send",
    "提交": "Submit",
    "返回": "Back",
    "主题标题": "Thread Title",
    "回复": "Replies",
    "查看": "Views",
    "评分": "Rating",
    "请注意": "Please note",
    "原因": "Reason",
    "时间": "Time",
    "作者": "Author",
    "操作": "Actions",
    "状态": "Status",
    "说明": "Description",
    "删除": "Delete",
    "编辑": "Edit",
    "保存": "Save",
    "取消": "Cancel",
    "确定": "OK",
    "关闭": "Close",

    # ---- 版块页 ----
    "(正在浏览此版块的会员: ": "(Users browsing this forum: ",
    "（版块已关闭，不能发新主题）": "(This forum is closed, you cannot post new threads)",
    "发表新主题": "Post New Thread",
    "订阅这个版块": "Subscribe to this Forum",
    "标记这个版块为已读": "Mark This Forum Read",
    "主题发起人": "Thread Starter",
    "回复数": "Replies",
    "查看数": "Views",
    "最后发表时间": "Last Post Time",
    "升序": "Ascending",
    "降序": "Descending",
    "最近一天": "Last Day",
    "最近一年": "Last Year",
    "从最开始": "The Beginning",
    "最近 ": "Last ",
    " 天": " Days",
    "论坛跳转:": "Forum Jump:",
    "请选择:": "(Please select)",
    "悄悄话": "Private Messages",
    "用户控制面板": "User Control Panel",
    "搜索论坛": "Search Forums",
    "搜索这个版块:": "Search this Forum:",
    "已关闭的主题": "Closed Thread",
    "版块规则:": "Forum Rules:",
    "你可以发表新主题": "You may post new threads",
    "你不能发表新主题": "You may not post new threads",
    "你可以回复主题": "You may post replies",
    "你可以上传附件": "You may post attachments",
    "你可以编辑自己的帖子": "You may edit your posts",
    "HTML 代码是 ": "HTML code is ",
    "vB 代码是 ": "vB code is ",
    "表情符号是 ": "Smilies are ",
    "[IMG] 代码是 ": "[IMG] code is ",
    "管理员选项": "Admin Options",
    "这个版块还没有主题": "There have been no threads in this forum",
    "发表第一个主题": "post the first thread",
    "回复超过 ": "More than ",

    # ---- 登录 / 注册 / 找回密码 ----
    "请登录": "Please log in",
    "你还没有登录，或者上次的会话已经过期。":
        "You are not logged in or you do not have permission to access this page.",
    "用户名:": "User Name:",
    "密码:": "Password:",
    "记住我": "Remember me",
    "重置": "Reset",
    "忘记密码了？": "Forgot your password?",
    "注册新账号": "Registration",
    "邮箱地址:": "Email Address:",
    "至少 8 位": "At least 8 characters",
    "确认密码:": "Confirm Password:",
    "提交注册": "Submit Registration",
    "找回密码": "Lost Password",
    "请填写你注册时使用的邮箱地址。系统会给你一个重设密码的链接。":
        "Please enter the email address you registered with. "
        "The system will send you a link you can use to reset your password.",
    "（本演示环境没有配置 SMTP 邮件服务，重设链接会直接显示在页面上。正式部署时改为发邮件即可。）":
        "(This demo has no SMTP mail service, so the reset link is shown right on "
        "this page. In a real deployment it would be sent by email.)",
    "发送重设链接": "Send Reset Link",
    "重设密码链接": "Password Reset Link",
    "本演示环境没有配置 SMTP，链接直接显示在这里。打开它即可设置新密码。":
        "This demo has no SMTP configured, so the link is shown here. Open it to set a new password.",
    "设置新密码": "Set New Password",
    "新密码:": "New Password:",
    "确认新密码:": "Confirm New Password:",
    "保存新密码": "Save New Password",
    "重新申请": "Request Again",
    "我的首页": "User CP",
    "编辑个人资料": "Edit Profile",
    "编辑选项": "Edit Options",
    "修改密码": "Edit Password",
    "编辑好友列表": "Edit Buddy List",
    "编辑忽略列表": "Edit Ignore List",
    "私信": "Private Messages",

    # ---- vB 代码说明页 ----
    "vB 代码说明": "vB Codes Explained",
    "vB 代码按钮": "vB Code Buttons",
    "发帖页的 vB 代码一栏里，这些按钮可以帮你插入标签：":
        "These buttons in the vB Code box on the new post page insert the tags for you:",
    "按钮": "Button",
    "插入的代码": "Code Inserted",
    "作用": "Function",
    "粗体": "Bold",
    "斜体": "Italic",
    "下划线": "Underline",
    "字号": "Font Size",
    "字号 1-4": "Size 1-4",
    "字体": "Font",
    "颜色": "Color",
    "插入超链接": "Insert Hyperlink",
    "插入邮箱": "Insert Email",
    "插入图片（需 http:// 开头）": "Insert Image (address must start with http://)",
    "代码块，等宽、保留空格": "Code block, monospaced, spaces preserved",
    "PHP 代码块": "PHP code block",
    "无序列表": "Unordered list",
    "引用": "Quote",
    "关闭最近打开的那个标签": "Close the most recently opened tag",
    "补上对应的结束标签": "Adds the matching closing tag",
    "关闭所有已打开的标签": "Close all open tags",
    "把未闭合的标签全部闭合": "Closes every unclosed tag",
    "什么是 vB 代码？": "What is vB Code?",
    "vB 代码是一组标签，语法比 HTML 简单，用来给帖子加格式，但永远不会破坏页面版式。某个版块能不能用 vB 代码由管理员按版块设置，发帖前请先看版块规则。":
        "vB code is a set of tags with a simpler syntax than HTML. They let you add formatting "
        "to your messages but will never break the layout of the pages you are viewing. "
        "Whether vB Code can be used is set on a forum-by-forum basis by the administrator, "
        "so you should check the forum rules when you post a new message.",
    "超链接": "URL Hyperlinking",
    "只要在正文里写完整网址，链接会自动生成；以 www. 开头时不必加 http:// 。也可以自己加标签：":
        "If you simply type in the full address of the page you are linking to, the hyperlink "
        "is created automatically; when the address begins with www. you do not need to add "
        "the http:// part. You can also add the tags yourself:",
    "要显示说明文字而不是网址本身，用带等号的形式：":
        "To show description text instead of the address itself, use the form with an equals sign:",
    "点击访问 vBulletin 论坛": "Click here to visit the vBulletin forums",
    "效果：": "Produces:",
    "邮箱链接": "Email Links",
    "也可以写成带说明的形式：": "You can also add a true email hyperlink using the following format:",
    "给我写信": "Click here to email me",
    "粗体、下划线、斜体": "Bold, Underlined and Italic Text",
    "颜色、字号与字体": "Using Different Colors, Sizes and Fonts",
    "这些可以叠加使用：": "You can also combine all the various text formatting tags:",
    "哇，这么多格式！": "Wow there's lots of formatting here!",
    "列表": "Bullets and Lists",
    "第一项": "first bulleted item",
    "第二项": "second bulleted item",
    "编号列表用 [list=1]，字母列表用 [list=A]。":
        "For a numbered list use [list=1], and for an alphabetical list use [list=A].",
    "插入图片": "Adding Images",
    "地址必须带 http:// ；还可以把 [img] 套进 [url] 做成点击放大的缩略图。":
        "The http:// part of the image URL is required for the [img] code. You can even create "
        "a thumbnail-type hyperlink by surrounding your [img] code with a [url] code.",
    "别试。": "No. Try not.",
    "要么做，要么不做，没有“试试看”。": "Do or do not, there is no try.",
    "[quote] 里的文字会自动缩进显示。":
        "The [quote] tags will automatically indent the enclosed text.",
    "代码与 PHP 标签": "The Code and PHP Tags",
    "贴程序源码或 ASCII 画时，用 [code]：内容按等宽字体显示、空格原样保留。":
        "If you want to post some programming source code, or perhaps some ASCII art, which "
        "would require a non-proportional font, you can use the [code] tag.",
    "PHP 代码用 [php]，会按 PHP 语法着色显示（本项目按代码块原样呈现）。":
        "A special case is for code written in the PHP language. If you are posting PHP code, "
        "you can enclose the source code in [php] tags (this rebuild renders it as a plain code block).",
    "常见错误": "Incorrect vB Code Usage",
    "—— 标签与内容之间不要留空格。":
        "- don't put spaces between the bracketed code and the text you are applying the code to.",
    "—— 结束标签要带斜杠：[":
        "- the end brackets must include a forward slash ([",
    "表情代码见 ": "For smilie codes, see the ",

    # ---- 表情列表页 ----
    "表情列表": "Smilies",
    "“表情”是一些能表达情绪或感受的小图标。如果你用过邮件或网络聊天，应该对这套东西不陌生。":
        "'Smilies' are small graphical images that can be used to convey an emotion or feeling. "
        "If you have used email or internet chat, you are likely familiar with the smilie concept.",
    "发帖时在正文里写下面对应的代码，发表后会自动变成表情图形。":
        "Certain standard strings are automatically converted into smilies.",
    "当前可用的表情：": "Here's the list of currently accepted smilies:",
    "输入什么": "What to Type",
    "含义": "Meaning",
    "显示成什么": "Graphic That Will Appear",
    "如果某篇帖子里不想让代码变成表情（例如贴程序代码时不想让":
        "If you want to disable smilies in a post that you make, you can select "
        "the 'Disable Smilies' option when posting. This is particularly useful if you are "
        "posting program code and you do not want",
    "可以在发帖的选项里选择不在本帖使用表情。":
        "converted to a smilie face!",

    # ---- 主题页 ----
    "上一个主题": "Previous Thread",
    "下一个主题": "Next Thread",
    "（你的选择）": "(Your Vote)",
    "合计:": "Total:",
    "这个投票已关闭。": "This poll is closed.",
    "你已经投过票了。": "You have already voted on this poll.",
    "投票": "Vote",
    "作者": "Author",
    "发表新主题": "Post New Thread",
    "回复主题": "Post Reply",
    "主题已关闭": "Thread Closed",
    "头像": "Avatar",
    "注册于:": "Registered:",
    "位置:": "Location:",
    "帖子数:": "Posts:",
    " 附带了这个图片:": " has attached this image:",
    "图片:": "Attached Image:",
    "附件": "Attached Files",
    "向版主举报本帖": "Report Post to Moderator",
    "在线": "Online",
    "查看公开资料": "View Public Profile",
    "发送悄悄话": "Send Private Message",
    "查找该用户更多帖子": "Find more posts by this user",
    "加为好友": "Add to Buddy List",
    "编辑/删除帖子": "Edit/Delete Post",
    "引用回复": "Reply With Quote",
    "显示可打印版本": "Show Printable Version",
    "用邮件推荐这个页面": "Email this page to a friend",
    "订阅这个主题": "Subscribe to this Thread",
    "取消订阅这个主题": "Unsubscribe from this Thread",
    "管理选项:": "Administrative Options:",
    "-- 主题选项 --": "-- Thread Options --",
    "重新开放主题": "Open Thread",
    "关闭主题": "Close Thread",
    "取消置顶": "Unstick Thread",
    "置顶主题": "Stick Thread",
    "编辑主题": "Edit Thread",
    "删除主题/帖子": "Delete Thread / Post",
    "移动/复制主题": "Move / Copy Thread",
    "合并主题": "Merge Threads",
    "拆分主题": "Split Thread",
    "评价本主题:": "Rate Thread:",
    "你已经给这个主题打过分了。": "You have already rated this thread.",
    "选择评分…": "Choose a rating…",
    "5 .. 最好": "5 .. Best",
    "3 .. 一般": "3 .. Average",
    "1 .. 最差": "1 .. Worst",

    # ---- 发帖 / 编辑页 ----
    "帖子预览:": "Preview:",
    "主题:": "Subject:",
    "帖子标题:": "Subject:",
    "消息图标:": "Message Icon:",
    "不使用图标": "No Icon",
    "vB 代码": "vB Code",
    "帮助": "Help",
    "普通模式": "Normal Mode",
    "增强模式": "Enhanced Mode",
    "小": "Small",
    "大": "Large",
    "特大": "Largest",
    "天蓝": "SkyBlue",
    "宝蓝": "RoyalBlue",
    "蓝": "Blue",
    "深蓝": "DarkBlue",
    "橙": "Orange",
    "橙红": "OrangeRed",
    "绯红": "Crimson",
    "红": "Red",
    "砖红": "Firebrick",
    "深红": "DarkRed",
    "绿": "Green",
    "亮绿": "LimeGreen",
    "海绿": "SeaGreen",
    "深粉": "DeepPink",
    "番茄": "Tomato",
    "珊瑚": "Coral",
    "紫": "Purple",
    "靛": "Indigo",
    "木色": "Sienna",
    "沙棕": "SandyBrown",
    "赭": "SaddleBrown",
    "巧克力": "Chocolate",
    "青": "Teal",
    "银": "Silver",
    "插入链接": "Insert Link",
    "代码块": "Code Block",
    "列表": "List",
    "用这些按钮插入 vB 代码": "Click these buttons to insert vB code",
    "关闭当前标签": "Close Current Tag",
    "关闭全部标签": "Close All Tags",
    "消息:": "Message:",
    "请先阅读下面的版块规则，": "Please read the forum rules below to see",
    "了解你可以在帖子里使用": "which codes you may use",
    "哪些代码。": "in your messages.",
    "表情": "Smilies",
    "查看全部表情": "Show all Smilies",
    "[检查消息长度]": "[Check Message Length]",
    "选项:": "Options:",
    "自动解析链接:": "Automatically parse links:",
    "自动在网址前后加上 [url] 与 [/url]。":
        "Automatically wrap URLs with [url] and [/url].",
    "邮件通知:": "Email Notification:",
    "有人回复时发邮件通知你，仅注册用户可用。":
        "Send you an email notification when someone replies; registered users only.",
    "显示签名:": "Show Signature:",
    "本贴禁用表情": "Disable Smilies in This Post",
    "附件:": "Attachments:",
    "每帖最多 5 个文件，图片会直接显示在帖子里。":
        "Up to 5 files per post; images are shown inline in the thread.",
    "发起投票:": "Post a Poll:",
    "是！随本帖发起一个投票": "Yes! Post a poll with this thread",
    "问题:": "Question:",
    "保存修改": "Save Changes",
    "提交回复": "Submit Reply",
    "提交新主题": "Submit New Thread",
    "预览帖子": "Preview Post",
    "已上传的附件": "Uploaded Attachments",
    "请遵守社区规范，发帖前先搜索，不要重复开贴。":
        "Please follow the community rules: search before posting and do not start duplicate threads.",

    # ---- 搜索页 ----
    "关键词:": "Keyword:",
    "搜索!": "Search!",
    "范围:": "Forum:",
    "（只在这个版块内搜索）": "(Search this forum only)",
    "全部版块": "All Forums",
    "搜索位置:": "Search in:",
    "标题和正文": "Titles and Posts",
    "仅标题": "Titles Only",
    "仅正文": "Posts Only",
    "作者:": "User Name:",
    "（留空 = 不限作者；填用户名 = 只看此人的主题/帖子）":
        "(leave blank for any author; enter a user name to see only that user's threads and posts)",
    "日期起止:": "Date Range:",
    "（可只填一端）": "(either bound may be left empty)",
    "排序:": "Sort:",
    "主题发表时间": "Thread Start Time",
    "命中位置": "Where Matched",

    # ---- 会员列表 ----
    "高级搜索": "Advanced Search",
    "按用户名排列": "Sorted by User Name",
    "按注册日期排列": "Sorted by Join Date",
    "其他": "Other",
    "主页": "Homepage",
    "查找帖子": "Find Posts",
    "注册日期": "Join Date",
    "查找": "Search",
    "没有符合条件的会员。": "No members matched your search criteria.",

    # ---- 在线用户 ----
    "当前没有会员在线。": "No members are currently online.",
    "名字为 ": "Names in ",
    " 的是版主，名字为 ": " are moderators; names in ",
    " 的是管理员。": " are administrators.",
    "粗斜体": "bold italic",
    "欢迎来到 ": "Welcome to ",

    # ---- 表情名（smilie 表里的中文标题）----
    "微笑": "Smile",
    "大笑": "Big Grin",
    "皱眉": "Frown",
    "尴尬": "Red Face",
    "吐舌": "Tongue",
    "眨眼": "Wink",
    "酷": "Cool",
    "翻白眼": "Roll Eyes",
    "生气": "Mad",
    "困惑": "Confused",
    "惊讶": "EEK!",

    # ---- vB 代码说明页里的示例串 ----
    "[B]文本[/B]": "[B]text[/B]",
    "[I]文本[/I]": "[I]text[/I]",
    "[U]文本[/U]": "[U]text[/U]",
    "[SIZE=3]文本[/SIZE]": "[SIZE=3]text[/SIZE]",
    "[FONT=arial]文本[/FONT]": "[FONT=arial]text[/FONT]",
    "[COLOR=red]文本[/COLOR]": "[COLOR=red]text[/COLOR]",
    "[URL]网址[/URL] 或 [URL=网址]说明[/URL]":
        "[URL]address[/URL] or [URL=address]description[/URL]",
    "[EMAIL]邮箱[/EMAIL]": "[EMAIL]email[/EMAIL]",
    "[IMG]图片地址[/IMG]": "[IMG]image address[/IMG]",
    "[CODE]代码[/CODE]": "[CODE]code[/CODE]",
    "[PHP]代码[/PHP]": "[PHP]code[/PHP]",
    "[LIST][*]项目[/LIST]": "[LIST][*]item[/LIST]",
    "[QUOTE]引文[/QUOTE]": "[QUOTE]quote[/QUOTE]",
    "x（关闭当前标签）": "x (close current tag)",
    "x（关闭全部标签）": "x (close all tags)",
    "http://www.example.com/图片地址.gif": "http://www.example.com/image.gif",
    "见 ": "see ",
    "这里": "here",
    "文本": "text",
    "只要在正文里写完整网址，链接会自动生成；以 ":
        "If you simply type in the full address of the page you are linking to, the hyperlink "
        "is created automatically; if the address begins with ",
    " 开头时不必加 ": " you do not need to add the ",
    "。也可以自己加标签：": ". You can also add the tags yourself:",
    "地址必须带 ": "The ",
    "；还可以把 [img] 套进 [url] 做成点击放大的缩略图。":
        " part of the image URL is required for the [img] code. You can even create a "
        "thumbnail-type hyperlink by surrounding your [img] code with a [url] code.",
    "请先登录。": "Please log in.",
    "页面不存在。": "Page not found.",
    "标题": "Title",
    "正文": "Post Body",

    # ---- 会员资料页（getinfo）----
    "查看会员资料": "View Member Profile",
    "注册日期:": "Join Date:",
    "状态:": "Status:",
    "帖子总数:": "Total Posts:",
    "主页:": "Homepage:",
    "ICQ 号码:": "ICQ Number:",
    "AOL 即时通讯账号:": "AOL Instant Messenger Handle:",
    "Yahoo 即时通讯账号:": "Yahoo! Messenger Handle:",
    "生日": "Birthday",
    "个人签名": "Signature",
    "来自": "From",
    "兴趣": "Interests",
    "职业": "Occupation",
    "会员管理": "Member Options",

    # ---- UCP 公共部分 ----
    "版块跳转：": "Forum Jump:",
    "请选择一项：": "(Please select)",
    "搜索版块": "Search Forums",
    "好友列表": "Buddy List",
    "忽略列表": "Ignore List",
    "离线": "Offline",
    "向好友发送私信": "Send Private Message to Buddy",
    "新私信": "New Private Message",
    "查看所有私信": "View all Private Messages",
    "自上次访问以来没有新私信。": "There are no new private messages since your last visit.",
    "订阅的版块": "Subscribed Forums",
    "订阅的主题": "Subscribed Threads",
    "查看所有订阅主题": "View all subscribed threads",
    "你目前没有订阅任何主题。": "You are not currently subscribed to any threads.",
    "你目前没有订阅任何主题。在主题页点「订阅这个主题」即可加入这里。":
        "You are not currently subscribed to any threads. Click 'Subscribe to this Thread' "
        "on a thread page to add one here.",
    "显示主题范围": "Show Threads From",
    "最近 1 天": "Last Day",
    "最近 2 天": "Last 2 Days",
    "最近 5 天": "Last 5 Days",
    "最近 10 天": "Last 10 Days",
    "最近 20 天": "Last 20 Days",
    "最近 30 天": "Last 30 Days",
    "最近 45 天": "Last 45 Days",
    "最近 60 天": "Last 60 Days",
    "最近 75 天": "Last 75 Days",
    "最近 100 天": "Last 100 Days",
    "全部时间": "All Time",

    # ---- 编辑选项（modifyoptions.html）----
    "编辑选项": "Edit Options",
    "登录、Cookie 与隐私": "Login, Cookies & Privacy",
    "隐身模式？": "Invisible Mode?",
    "选择 yes 后你浏览论坛时不会出现在「当前在线用户」列表里。":
        "Selecting yes allows you to surf the forums without appearing in the 'Logged In Users' list.",
    "下次访问自动登录？（使用 Cookie）":
        "Automatically login when you return to the site? (uses cookies)",
    "使用 Cookie 浏览论坛？": "Browse board with cookies?",
    "选择 yes 会用 Cookie 保存本会话的身份；选择 no 则把身份信息放在链接里。（选 no 后，与你在同一代理后面的人共享链接时可能出问题）":
        "Clicking yes will use cookies to keep your id for this session. Clicking no will send it "
        "through the links. (Selecting no may cause problems when sharing links with people "
        "behind the same proxy as you)",
    "私信与通知": "Messaging & Notification",
    "允许论坛管理员和版主向你发送邮件通知？":
        "Allow Bulletin Board Administrators and Moderators To Send You Email Notices?",
    "隐藏邮箱地址？": "Hide Email Address?",
    "选择 yes 会在你的公开资料里隐藏邮箱地址，其他用户无法查看。":
        "Clicking yes hides your email address in your public profile, so that it is not "
        "accessible by other users.",
    "默认使用“邮件通知”？": "Use 'Email Notification' by default?",
    "开启后，只要你参与过的主题有人回复，就会给你发邮件。":
        "Using this option emails you whenever someone replies to a thread that you have "
        "participated in.",
    "启用私信？": "Enable Private Messaging?",
    "允许他人向你发送私信": "Allows people to send Private Messages to you",
    "收到私信时邮件通知？": "Send you an email when you receive a Private Message?",
    "收到私信时弹窗提示？": "Pop up a box when you receive a Private Message?",
    "收到私信时弹出一个小提示框，询问你是否要查看这条私信。":
        "This will pop up a small warning box when you receive a Private Message asking "
        "whether you want to view the message.",
    "主题浏览选项": "Thread View Options",
    "在帖子中显示用户签名？": "Show user's signatures in their posts?",
    "在帖子中显示用户头像？": "Show user's avatar in their posts?",
    "在帖子中显示图片附件和 [img] 代码？": "Show image attachments and [img] code in Posts?",
    "选择 no 时将改为显示一个超链接。": "Selecting no will show a hyperlink instead.",
    "默认主题浏览范围：": "Default Thread View:",
    "每页帖子数：": "Default Posts per Thread:",
    "一个主题每页显示的帖子数。": "Number of posts that are shown on one page of a thread.",
    "使用版块默认": "Use forum default",
    "显示最近 1 天的主题": "Show threads from last day",
    "显示最近 2 天的主题": "Show threads from last 2 days",
    "显示最近 5 天的主题": "Show threads from last 5 days",
    "显示最近 10 天的主题": "Show threads from last 10 days",
    "显示最近 20 天的主题": "Show threads from last 20 days",
    "显示最近 30 天的主题": "Show threads from last 30 days",
    "显示最近 45 天的主题": "Show threads from last 45 days",
    "显示最近 60 天的主题": "Show threads from last 60 days",
    "显示最近 75 天的主题": "Show threads from last 75 days",
    "显示最近 100 天的主题": "Show threads from last 100 days",
    "显示最近一年的主题": "Show threads from the last year",
    "显示全部主题": "Show all threads",
    "显示在你的帖子中用户名下方的头衔。":
        "The title shown below your user name in your posts.",
    "日期与时间选项": "Date & Time Options",
    "星期日": "Sunday",
    "星期一": "Monday",
    "星期二": "Tuesday",
    "星期三": "Wednesday",
    "星期四": "Thursday",
    "星期五": "Friday",
    "星期六": "Saturday",
    # 时区下拉（原文见 templates/modifyoptions.html）
    "(GMT -12:00) 埃尼威托克、夸贾林": "(GMT -12:00 hours) Eniwetok, Kwajalein",
    "(GMT -11:00) 中途岛、萨摩亚": "(GMT -11:00 hours) Midway Island, Samoa",
    "(GMT -10:00) 夏威夷": "(GMT -10:00 hours) Hawaii",
    "(GMT -9:00) 阿拉斯加": "(GMT -9:00 hours) Alaska",
    "(GMT -8:00) 太平洋时间（美国/加拿大）": "(GMT -8:00 hours) Pacific Time (US & Canada)",
    "(GMT -7:00) 山地时间（美国/加拿大）": "(GMT -7:00 hours) Mountain Time (US & Canada)",
    "(GMT -6:00) 中部时间（美国/加拿大），墨西哥城":
        "(GMT -6:00 hours) Central Time (US & Canada), Mexico City",
    "(GMT -5:00) 东部时间（美国/加拿大），波哥大、利马、基多":
        "(GMT -5:00 hours) Eastern Time (US & Canada), Bogota, Lima, Quito",
    "(GMT -4:00) 大西洋时间（加拿大），加拉加斯、拉巴斯":
        "(GMT -4:00 hours) Atlantic Time (Canada), Caracas, La Paz",
    "(GMT -3:30) 纽芬兰": "(GMT -3:30 hours) Newfoundland",
    "(GMT -3:00) 巴西、布宜诺斯艾利斯、乔治敦":
        "(GMT -3:00 hours) Brazil, Buenos Aires, Georgetown",
    "(GMT -2:00) 中大西洋": "(GMT -2:00 hours) Mid-Atlantic",
    "(GMT -1:00) 亚速尔群岛、佛得角群岛": "(GMT -1:00 hours) Azores, Cape Verde Islands",
    "(GMT) 西欧时间，伦敦、里斯本、卡萨布兰卡、蒙罗维亚":
        "(GMT) Western Europe Time, London, Lisbon, Casablanca, Monrovia",
    "(GMT +1:00) 中欧时间，布鲁塞尔、哥本哈根、马德里、巴黎":
        "(GMT +1:00 hours) CET(Central Europe Time), Brussels, Copenhagen, Madrid, Paris",
    "(GMT +2:00) 东欧时间，加里宁格勒、南非":
        "(GMT +2:00 hours) EET(Eastern Europe Time), Kaliningrad, South Africa",
    "(GMT +3:00) 巴格达、科威特、利雅得、莫斯科、圣彼得堡、伏尔加格勒、内罗毕":
        "(GMT +3:00 hours) Baghdad, Kuwait, Riyadh, Moscow, St. Petersburg, Volgograd, Nairobi",
    "(GMT +3:30) 德黑兰": "(GMT +3:30 hours) Tehran",
    "(GMT +4:00) 阿布扎比、马斯喀特、巴库、第比利斯":
        "(GMT +4:00 hours) Abu Dhabi, Muscat, Baku, Tbilisi",
    "(GMT +4:30) 喀布尔": "(GMT +4:30 hours) Kabul",
    "(GMT +5:00) 叶卡捷琳堡、伊斯兰堡、卡拉奇、塔什干":
        "(GMT +5:00 hours) Ekaterinburg, Islamabad, Karachi, Tashkent",
    "(GMT +5:30) 孟买、加尔各答、马德拉斯、新德里":
        "(GMT +5:30 hours) Bombay, Calcutta, Madras, New Delhi",
    "(GMT +6:00) 阿拉木图、达卡、科伦坡": "(GMT +6:00 hours) Almaty, Dhaka, Colombo",
    "(GMT +7:00) 曼谷、河内、雅加达": "(GMT +7:00 hours) Bangkok, Hanoi, Jakarta",
    "(GMT +8:00) 北京、珀斯、新加坡、香港、重庆、乌鲁木齐、台北":
        "(GMT +8:00 hours) Beijing, Perth, Singapore, Hong Kong, Chongqing, Urumqi, Taipei",
    "(GMT +9:00) 东京、首尔、大阪、札幌、雅库茨克":
        "(GMT +9:00 hours) Tokyo, Seoul, Osaka, Sapporo, Yakutsk",
    "(GMT +9:30) 阿德莱德、达尔文": "(GMT +9:30 hours) Adelaide, Darwin",
    "(GMT +10:00) 东澳标准时间、关岛、巴布亚新几内亚、符拉迪沃斯托克":
        "(GMT +10:00 hours) EAST(East Australian Standard), Guam, Papua New Guinea, Vladivostok",
    "(GMT +11:00) 马加丹、所罗门群岛、新喀里多尼亚":
        "(GMT +11:00 hours) Magadan, Solomon Islands, New Caledonia",
    "(GMT +12:00) 奥克兰、惠灵顿、斐济、堪察加、马绍尔群岛":
        "(GMT +12:00 hours) Auckland, Wellington, Fiji, Kamchatka, Marshall Island",
    "每周起始日": "Start of the week",
    "请选择你所在文化中一周开始的那一天。这样日历显示才符合你的习惯。":
        "Please choose the day of the week on which weeks start in your culture. "
        "This is so your calendar appears correct to you.",
    "时区偏移：": "Time offset:",
    "其他选项": "Other Options",
    "在发帖界面显示 vBCode 快捷链接？": "Use vBCode quick links on your message input screens?",
    "开启后你可以快速调整帖子的颜色、字体和字号，也可以点击表情把它们插入帖子。如果这个功能给你带来麻烦，可以关掉它。":
        "Enabling this option allows you to quickly manipulate different aspects of your posts "
        "including color, font, and size. In addition you can click on smilies to have them "
        "inserted into your posts. You may disable this option if it causes problems for you.",
    "风格：": "Style:",
    "你可以选择浏览论坛时使用的风格，它可能会覆盖默认设置。":
        "You can choose the style you want to browse the forums with; it may override the default.",
    "使用论坛默认": "Use forum default",
    "默认风格": "Default Style",
    "更多信息...": "More info...",
    "你当前的头像": "Your current avatar",
    "更换头像": "Change Avatar",
    "提交修改": "Submit Modifications",
    "重填": "Reset Fields",

    # ---- 编辑个人资料（modifyprofile.html）----
    "更新资料": "Update Profile",
    "注册信息: 必填项": "Registration Information: Required Fields",
    "所有项目都必须填写。": "All fields in this section must be filled in.",
    "确认邮箱地址:": "Confirm Email Address:",
    "可选信息": "Optional Information",
    "这些信息会被其他会员看到。": "This information will be visible to other members.",
    "个人签名:": "Signature:",
    "可选的签名，会显示在你每个帖子的底部。":
        "An optional signature that is shown at the bottom of every post you make.",
    "自定义头衔:": "Custom User Title:",
    "若想恢复用户组默认头衔，请勾选「恢复默认」。不允许 HTML。":
        "To reset to your user group's default title, tick \"Reset to default\". HTML is not allowed.",
    "当前头衔:": "Current Title:",
    "新头衔:": "New Title:",
    "恢复默认:": "Reset to default:",
    "生日:": "Birthday:",
    "格式 YYYY-MM-DD，可留空": "Format YYYY-MM-DD, may be left blank",
    "附加信息": "Additional Information",
    "来自:": "From:",
    "兴趣:": "Interests:",
    "职业:": "Occupation:",

    # ---- 好友/忽略列表（usercp_buddy / lists）----
    "要从列表中删除某个用户，把他的名字删掉即可。要添加用户，就在其中一个空框里填入用户名。":
        "To remove a user from your list, simply delete their name from the list. "
        "To add a user, enter their name in one of the empty boxes.",
    "要查看完整的会员列表，请点击 ": "To view the complete Members List, click ",
    "更新列表": "Update List",

    # ---- 订阅列表 ----
    "取消订阅": "Unsubscribe",
    "· 作者：": "· Author: ",
    "· 最后发表 ": "· Last Post ",
    "· 订阅于 ": "· Subscribed on ",

    # ---- 悄悄话 ----
    "写悄悄话": "Send New Private Message",
    "写新悄悄话": "Send New Private Message",
    "收件箱": "Inbox",
    "已发送": "Sent Items",
    "收件人:": "To:",
    "全部删除": "Delete All",

    # ---- 发帖页补充 ----
    "支持 [b] [i] [u] [size] [font] [color] [url] [email] [img] [code] [php] [quote] [list]":
        "Uses [b] [i] [u] [size] [font] [color] [url] [email] [img] [code] [php] [quote] [list]",
    "显示签名:": "Show Signature:",
    "附带你的个人签名，仅注册用户可用。":
        "Enclose your signature; registered users only.",

    # ---- 可打印版本 ----
    "返回主题": "Return to Thread",
}
