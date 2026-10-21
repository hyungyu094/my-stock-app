import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import json
import os

# 페이지 설정 (모바일 최적화)
st.set_page_config(
    page_title="망고의 롤댄스 주식",
    page_icon="📈",
    layout="wide"
    layout="centered",
    initial_sidebar_state="expanded"
)
# 한글 폰트 설정
plt.rc('font', family='Malgun Gothic')
plt.rc('axes', unicode_minus=False)

# 기본 추천 관심 종목
STOCKS = {
    "아이온큐 (IONQ)": "IONQ",
    "리게티 컴퓨팅 (RGTI)": "RGTI",
    "KORU (한국 3배 레버리지)": "KORU",
    "SOXL (반도체 3배 레버리지)": "SOXL",
    "SOXX (반도체 ETF)": "SOXX",
    "SK하이닉스": "000660.KS",
    "삼성전자": "005930.KS",
    "두산로보틱스": "454910.KS"
}

US_KO_MAPPING = {
    "테슬라": "TSLA", "엔비디아": "NVDA", "애플": "AAPL", "마이크로소프트": "MSFT",
    "아마존": "AMZN", "구글": "GOOGL", "알파벳": "GOOGL", "메타": "META",
    "페이스북": "META", "넷플릭스": "NFLX", "아이온큐": "IONQ", "리게티": "RGTI",
    "팔란티어": "PLTR", "코인베이스": "COIN", "초마이크로": "SMCI", "슈퍼마이크로": "SMCI",
    "AMD": "AMD", "인텔": "INTC", "ARM": "ARM", "브로드컴": "AVGO", "소니": "SONY"
}

FAV_FILE = "favorites.json"

def load_favorites():
    if os.path.exists(FAV_FILE):
        try:
            with open(FAV_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_favorites(favs):
    try:
        with open(FAV_FILE, "w", encoding="utf-8") as f:
            json.dump(favs, f, ensure_ascii=False, indent=4)
    except:
        pass

if 'favorites' not in st.session_state:
    st.session_state['favorites'] = load_favorites()

def resolve_ticker(user_input):
    user_input = user_input.strip()
    if not user_input:
        return None, None
    if user_input in STOCKS:
        return STOCKS[user_input], user_input
    if user_input in st.session_state['favorites']:
        return st.session_state['favorites'][user_input], user_input
    if user_input in US_KO_MAPPING:
        ticker = US_KO_MAPPING[user_input]
        return ticker, f"{user_input} ({ticker})"
    if user_input.isdigit() and len(user_input) == 6:
        return f"{user_input}.KS", f"한국주식({user_input})"
    if user_input.isalpha() and user_input.isascii():
        return user_input.upper(), user_input.upper()
    
    # 네이버 금융 검색 연동
    try:
        naver_url = f"https://ac.finance.naver.com/ac?q={requests.utils.quote(user_input)}&target=stock"
        res = requests.get(naver_url, timeout=3).json()
        items = res.get('items', [])
        if items and len(items[0]) > 0:
            top_item = items[0][0]
            code = top_item[0]
            name = top_item[1]
            market_type = top_item[3] if len(top_item) > 3 else ""
            market_suffix = ".KQ" if "코스닥" in market_type or market_type == "2" else ".KS"
            return f"{code}{market_suffix}", f"{name} ({code})"
    except:
        pass

    return user_input.upper(), user_input

def fetch_news(ticker_symbol, display_name):
    clean_ticker = ticker_symbol.split('.')[0]
    is_korean = ticker_symbol.endswith(".KS") or ticker_symbol.endswith(".KQ")
    news_items = []
    
    try:
        if is_korean:
            clean_name = display_name.split('(')[0].strip()
            search_query = f"{clean_name}+주가+하락+상승+이유+실적"
            url = f"https://news.google.com/rss/search?q={search_query}&hl=ko&gl=KR&ceid=KR:ko"
        else:
            search_query = f"{clean_ticker}+stock+why+down+up+earnings"
            url = f"https://news.google.com/rss/search?q={search_query}&hl=en-US&gl=US&ceid=US:en"
            
        res = requests.get(url, timeout=4)
        if res.status_code == 200:
            root = ET.fromstring(res.content)
            count = 0
            for item in root.findall('.//item'):
                if count >= 4: break
                title = item.find('title').text.split('-')[0].strip()
                link = item.find('link').text
                news_items.append((title, link))
                count += 1
    except:
        pass
    return news_items

# UI 구성
st.title("📈 스마트 주식 분석 & 골든크로스")
st.markdown("모바일과 PC에서 실시간 이평선 분석과 호재/악재 뉴스를 확인하세요.")

# 사이드바 (검색 및 즐겨찾기)
st.sidebar.header("🔍 종목 검색 및 설정")

selected_rec = st.sidebar.selectbox("📌 추천 목록", ["선택하세요"] + list(STOCKS.keys()))

fav_keys = list(st.session_state['favorites'].keys())
selected_fav = st.sidebar.selectbox("⭐ 내 즐겨찾기", ["선택하세요"] + fav_keys)

user_search = st.sidebar.text_input("직접 검색 (한글명/티커)", placeholder="예: 테슬라, 카카오, NVDA")

target_query = None
if user_search:
    target_query = user_search
elif selected_rec != "선택하세요":
    target_query = selected_rec
elif selected_fav != "선택하세요":
    target_query = selected_fav

if target_query:
    ticker, display_name = resolve_ticker(target_query)
    
    if ticker:
        st.subheader(f"📊 분석 결과: {display_name}")
        
        with st.spinner("실시간 데이터 분석 및 뉴스 수집 중..."):
            stock = yf.Ticker(ticker)
            df = stock.history(period="1y")
            
        if not df.empty:
            df['MA5'] = df['Close'].rolling(window=5).mean()
            df['MA20'] = df['Close'].rolling(window=20).mean()
            df['MA60'] = df['Close'].rolling(window=60).mean()
            df['MA120'] = df['Close'].rolling(window=120).mean()
            
            current_price = df['Close'].iloc[-1]
            ma5 = df['MA5'].iloc[-1]
            ma20 = df['MA20'].iloc[-1]
            ma60 = df['MA60'].iloc[-1] if not pd.isna(df['MA60'].iloc[-1]) else 0
            ma120 = df['MA120'].iloc[-1] if not pd.isna(df['MA120'].iloc[-1]) else 0

            prev_ma5 = df['MA5'].iloc[-2]
            prev_ma20 = df['MA20'].iloc[-2]

            # 지표 메트릭 출력
            col1, col2, col3 = st.columns(3)
            col1.metric("현재가", f"{current_price:,.2f}")
            col2.metric("5일선 (단기)", f"{ma5:,.2f}")
            col3.metric("20일선 (생명선)", f"{ma20:,.2f}")

            # 골든크로스 / 데드크로스 메시지
            if prev_ma5 <= prev_ma20 and ma5 > ma20:
                st.success("🟢 [단기 골든크로스 발생!] 5일선이 20일선을 상향 돌파했습니다.")
            elif prev_ma5 >= prev_ma20 and ma5 < ma20:
                st.error("🔴 [단기 데드크로스 발생] 5일선이 20일선 아래로 하락했습니다.")
            else:
                st.info("✅ 단기 추세 안정권 (정배열 혹은 횡보)")

            # 즐겨찾기 추가/삭제 버튼
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if st.button("⭐ 즐겨찾기 추가"):
                    st.session_state['favorites'][display_name] = ticker
                    save_favorites(st.session_state['favorites'])
                    st.success("즐겨찾기에 저장되었습니다!")
                    st.rerun()
            with col_b2:
                if display_name in st.session_state['favorites']:
                    if st.button("🗑️ 즐겨찾기 삭제"):
                        del st.session_state['favorites'][display_name]
                        save_favorites(st.session_state['favorites'])
                        st.warning("즐겨찾기에서 삭제되었습니다.")
                        st.rerun()

            # 차트 시각화
            st.markdown("### 📈 이동평균선 차트")
            fig, ax = plt.subplots(figsize=(10, 4), dpi=100)
            df_chart = df.tail(120)
            ax.plot(df_chart.index, df_chart['Close'], label='주가', color='black', linewidth=1.2)
            ax.plot(df_chart.index, df_chart['MA5'], label='5일선', color='red', linestyle='--', linewidth=1)
            ax.plot(df_chart.index, df_chart['MA20'], label='20일선', color='blue', linestyle='--', linewidth=1)
            if ma60 > 0:
                ax.plot(df_chart.index, df_chart['MA60'], label='60일선', color='green', linestyle=':', linewidth=1)
            ax.legend(loc='upper left', fontsize=8)
            ax.grid(True, linestyle=':', alpha=0.6)
            fig.tight_layout()
            st.pyplot(fig)

            # 뉴스 링크 출력
            st.markdown("### 📰 실시간 주요 뉴스")
            news_list = fetch_news(ticker, display_name)
            if news_list:
                for title, link in news_list:
                    st.markdown(f"- [{title}]({link})")
            else:
                st.write("관련 뉴스를 불러오지 못했습니다.")
        else:
            st.error("해당 종목의 데이터를 찾을 수 없습니다.")
else:
    st.info("👈 왼쪽 사이드바에서 추천 목록을 고르거나 종목을 검색해 주세요!")
