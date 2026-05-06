import pandas as pd
import FinanceDataReader as fdr
from valuation import fetch_market_multiples

def get_industry_averages(target_ticker: str, sector_name: str = "") -> dict:
    """
    특정 종목이 속한 산업군의 평균 PER, PBR을 계산합니다.
    (로컬 환경의 pykrx 에러로 인해 더미 데이터가 반환될 경우를 대비한 안전장치 포함)
    """
    try:
        desc_df = fdr.StockListing('KRX-DESC')
        
        company_row = desc_df[desc_df['Code'] == target_ticker]
        if company_row.empty:
            return _get_fallback_averages(sector_name)
            
        target_sector = company_row.iloc[0]['Sector']
        if pd.isna(target_sector):
            return _get_fallback_averages(sector_name)
            
        peer_tickers = desc_df[desc_df['Sector'] == target_sector]['Code'].tolist()
        fundamentals_df = fetch_market_multiples()
        
        peers_fundamental = fundamentals_df[fundamentals_df.index.isin(peer_tickers)]
        
        valid_per = peers_fundamental[peers_fundamental['PER'] > 0]['PER']
        valid_pbr = peers_fundamental[peers_fundamental['PBR'] > 0]['PBR']
        
        if valid_per.empty or len(valid_per) < 2:
            return _get_fallback_averages(sector_name)
            
        return {
            "PER": valid_per.mean(),
            "PBR": valid_pbr.mean()
        }
    except Exception:
        return _get_fallback_averages(sector_name)

def _get_fallback_averages(sector_name: str) -> dict:
    """pykrx 데이터 수집 실패 시 UI 시연을 위한 업종 평균 기본값"""
    if "반도체" in sector_name:
        return {"PER": 18.5, "PBR": 1.8}
    elif "자동차" in sector_name:
        return {"PER": 8.5, "PBR": 0.9}
    elif "바이오" in sector_name or "의약" in sector_name:
        return {"PER": 45.0, "PBR": 4.5}
    return {"PER": 15.0, "PBR": 1.2}
