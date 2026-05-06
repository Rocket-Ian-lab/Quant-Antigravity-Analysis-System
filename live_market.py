import requests
from bs4 import BeautifulSoup
import pandas as pd

def get_top_10_gainers() -> pd.DataFrame:
    """
    네이버 금융의 상승 종목 페이지를 크롤링하여
    실시간 주가 상승률 상위 10개 기업의 데이터를 가져옵니다.
    """
    url = "https://finance.naver.com/sise/sise_rise.naver"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        response.encoding = 'euc-kr' # 네이버 금융 인코딩 대응
        
        soup = BeautifulSoup(response.text, 'lxml')
        
        # 상승 종목 테이블에서 각 행(tr)을 가져옵니다. (tbody 명시 시 파싱 실패할 수 있음)
        rows = soup.select('table.type_2 tr')
        
        data = []
        for row in rows:
            cols = row.select('td')
            # 정상적인 데이터 행은 여러 개의 td를 포함합니다.
            if len(cols) >= 10:
                name_tag = cols[1].select_one('.tltle')
                if name_tag:
                    name = name_tag.text.strip()
                    price = cols[2].text.strip()
                    change_rate = cols[4].text.strip()
                    
                    data.append({
                        "종목명": name,
                        "현재가": price,
                        "등락률": change_rate
                    })
                    
            if len(data) == 10:
                break
                
        return pd.DataFrame(data)
        
    except Exception as e:
        print(f"실시간 데이터 크롤링 에러: {e}")
        return pd.DataFrame()
