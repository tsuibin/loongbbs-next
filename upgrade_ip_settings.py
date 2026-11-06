"""组 15「IP 记录选项」的数据迁移：posts 表补 vB 的 ipaddress 列。"""
import sqlite3

DB = r"C:\Users\tsuibin\Doubao\chats\2026-11-06\new-chat-1\loongbbs-next\loongbbs.db"

conn = sqlite3.connect(DB)
columns = [row[1] for row in conn.execute("PRAGMA table_info(posts)")]
if "ipaddress" in columns:
    print("posts.ipaddress 已存在，跳过")
else:
    conn.execute("ALTER TABLE posts ADD COLUMN ipaddress VARCHAR(45)")
    conn.commit()
    print("已给 posts 增加 ipaddress 列")
conn.close()
