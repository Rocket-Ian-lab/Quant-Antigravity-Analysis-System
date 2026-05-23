import streamlit as st
import pandas as pd
from main import analyze_company
from news_api import fetch_news
from ai_summary import summarize_news
from live_market import get_top_10_gainers
from industry_avg import get_industry_averages
from corp_mapper import load_corp_mapping
import FinanceDataReader as fdr
import datetime
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
# 페이지 기본 설정
st.set_page_config(
    page_title="Quant-Antigravity Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS (프리미엄 디자인)
st.markdown("""
<style>
    .reportview-container .main .block-container{
        padding-top: 2rem;
    }
    .metric-card {
        background-color: #1E1E1E;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        margin-bottom: 20px;
    }
    .st-emotion-cache-16idsys p {
        font-size: 1.1rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("🚀 Quant-Antigravity Analysis System")
st.markdown("Phase 3: Web-based Value & Sector Screening Dashboard")

# 사이드바 입력창
with st.sidebar:
    st.header("🔍 검색 옵션")
    
    # 기업 데이터 매핑 (캐시됨)
    corp_mapping = load_corp_mapping()
    
    if corp_mapping:
        company_names = sorted(list(corp_mapping.keys()))
        default_idx = company_names.index("삼성전자") if "삼성전자" in company_names else 0
        
        # 기업명 검색 (자동완성 지원)
        company_name = st.selectbox("🏢 기업명 검색", options=company_names, index=default_idx)
        
        # 선택된 기업에 맞춰 종목코드와 고유번호 자동 할당
        ticker = corp_mapping[company_name]["ticker"]
        corp_code = corp_mapping[company_name]["corp_code"]
        
        st.text_input("종목코드 (자동입력)", value=ticker, disabled=True)
        st.text_input("DART 고유번호 (자동입력)", value=corp_code, disabled=True)
    else:
        # 매핑 에러 시 폴백(수동입력)
        company_name = st.text_input("기업명", "삼성전자")
        ticker = st.text_input("종목코드", "005930")
        corp_code = st.text_input("고유번호", "00126380")
        
    target_year = st.number_input("분석 연도", min_value=2015, max_value=2026, value=2024, step=1)
    
    run_btn = st.button("🚀 분석 실행", type="primary", use_container_width=True)
    
    st.divider()
    st.header("📈 실시간 급등주 Top 10")
    with st.spinner("급등주 정보 로딩 중..."):
        top_gainers_df = get_top_10_gainers()
        if not top_gainers_df.empty:
            st.dataframe(
                top_gainers_df,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning("실시간 급등주 정보를 가져오지 못했습니다.")

if run_btn:
    with st.spinner(f"'{company_name}' 데이터를 수집하고 분석 중입니다..."):
        try:
            # 1. 재무 및 시장 데이터 분석
            profile = analyze_company(ticker, corp_code, company_name, target_year)
            
            if profile:
                fin = profile.financials[-1]
                mkt = profile.market_data
                
                # --- 상단 헤더 영역 ---
                st.subheader(f"📊 {profile.company_name} ({profile.ticker}) 종합 분석")
                st.caption(f"분류 섹터: **{profile.sector}** | 기준 연도: {fin.year}년")
                st.divider()
                
                # --- 주가 차트 영역 (최근 1년) ---
                st.markdown("### 📈 최근 1년 주가 추이")
                with st.spinner("주가 데이터를 불러오는 중..."):
                    try:
                        from pykrx import stock
                        end_date = datetime.datetime.now()
                        # MA120 계산을 위해 2년치 데이터 먼저 로드
                        start_date_extended = end_date - datetime.timedelta(days=730)
                        one_year_ago = end_date - datetime.timedelta(days=365)
                        
                        start_str_extended = start_date_extended.strftime("%Y%m%d")
                        end_str = end_date.strftime("%Y%m%d")
                        
                        # pykrx를 사용하여 안정적으로 OHLCV 데이터 로드
                        price_df = stock.get_market_ohlcv(start_str_extended, end_str, ticker)
                        
                        if not price_df.empty:
                            # 윈도우 환경 인코딩 깨짐 방지를 위해 컬럼 인덱스로 접근
                            close_series = price_df.iloc[:, 3].astype(float)
                            volume_series = price_df.iloc[:, 4].astype(float)
                            open_series = price_df.iloc[:, 0].astype(float)
                            
                            # 이동평균선(MA) 및 볼린저 밴드 계산
                            price_df['MA20'] = close_series.rolling(window=20).mean()
                            price_df['MA60'] = close_series.rolling(window=60).mean()
                            price_df['MA120'] = close_series.rolling(window=120).mean()
                            price_df['STD20'] = close_series.rolling(window=20).std()
                            price_df['Upper_BB'] = price_df['MA20'] + (price_df['STD20'] * 2)
                            price_df['Lower_BB'] = price_df['MA20'] - (price_df['STD20'] * 2)
                            
                            # 차트 출력용으로는 최근 1년 데이터만 남기기
                            price_df = price_df[price_df.index >= one_year_ago].copy()
                            close_series = price_df.iloc[:, 3].astype(float)
                            volume_series = price_df.iloc[:, 4].astype(float)
                            
                            # 한국은행 ECOS API에서 한국 M2 통화량(평잔, 원계열) 로드
                            try:
                                bok_api_key = st.secrets.get("BOK_API_KEY", "")
                                if bok_api_key and bok_api_key != "YOUR_BOK_API_KEY_HERE":
                                    start_m = (one_year_ago - datetime.timedelta(days=60)).strftime("%Y%m")
                                    end_m = end_date.strftime("%Y%m")
                                    # 101Y004 (M2 평잔) 통계코드 사용
                                    url = f"https://ecos.bok.or.kr/api/StatisticSearch/{bok_api_key}/json/kr/1/1000/101Y004/M/{start_m}/{end_m}/"
                                    r = requests.get(url)
                                    res = r.json()
                                    if 'StatisticSearch' in res:
                                        m2_data = res['StatisticSearch']['row']
                                        m_df = pd.DataFrame(m2_data)
                                        # 시간 인덱스 설정
                                        m_df['TIME'] = pd.to_datetime(m_df['TIME'], format='%Y%m')
                                        m_df.set_index('TIME', inplace=True)
                                        m_df['DATA_VALUE'] = pd.to_numeric(m_df['DATA_VALUE'])
                                        m2_series = m_df['DATA_VALUE']
                                    else:
                                        m2_series = pd.Series(dtype=float)
                                        st.sidebar.warning(f"한국 M2 데이터 조회 실패: {res.get('RESULT', {}).get('MESSAGE', '알 수 없는 오류')}")
                                else:
                                    # API 키가 없을 경우 안내를 위해 빈 시리즈 생성
                                    m2_series = pd.Series(dtype=float)
                                    st.sidebar.warning("한국은행 ECOS API 키가 설정되지 않아 M2 데이터를 가져올 수 없습니다. '.streamlit/secrets.toml'에 'BOK_API_KEY'를 추가하세요.")
                            except Exception as e:
                                m2_series = pd.Series(dtype=float)
                                st.sidebar.error(f"한국 M2 데이터 로딩 에러: {e}")
                            
                            # 주가 날짜를 기준으로 M2 데이터를 과거 방향으로 병합 (결측치 방지)
                            if not m2_series.empty:
                                # 결측치를 앞으로 채우기 (ffill)하여 일별 데이터처럼 사용할 수 있게 함
                                m_df = pd.DataFrame(m2_series, columns=["DATA_VALUE"]).sort_index()
                                m_df.rename(columns={"DATA_VALUE": "M2_KR"}, inplace=True)
                            else:
                                m_df = pd.DataFrame(columns=["M2_KR"])
                            
                            merged = pd.merge_asof(price_df, m_df, left_index=True, right_index=True, direction='backward')
                            
                            if len(merged) > 0:
                                # ---- 기술적 분석 시그널 생성 ----
                                latest = merged.iloc[-1]
                                is_bull_aligned = (latest['MA20'] > latest['MA60']) and (latest['MA60'] > latest['MA120'])
                                
                                # 거래량 급증 확인 (최근 20일 평균 거래량 대비 2배 이상 돌파 여부)
                                avg_vol_20 = volume_series.rolling(window=20).mean().iloc[-1]
                                is_vol_spike = latest.iloc[4] > (avg_vol_20 * 2) if avg_vol_20 > 0 else False
                                
                                # 시그널 UI 출력
                                st.markdown("#### 📊 기술적 분석 (Technical Indicators)")
                                t_col1, t_col2 = st.columns(2)
                                
                                if is_bull_aligned:
                                    t_col1.success("📈 **추세 (MA): 정배열 상태 유지** (단기 > 중기 > 장기 상승 추세)")
                                else:
                                    t_col1.warning("📉 **추세 (MA): 정배열 아님** (조정 또는 하락 추세 유의)")
                                    
                                if is_vol_spike:
                                    t_col2.success("🔥 **거래량: 최근 거래량 급증 포착** (20일 평균 대비 2배 이상 돌파)")
                                else:
                                    t_col2.info("📊 **거래량: 특이사항 없음** (평균적인 거래량 수준 유지 중)")
                                
                                # ---- Plotly 이중 축 차트 생성 (상단: 주가+MA+M2, 하단: 거래량) ----
                                fig = make_subplots(
                                    rows=2, cols=1, 
                                    shared_xaxes=True, 
                                    vertical_spacing=0.15, 
                                    row_heights=[0.7, 0.3],
                                    specs=[[{"secondary_y": True}], [{"secondary_y": False}]]
                                )
                                
                                # 볼린저 밴드 (상단 -> 하단 순서로 추가하여 사이를 색칠함)
                                fig.add_trace(go.Scatter(x=merged.index, y=merged['Upper_BB'], name="볼린저 상단", line=dict(color="rgba(44, 160, 44, 0.5)", width=1, dash='dot')), row=1, col=1, secondary_y=False)
                                fig.add_trace(go.Scatter(x=merged.index, y=merged['Lower_BB'], name="볼린저 하단", line=dict(color="rgba(44, 160, 44, 0.5)", width=1, dash='dot'), fill='tonexty', fillcolor="rgba(44, 160, 44, 0.1)"), row=1, col=1, secondary_y=False)

                                # 주가 및 이동평균선 (기본 Y축, 왼쪽, Row 1)
                                fig.add_trace(go.Scatter(x=merged.index, y=merged.iloc[:, 3], name="주가 (종가)", line=dict(color="#FF4B4B", width=2)), row=1, col=1, secondary_y=False)
                                fig.add_trace(go.Scatter(x=merged.index, y=merged['MA20'], name="20일선", line=dict(color="#FF8C00", width=1.5)), row=1, col=1, secondary_y=False)
                                fig.add_trace(go.Scatter(x=merged.index, y=merged['MA60'], name="60일선", line=dict(color="#2CA02C", width=1.5)), row=1, col=1, secondary_y=False)
                                fig.add_trace(go.Scatter(x=merged.index, y=merged['MA120'], name="120일선", line=dict(color="#9467BD", width=1.5)), row=1, col=1, secondary_y=False)
                                
                                # M2 통화량 (보조 Y축, 오른쪽, Row 1)
                                if "M2_KR" in merged.columns and merged["M2_KR"].notna().any():
                                    fig.add_trace(go.Scatter(x=merged.index, y=merged["M2_KR"], name="대한민국 M2 통화량", line=dict(color="#1f77b4", width=2, dash='dot')), row=1, col=1, secondary_y=True)
                                
                                # 거래량 (기본 Y축, Row 2)
                                # 종가 >= 시가 이면 빨강(상승), 아니면 파랑(하락)
                                colors = ['#FF4B4B' if c >= o else '#1f77b4' for c, o in zip(merged.iloc[:, 3], merged.iloc[:, 0])]
                                fig.add_trace(go.Bar(x=merged.index, y=merged.iloc[:, 4], name="거래량", marker_color=colors), row=2, col=1)
                                
                                fig.update_layout(
                                    title_text="주가(이동평균선), 거래량 및 M2 트렌드 분석 (최근 1년)",
                                    hovermode="x unified",
                                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                                    margin=dict(l=0, r=0, t=60, b=0),
                                    height=650
                                )
                                
                                fig.update_yaxes(title_text="<b>주가</b> (원)", secondary_y=False, showgrid=True, row=1, col=1)
                                fig.update_yaxes(showticklabels=False, title_text="", showgrid=False, secondary_y=True, row=1, col=1)
                                fig.update_yaxes(title_text="<b>거래량</b>", showgrid=False, row=2, col=1)
                                
                                st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.line_chart(close_series, use_container_width=True)
                        else:
                            st.warning("주가 차트 데이터를 가져오지 못했습니다.")
                    except Exception as e:
                        st.error(f"차트 로딩 에러: {e}")
                
                st.divider()
                
                # --- 핵심 재무 지표 영역 ---
                st.markdown("### 1. 펀더멘털 지표")
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("시가총액", f"{mkt.market_cap / 100000000:,.0f} 억원")
                col2.metric("자본총계", f"{fin.total_equity / 100000000:,.0f} 억원")
                col3.metric("영업이익", f"{fin.operating_profit / 100000000:,.0f} 억원")
                
                # 부채비율 계산 및 표시
                debt_ratio = (fin.total_debt / fin.total_equity * 100) if fin.total_equity > 0 else 0
                col4.metric("부채비율", f"{debt_ratio:.1f}%", delta="-안전" if debt_ratio < 100 else "위험", delta_color="inverse")
                
                # 수익성 지표 추가 (ROE, ROA)
                st.write("") # 간격 띄우기
                f_col1, f_col2, f_col3 = st.columns(3)
                f_col1.metric("당기순이익", f"{fin.net_income / 100000000:,.0f} 억원", delta="적자" if fin.net_income < 0 else None, delta_color="inverse")
                
                roe_color = "normal" if fin.roe > 0 else "inverse"
                f_col2.metric("ROE (자기자본이익률)", f"{fin.roe:.1f}%", delta="우수" if fin.roe >= 10 else None, delta_color=roe_color)
                f_col3.metric("ROA (총자산이익률)", f"{fin.roa:.1f}%")
                
                st.divider()
                
                # --- 가치 평가(Valuation) 영역 ---
                st.markdown("### 2. 가치 평가 (Valuation Multiples)")
                v_col1, v_col2, v_col3, v_col4 = st.columns(4)
                
                # 업종 평균 가져오기
                ind_avg = get_industry_averages(ticker, profile.sector)
                
                # 차이 계산 (낮을수록 저평가이므로 delta_color="inverse" 적용)
                per_diff = mkt.per - ind_avg['PER']
                pbr_diff = mkt.pbr - ind_avg['PBR']
                
                per_display = f"{mkt.per:.2f}배" if mkt.per > 0 else "N/A (적자 등)"
                pbr_display = f"{mkt.pbr:.2f}배" if mkt.pbr > 0 else "N/A"
                
                v_col1.metric("PER (이익 대비)", per_display, 
                              delta=f"업종평균({ind_avg['PER']:.1f}) 대비 {per_diff:+.2f}배" if mkt.per > 0 else None, delta_color="inverse")
                v_col2.metric("PBR (자본 대비)", pbr_display, 
                              delta=f"업종평균({ind_avg['PBR']:.1f}) 대비 {pbr_diff:+.2f}배" if mkt.pbr > 0 else None, delta_color="inverse")
                v_col3.metric("PSR (매출 대비)", f"{mkt.psr:.2f}배" if mkt.psr > 0 else "N/A")
                
                div_display = f"{mkt.dividend_yield:.2f}%" if mkt.dividend_yield > 0 else "N/A"
                v_col4.metric("배당수익률", div_display, delta="매력적" if mkt.dividend_yield >= 3.0 else None, delta_color="normal")
                
                # 시각적 가이드 박스
                st.info("💡 **가치투자 체크리스트**: ROE가 10% 이상이면 자본효율이 뛰어나며, 배당수익률이 높을수록 방어적 투자가 가능합니다.")
                
                st.divider()
                
                # --- 뉴스 및 AI 요약 영역 ---
                st.markdown("### 3. 시장 동향 및 AI 요약")
                
                with st.spinner("최신 뉴스 수집 및 AI 요약 생성 중..."):
                    kr_news = fetch_news(query=company_name, is_global=False, max_results=3)
                    en_news = fetch_news(query="Samsung Electronics" if company_name=="삼성전자" else company_name, is_global=True, max_results=3)
                    all_news = kr_news + en_news
                    
                    ai_summary_text = summarize_news(all_news, company_name)
                    
                # AI 요약 결과 출력
                st.success("🤖 **Gemini AI 3줄 요약**")
                st.markdown(ai_summary_text)
                
                # 뉴스 리스트를 아코디언(Expander)으로 제공
                with st.expander("📰 수집된 전체 뉴스 헤드라인 보기"):
                    st.markdown("#### 국내 뉴스")
                    for news in kr_news:
                        st.markdown(f"- [{news['title']}]({news['link']})")
                    st.markdown("#### 글로벌 뉴스")
                    for news in en_news:
                        st.markdown(f"- [{news['title']}]({news['link']})")
                        
            else:
                st.error("데이터를 불러오지 못했습니다. 종목코드와 DART 고유번호를 다시 확인해주세요.")
                
        except Exception as e:
            st.error(f"분석 중 오류가 발생했습니다: {e}")
