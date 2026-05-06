import os
import requests
import zipfile
import io
import xml.etree.ElementTree as ET
import streamlit as st

try:
    DART_API_KEY = st.secrets["DART_API_KEY"]
except (FileNotFoundError, KeyError):
    DART_API_KEY = os.environ.get("DART_API_KEY", "")
@st.cache_data(show_spinner=False)
def load_corp_mapping() -> dict:
    """
    OpenDART의 고유번호 ZIP 파일을 다운로드하여 파싱하고,
    '기업명'을 키(Key)로, '종목코드'와 '고유번호'를 값(Value)으로 갖는 딕셔너리를 생성합니다.
    (Streamlit 캐싱을 사용하여 최초 1회만 다운로드/실행됩니다.)
    """
    url = "https://opendart.fss.or.kr/api/corpCode.xml"
    params = {"crtfc_key": DART_API_KEY}
    
    mapping = {}
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        # 다운로드 받은 ZIP 파일 메모리에서 바로 압축 해제
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            with z.open('CORPCODE.xml') as f:
                tree = ET.parse(f)
                root = tree.getroot()
                
                for list_tag in root.findall('list'):
                    corp_name = list_tag.find('corp_name').text
                    corp_code = list_tag.find('corp_code').text
                    stock_code = list_tag.find('stock_code').text
                    
                    # stock_code가 있는 상장사만 매핑에 포함합니다. (공백이 아닌 경우)
                    if stock_code and stock_code.strip():
                        # 주식 시장에는 동일 이름의 기업이 드물지만, 최신 정보 덮어쓰기
                        mapping[corp_name.strip()] = {
                            "corp_code": corp_code.strip(),
                            "ticker": stock_code.strip()
                        }
    except Exception as e:
        print(f"고유번호 매핑 데이터 로드 중 에러: {e}")
        
    return mapping

def get_codes_by_name(corp_name: str, mapping: dict):
    """이름으로 종목코드와 고유번호를 반환합니다."""
    return mapping.get(corp_name, None)
