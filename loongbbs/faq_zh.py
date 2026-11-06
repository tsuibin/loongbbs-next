import re

"""FAQ 页的中文化词条（英文原文 → 中文）。

参考站 vB 2.3.11 在中文语言包下就是把这些 phrase 替换进 faq*.html 模板输出，
所以中文模式下的 FAQ 页面本身是中英混排：小节标题、问题标题、列表项与部分短句为中文，
语言包没收录的长段落仍是英文。本表逐条来自参考站 admin/lang_zh.php，
由 _vb2ref/tmp_faq_lang.py 导出，保持与参考站相同的替换顺序（长串优先）。
"""

FAQ_ZH: tuple[tuple[str, str], ...] = (
    ("Set up a 'buddy-list' to quickly see which of your friends are currently online", "建立“好友列表”可快速查看哪些好友当前在线"),
    ("Are there any special codes/tags I can use to format my posts and messages?", "有可以用来格式化帖子的特殊代码/标签吗？"),
    ("This page is divided into two sections: unread messages and read messages.", "本页分为两部分：未读消息和已读消息。"),
    ("When you post a new thread, you may have the option to also create a poll.", "发表新主题时，你也可以选择同时创建投票。"),
    ("You may send a private message to a member of this board by clicking the '", "你可以点击“"),
    ("button (alt+c). You may also nest tags in enhanced mode, and then use the", "按钮（alt+c）。在增强模式下还可以嵌套标签，然后使用"),
    ("Receive email notification of replies to posts and threads you specify", "对你指定的帖子/主题的回复发送邮件通知"),
    ("You may create additional folders for your messages by clicking the '", "你可以点击“"),
    ("Email notification is also referred to as 'Thread Subscription'.", "邮件通知也称为“主题订阅”。"),
    ("system, registered members may send each other private messages.", "系统中，注册会员之间可以互相发送私信。"),
    (", which allow you to use small icons to convey emotion, and the", "（可用小图标表达情绪），以及"),
    ("' link on any page that requires you to fill in your password.", "”链接（用于任何需要输入密码的页面）。"),
    ("Here are the instructions for Internet Explorer 5 on Windows:", "以下是 Windows 上 Internet Explorer 5 的操作说明："),
    ("If you enter your birthday, your name will also appear on the", "如果填写生日，你的名字还会显示在"),
    ("and entering the text you want in the Custom User Text field.", "并在自定义头衔字段中输入想要的文字。"),
    ("For a list of the smilies currently used by this board,", "查看本论坛当前使用的表情列表，请"),
    ("Why have some of the words in my post been blanked-out?", "为什么我帖子里的某些词被屏蔽了？"),
    ("code, which allows you to add pictures to your message.", "代码，可在消息中添加图片。"),
    ("link (if available) to access the full list of smilies.", "链接（如果有）查看完整表情列表。"),
    ("system. For more information about private messaging,", "系统。关于私信的更多信息，"),
    ("You may also find that the administrator has enabled", "你也可能发现管理员已启用"),
    ("If you forget your password, you can click on the '", "如果忘记密码，可以点击“"),
    ("How can I change the information in my profile? [", "如何修改我的个人资料？["),
    ("Can I send email to other members of this board?", "我可以给论坛其他会员发邮件吗？"),
    ("How can I change the information in my profile?", "如何修改我的个人资料？"),
    (": public events, private events and birthdays.", "：公开事件、私人事件和生日。"),
    ("How do I add a custom status to my profile? [", "如何为个人资料添加自定义状态？["),
    ("How do I add a custom status to my profile?", "如何为个人资料添加自定义状态？"),
    ("How do I get a picture under my username? [", "如何让用户名下方显示图片？["),
    ("You may clear all your cookies by clicking", "你可以点击以下链接清除所有 Cookie"),
    ("How do I get a picture under my username?", "如何让用户名下方显示图片？"),
    ("represents two eyes and a smiling mouth.", "代表两只眼睛和微笑的嘴。"),
    ("To edit or delete your posts, click the", "要编辑或删除帖子，请点击"),
    ("button on any post made by that member.", "该会员任意帖子上的按钮。"),
    ("Send private messages to other members", "向其他会员发送私信"),
    ("There are three types of events on the", "日历上有三类事件："),
    ("What are the buddy and ignore lists? [", "什么是好友列表和忽略列表？["),
    ("Close all Internet Explorer windows.", "关闭所有 Internet Explorer 窗口。"),
    ("If the administrator has enabled the", "如果管理员启用了"),
    ("What are the buddy and ignore lists?", "什么是好友列表和忽略列表？"),
    ("vBulletin Frequently Asked Questions", "vBulletin 常见问题"),
    ("Click the &quot;Start&quot; button.", "点击“开始”按钮。"),
    ("For more information about avatars,", "关于头像的更多信息，"),
    ("For more information about vB code,", "关于 vB 代码的更多信息，"),
    ("Code Buttons and Clickable Smilies", "代码按钮与可点击表情"),
    ("Enter events in the board calendar", "在论坛日历中添加事件"),
    ("How do I create and vote in polls?", "如何创建投票并投票？"),
    ("I lost my password, what can I do?", "忘记密码怎么办？"),
    ("Reply to other peoples' threads", "回复他人的主题"),
    ("Sky-blue pink with yellow spots", "带黄色斑点的天蓝粉色"),
    ("There are two modes available:", "有两种模式可用："),
    ("How do I use the Member List?", "如何使用会员列表？"),
    ("These small images are called", "这些小图片称为"),
    ("You can set your signature by", "你可以通过以下方式设置签名："),
    ("Does this board use cookies?", "本论坛使用 Cookie 吗？"),
    ("Reading and Posting Messages", "阅读与发表消息"),
    ("Voting in and viewing a poll", "参与和查看投票"),
    ("What is the signature for? [", "签名有什么用途？["),
    ("What is your favorite color?", "你最喜欢什么颜色？"),
    ("What is email notification?", "什么是邮件通知？"),
    ("button in a member's posts.", "帖子中的按钮。"),
    ("Frequently Asked Questions", "常见问题解答"),
    ("How do I clear my cookies?", "如何清除 Cookie？"),
    ("How do I use the calendar?", "如何使用日历？"),
    ("The member list also has a", "会员列表还提供"),
    ("What is Private Messaging?", "什么是私信？"),
    ("What is the signature for?", "签名有什么用途？"),
    ("An example poll might be:", "投票示例："),
    ("Can I search the board? [", "我可以搜索论坛吗？["),
    ("Help! I lost my password!", "我忘记密码了！"),
    ("when it is your birthday.", "在你生日时。"),
    ("Can I edit my own posts?", "我可以编辑自己的帖子吗？"),
    ("Private Message Tracking", "私信跟踪"),
    ("Sending Private Messages", "发送私信"),
    ("Why should I register? [", "为什么要注册？["),
    ("Can I search the board?", "我可以搜索论坛吗？"),
    ("Forgotten Your Password", "忘记密码"),
    ("How do I rate a thread?", "如何评价主题？"),
    ("Private Message Folders", "私信文件夹"),
    ("What are announcements?", "什么是公告？"),
    ("What are message icons?", "什么是帖子图标？"),
    ("Send A Private Message", "发送私信"),
    ("Why should I register?", "为什么要注册？"),
    ("What Are Attachments?", "什么是附件？"),
    ("What Are Moderators?", "什么是版主？"),
    ("editing your profile", "编辑个人资料"),
    ("in a member's posts.", "在会员的帖子中。"),
    ("Creating a new poll", "创建新投票"),
    ("General Board Usage", "论坛基本使用"),
    ("What are referrals?", "什么是推荐？"),
    ("Close Current Tag", "关闭当前标签"),
    ("Edit your profile", "编辑个人资料"),
    ("Private Messaging", "私信"),
    ("What are smilies?", "什么是表情？"),
    ("click to register", "点击注册"),
    ("edit your options", "编辑选项"),
    ("edit your profile", "编辑个人资料"),
    ("private messaging", "私信"),
    ("Message Tracking", "消息跟踪"),
    ("Post new threads", "发表新主题"),
    ("User Maintenance", "用户维护"),
    ("edit ignore list", "编辑忽略列表"),
    ("Edit your posts", "编辑你的帖子"),
    ("edit buddy list", "编辑好友列表"),
    ("main forum page", "论坛主页"),
    ("search function", "搜索功能"),
    ("unread messages", "未读消息"),
    (", or click the", "，或点击"),
    ("Close All Tags", "关闭所有标签"),
    ("Private events", "私人事件"),
    ("use the search", "使用搜索"),
    ("Public events", "公开事件"),
    ("read messages", "已读消息"),
    ("Edit Folders", "编辑文件夹"),
    ("another user", "其他用户"),
    ("member list", "会员列表"),
    ("My vB Home", "我的首页"),
    ("When using", "使用"),
    ("click here", "点击这里"),
    ("Birthdays", "生日"),
    ("this page", "此页面"),
    ("Get More", "获取更多"),
    ("' link.", "”链接。"),
    ("Avatars", "头像"),
    ("Yellow", "黄色"),
    ("Green", "绿色"),
    ("Blue", "蓝色"),
    ("Red", "红色"),
)


_MAP: dict[str, str] = dict(FAQ_ZH)

# 注释 / script / style 先挖掉，避免把英文串替进代码
_PROTECT_RE = re.compile(r"<!--.*?-->|<script.*?</script>|<style.*?</style>", re.S | re.I)
_TAG_RE = re.compile(r"<[^>]+>")


def translate_faq_html(html: str) -> str:
    """按「整段文本节点」把 FAQ 模板里的英文换成中文。

    参考站的做法是按纯文本节点整段命中的：`<a>Page 1: User Maintenance</a>` 这种
    整串不在语言包里就保留英文；而单独成节点的 `User Maintenance`、
    `Why should I register? [` 才会被替换。所以这里也只做整节点匹配（模板换行先归一成
    空格），不做子串替换，否则会出现「Entering 你的邮箱地址将 not leave you...」这类碎片。
    """
    if not isinstance(html, str) or "<" not in html:
        return html

    stash: dict[str, str] = {}

    def _stash(match: re.Match) -> str:
        token = f"\x00{len(stash)}\x00"
        stash[token] = match.group(0)
        return token

    protected = _PROTECT_RE.sub(_stash, html)
    pieces = _TAG_RE.split(protected)
    tags = _TAG_RE.findall(protected)

    rebuilt: list[str] = []
    for index, chunk in enumerate(pieces):
        stripped = chunk.strip()
        normalized = re.sub(r"\s+", " ", stripped) if stripped else ""
        if normalized and normalized in _MAP:
            lead = chunk[: len(chunk) - len(chunk.lstrip())]
            tail = chunk[len(chunk.rstrip()):]
            chunk = lead + _MAP[normalized] + tail
        rebuilt.append(chunk)
        if index < len(tags):
            rebuilt.append(tags[index])

    out = "".join(rebuilt)
    for token, original in stash.items():
        out = out.replace(token, original)
    return out
