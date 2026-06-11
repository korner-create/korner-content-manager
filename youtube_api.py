# -*- coding: utf-8 -*-
import os
import pandas as pd
from googleapiclient.discovery import build
from database import upsert_videos

API_KEY = os.environ.get('YOUTUBE_API_KEY', '')

def get_service():
    return build('youtube', 'v3', developerKey=API_KEY)

def fetch_channel_videos(channel_id, max_results=50):
    """채널의 최근 영상 목록을 가져옴"""
    svc = get_service()

    # 업로드 재생목록 ID 가져오기
    ch = svc.channels().list(part='contentDetails,statistics', id=channel_id).execute()
    uploads_id = ch['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    # 영상 목록
    videos = []
    next_page = None
    while len(videos) < max_results:
        pl = svc.playlistItems().list(
            part='contentDetails',
            playlistId=uploads_id,
            maxResults=min(50, max_results - len(videos)),
            pageToken=next_page
        ).execute()
        for item in pl['items']:
            videos.append(item['contentDetails']['videoId'])
        next_page = pl.get('nextPageToken')
        if not next_page:
            break

    return videos

def fetch_video_stats(video_ids):
    """영상 상세 통계 가져오기 (50개씩 배치)"""
    svc = get_service()
    results = []
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i+50]
        res = svc.videos().list(
            part='snippet,contentDetails,statistics',
            id=','.join(batch)
        ).execute()
        for item in res.get('items', []):
            dur = item['contentDetails']['duration']
            sec = parse_duration(dur)
            stats = item.get('statistics', {})
            results.append({
                'video_id': item['id'],
                'title': item['snippet']['title'],
                'type': '숏폼' if sec <= 60 else '롱폼',
                'published_at': item['snippet']['publishedAt'][:10],
                'duration_sec': sec,
                'views': int(stats.get('viewCount', 0)),
                'watch_hours': 0,
                'avg_view_pct': 0,
                'ctr': 0,
                'subscribers': 0,
                'revenue_usd': 0,
                'impressions': 0,
            })
    return results

def parse_duration(duration):
    """ISO 8601 duration → 초"""
    import re
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
    if not match:
        return 0
    h = int(match.group(1) or 0)
    m = int(match.group(2) or 0)
    s = int(match.group(3) or 0)
    return h * 3600 + m * 60 + s

def safe_int(val):
    try:
        return int(float(val)) if val == val and val is not None else 0
    except:
        return 0

def safe_float(val):
    try:
        return float(val) if val == val and val is not None else 0.0
    except:
        return 0.0

def import_from_csv(csv_path):
    """YouTube Studio CSV에서 영상 데이터를 DB로 가져오기"""
    df = pd.read_csv(csv_path, encoding='utf-8')
    df = df.where(pd.notnull(df), None)
    df.columns = df.columns.str.strip()
    df = df[df['콘텐츠'].notna() & (df['콘텐츠'] != '합계')].copy()

    num_cols = ['길이', '조회수', '시청 시간(단위: 시간)', '평균 조회율 (%)',
                '노출수', '노출 클릭률 (%)', '구독자', '예상 수익 (USD)']
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')

    rows = []
    for _, row in df.iterrows():
        raw_len = row.get('길이', 0)
        sec = int(raw_len) if pd.notna(raw_len) and raw_len == raw_len else 0
        rows.append({
            'video_id': row['콘텐츠'],
            'title': row.get('동영상 제목', ''),
            'type': '숏폼' if sec <= 60 else '롱폼',
            'published_at': str(row.get('동영상 게시 시간', '')),
            'duration_sec': sec,
            'views': safe_int(row.get('조회수')),
            'watch_hours': safe_float(row.get('시청 시간(단위: 시간)')),
            'avg_view_pct': safe_float(row.get('평균 조회율 (%)')),
            'ctr': safe_float(row.get('노출 클릭률 (%)')),
            'subscribers': safe_int(row.get('구독자')),
            'revenue_usd': safe_float(row.get('예상 수익 (USD)')),
            'impressions': safe_int(row.get('노출수')),
        })

    upsert_videos(rows)
    return len(rows)
