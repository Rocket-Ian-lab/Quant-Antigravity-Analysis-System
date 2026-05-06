import urllib.request
import xml.etree.ElementTree as ET
from typing import List, Dict

def fetch_news(query: str, is_global: bool = False, max_results: int = 5) -> List[Dict[str, str]]:
    """
    Google News RSS를 활용하여 특정 키워드(query)에 대한 최신 뉴스를 가져옵니다.
    별도의 가입이나 API 키 발급이 필요 없는 완전 무료/공개 방식입니다.
    
    :param query: 검색어 (예: "삼성전자" 또는 "Samsung Electronics")
    :param is_global: True면 미국/영어권 뉴스, False면 한국/한국어 뉴스
    :param max_results: 가져올 최대 뉴스 개수
    """
    # 띄어쓰기 등 특수문자를 URL 형식에 맞게 변환합니다.
    encoded_query = urllib.parse.quote(query)
    
    if is_global:
        # 글로벌 (영어) 뉴스 설정
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    else:
        # 한국 (한국어) 뉴스 설정
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ko&gl=KR&ceid=KR:ko"
        
    try:
        # 브라우저인 것처럼 속여서(User-Agent) 구글 서버의 차단을 막습니다.
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
            
        # XML 데이터를 파이썬이 다루기 쉬운 형태로 파싱(해석)합니다.
        root = ET.fromstring(xml_data)
        
        news_list = []
        # <item> 태그 안에 개별 기사 정보가 들어있습니다.
        for item in root.findall('.//item')[:max_results]:
            title = item.find('title').text if item.find('title') is not None else ""
            link = item.find('link').text if item.find('link') is not None else ""
            pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
            
            # description(요약)은 HTML 태그가 섞여있을 수 있어, 정제가 필요할 수 있습니다.
            description = item.find('description').text if item.find('description') is not None else ""
            
            news_list.append({
                "title": title,
                "link": link,
                "pub_date": pub_date,
                "description": description
            })
            
        return news_list
        
    except Exception as e:
        print(f"[뉴스 API 에러] 뉴스를 가져오는 데 실패했습니다: {e}")
        return []
