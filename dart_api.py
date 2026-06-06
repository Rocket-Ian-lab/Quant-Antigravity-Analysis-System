import requests
from typing import Optional, List, Dict, Any

import os
import streamlit as st

# 발급받으신 OpenDART API 키를 여기에 입력합니다.
try:
    DART_API_KEY = st.secrets["DART_API_KEY"]
except (FileNotFoundError, KeyError):
    DART_API_KEY = os.environ.get("DART_API_KEY", "")
def get_corp_code_by_name(corp_name: str) -> Optional[str]:
    """
    (참고용) 기업명으로 고유번호(corp_code)를 찾는 함수가 필요할 수 있습니다.
    실제 OpenDART에서는 전체 기업 고유번호 XML 파일을 다운받아 파싱해야 합니다.
    여기서는 편의상 미리 알고 있는 고유번호를 직접 사용하도록 예시로 둡니다.
    """
    pass

def fetch_financial_statement(corp_code: str, year: int, reprt_code: str = "11011", fs_div: str = "CFS") -> Optional[List[Dict[str, Any]]]:
    """
    OpenDART API를 통해 특정 기업의 단일연도 혹은 분기/반기 전체 재무제표를 가져옵니다.
    
    :param corp_code: 기업 고유번호 (8자리 숫자, 예: 삼성전자 '00126380')
    :param year: 사업연도 (예: 2023)
    :param reprt_code: 보고서 코드 ('11011'=사업, '11013'=1분기, '11012'=반기, '11014'=3분기)
    :param fs_div: 'CFS'(연결재무제표) 또는 'OFS'(별도재무제표)
    """
    url = "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json"
    
    # 요청에 필요한 파라미터(설정값)들을 딕셔너리로 만듭니다.
    params = {
        "crtfc_key": DART_API_KEY,  # API 키
        "corp_code": corp_code,     # 기업 고유번호
        "bsns_year": str(year),     # 사업연도
        "reprt_code": reprt_code,   # 보고서 코드
        "fs_div": fs_div            # 재무제표 종류
    }
    
    try:
        # 파이썬의 requests 라이브러리를 사용해 API 서버에 데이터를 달라고 요청합니다.
        response = requests.get(url, params=params)
        
        # 서버에서 받은 응답(JSON 포맷)을 파이썬의 딕셔너리 형태로 바꿉니다.
        data = response.json()
        
        # 'status' 코드가 '000'이면 성공적으로 데이터를 가져온 것입니다.
        if data.get("status") == "000" and "list" in data:
            return data["list"]
        else:
            print(f"[경고] 데이터를 가져올 수 없습니다. (연도: {year}, 코드: {corp_code}) / 메시지: {data.get('message')}")
            return None
            
    except Exception as e:
        print(f"[오류] API 호출 중 문제가 발생했습니다: {e}")
        return None

def extract_account_value(account_list: List[Dict], keywords: List[str]) -> float:
    """
    OpenDART 재무제표 리스트에서 특정 계정과목(예: 매출액)의 금액을 찾아냅니다.
    
    :param account_list: OpenDART에서 받아온 재무제표 데이터 리스트
    :param keywords: 찾고 싶은 계정과목 이름(키워드)들
    """
    for item in account_list:
        account_name = item.get("account_nm", "").replace(" ", "") # 띄어쓰기를 모두 없앱니다
        
        # 키워드 중 하나라도 계정과목 이름에 포함되어 있다면
        for kw in keywords:
            if kw.replace(" ", "") in account_name:
                # 당기 금액(thstrm_amount)을 가져옵니다.
                amount_str = item.get("thstrm_amount", "")
                if amount_str:
                    # 숫자에 쉼표(,)가 있으면 없애고 float(실수형)로 변환합니다.
                    return float(amount_str.replace(",", ""))
    
    return 0.0 # 못 찾으면 0 반환
