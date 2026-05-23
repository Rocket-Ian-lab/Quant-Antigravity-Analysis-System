import pandas as pd
from data_models import FinancialStatement, CompanyProfile
from dart_api import fetch_financial_statement, extract_account_value
from valuation import fetch_market_multiples, get_stock_market_data
from theme_scraper import get_stock_sector
from news_api import fetch_news
from ai_summary import summarize_news
from chart import plot_bollinger_bands

def analyze_company(ticker: str, corp_code: str, company_name: str, target_year: int = 2023):
    print(f"\n[{company_name}] 기업 분석을 시작합니다...")
    
    # 1. OpenDART에서 재무제표 가져오기
    print("1. OpenDART API에서 재무제표 데이터를 가져오는 중...")
    accounts_data = fetch_financial_statement(corp_code, target_year, fs_div="CFS")
    
    if not accounts_data:
        accounts_data = fetch_financial_statement(corp_code, target_year, fs_div="OFS")
        
    if not accounts_data:
        print(f"[실패] {company_name}의 재무 데이터를 가져오지 못했습니다.")
        return None

    # 2. 필요한 핵심 재무 지표 추출
    kw_assets = ['자산총계', '총자산', '자산 합계']
    kw_equity = ['자본총계', '자본 합계']
    kw_debt = ['부채총계', '부채 합계']
    kw_cur_assets = ['유동자산']
    kw_cur_liab = ['유동부채']
    kw_op_profit = ['영업이익', '영업이익(손실)', '영업손익']
    kw_net_income = ['당기순이익', '당기순이익(손실)']
    kw_sales = ['매출액', '수익(매출액)', '영업수익', '매출']

    fin_state = FinancialStatement(
        year=target_year,
        total_assets=extract_account_value(accounts_data, kw_assets),
        total_equity=extract_account_value(accounts_data, kw_equity),
        total_debt=extract_account_value(accounts_data, kw_debt),
        current_assets=extract_account_value(accounts_data, kw_cur_assets),
        current_liabilities=extract_account_value(accounts_data, kw_cur_liab),
        operating_profit=extract_account_value(accounts_data, kw_op_profit),
        net_income=extract_account_value(accounts_data, kw_net_income),
        sales=extract_account_value(accounts_data, kw_sales)
    )

    # 3. pykrx 라이브러리로 주식 시장 데이터 가져오기
    print("2. 주식 시장(KRX) 밸류에이션 데이터를 가져오는 중...")
    market_df = fetch_market_multiples() 
    market_data = get_stock_market_data(ticker, market_df)

    if fin_state.sales > 0 and market_data.market_cap > 0:
        market_data.psr = market_data.market_cap / fin_state.sales

    # 4. 네이버 주식 테마(섹터) 데이터 크롤링
    print("3. 네이버 금융에서 세부 테마/섹터 정보를 가져오는 중...")
    sector = get_stock_sector(ticker)

    # 최종 종합 프로필 완성
    profile = CompanyProfile(
        ticker=ticker,
        company_name=company_name,
        sector=sector,
        financials=[fin_state],
        market_data=market_data
    )
    
    return profile

def run_pipeline():
    company_name = "삼성전자"
    ticker = "005930"
    corp_code = "00126380"

    target_company = analyze_company(ticker=ticker, corp_code=corp_code, company_name=company_name)
    
    if target_company:
        print("\n" + "="*60)
        print(f"[Phase 2 분석 결과] {target_company.company_name} ({target_company.ticker})")
        print("="*60)
        print(f"- 세부 섹터/테마: {target_company.sector}")
        print(f"- 최근 연도: {target_company.financials[-1].year}년")
        print(f"- 자본총계: {target_company.financials[-1].total_equity:,.0f} 원")
        print(f"- 부채총계: {target_company.financials[-1].total_debt:,.0f} 원")
        print(f"- 영업이익: {target_company.financials[-1].operating_profit:,.0f} 원")
        
        print("-"*60)
        print("[가치 평가 지표 (Valuation)]")
        print(f"- 현재 주가: {target_company.market_data.price:,.0f} 원")
        print(f"- 시가총액: {target_company.market_data.market_cap:,.0f} 원")
        print(f"- PER (이익 대비 저평가 여부): {target_company.market_data.per:.2f}배")
        print(f"- PBR (자산 대비 저평가 여부): {target_company.market_data.pbr:.2f}배")
        print(f"- PSR (매출 대비 저평가 여부): {target_company.market_data.psr:.2f}배")
        
        print("-"*60)
        print(f"[{company_name} 최신 뉴스 및 AI 요약 (로딩 중...)]")
        # 한국 뉴스 & 글로벌 뉴스 모두 가져오기
        kr_news = fetch_news(query=company_name, is_global=False, max_results=3)
        en_news = fetch_news(query="Samsung Electronics", is_global=True, max_results=3)
        all_news = kr_news + en_news
        
        # AI로 3줄 요약 (Gemini API 키가 설정되지 않았다면 뉴스 제목만 출력됩니다)
        ai_summary_text = summarize_news(all_news, company_name)
        
        print(ai_summary_text)
        print("="*60)
        
        print(f"[{company_name} 주가 차트 (볼린저 밴드) 생성 중...]")
        plot_bollinger_bands(ticker, company_name)
        print("="*60)

if __name__ == "__main__":
    run_pipeline()
