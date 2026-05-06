import google.generativeai as genai
from typing import List, Dict

import os
import streamlit as st

# 사용자님의 Gemini API 키를 여기에 입력하세요.
# (구글 AI Studio에서 무료로 발급받으실 수 있습니다: https://aistudio.google.com/)
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except (FileNotFoundError, KeyError):
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

def summarize_news(news_list: List[Dict[str, str]], company_name: str) -> str:
    """
    가져온 뉴스 기사 제목들을 바탕으로 Gemini AI가 3줄 요약을 작성합니다.
    
    :param news_list: news_api에서 가져온 뉴스 딕셔너리 리스트
    :param company_name: 분석 대상 기업명
    """
    if not news_list:
        return "관련 뉴스가 없습니다."
        
    if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
        # API 키가 설정되지 않은 경우, 단순히 뉴스 제목만 나열해서 보여줍니다.
        summary = "[AI 요약 불가: Gemini API 키가 설정되지 않았습니다.]\n"
        for i, news in enumerate(news_list):
            summary += f"{i+1}. {news['title']}\n"
        return summary

    try:
        # Gemini API 설정
        genai.configure(api_key=GEMINI_API_KEY)
        # 최신 텍스트 모델인 gemini-pro (또는 gemini-1.5-pro)를 사용합니다.
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # AI에게 지시할 프롬프트(명령어)를 작성합니다.
        prompt = f"다음은 '{company_name}'에 대한 최신 뉴스 헤드라인들입니다:\n\n"
        for i, news in enumerate(news_list):
            prompt += f"- {news['title']}\n"
            
        prompt += f"\n이 뉴스들을 종합하여, 현재 이 기업을 둘러싼 가장 중요한 핵심 상황을 딱 3줄로 요약해주세요. (마크다운의 불릿 포인트 '-' 를 사용하세요)"
        
        # AI 모델에 텍스트 생성을 요청합니다.
        response = model.generate_content(prompt)
        
        return response.text
        
    except Exception as e:
        return f"[AI 요약 실패] 에러가 발생했습니다: {e}"
