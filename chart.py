import matplotlib.pyplot as plt
from pykrx import stock
from datetime import datetime, timedelta
import pandas as pd

def plot_bollinger_bands(ticker: str, company_name: str, days: int = 250):
    """
    특정 종목의 최근 주가 데이터를 불러와 20일 이동평균선과 볼린저 밴드를 그립니다.
    """
    # 한글 폰트 설정
    plt.rcParams['font.family'] = 'Malgun Gothic'
    plt.rcParams['axes.unicode_minus'] = False
    
    end_date = datetime.today()
    start_date = end_date - timedelta(days=days)
    
    start_str = start_date.strftime("%Y%m%d")
    end_str = end_date.strftime("%Y%m%d")
    
    try:
        # 주가 데이터 가져오기 (시가, 고가, 저가, 종가, 거래량 등)
        df = stock.get_market_ohlcv(start_str, end_str, ticker)
        
        if df is None or df.empty:
            print(f"[경고] {company_name}의 주가 데이터를 가져오지 못했습니다.")
            return

        # 볼린저 밴드 계산
        # 1. 20일 이동평균선 (중심선)
        df['MA20'] = df['종가'].rolling(window=20).mean()
        
        # 2. 20일 표준편차
        df['STD'] = df['종가'].rolling(window=20).std()
        
        # 3. 상단 밴드 및 하단 밴드 계산 (이동평균 +- 2 * 표준편차)
        df['Upper'] = df['MA20'] + (df['STD'] * 2)
        df['Lower'] = df['MA20'] - (df['STD'] * 2)

        # 차트 그리기
        plt.figure(figsize=(12, 6))
        
        # 종가 라인
        plt.plot(df.index, df['종가'], label='종가', color='blue', linewidth=1.5)
        
        # 20일 이동평균선
        plt.plot(df.index, df['MA20'], label='20일 이동평균(MA20)', color='red', linestyle='--', linewidth=1.5)
        
        # 상/하단 밴드
        plt.plot(df.index, df['Upper'], label='볼린저 밴드 상단', color='green', linestyle=':', linewidth=1)
        plt.plot(df.index, df['Lower'], label='볼린저 밴드 하단', color='green', linestyle=':', linewidth=1)
        
        # 밴드 사이 색칠
        plt.fill_between(df.index, df['Lower'], df['Upper'], color='green', alpha=0.1)
        
        plt.title(f"{company_name} ({ticker}) - 주가 추이 및 볼린저 밴드 (20일)", fontsize=16, fontweight='bold')
        plt.xlabel('날짜', fontsize=12)
        plt.ylabel('주가 (원)', fontsize=12)
        plt.legend(loc='best', fontsize=10)
        plt.grid(True, alpha=0.3, linestyle='--')
        plt.tight_layout()
        
        # 화면에 출력
        plt.show()
        print(f"[완료] {company_name} 주가 차트 렌더링 성공.")
        
    except Exception as e:
        print(f"[오류] 차트를 생성하는 중 문제가 발생했습니다: {e}")
