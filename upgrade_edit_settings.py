"""组 14「编辑选项」的数据迁移：posts 表补 vB 的 edituserid 列。"""
import sqlite3

DB = r"C:\Users\tsuibin\Doubao\chats\2026-11-06\new-chat-1\loongbbs-next\loongbbs.db"

conn = sqlite3.connect(DB)
columns = [row[1] for row in conn.execute("PRAGMA table_info(posts)")]
if "edit_user_id" in columns:
    print("posts.edit_user_id 已存在，跳过")
else:
    conn.execute("ALTER TABLE posts ADD COLUMN edit_user_id INTEGER")
    conn.commit()
    print("已给 posts 增加 edit_user_id 列")
conn.close()
