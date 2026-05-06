from dataclasses import dataclass
from typing import List, Optional

# @dataclass는 클래스(데이터를 담는 틀)를 쉽게 만들 수 있게 해주는 파이썬의 기능입니다.
# 변수 이름과 타입만 적어주면 내부적으로 초기화(init) 등의 코드를 자동 생성해줍니다.

@dataclass
class FinancialStatement:
    """연도별 재무제표 핵심 항목 (위험 관리용 데이터 모델)"""
    year: int                   # 연도 (예: 2023)
    total_assets: float         # 자산총계 (회사가 가진 모든 자산)
    total_equity: float         # 자본총계 (순수한 회사의 돈)
    total_debt: float           # 부채총계 (갚아야 할 빚)
    current_assets: float       # 유동자산 (1년 안에 현금화할 수 있는 자산)
    current_liabilities: float  # 유동부채 (1년 안에 갚아야 할 빚)
    operating_profit: float     # 영업이익 (회사가 주된 영업활동으로 번 돈)
    net_income: float           # 당기순이익 (세금 등을 모두 빼고 최종적으로 남은 돈)
    sales: float                # 매출액 (상품을 팔고 받은 총액)

    @property
    def roe(self) -> float:
        """자기자본이익률 (ROE, %)"""
        if self.total_equity <= 0: return 0.0
        return (self.net_income / self.total_equity) * 100

    @property
    def roa(self) -> float:
        """총자산이익률 (ROA, %)"""
        if self.total_assets <= 0: return 0.0
        return (self.net_income / self.total_assets) * 100

@dataclass
class MarketData:
    """시장 가치 및 멀티플 (가치 평가용 데이터 모델)"""
    date: str                   # 기준 일자
    price: float                # 현재 주가
    market_cap: float           # 시가총액 (주가 x 발행주식수, 회사의 전체 시장 가치)
    per: float                  # 주가수익비율 (주가가 1주당 순이익의 몇 배인가?)
    pbr: float                  # 주가순자산비율 (주가가 1주당 순자산의 몇 배인가?)
    psr: float                  # 주가매출비율 (주가가 1주당 매출액의 몇 배인가?)
    dividend_yield: float = 0.0 # 배당수익률 (%)
    sector_per: Optional[float] = None  # 속한 업종(섹터)의 평균 PER
    sector_pbr: Optional[float] = None  # 속한 업종(섹터)의 평균 PBR

@dataclass
class CompanyProfile:
    """단일 종목의 종합 데이터 모델 (재무제표 + 시장가치)"""
    ticker: str                 # 종목코드 (예: 삼성전자는 '005930')
    company_name: str           # 기업명
    sector: str                 # 섹터/업종 (예: '반도체')
    financials: List[FinancialStatement]  # 최근 몇 년간의 재무제표 리스트
    market_data: Optional[MarketData] = None  # 최신 주가 및 멀티플 데이터

    # @property는 메서드(함수)를 변수처럼 사용할 수 있게 해줍니다. 
    # 즉, profile.latest_debt_ratio 와 같이 괄호 없이 값을 가져올 수 있습니다.

    @property
    def latest_debt_ratio(self) -> float:
        """가장 최근의 부채비율 (%)를 계산합니다. (부채총계 / 자본총계)"""
        if not self.financials:
            return float('inf') # 재무데이터가 없으면 부채비율을 무한대로 처리
        
        latest = self.financials[-1] # 리스트의 마지막 요소(최근 연도)
        if latest.total_equity <= 0:
            return float('inf') # 자본잠식(자본이 0 이하)인 경우 무한대로 처리
            
        return (latest.total_debt / latest.total_equity) * 100

    @property
    def latest_current_ratio(self) -> float:
        """가장 최근의 유동비율 (%)를 계산합니다. (유동자산 / 유동부채)"""
        if not self.financials:
            return 0
            
        latest = self.financials[-1]
        if latest.current_liabilities <= 0:
            return 0 # 유동부채가 없는 예외적인 경우
            
        return (latest.current_assets / latest.current_liabilities) * 100

    @property
    def is_consecutive_profit(self) -> bool:
        """최근 3년 연속 영업이익이 흑자(0보다 큰가)인지 확인합니다."""
        if len(self.financials) < 3:
            return False # 3년치 데이터가 안 모였으면 False
            
        # [-3:]은 리스트에서 뒤에서부터 3개의 요소를 가져온다는 뜻입니다.
        recent_3_years = self.financials[-3:]
        
        # all() 함수는 리스트 안의 모든 조건이 True일 때만 True를 반환합니다.
        return all(f.operating_profit > 0 for f in recent_3_years)
