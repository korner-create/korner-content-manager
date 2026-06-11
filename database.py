# -*- coding: utf-8 -*-
import os
from supabase import create_client

SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')

def get_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def init_db():
    # Supabase 테이블은 SQL Editor에서 미리 생성 — 여기선 연결 확인만
    pass

def add_idea(title, type_, series, memo=''):
    sb = get_client()
    sb.table('ideas').insert({
        'title': title,
        'type': type_,
        'series': series,
        'memo': memo,
        'status': '아이디어'
    }).execute()

def get_ideas(status=None, type_=None):
    sb = get_client()
    q = sb.table('ideas').select('*')
    if status:
        q = q.eq('status', status)
    if type_:
        q = q.eq('type', type_)
    res = q.order('created_at', desc=True).execute()
    return res.data

def update_idea_status(idea_id, status):
    sb = get_client()
    sb.table('ideas').update({'status': status}).eq('id', idea_id).execute()

def delete_idea(idea_id):
    sb = get_client()
    sb.table('ideas').delete().eq('id', idea_id).execute()

def upsert_videos(rows):
    sb = get_client()
    for r in rows:
        sb.table('videos').upsert(r, on_conflict='video_id').execute()

def get_videos(type_=None, limit=50):
    sb = get_client()
    q = sb.table('videos').select('*')
    if type_:
        q = q.eq('type', type_)
    res = q.order('views', desc=True).limit(limit).execute()
    return res.data
