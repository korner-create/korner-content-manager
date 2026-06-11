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

        # 전체 요약
        longform = df[df['type'] == '롱폼']
        shortform = df[df['type'] == '숏폼']

        st.markdown('#### 전체 요약')
        c1, c2, c3, c4 = st.columns(4)
        c1.metric('총 영상', f"{len(df)}개")
        c2.metric('총 조회수', f"{df['views'].sum()/10000:.0f}만")
        c3.metric('총 시청 시간', f"{df['watch_hours'].sum():,.0f}h")
        c4.metric('총 예상 수익', f"${df['revenue_usd'].sum():,.0f}")

        st.markdown('#### 롱폼 vs 숏폼')
        col1, col2 = st.columns(2)

        with col1:
            fig, ax = plt.subplots(figsize=(5, 4))
            vals = [longform['views'].sum(), shortform['views'].sum()]
            labels = [f'롱폼\n{vals[0]/10000:.0f}만', f'숏폼\n{vals[1]/10000:.0f}만']
            ax.pie(vals, labels=labels, autopct='%1.1f%%',
                   colors=['#4A90D9', '#E94B3C'], startangle=90)
            ax.set_title('조회수 비율')
            st.pyplot(fig)
            plt.close()

        with col2:
            fig, ax = plt.subplots(figsize=(5, 4))
            metrics = ['롱폼', '숏폼']
            views = [longform['views'].sum()/10000, shortform['views'].sum()/10000]
            ax.bar(metrics, views, color=['#4A90D9', '#E94B3C'])
            ax.set_ylabel('조회수 (만)')
            ax.set_title('유형별 총 조회수')
            for i, v in enumerate(views):
                ax.text(i, v + 5, f'{v:.0f}만', ha='center', fontsize=10)
            st.pyplot(fig)
            plt.close()

        # 롱폼 TOP 15
        st.markdown('#### 롱폼 TOP 15 (조회수)')
        top_long = longform.nlargest(15, 'views')[['title', 'views', 'avg_view_pct', 'ctr', 'subscribers']].copy()
        top_long.columns = ['제목', '조회수', '평균조회율(%)', 'CTR(%)', '구독자증가']
        top_long['조회수'] = top_long['조회수'].apply(lambda x: f'{x:,}')
        st.dataframe(top_long, use_container_width=True, hide_index=True)

        # 숏폼 TOP 15
        st.markdown('#### 숏폼 TOP 15 (조회수)')
        top_short = shortform.nlargest(15, 'views')[['title', 'views', 'avg_view_pct', 'subscribers']].copy()
        top_short.columns = ['제목', '조회수', '평균조회율(%)', '구독자증가']
        top_short['조회수'] = top_short['조회수'].apply(lambda x: f'{x:,}')
        st.dataframe(top_short, use_container_width=True, hide_index=True)

        # CTR vs 시청 지속률
        st.markdown('#### 롱폼: CTR vs 시청 지속률')
        lf = longform.dropna(subset=['ctr', 'avg_view_pct', 'views'])
        lf = lf[lf['ctr'] > 0]
        if not lf.empty:
            fig, ax = plt.subplots(figsize=(9, 5))
            sc = ax.scatter(lf['ctr'], lf['avg_view_pct'],
                            c=lf['views'], cmap='YlOrRd', alpha=0.7,
                            s=lf['views']/lf['views'].max()*300+20)
            plt.colorbar(sc, ax=ax, label='조회수')
            ax.axvline(lf['ctr'].median(), color='gray', linestyle='--', alpha=0.5, label='CTR 중앙값')
            ax.axhline(lf['avg_view_pct'].median(), color='gray', linestyle=':', alpha=0.5, label='지속률 중앙값')
            ax.set_xlabel('CTR (%)')
            ax.set_ylabel('평균 조회율 (%)')
            ax.set_title('CTR vs 시청 지속률  (원 크기 = 조회수)')
            ax.legend(fontsize=9)
            st.pyplot(fig)
            plt.close()

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
    st.markdown('#### YouTube API 키 설정')
    st.caption('API 키를 설정하면 CSV 없이도 자동으로 최신 데이터를 가져올 수 있어요.')
    api_key_input = st.text_input('API Key', type='password', value=os.environ.get('YOUTUBE_API_KEY', ''))
    if st.button('API 키 저장'):
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        with open(env_path, 'w') as f:
            f.write(f'YOUTUBE_API_KEY={api_key_input}\n')
        st.success('저장됐어요! 앱을 재시작하면 적용돼요.')
