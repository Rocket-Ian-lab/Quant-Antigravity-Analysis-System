import requests
from bs4 import BeautifulSoup

def get_stock_sector(ticker: str) -> str:
    """
    네이버 금융 종목 홈 페이지에서 해당 종목이 속한 세부 업종(WICS 기준 등)을 크롤링합니다.
    예: 삼성전자의 경우 "반도체와반도체장비" 등을 가져옵니다.
    
    :param ticker: 종목코드 (예: '005930')
    """
    url = f"https://finance.naver.com/item/main.naver?code={ticker}"
    
    # 네이버 금융은 봇(Bot) 접근을 막는 경우가 있으므로, 일반 브라우저인 척 헤더를 추가합니다.
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status() # 웹페이지를 정상적으로 못 가져오면 에러를 냅니다.
        
        soup = BeautifulSoup(response.text, 'lxml')
        
        # 네이버 금융 메인 페이지에서 우측 '동일업종' 섹션의 타이틀을 찾습니다.
        # 동일업종비교 테이블의 th 태그나 h4 태그 주변을 탐색합니다.
        # 가장 쉬운 방법은 <table class="type2"> 바로 위의 <h4 class="h_sub sub_tit7"> 부분에서 업종명을 찾는 것입니다.
        # html 구조 변경 시 깨질 수 있습니다.
        
        # 1. 동일업종명 크롤링 시도
        upjong_elem = soup.select_one('.trade_compare h4.h_sub')
        if upjong_elem:
            # "동일업종 비교" 부분을 파싱 (예: h4 태그 안에 텍스트와 a 태그가 섞여 있음)
            a_tag = upjong_elem.select_one('a')
            if a_tag:
                return a_tag.text.strip()
                
        return "업종 정보 없음"
        
    except Exception as e:
        print(f"[업종 크롤링 에러] 업종 정보를 가져올 수 없습니다: {e}")
        return "업종 파악 불가"
