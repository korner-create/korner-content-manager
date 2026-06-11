# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os, sys

sys.path.insert(0, os.path.dirname(__file__))
from database import init_db, add_idea, get_ideas, update_idea_status, delete_idea, get_videos
from youtube_api import import_from_csv

# ── 초기화 ───────────────────────────────────────────────────────
init_db()

# ── 한글 폰트 ────────────────────────────────────────────────────
def set_korean_font():
    available = {f.name for f in fm.fontManager.ttflist}
    for font in ['Malgun Gothic', 'NanumGothic', 'AppleGothic']:
        if font in available:
            plt.rcParams['font.family'] = font
            break
    plt.rcParams['axes.unicode_minus'] = False

set_korean_font()

# ── 페이지 설정 ──────────────────────────────────────────────────
st.set_page_config(
    page_title='코너 콘텐츠 매니저',
    page_icon='🎬',
    layout='wide'
)

st.title('🎬 코너 콘텐츠 매니저')

tab1, tab2, tab3 = st.tabs(['💡 기획 뱅크', '📊 채널 분석', '⬆️ 데이터 가져오기'])

# ════════════════════════════════════════════════════════════════
# TAB 1 — 기획 뱅크
# ════════════════════════════════════════════════════════════════
with tab1:
    st.subheader('💡 기획 뱅크')

    # 아이디어 추가
    with st.expander('➕ 새 아이디어 추가', expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            new_title = st.text_input('제목 (아이디어)', placeholder='예: 함부로 편의점 도시락만 먹으면 안되는 이유')
        with col2:
            new_type = st.selectbox('유형', ['롱폼', '숏폼'])
            new_series = st.selectbox('시리즈', ['함부로 시리즈', '진짜일까?', '돈 숨기기', '멤버 대결', '챌린지', '기타'])
        with col3:
            new_memo = st.text_area('메모', placeholder='촬영 아이디어, 준비물, 참고 사항 등', height=100)
        if st.button('추가하기', type='primary'):
            if new_title.strip():
                add_idea(new_title.strip(), new_type, new_series, new_memo)
                st.success('추가됐어요!')
                st.rerun()
            else:
                st.warning('제목을 입력해주세요.')

    st.divider()

    # 필터
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        filter_status = st.selectbox('상태 필터', ['전체', '아이디어', '기획중', '촬영예정', '편집중', '업로드완료'])
    with col_f2:
        filter_type = st.selectbox('유형 필터', ['전체', '롱폼', '숏폼'])
    with col_f3:
        st.write('')

    status_arg = None if filter_status == '전체' else filter_status
    type_arg = None if filter_type == '전체' else filter_type
    ideas = get_ideas(status=status_arg, type_=type_arg)

    if not ideas:
        st.info('아이디어가 없어요. 위에서 추가해보세요!')
    else:
        status_colors = {
            '아이디어': '⚪',
            '기획중': '🟡',
            '촬영예정': '🔵',
            '편집중': '🟠',
            '업로드완료': '🟢',
        }
        status_options = ['아이디어', '기획중', '촬영예정', '편집중', '업로드완료']

        for idea in ideas:
            with st.container():
                col_a, col_b, col_c, col_d = st.columns([4, 1, 1, 1])
                with col_a:
                    emoji = '📹' if idea['type'] == '롱폼' else '⚡'
                    st.markdown(f"**{emoji} {idea['title']}**")
                    if idea['memo']:
                        st.caption(idea['memo'])
                    st.caption(f"시리즈: {idea['series']} | 추가: {idea['created_at'][:10]}")
                with col_b:
                    st.markdown(f"{status_colors.get(idea['status'], '⚪')} **{idea['status']}**")
                with col_c:
                    new_s = st.selectbox(
                        '상태 변경',
                        status_options,
                        index=status_options.index(idea['status']),
                        key=f"status_{idea['id']}",
                        label_visibility='collapsed'
                    )
                    if new_s != idea['status']:
                        update_idea_status(idea['id'], new_s)
                        st.rerun()
                with col_d:
                    if st.button('🗑️', key=f"del_{idea['id']}", help='삭제'):
                        delete_idea(idea['id'])
                        st.rerun()
                st.divider()

    # 상태별 요약
    all_ideas = get_ideas()
    if all_ideas:
        st.subheader('📋 현황 요약')
        df_ideas = pd.DataFrame(all_ideas)
        counts = df_ideas['status'].value_counts()
        cols = st.columns(5)
        for i, s in enumerate(['아이디어', '기획중', '촬영예정', '편집중', '업로드완료']):
            with cols[i]:
                st.metric(f"{status_colors[s]} {s}", counts.get(s, 0))

# ════════════════════════════════════════════════════════════════
# TAB 2 — 채널 분석
# ════════════════════════════════════════════════════════════════
with tab2:
    st.subheader('📊 채널 분석')

    videos = get_videos(limit=500)
    if not videos:
        st.info('데이터가 없어요. "데이터 가져오기" 탭에서 CSV를 먼저 불러오세요.')
    else:
        df = pd.DataFrame(videos)
        longform = df[df['type'] == '롱폼'].copy()
        shortform = df[df['type'] == '숏폼'].copy()

        # ── 전체 요약 ──────────────────────────────────────────
        c1, c2, c3, c4 = st.columns(4)
        c1.metric('총 영상', f"{len(df)}개  (롱폼 {len(longform)} / 숏폼 {len(shortform)})")
        c2.metric('총 조회수', f"{df['views'].sum()/10000:.0f}만")
        c3.metric('총 시청 시간', f"{df['watch_hours'].sum()/10000:.0f}만 시간")
        c4.metric('총 예상 수익', f"${df['revenue_usd'].sum():,.0f}")

        st.divider()

        # ── 섹션 선택 ──────────────────────────────────────────
        section = st.radio('분석 섹션', ['🏆 잘 된 영상', '📺 롱폼 인사이트', '⚡ 숏폼 인사이트', '🔍 롱폼 vs 숏폼'], horizontal=True)

        # ── 잘 된 영상 ─────────────────────────────────────────
        if section == '🏆 잘 된 영상':
            sort_col1, sort_col2, sort_col3 = st.columns(3)
            with sort_col1:
                sort_by = st.selectbox('정렬 기준', ['조회수', '시청 지속률', 'CTR'], key='sort_by')
            with sort_col2:
                sort_order = st.radio('정렬 방향', ['내림차순 ↓', '오름차순 ↑'], horizontal=True, key='sort_order')
            with sort_col3:
                top_n = st.slider('표시 개수', 5, 30, 10, key='top_n')

            sort_map = {'조회수': 'views', '시청 지속률': 'avg_view_pct', 'CTR': 'ctr'}
            col_key = sort_map[sort_by]
            ascending = sort_order == '오름차순 ↑'

            st.markdown(f'### {sort_by} {"▲" if ascending else "▼"} TOP {top_n} — 롱폼')
            top_long = longform.sort_values(col_key, ascending=ascending).head(top_n).reset_index(drop=True)
            for i, row in top_long.iterrows():
                with st.container():
                    col_r, col_t, col_m1, col_m2, col_m3 = st.columns([0.3, 3.5, 1, 1, 1])
                    col_r.markdown(f"**#{i+1}**")
                    col_t.markdown(f"**{row['title']}**")
                    col_m1.metric('조회수', f"{row['views']/10000:.1f}만")
                    col_m2.metric('시청 지속률', f"{row['avg_view_pct']:.1f}%")
                    col_m3.metric('CTR', f"{row['ctr']:.1f}%")
                st.divider()

            st.markdown(f'### {sort_by} {"▲" if ascending else "▼"} TOP {top_n} — 숏폼')
            sort_map_sf = {'조회수': 'views', '시청 지속률': 'avg_view_pct', 'CTR': 'views'}
            top_short = shortform.sort_values(sort_map_sf.get(sort_by, 'views'), ascending=ascending).head(top_n).reset_index(drop=True)
            for i, row in top_short.iterrows():
                with st.container():
                    col_r, col_t, col_m1, col_m2 = st.columns([0.3, 4, 1, 1])
                    col_r.markdown(f"**#{i+1}**")
                    col_t.markdown(f"**{row['title']}**")
                    col_m1.metric('조회수', f"{row['views']/10000:.1f}만")
                    col_m2.metric('시청 지속률', f"{row['avg_view_pct']:.1f}%")
                st.divider()

        # ── 롱폼 인사이트 ──────────────────────────────────────
        elif section == '📺 롱폼 인사이트':
            lf = longform.dropna(subset=['views', 'avg_view_pct', 'ctr'])
            lf = lf[lf['views'] > 0]

            avg_views = lf['views'].mean()
            avg_retention = lf['avg_view_pct'].mean()
            avg_ctr = lf['ctr'].mean()

            st.markdown('### 롱폼 평균 성과')
            c1, c2, c3 = st.columns(3)
            c1.metric('평균 조회수', f"{avg_views/10000:.1f}만")
            c2.metric('평균 시청 지속률', f"{avg_retention:.1f}%")
            c3.metric('평균 CTR', f"{avg_ctr:.1f}%")

            st.markdown('### 시청 지속률 TOP 10 — 끝까지 본 영상')
            st.caption('시청자가 영상을 얼마나 끝까지 봤는지 — 높을수록 콘텐츠 완성도가 높은 것')
            top_ret = lf[lf['views'] >= 10000].nlargest(10, 'avg_view_pct').reset_index(drop=True)
            for i, row in top_ret.iterrows():
                diff = row['avg_view_pct'] - avg_retention
                arrow = '🔥' if diff >= 10 else ('📈' if diff >= 0 else '📉')
                with st.container():
                    col_r, col_t, col_m1, col_m2, col_m3 = st.columns([0.3, 3.5, 1, 1, 1])
                    col_r.markdown(f"**#{i+1}**")
                    col_t.markdown(f"**{row['title']}**")
                    col_m1.metric('지속률', f"{row['avg_view_pct']:.1f}%", f"{diff:+.1f}%p")
                    col_m2.metric('조회수', f"{row['views']/10000:.1f}만")
                    col_m3.markdown(f"<div style='font-size:2rem;text-align:center;padding-top:8px'>{arrow}</div>", unsafe_allow_html=True)
                st.divider()

            st.markdown('### CTR TOP 10 — 썸네일/제목이 잘 먹힌 영상')
            st.caption('노출됐을 때 클릭한 비율 — 높을수록 제목/썸네일이 효과적인 것')
            top_ctr = lf[lf['views'] >= 10000].nlargest(10, 'ctr').reset_index(drop=True)
            for i, row in top_ctr.iterrows():
                diff = row['ctr'] - avg_ctr
                with st.container():
                    col_r, col_t, col_m1, col_m2 = st.columns([0.3, 4, 1, 1])
                    col_r.markdown(f"**#{i+1}**")
                    col_t.markdown(f"**{row['title']}**")
                    col_m1.metric('CTR', f"{row['ctr']:.1f}%", f"{diff:+.1f}%p")
                    col_m2.metric('조회수', f"{row['views']/10000:.1f}만")
                st.divider()

            st.markdown('### 구독자 전환율 TOP 10 — 팬을 만든 영상')
            st.caption('조회수 대비 구독자를 가장 많이 늘린 영상')
            lf_sub = lf[lf['views'] >= 10000].copy()
            lf_sub['구독전환율'] = lf_sub['subscribers'] / lf_sub['views'] * 100
            top_sub = lf_sub.nlargest(10, '구독전환율').reset_index(drop=True)
            for i, row in top_sub.iterrows():
                with st.container():
                    col_r, col_t, col_m1, col_m2 = st.columns([0.3, 4, 1, 1])
                    col_r.markdown(f"**#{i+1}**")
                    col_t.markdown(f"**{row['title']}**")
                    col_m1.metric('구독 전환율', f"{row['구독전환율']:.3f}%")
                    col_m2.metric('구독자 +', f"{int(row['subscribers']):+,}명")
                st.divider()

        # ── 숏폼 인사이트 ──────────────────────────────────────
        elif section == '⚡ 숏폼 인사이트':
            sf = shortform.dropna(subset=['views', 'avg_view_pct'])
            sf = sf[sf['views'] > 0]

            avg_views_s = sf['views'].mean()
            avg_ret_s = sf['avg_view_pct'].mean()

            st.markdown('### 숏폼 평균 성과')
            c1, c2, c3 = st.columns(3)
            c1.metric('평균 조회수', f"{avg_views_s/10000:.1f}만")
            c2.metric('평균 시청 지속률', f"{avg_ret_s:.1f}%")
            c3.metric('100% 이상 지속률 영상', f"{len(sf[sf['avg_view_pct'] >= 100])}개")

            st.markdown('### 시청 지속률 TOP 10 — 반복 시청된 영상')
            st.caption('숏폼은 100% 이상이면 반복 시청 — 루프 구조가 잘 된 것')
            top_sf = sf.nlargest(10, 'avg_view_pct').reset_index(drop=True)
            for i, row in top_sf.iterrows():
                loop = '🔁 반복시청' if row['avg_view_pct'] >= 100 else ''
                with st.container():
                    col_r, col_t, col_m1, col_m2, col_badge = st.columns([0.3, 3.5, 1, 1, 1])
                    col_r.markdown(f"**#{i+1}**")
                    col_t.markdown(f"**{row['title']}**")
                    col_m1.metric('지속률', f"{row['avg_view_pct']:.1f}%")
                    col_m2.metric('조회수', f"{row['views']/10000:.1f}만")
                    col_badge.markdown(f"<div style='padding-top:12px;color:#E94B3C;font-weight:bold'>{loop}</div>", unsafe_allow_html=True)
                st.divider()

            st.markdown('### 조회수 TOP 10 대비 지속률 분석')
            st.caption('조회수가 많지만 지속률이 낮으면 — 제목은 좋았지만 내용이 기대에 못 미친 것')
            top10_sf = sf.nlargest(10, 'views').reset_index(drop=True)
            for i, row in top10_sf.iterrows():
                gap = row['avg_view_pct'] - avg_ret_s
                flag = '✅ 기대 이상' if gap >= 5 else ('⚠️ 기대 이하' if gap <= -10 else '➖ 평균')
                with st.container():
                    col_r, col_t, col_m1, col_m2, col_f = st.columns([0.3, 3.5, 1, 1, 1])
                    col_r.markdown(f"**#{i+1}**")
                    col_t.markdown(f"**{row['title']}**")
                    col_m1.metric('조회수', f"{row['views']/10000:.1f}만")
                    col_m2.metric('지속률', f"{row['avg_view_pct']:.1f}%", f"{gap:+.1f}%p")
                    col_f.markdown(f"<div style='padding-top:12px;font-weight:bold'>{flag}</div>", unsafe_allow_html=True)
                st.divider()

        # ── 롱폼 vs 숏폼 비교 ─────────────────────────────────
        elif section == '🔍 롱폼 vs 숏폼':
            st.markdown('### 채널 기여도 비교')

            metrics = {
                '조회수': (longform['views'].sum(), shortform['views'].sum(), '만', 10000),
                '시청 시간': (longform['watch_hours'].sum(), shortform['watch_hours'].sum(), '만h', 10000),
                '구독자 증가': (longform['subscribers'].sum(), shortform['subscribers'].sum(), '명', 1),
                '예상 수익': (longform['revenue_usd'].sum(), shortform['revenue_usd'].sum(), '$', 1),
            }

            for label, (lv, sv, unit, div) in metrics.items():
                total = lv + sv if (lv + sv) > 0 else 1
                l_pct = lv / total * 100
                s_pct = sv / total * 100
                st.markdown(f"**{label}**")
                col_l, col_bar, col_r = st.columns([1.5, 5, 1.5])
                col_l.markdown(f"<div style='text-align:right;color:#4A90D9'>롱폼<br><b>{lv/div:,.0f}{unit}</b> ({l_pct:.0f}%)</div>", unsafe_allow_html=True)
                col_bar.markdown(
                    f"<div style='background:#4A90D9;width:{l_pct:.0f}%;height:24px;display:inline-block;border-radius:4px 0 0 4px'></div>"
                    f"<div style='background:#E94B3C;width:{s_pct:.0f}%;height:24px;display:inline-block;border-radius:0 4px 4px 0'></div>",
                    unsafe_allow_html=True
                )
                col_r.markdown(f"<div style='color:#E94B3C'>숏폼<br><b>{sv/div:,.0f}{unit}</b> ({s_pct:.0f}%)</div>", unsafe_allow_html=True)
                st.write('')

            st.divider()
            st.markdown('### 핵심 인사이트')
            lf_rpm = longform['revenue_usd'].sum() / (longform['views'].sum() / 1000) if longform['views'].sum() > 0 else 0
            sf_rpm = shortform['revenue_usd'].sum() / (shortform['views'].sum() / 1000) if shortform['views'].sum() > 0 else 0

            col1, col2 = st.columns(2)
            with col1:
                st.info(f"""
**📺 롱폼**
- RPM: **${lf_rpm:.2f}** / 1000회
- 평균 지속률: **{longform['avg_view_pct'].mean():.1f}%**
- 평균 CTR: **{longform['ctr'].mean():.1f}%**
- 구독자 기여: **{longform['subscribers'].sum():,}명**
""")
            with col2:
                st.info(f"""
**⚡ 숏폼**
- RPM: **${sf_rpm:.2f}** / 1000회
- 평균 지속률: **{shortform['avg_view_pct'].mean():.1f}%**
- 구독자 기여: **{shortform['subscribers'].sum():,}명**
- 롱폼 대비 RPM: **{sf_rpm/lf_rpm*100:.0f}%** 수준
""" if lf_rpm > 0 else "숏폼 데이터 집계 중")

# ════════════════════════════════════════════════════════════════
# TAB 3 — 데이터 가져오기
# ════════════════════════════════════════════════════════════════
with tab3:
    st.subheader('⬆️ 데이터 가져오기')

    st.markdown('#### YouTube Studio CSV 업로드')
    st.caption('YouTube Studio → 분석 → 고급 모드 → 콘텐츠 탭 → 내보내기(↓)에서 받은 **표 데이터.csv** 파일을 올려주세요.')

    uploaded = st.file_uploader('표 데이터.csv 선택', type='csv')
    if uploaded:
        if st.button('📥 데이터 저장하기', type='primary'):
            import tempfile, traceback
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv', mode='wb') as tmp:
                tmp.write(uploaded.read())
                tmp_path = tmp.name
            try:
                with st.spinner('저장 중...'):
                    count = import_from_csv(tmp_path)
                st.success(f'✅ {count}개 영상 데이터가 저장됐어요!')
                st.rerun()
            except Exception as e:
                st.error(f'오류: {e}')
                st.code(traceback.format_exc())
            finally:
                os.unlink(tmp_path)

    st.divider()
    st.markdown('#### 저장된 데이터 현황')
    videos = get_videos(limit=1000)
    if videos:
        df = pd.DataFrame(videos)
        col1, col2, col3 = st.columns(3)
        col1.metric('총 영상 수', f"{len(df)}개")
        col2.metric('롱폼', f"{len(df[df['type']=='롱폼'])}개")
        col3.metric('숏폼', f"{len(df[df['type']=='숏폼'])}개")
        st.caption(f"마지막 업데이트: {df['fetched_at'].max()}")
    else:
        st.info('아직 데이터가 없어요.')

    st.divider()
    st.markdown('#### YouTube API 자동 수집')
    st.caption('API로 최신 영상 목록과 조회수를 자동으로 가져와요. (하루 할당량: 10,000유닛)')

    CHANNEL_ID = 'UCYACixxri8vQLQ6BSriQehw'

    col_a, col_b = st.columns(2)
    with col_a:
        max_results = st.slider('가져올 영상 수', 10, 200, 50, step=10)
    with col_b:
        st.write('')
        st.write('')
        if st.button('🔄 최신 데이터 가져오기', type='primary'):
            try:
                api_key = st.secrets.get('YOUTUBE_API_KEY', os.environ.get('YOUTUBE_API_KEY', ''))
                if not api_key:
                    st.error('API 키가 설정되지 않았어요.')
                else:
                    from youtube_api import fetch_channel_videos, fetch_video_stats
                    import youtube_api as yt
                    yt.API_KEY = api_key
                    with st.spinner('YouTube에서 데이터 가져오는 중...'):
                        video_ids = fetch_channel_videos(CHANNEL_ID, max_results=max_results)
                        stats = fetch_video_stats(video_ids)
                        from database import upsert_videos
                        upsert_videos(stats)
                    st.success(f'✅ {len(stats)}개 영상 데이터 업데이트 완료!')
                    st.rerun()
            except Exception as e:
                import traceback
                st.error(f'오류: {e}')
                st.code(traceback.format_exc())
