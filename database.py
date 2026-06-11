# -*- coding: utf-8 -*-
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'korner.db')

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS ideas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            type TEXT NOT NULL,          -- 롱폼 / 숏폼
            series TEXT,                 -- 함부로 / 진짜일까 / 돈숨기기 / 기타
            status TEXT DEFAULT '아이디어',  -- 아이디어 / 기획중 / 촬영예정 / 편집중 / 업로드완료
            memo TEXT,
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            updated_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            video_id TEXT PRIMARY KEY,
            title TEXT,
            type TEXT,               -- 롱폼 / 숏폼
            published_at TEXT,
            duration_sec INTEGER,
            views INTEGER,
            watch_hours REAL,
            avg_view_pct REAL,
            ctr REAL,
            subscribers INTEGER,
            revenue_usd REAL,
            impressions INTEGER,
            fetched_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS channel_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            total_views INTEGER,
            total_watch_hours REAL,
            total_subscribers INTEGER,
            fetched_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    ''')

    conn.commit()
    conn.close()

def add_idea(title, type_, series, memo=''):
    conn = get_conn()
    conn.execute(
        'INSERT INTO ideas (title, type, series, memo) VALUES (?, ?, ?, ?)',
        (title, type_, series, memo)
    )
    conn.commit()
    conn.close()

def get_ideas(status=None, type_=None):
    conn = get_conn()
    query = 'SELECT * FROM ideas WHERE 1=1'
    params = []
    if status:
        query += ' AND status = ?'
        params.append(status)
    if type_:
        query += ' AND type = ?'
        params.append(type_)
    query += ' ORDER BY updated_at DESC'
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_idea_status(idea_id, status):
    conn = get_conn()
    conn.execute(
        "UPDATE ideas SET status=?, updated_at=datetime('now','localtime') WHERE id=?",
        (status, idea_id)
    )
    conn.commit()
    conn.close()

def delete_idea(idea_id):
    conn = get_conn()
    conn.execute('DELETE FROM ideas WHERE id=?', (idea_id,))
    conn.commit()
    conn.close()

def upsert_videos(rows):
    conn = get_conn()
    for r in rows:
        conn.execute('''
            INSERT INTO videos (video_id, title, type, published_at, duration_sec,
                views, watch_hours, avg_view_pct, ctr, subscribers, revenue_usd, impressions)
            VALUES (:video_id,:title,:type,:published_at,:duration_sec,
                :views,:watch_hours,:avg_view_pct,:ctr,:subscribers,:revenue_usd,:impressions)
            ON CONFLICT(video_id) DO UPDATE SET
                views=excluded.views, watch_hours=excluded.watch_hours,
                avg_view_pct=excluded.avg_view_pct, ctr=excluded.ctr,
                subscribers=excluded.subscribers, revenue_usd=excluded.revenue_usd,
                impressions=excluded.impressions,
                fetched_at=datetime('now','localtime')
        ''', r)
    conn.commit()
    conn.close()

def get_videos(type_=None, limit=50):
    conn = get_conn()
    query = 'SELECT * FROM videos WHERE 1=1'
    params = []
    if type_:
        query += ' AND type=?'
        params.append(type_)
    query += ' ORDER BY views DESC LIMIT ?'
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]
