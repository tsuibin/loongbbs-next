"""后台设置项与分组的英文原文。

来源：参考站 vBulletin 2.3.11 的 `setting` / `settinggroup` 两张表（原版 DB 里存的就是
英文原文，中文是 admin/lang_zh.php 翻出来的）。英文界面直接用这份原文，
不再依赖中英词典逐句翻译，措辞与原版后台一致。
"""

GROUP_TITLES = {
    1: 'Turn Your vBulletin on and off',
    2: 'General Settings',
    3: 'Contact Details',
    4: 'Posting Code allowances (vB code / HTML / etc)',
    5: 'Forums Home Page Options',
    6: 'User and registration options',
    7: 'Memberlist options',
    8: 'Thread display options',
    9: 'Forum Display Options',
    10: 'Search Options',
    11: 'Email Options',
    12: 'Date / Time options',
    13: 'Censorship Options',
    14: 'Edit Options',
    15: 'IP Logging Options',
    16: 'Floodcheck Options',
    17: 'Banning Options',
    18: 'Language Options',
    19: 'Private Messaging Options',
    20: 'HTTP Headers and output',
    21: 'Version Info',
    22: 'Spell Check',
    23: 'Templates',
    24: 'Load limiting options',
    25: 'Polls',
    26: 'Avatars',
    27: 'Attachments',
    28: 'Custom User Titles',
    29: 'Calendar',
    30: 'Upload Options',
    31: "Who's Online",
}

SETTINGS_EN = {
    'templateversion': {
        "title": 'Template version number',
        "description": "Don't touch!",
    },
    'bbactive': {
        "title": 'Bulletin Board Active',
        "description": 'From time to time, you may want to turn your bulletin board off to the public while you perform maintenance, update versions, etc. When you turn your BB off, visitors will receive a message that states that the bulletin board is temporarily unavailable. <b>Administrators will still be able to see the board</b></p>\n<p>Use this as a master switch for your board. You can set options for individual user groups in the User Permissions area.',
    },
    'bbclosedreason': {
        "title": 'Reason for turning board off',
        "description": 'The text that is presented when the BB is closed.</p>\n<p>Note: you, as an administrator, will be able to see the forums as usual, even when you have turned them off to the public.',
    },
    'bbtitle': {
        "title": 'Board Title',
        "description": 'Title of board. Appears in the title of every page',
    },
    'hometitle': {
        "title": 'Homepage Name',
        "description": 'Name of your homepage. Appears at the bottom of every page.',
    },
    'bburl': {
        "title": 'URL',
        "description": 'URL (with no final "/") of the BB. Do not include "/index.php" on the end! Your URL should look something like this: http://www.example.com/forum',
    },
    'homeurl': {
        "title": 'URL of homepage',
        "description": 'URL of your home page. Appears at the bottom of every page.',
    },
    'copyrighttext': {
        "title": 'Copyright Text',
        "description": 'Copyright text to insert the footer of the page.',
    },
    'privacyurl': {
        "title": 'URL of Privacy Statement',
        "description": 'Enter the URL of your privacy statement, if one exists.',
    },
    'gdversion': {
        "title": 'GD Version',
        "description": 'Version of GD installed on your server. If GD is enabled, you can find the version listed in your phpinfo().',
    },
    'contactuslink': {
        "title": 'Contact Us Link',
        "description": 'Link for contacting the site. Can just be mailto:webmaster@whereever.com or your own form. Appears at the bottom of every page.',
    },
    'webmasteremail': {
        "title": "Webmaster's email",
        "description": 'Email address of the webmaster.',
    },
    'faxnumber': {
        "title": 'Fax Number',
        "description": 'Enter the fax number for your company here. COPPA forms will be faxed to it.\n</p>\n<p>You may wish to check out <a href="http://www.efax.com/" target=_blank>http://www.efax.com/</a>',
    },
    'address': {
        "title": 'Address',
        "description": 'Address of your company. This is required for COPPA forms to be posted to.',
    },
    'companyname': {
        "title": 'Company Name',
        "description": 'The name of your company. Required for COPPA.',
    },
    'allowbbimagecode': {
        "title": 'Allow vB IMG code in signatures?',
        "description": '',
    },
    'allowbbcode': {
        "title": 'Allow vB code in signatures?',
        "description": '',
    },
    'allowsmilies': {
        "title": 'Allow smilies in signatures?',
        "description": '',
    },
    'allowhtml': {
        "title": 'Allow HTML in signatures?',
        "description": '',
    },
    'maximages': {
        "title": 'Maximum images per post/signature',
        "description": 'Maximum number of images to allow in posts / signatures. Set this to 0 to have no effect.',
    },
    'smcolumns': {
        "title": 'Clickable Smilies per Row',
        "description": 'When a user has enabled the clickable vbcode/smilies how many smilies do you want to show per row?',
    },
    'smtotal': {
        "title": 'Clickable Smilies Total',
        "description": 'When a user has enabled the clickable vbcode/smilies how many smilies do you want to display on the screen before the user is prompted to click for more.',
    },
    'allowdynimg': {
        "title": 'Allow Dynamic URL for [img] tags?',
        "description": "If this is set to 'no', the [img] tag will not be displayed if the path to the image contains dynamic characters such as ? and &. This can prevent malicious use of the tag.",
    },
    'allowvbcodebuttons': {
        "title": 'Allow vBcode Buttons & Clickable Smilies?',
        "description": 'This global switch allows you to completely disable vBcode buttons and clickable smilies.',
    },
    'showforumdescription': {
        "title": 'Show forum descriptions on the homepage.',
        "description": '',
    },
    'showbirthdays': {
        "title": "Show today's birthdays on the homepage?",
        "description": '',
    },
    'displayloggedin': {
        "title": 'Display logged in users on home page',
        "description": 'Display logged in and active members on the home page? This option displays those users that have been active in the last {your cookie timeout} seconds on the home page.',
    },
    'highlightadmin': {
        "title": 'Highlight Admin',
        "description": "Enabling this will show Admin names in Bold and Italics and Moderators' names in Bold on the logged in users and Who's Online.",
    },
    'hideprivateforums': {
        "title": 'Hide private forum',
        "description": "Select 'yes' here to hide private forums from users who are not allowed to access them. Users who do have permission to access them will have to log in before they can see these forums too. This option applies to the forum home page, and the Jump To... box.",
    },
    'showlocks': {
        "title": 'Show Locked forums?',
        "description": 'Do you wish to have the new post indicators shown on the index page (on.gif and off.gif) be shown with locks to guests & other members who have no access to post?',
    },
    'forumhomedepth': {
        "title": 'Depth of Forums',
        "description": 'Depth to show forums on home page. Do not go too large on this value for performance reasons.',
    },
    'displayemails': {
        "title": 'Display email addresses',
        "description": 'Allow public viewing of email addresses.',
    },
    'secureemail': {
        "title": 'Use email form?',
        "description": 'If "display email addresses" is set to yes, then how should then email address be displayed? If this is set to yes, then an online form must be filled in to send a user an email, thus hiding the destination email address. If secureemail is set to no, then the user is just given the email address.',
    },
    'allowsignatures': {
        "title": 'Allow signatures',
        "description": "Allow registered users to have signatures. Don't forget to update these templates: newtopic newreply editpost modifyprofile register",
    },
    'newuseremail': {
        "title": 'Notify about new members',
        "description": 'Email address to receive email when a new user signs up. Leave blank for no email.',
    },
    'requireuniqueemail': {
        "title": 'Require unique email addresses',
        "description": 'The default option is to require unique email addresses for each registered user. This means that no two users can have the same email address. You can disable this requirement by checking the "Unique Email Not Required" box.',
    },
    'illegalusernames': {
        "title": 'Illegal user names',
        "description": 'Enter names in here that you do not want people to register. If any of the names here are included within the username, the user will told that there is an error. Separate names by spaces.',
    },
    'allowregistration': {
        "title": 'Allow new user registrations',
        "description": 'If you would like to temporarily (or permanently) prevent anyone new from registering, you can do so. The REGISTER button will still be seen throughout the BB, but anyone attempting to register will be told that you are not accepting new registrations at this time.',
    },
    'allowmultiregs': {
        "title": 'Allow multiple registrations per user',
        "description": "Normally, vBulletin will stop users signing up for multiple names by checking for a cookie on the user's machine. If one exists, then the user may not sign up for additional names. If you wish to allow your users to sign up for multiple names, then select yes for this option, and they will not be blocked from registering additional usernames.",
    },
    'verifyemail': {
        "title": 'Verify Email address in registration',
        "description": 'The password is emailed to the new member after they submit their registration to confirm their identity and email address. If account is not activated, they will remain in the "users awaiting activation" usergroup.',
    },
    'moderatenewmembers': {
        "title": 'Moderate New Members',
        "description": 'Allows you to validate new members before they are classified as registered members and are allowed to post.',
    },
    'regimagecheck': {
        "title": 'Image Verification',
        "description": 'If enabled, this option will display a random image to new users at registration time. The user will have to copy the contents of the image in order to verify that an automated system is not processing registrations. Requires GD to be enabled on your server.',
    },
    'usecoppa': {
        "title": 'Use COPPA Registration system',
        "description": 'Use the COPPA registration system. This complies with the COPPA laws and requires children under the age of 13 to get parental consent before they can post. For more info about this law, see here:<br>\n<a href="http://www.ftc.gov/opa/1999/9910/childfinal.htm">http://www.ftc.gov/opa/1999/10/childfinal.htm</a>',
    },
    'cookietimeout': {
        "title": 'Timeout for Cookie',
        "description": 'This is the time in seconds that a user must remain inactive before the unread posts are reset to read.',
    },
    'allowchangestyles': {
        "title": 'Allow Users To Change Styles',
        "description": 'This allows users to set their preferred style set on registration or when editing their option. Setting this to "no" disables that option and will force them to use whatever style has been specified.',
    },
    'enableaccess': {
        "title": 'Enable Access Masks?',
        "description": "Access masks are a simple way to manage forum permissions, however they add additional queries on most pages. If you don't use it, it is recommended that you disable it.",
    },
    'usereferrer': {
        "title": 'Referrer',
        "description": 'Enable the referrer system? If yes than a user that visits your forum through a link that contains "referrerid=XXX" will give referral credit to the owner of the referrerid when they register (where XXX is the userid of the referrer).',
    },
    'minuserlength': {
        "title": 'Minimum Username Length',
        "description": 'Enter the minimum length a user can register with.',
    },
    'maxuserlength': {
        "title": 'Maximum Username Length',
        "description": 'Enter the maximum length a user can register with.',
    },
    'ignoremods': {
        "title": 'Allow Ignore Moderators',
        "description": 'Allow users to add Moderators and admins to their ignore list?',
    },
    'enablememberlist': {
        "title": 'Enable members list',
        "description": 'Enable the member list addon? This allows users to view a list of registered users and (optionally) search through it.',
    },
    'usememberlistadvsearch': {
        "title": 'Allow advanced searches',
        "description": 'Allow the use of the advanced search tool for the member list.',
    },
    'memberlistperpage': {
        "title": 'Members per page',
        "description": 'The number of records per page that will be shown by default in the members list.',
    },
    'memberlisttopposters': {
        "title": 'Number of top posters to show',
        "description": "On the 'Display top x posters' , this option allows you to specify a value for x.",
    },
    'memberAllGood': {
        "title": 'Restrict Listing',
        "description": "Select Yes to hide members from appearing on the member's list who are Awaiting Confirmation, Awaiting Coppa, and in the Not Registered/Not Logged in usergroups.",
    },
    'postorder': {
        "title": 'Order of posts within a thread',
        "description": 'The standard (recommended) way to display threads is chronologically from original topic to the latest reply. You can reverse this, if you prefer, to have threads displayed in reverse, from latest post to oldest post.',
    },
    'maxposts': {
        "title": 'Maximum number of posts to display on a thread page before splitting over multiple pages',
        "description": '',
    },
    'usermaxposts': {
        "title": 'User Settable Maximum Posts per Page',
        "description": 'If you would like to allow the user to set their own maximum posts per thread then give the options seperated by commas. Leave the field blank to force them to use the MAXPOSTS setting above this option.\n\nex. 10,20,30,40',
    },
    'pagenavpages': {
        "title": 'Pages to show in nav bar',
        "description": 'In the list of links of pages in the current thread (or current forum), this option selects how many pages either side of the current page are shown. Set this to 0 to display all pages.',
    },
    'wordwrap': {
        "title": 'Number of characters before wrapping',
        "description": 'If you want posts to automatically insert spaces into long words to make them wrap after a certain number of characters, set the number of characters in the box above. If you do not want this to occur, enter 0.',
    },
    'postmaxchars': {
        "title": 'Maximum Characters per post',
        "description": 'The maximum number of characters that you want to allow per post. Set this to 0 to disable it.',
    },
    'showdeficon': {
        "title": 'Show default icon',
        "description": "Show a default icon if a user doesn't choose a message icon or is unable to choose one based on forum settings? {imagesfolder}/icons/icon1.gif will be used.",
    },
    'stopshouting': {
        "title": "Stop 'Shouting' in titles",
        "description": "Prevent your users 'shouting' in their thread titles by changing all-uppercase titles to capitalization only on the first letters of some words. Disable this for some international boards with different character sets, as this may cause problems.",
    },
    'maxthreads': {
        "title": 'Threads per Page',
        "description": 'The number of threads to display on a forum page before splitting it over multiple pages.',
    },
    'usehotthreads': {
        "title": "Use 'hot' icons",
        "description": 'Hot icons indicate topics with a lot of activity. The icons are animated to show a folder on fire.',
    },
    'hotnumberviews': {
        "title": 'Number of views to qualify as a hot thread',
        "description": '',
    },
    'hotnumberposts': {
        "title": 'Number of posts to qualify as a hot thread',
        "description": '',
    },
    'showdots': {
        "title": "Use 'dot' icons?",
        "description": 'When this feature is enabled, a logged in user will see a "dot" (or whatever graphic you choose) on the folder icons (hot folders, new folders, etc) next to the threads that they have participated in.',
    },
    'linktopages': {
        "title": 'Link to individual pages of a multipage thread on the forum listing?',
        "description": '',
    },
    'maxmultipage': {
        "title": 'Maximum links to individual pages',
        "description": "When linking to multiple pages in the forum display, this allows you to set the cut off point on which long posts stop adding more page numbers and are replaced by 'more...'",
    },
    'showvotes': {
        "title": 'Showing Votes',
        "description": 'How many votes will a thread need before the votes are displayed?',
    },
    'votechange': {
        "title": 'Change Votes?',
        "description": 'Allow users to change their thread rating votes?',
    },
    'movedthreadprefix': {
        "title": 'Prefix for moved threads',
        "description": 'The text with which to prefix a thread that has been moved to another forum. (You may use HTML)',
    },
    'stickythreadprefix': {
        "title": 'Prefix for Sticky threads',
        "description": 'Prefix to append to the beginning of thread titles that have been set to "Sticky". These threads always appear at the top of the thread list. (You may use HTML)',
    },
    'pollthreadprefix': {
        "title": 'Prefix for Polls',
        "description": 'Prefix to append to the beginning of Poll thread titles. (You may use HTML)',
    },
    'useforumjump': {
        "title": 'Use Forumjump?',
        "description": 'Do you want to use the Forumjump drop-down menu on your pages?  If your mysql server is optimized and you still are having problems you can try disabling this option to save queries.',
    },
    'forumdisplaydepth': {
        "title": 'Depth of Forums',
        "description": 'Depth of forums to show on forum display when displaying subforums. Do not go too large on this value for performance reasons.',
    },
    'showforumusers': {
        "title": 'Show users browsing forums?',
        "description": 'Enabling this options will show the current users browsing a particular forum on forumdisplay.php while adding one query. Should not affect performance.',
    },
    'enablesearches': {
        "title": 'Enable searches?',
        "description": 'Allow searching for posts within the BB. This is quite a server intensive process so you may want to disable it.</p>\n<p>To disable searching of all forums, delete the option from the searchintro template.',
    },
    'searchperpage': {
        "title": 'Number of posts per page',
        "description": 'Number of successful search items to display per page.',
    },
    'searchfloodtime': {
        "title": 'Floodcheck - Minimum time between searches',
        "description": 'The minimum time (in seconds) that must expire before the user can search again. Set this to 0 to disable it.',
    },
    'minsearchlength': {
        "title": 'Minimum Word Length',
        "description": 'Enter the minimum word length that the search engine is to index.  The smaller this number is, the larger your search index, and conversely your database is going to be.',
    },
    'maxsearchlength': {
        "title": 'Maximum Word Length',
        "description": 'Enter the maximum word length that the search engine is to index.  The larger this number is, the larger your search index, and conversely your database is going to be.',
    },
    'allowwildcards': {
        "title": 'Allow Wild Cards?',
        "description": 'Allow users to use a star (*) in searches to match partial words?',
    },
    'enableemail': {
        "title": 'Enable Email features?',
        "description": 'Enable email sending features: send to friend and email notification for posters and moderators. Don\'t forget to remove those links from the <i>forumdisplay, newreply, newtopic</i>, &amp; <i>editpost</i> templates<br><br>You can turn off the \'Send to Friend\' feature for invidual user groups in the <a href="usergroup.php?s=&amp;action=modify" target="_blank">User Permissions area</a>.',
    },
    'timeoffset': {
        "title": 'Time Zone Offset',
        "description": 'Time (in hours) that the server is offset from GMT. Please select the most appropriate option.',
    },
    'dateformat': {
        "title": 'Format of dates',
        "description": 'Format that the date is presented in on the pages.</p>\n<p>See: <a href="http://www.php.net/manual/function.date.php3" target=_blank>http://www.php.net/manual/function.date.php3</a></p>\n<p>Examples:<br>\nUS Format (e.g., 04-25-98) - m-d-y<br>\nExpanded US Format (e.g., April 25th, 1998) - F jS, Y<br>\nEuropean Format (e.g., 25-04-98) - d-m-Y<br>\nExpanded European Format (e.g., 25th April 1998) - jS F Y',
    },
    'timeformat': {
        "title": 'Format of times',
        "description": 'Format that the time is presented in on the pages.</p>\n<p>See: <a href="http://www.php.net/manual/function.date.php3" target=_blank>http://www.php.net/manual/function.date.php3</a></p>\n<p>Examples:<br>\nUse AM/PM Time Format (eg, 11:15 PM) - h:i A<br>\nUser 24-Hour Format Time (eg, 23:15) - H:i',
    },
    'registereddateformat': {
        "title": 'Format for registration date',
        "description": 'This is used to format dates shown with users\' posts. In the left hand column of a thread display, under the username and title, there is some text showing when the user registered.</p>\n<p>See: <a href="http://www.php.net/manual/function.date.php3" target=_blank>http://www.php.net/manual/function.date.php3</a>',
    },
    'calformat1': {
        "title": 'Birthday Format',
        "description": 'Format of date shown in profile when user gives their birthyear.',
    },
    'calformat2': {
        "title": 'Birthday Format #2',
        "description": "Format of user's birthday shown on profile when the user does specify their birth year. DO NOT put in a code for the year.",
    },
    'enablecensor': {
        "title": 'Enable censor?',
        "description": 'You may have certain words censored on your BB. Words you choose to censor will be replaced by asterisks. All subjects and messages will be affected.',
    },
    'censorwords': {
        "title": 'Words to censor',
        "description": 'Type all words you want censored in the field below. Do not use commas to separate words, just use spaces. For example, type "dog cat boy", rather than "dog, cat, boy." If you type "dog", all words containing the string "dog" would be censored (dogma, for instance, would appear as "***ma"). To censor more accurately, you can require that censors occur only for exact words. You can do this by placing a censor word in curly braces, as in {dog}. Signifying "dog" in the curly braces would mean that dogma would appear as dogma, but dog would appear as "***". Thus your censor list may appear as: cat {dog} {barn} barn<br>Do not use quotation marks and make sure you use curly braces, not parentheses, when specifying exact words.<br>This field can contain a maximum 250 characters.',
    },
    'censorchar': {
        "title": 'Character to use to replace censored words:',
        "description": '',
    },
    'showeditedby': {
        "title": "Show the 'Edited by xxx on yyy' when a post is edited?",
        "description": '',
    },
    'showeditedbyadmin': {
        "title": "Show 'edited by' for admins?",
        "description": 'If you want the [edited by xxx] message to appear when an admin edits a message, select yes here. This message will appear automatically for all moderators and other users, but using this option you can optionally turn it off.',
    },
    'noeditedbytime': {
        "title": "Time to wait before starting to display 'edited by...'",
        "description": 'Time limit (in minutes) to allow user to edit the post without the [edited by xxx] message appearing at the bottom of the post.',
    },
    'edittimelimit': {
        "title": 'Time limit on editing of posts',
        "description": 'Time limit (in minutes) to impose on editing of messages. After this time limit only moderators will be able edit or delete the message. 1 day is 1440 minutes. Set this to 0 if you do not want it to be active.',
    },
    'editthreadtitlelimit': {
        "title": 'Time limit on editing of thread title',
        "description": 'Specify the time-limit (in minutes) within which the thread-title may be edited by the thread starter.',
    },
    'logip': {
        "title": 'Log IP addresses?',
        "description": 'For security reasons, you may wish to display the IP number of the person posting a message. The default is OFF. You may log the IP to file only- in which case the IP number is not viewable on the bulletin board, but is logged, or you may have the IP numbers logged and displayed publicly on the bulletin board.',
    },
    'enablefloodcheck': {
        "title": 'Enable checking for post flooding?',
        "description": 'You may prevent your users from flooding your board with posts by activating this feature. By enabling floodcheck, you disallow users from posting within a given time span of their last post. In other words, if you set a floodcheck time span of 60 seconds, a user may not post a note within 60 seconds of his last post. Administrators and moderators are exempt from floodcheck.',
    },
    'floodchecktime': {
        "title": 'Minimum time between posts',
        "description": 'Set the amount of time in seconds used by flood check to prevent post flooding. Recommended: 60. Type the number of seconds only.',
    },
    'enablebanning': {
        "title": 'Enable Banning Options?',
        "description": 'Banning allows you to stop certain IP addresses and email addresses from registering and posting to the board.',
    },
    'banip': {
        "title": 'IPs to ban:',
        "description": 'IP Number Ban Lists: You may ban any IP numbers from registering and posting. Type in the complete IP number (as in 243.21.31.7), or use a partial IP number (as in 243.21.31). The BB will do matches from the beginning of each IP number that you enter. Thus, If you enter a partial IP of 243.21.31, someone attempting to register who has an IP number of 243.21.31.5 will not be able to register. Similarly, if you have an IP ban on 243.21, someone registering who has an IP of 243.21.3.44 will not be able to register. Thus, be careful when you add IPs to your ban list and be as specific as possible. As with the email ban list, put a space between each IP number. The IP Ban prevents anyone with matching IP number from registering and posting.',
    },
    'banemail': {
        "title": 'Email addresses to ban',
        "description": 'Email Ban Lists: You may ban certain email addresses from registering on your forums. To ban a specific email, type the full email address (as in, waldo@whereiswaldo.com). To ban all email addresses from certain domains, such as hotmail, simply type the domain name (as in hotmail.com)- that will prevent anyone using a hotmail address from registering. Put a space between each banned email.',
    },
    'allowkeepbannedemail': {
        "title": 'Allow user to keep banned email',
        "description": 'If you ban an email address and a user already uses that address, a problem will occur. Using this option, you can specify whether the user will have to enter a new email address in their profile when they next modify their email address, or whether the user can just keep the email address which you have banned.',
    },
    'ontext': {
        "title": "Text for 'on'",
        "description": 'Text that means on. This is used to keep the code language independent. It is used with the vB code / HTML code On / Off settings for postings.',
    },
    'offtext': {
        "title": "Text for 'off'",
        "description": 'Text that means off. This is used to keep the code language independent. It is used with the vB code / HTML code On / Off settings for postings.',
    },
    'enablepms': {
        "title": 'Enable Private Messaging?',
        "description": 'Enabling this will add some performance overhead on the main index and it may not be a feature you wish to have at all.',
    },
    'privallowbbimagecode': {
        "title": 'Allow vB IMG code in private messages?',
        "description": '',
    },
    'privallowbbcode': {
        "title": 'Allow vB code in private messages?',
        "description": '',
    },
    'privallowsmilies': {
        "title": 'Allow smilies in private messages?',
        "description": '',
    },
    'privallowhtml': {
        "title": 'Allow HTML in private messages?',
        "description": '',
    },
    'privallowicons': {
        "title": 'Allow message icons',
        "description": 'Allow the use of the standard message icons for private messages.',
    },
    'pmquota': {
        "title": 'Maximum saved messages',
        "description": 'Maximum number of saved messages a user can have. 0 means unlimited',
    },
    'inboxname': {
        "title": 'Inbox name',
        "description": 'The name of the inbox folder.',
    },
    'sentitemsname': {
        "title": 'Sent Items Name',
        "description": 'The name of the Sent Items folder.',
    },
    'checknewpm': {
        "title": 'IM Support - Check for new PMs',
        "description": 'Selecting yes for this option will cause the system to check the PM database every time a user loads a page, and will display a visible prompt for it.',
    },
    'pmfloodtime': {
        "title": 'Floodcheck - Minimum time between messages',
        "description": "Private Message Flood Checking. Select the minimum time that must pass before a user can send another private message. This is to prevent a single user 'spamming' by sending lots of messages very quickly. Set this to 0 to disable the option.",
    },
    'pmmaxchars': {
        "title": 'Maximum characters per private message',
        "description": 'Maximum characters to allow in a private message. Set this to 0 for no limit.',
    },
    'pmcancelledword': {
        "title": 'Word to denote cancelled message',
        "description": "This is the word that will prefix the title of 'cancelled' messages in the <i>message tracking</i> section. (You may use HTML)",
    },
    'pmcancelkill': {
        "title": "Delete 'cancelled' messages?",
        "description": "When users 'cancel' messages in the message tracking area, would you like to remove the message completely? WARNING: Selecting 'yes' could confuse users who have been notified by email about the message.",
    },
    'addheaders': {
        "title": 'Add Standard headers',
        "description": 'This option does not work with some combinations of web server, so is off by default. However, some IIS setups may need it turned on.</p>\n\n<p>It will send the 200 OK HTTP headers if turned on.',
    },
    'nocacheheaders': {
        "title": 'Add No-cache headers',
        "description": 'Selecting yes will cause vBulletin to add no-cache HTTP headers. These are very effective, so adding them may cause server load to increase due to increase page requests.',
    },
    'gzipoutput': {
        "title": 'GZIP Output',
        "description": 'Selecting yes will enable vBulletin to gzip the output of pages, thus reducing bandwidth requirements. This will be only used on clients that support it, and are HTTP 1.1 compliant. There will be a performance overhead. This feature requires PHP 4.0.1 or greater, and the ZLIB library.',
    },
    'gziplevel': {
        "title": 'GZIP compression level',
        "description": 'Set the level of GZIP compression that will take place on the output. 0=none; 9=max.',
    },
    'cookiedomain': {
        "title": 'Cookie Domain',
        "description": 'The domain on which you want the cookie to have effect. If you want this to affect all of yourhost.com rather than just forums.yourhost.com, enter .yourhost.com here (note the 2 dots!!!). Can be left blank.',
    },
    'cookiepath': {
        "title": 'Path to save cookies',
        "description": 'The path that the cookie is saved to. If you run more than one board on the same domain, it will be necessary to set this to the individual directories of the forums. Otherwise, just leave it as / .',
    },
    'spellchecklang': {
        "title": 'Spell Check Language',
        "description": 'The language used for the spell checking features, provided by <a href="http://www.spellchecker.net/" target=_blank>Spellchecker.net</a>. If you do not want to use these features, you should remove them from the template.',
    },
    'addtemplatename': {
        "title": 'Add template name in comments',
        "description": 'Add the template name at the beginning and end of every template rendered. This is useful for debugging and analyzing the HTML code, but turn it off to save bandwidth when running in a production environment.',
    },
    'sessionlimit': {
        "title": 'Simultaneous sessions limit',
        "description": 'Set this to the maximum number of simultaneous sessions that you want to be active at any one time. If this number is exceeded, new users are turned away until the server is less busy. Set this to 0 to disable this option.',
    },
    'loadlimit': {
        "title": '*NIX Load Limit',
        "description": 'vBulletin can read the overall load of the server on certain *nix setups (including Linux). This allows vBulletin to determine the load on the server and processor, and to turn away further users if the load becomes too high. If you do not want to use this option, set it to 0. A typical level would be 5.00 for a reasonable warning level.',
    },
    'maxpolloptions': {
        "title": 'Maximum Options',
        "description": 'Maximum number of options a user can select for the poll. Set this to 0 to allow infinitely many options.',
    },
    'updatelastpost': {
        "title": 'Update last post time',
        "description": 'Update the last post time for the thread (thus returning it to the top of a forum) when a vote is placed.',
    },
    'avatarenabled': {
        "title": 'Enable Avatars',
        "description": 'Use this option to enable/disable the overall use of avatars.<br><br>Avatars are small images displayed under usernames in thread display and user info pages.',
    },
    'avatarcustomposts': {
        "title": 'Minimum custom posts',
        "description": 'Minimum number of posts that a user required before they can specify a custom avatar for use.',
    },
    'avatarallowupload': {
        "title": 'Allow uploads',
        "description": 'Allow user to upload their own custom avatar if they have enough posts?',
    },
    'avatarallowwebsite': {
        "title": 'Allow website uploads',
        "description": 'Allow user to upload their own custom avatar from another website if they have enough posts?',
    },
    'avatarmaxdimension': {
        "title": 'Maximum Dimensions',
        "description": 'Maximum width and height (in pixels) that the custom avatar image can be.',
    },
    'avatarmaxsize': {
        "title": 'Maximum File Size',
        "description": 'The maximum file size (in bytes) that an avatar can be.\n\n1 KB = 1024 bytes\n1 MB = 1048576 bytes',
    },
    'numavatarshigh': {
        "title": 'Display Height',
        "description": 'How many rows of avatars do you wish to display to the user when selecting an avatar?',
    },
    'numavatarswide': {
        "title": 'Display Width',
        "description": 'How many columns of avatars do you wish to display to the user when selecting an avatar?',
    },
    'maxattachsize': {
        "title": 'Maximum File Size',
        "description": 'Specify the maximum size in bytes that an upload may be. Set this value to 0 to enable any sized uploads.\n\n1 KB = 1024 bytes\n1 MB = 1048576 bytes',
    },
    'attachextensions': {
        "title": 'Valid Extensions',
        "description": 'Valid extensions that uploads may have. Separate each item with a space.\n\nFor each extension, you should have a file in the /images/attach/ folder called xxx.gif where xxx is the extension of the file. This allows you to have an icon for each file type.',
    },
    'viewattachedimages': {
        "title": 'View Images',
        "description": 'Do you wish to display attached images in the threads? Select no to just generate a link to download the image.',
    },
    'maxattachwidth': {
        "title": 'Maximum Image Width',
        "description": 'Set this to the maximum width attached images (jpg and gif) may have. Set it to 0 to not limit the width.',
    },
    'maxattachheight': {
        "title": 'Maximum Image Height',
        "description": 'Set this to the maximum height attached images (jpg and gif) may have. Set it to 0 to not limit the height.',
    },
    'allowduplicates': {
        "title": 'Allow Duplicate Images',
        "description": 'Setting this to NO will cause the post to refer to the previous existence of the attachment instead of adding another copy of it to the database. It only checks for attachments posted by the user that is making the post.',
    },
    'attachthumbmode': {
        "title": 'Display Attachments as Thumbnails',
        "description": 'Show a scaled-down copy of image attachments inside posts. Clicking the thumbnail opens the original image. Select No to always show attachments at their original size.',
    },
    'attachthumbwidth': {
        "title": 'Thumbnail Maximum Width',
        "description": 'Maximum width in pixels for attachment thumbnails; larger images are scaled proportionally. 0 = no limit.',
    },
    'attachthumbheight': {
        "title": 'Thumbnail Maximum Height',
        "description": 'Maximum height in pixels for attachment thumbnails. 0 = no limit.',
    },
    'ctEnable': {
        "title": 'Enable Titles',
        "description": 'Enable Custom User titles?',
    },
    'ctMaxChars': {
        "title": 'Maximum Chars',
        "description": 'Maximum length users will be allowed to set their custom title to.',
    },
    'ctPosts': {
        "title": 'Number of Posts',
        "description": 'Number of posts a user must have before they can use custom titles.',
    },
    'ctDays': {
        "title": 'Number of Days',
        "description": 'Number of days a user must be registered before they can use custom titles.',
    },
    'ctAdmin': {
        "title": 'Allow Mods/Admins to Change titles',
        "description": 'Allow Admins/Mods to change titles whether or not they have enough posts or have been registered long enough? User titles must be enabled.',
    },
    'ctEitherOr': {
        "title": 'Boolean',
        "description": 'Do you want a user to have to have the number of posts you specified above AND be registered the number of days you specified above? If you select NO then if a user satisfies EITHER criteria than they can use custom titles. For Ex a User has been registered for 1 year but only has 20 posts. If you specified 100 posts and 1 year then they could use titles if you select NO.',
    },
    'ctCensorWords': {
        "title": 'Censored Words',
        "description": 'Type all words you want censored in the field below. Do not use commas to separate words, just use spaces. For example, type "dog cat boy", rather than "dog, cat, boy." If you type "dog", all words containing the string "dog" would be censored (dogma, for instance, would appear as "***ma"). To censor more accurately, you can require that censors occur only for exact words. You can do this by placing a censor word in curly braces, as in {dog}. Signifying "dog" in the curly braces would mean that dogma would appear as dogma, but dog would appear as "***". Thus your censor list may appear as: cat {dog} {barn} barn<br>\nDo not use quotation marks and make sure you use curly braces, not parentheses, when specifying exact words.',
    },
    'ctCensorMod': {
        "title": 'Exempt Mod from Censor',
        "description": 'Do you want to exempt mods from the censor words? You will want to set this to yes if you censor anything that is part of a moderator\'s title like "moderator" as they have custom titles by default and will get censored.',
    },
    'calendarenabled': {
        "title": 'Enable Calendar',
        "description": 'Disable/enable the calendar',
    },
    'calbirthday': {
        "title": 'Birthdays',
        "description": 'Use birthdays?',
    },
    'calshowbirthdays': {
        "title": 'Individual Birthdays',
        "description": 'Show the individual birthdays for each user on the calendar? Set this to NO to just show a link if a particular day has birthdays on it.',
    },
    'calallowhtml': {
        "title": 'html',
        "description": 'Allow HTML to be used in the calendar events?',
    },
    'calbbimagecode': {
        "title": 'bbimagecode',
        "description": 'Allow [IMG] code to be used in calendar events?',
    },
    'calallowsmilies': {
        "title": 'smilies',
        "description": 'Allow smilies to be used in calendar events?',
    },
    'calallowbbcode': {
        "title": 'bbcode',
        "description": 'Allow VB code to be used in calendar events?',
    },
    'caltitlelength': {
        "title": 'title length',
        "description": 'Length to cut off titles when displayed on the main calendar. 0 disables cut-off.',
    },
    'calStart': {
        "title": 'Starting Day',
        "description": "Pick the day that you would like the weeks on your calendar to start with. Users can also change this in their profile to match their locale's customs.",
    },
    'safeupload': {
        "title": 'Upload In Safe Mode?',
        "description": 'If your server runs PHP with <b>SAFE MODE</b> Restrictions, set this to yes.',
    },
    'tmppath': {
        "title": 'Safe Mode Temp Directory',
        "description": 'If your server is running in safe_mode, you\'ll need to specify a directory that is CHMOD to 777 that will act as a temporary directory for uploads.  All files are removed from this directory after database insertion. <br><b>Note:</b> Do NOT include the trailing slash ("/") after the directory name.',
    },
    'WOLenable': {
        "title": "Enable Who's Online",
        "description": "Selecting NO will disable Who's Online for everyone.",
    },
    'WOLguests': {
        "title": 'Enable Guests',
        "description": "Display Guest activity on Who's Online?",
    },
    'WOLresolve': {
        "title": 'Resolve IPs',
        "description": "Resolve IP addresses for those who have access to view them? This can slow down the Display of Who's Online.",
    },
    'WOLrefresh': {
        "title": 'Refresh',
        "description": "Time period in seconds to refresh the Who's Online display. 0 disables refresh.",
    },
}
