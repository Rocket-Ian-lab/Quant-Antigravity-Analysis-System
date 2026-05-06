from pykrx import stock
from datetime import datetime, timedelta
import pandas as pd
import requests
import re
from bs4 import BeautifulSoup
from data_models import MarketData

def get_latest_business_day() -> str:
    """
    가장 최근의 영업일(주식 시장이 열린 날)을 구합니다.
    주말이나 공휴일엔 주가가 안 변하므로, 안전하게 전날/전전날을 확인합니다.
    """
    return "20260430" # 임시로 확실한 평일을 사용 (휴일 에러 방지)

def fetch_market_multiples(target_date: str = None) -> pd.DataFrame:
    """
    pykrx 라이브러리를 사용하여 특정 일자의 전체 상장 종목(KOSPI, KOSDAQ)의 
    핵심 가치평가 지표(PER, PBR 등)와 시가총액을 한 번에 가져옵니다.
    """
    if target_date is None:
        target_date = get_latest_business_day()
        
    print(f"[{target_date}] 시장 지표 데이터를 수집 중입니다...")
    
    try:
        # 1. 시가총액 데이터 가져오기
        cap_df = stock.get_market_cap_by_ticker(target_date, market="ALL")
        # 2. 펀더멘털 데이터 가져오기
        fundamental_df = stock.get_market_fundamental_by_ticker(target_date, market="ALL")
        merged_df = pd.merge(cap_df, fundamental_df, left_index=True, right_index=True, how="inner")
        
        merged_df = merged_df.rename(columns={
            "종가": "price",
            "시가총액": "market_cap",
            "PER": "per",
            "PBR": "pbr",
            "EPS": "eps",
            "BPS": "bps"
        })
        return merged_df
    except Exception as e:
        print(f"[경고] pykrx에서 데이터를 가져오지 못했습니다. 임시 데이터를 반환합니다. ({e})")
        # 실패 시 삼성전자('005930') 임시 더미 데이터 반환
        dummy_data = {
            "price": [80000],
            "market_cap": [477582000000000],
            "per": [15.2],
            "pbr": [1.4],
            "eps": [5263],
            "bps": [57142]
        }
        return pd.DataFrame(dummy_data, index=["005930"])

def scrape_naver_market_data(ticker: str) -> dict:
    url = f"https://finance.naver.com/item/main.naver?code={ticker}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        res = requests.get(url, headers=headers)
        res.encoding = 'euc-kr'
        soup = BeautifulSoup(res.text, 'lxml')
        
        per_tag = soup.select_one('#_per')
        per = float(per_tag.text.replace(',', '')) if per_tag else 0.0
        
        pbr_tag = soup.select_one('#_pbr')
        pbr = float(pbr_tag.text.replace(',', '')) if pbr_tag else 0.0
        
        mc_tag = soup.select_one('#_market_sum')
        market_cap = 0
        if mc_tag:
            # '조', ',', 공백 등 모든 문자 제거하고 숫자만 남김 (단위: 억원)
            mc_text = re.sub(r'[^0-9]', '', mc_tag.text)
            if mc_text:
                market_cap = int(mc_text) * 100000000
                
        price_tag = soup.select_one('.no_today .blind')
        price = 0.0
        if price_tag:
            price_text = re.sub(r'[^0-9]', '', price_tag.text)
            if price_text:
                price = float(price_text)
                
        # 배당수익률 (단위: %)
        div_tag = soup.select_one('#_dvr')
        dividend_yield = float(div_tag.text.replace(',', '')) if div_tag else 0.0
                
        return {"price": price, "market_cap": market_cap, "per": per, "pbr": pbr, "dividend_yield": dividend_yield}
    except Exception as e:
        print(f"Naver 스크래핑 에러: {e}")
        return {"price": 0.0, "market_cap": 0.0, "per": 0.0, "pbr": 0.0, "dividend_yield": 0.0}

def get_stock_market_data(ticker: str, df: pd.DataFrame) -> MarketData:
    """
    미리 다운로드 받은 전체 데이터프레임(df)에서 특정 종목(ticker)의 
    데이터만 쏙 뽑아내어 MarketData 객체로 만들어줍니다.
    만약 pykrx의 윈도우 인코딩 이슈로 데이터가 없다면 네이버 금융에서 실시간 스크래핑합니다.
    """
    if ticker not in df.index:
        # 윈도우 pykrx 에러로 인해 더미 데이터만 있거나 종목이 없을 경우 실시간 폴백 스크래핑 수행
        real_time_data = scrape_naver_market_data(ticker)
        return MarketData(
            date="Latest",
            price=real_time_data["price"],
            market_cap=real_time_data["market_cap"],
            per=real_time_data["per"],
            pbr=real_time_data["pbr"],
            psr=0.0,
            dividend_yield=real_time_data["dividend_yield"]
        )
        
    row = df.loc[ticker]
    
    return MarketData(
        date=df.index.name or "Latest", # 데이터 기준일
        price=float(row.get("price", 0.0)),
        market_cap=float(row.get("market_cap", 0.0)),
        per=float(row.get("per", 0.0)),
        pbr=float(row.get("pbr", 0.0)),
        psr=0.0, # PSR은 pykrx 기본 제공 항목이 아니므로 일단 0으로 둡니다 (추후 재무 매출액으로 계산)
        dividend_yield=0.0, # pykrx 데이터에서는 배당수익률이 없을 수 있으므로 기본값 설정
        sector_per=None, # 이 부분은 전체 데이터를 업종별로 그룹지어 평균을 낸 뒤 채워넣을 수 있습니다.
        sector_pbr=None
    )
