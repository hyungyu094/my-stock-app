import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# 1. 페이지 기본 설정 (에러 방지용 안전 모드)
st.set_page_config(
    page_title="망고의 롤댄스 주식",
    page_icon="📈",
    layout="wide"
)

# 2. 앱 제목
st.title("📈 망고의 롤댄스 주식")
st.write("안정적으로 실행되는 기본 주식 분석 화면입니다.")

# 3. 간단한 주식 검색 및 차트 예시 기능
st.sidebar.header("종목 검색 설정")
ticker_symbol = st.sidebar.text_input("티커 입력 (예: AAPL, TSLA, MSFT)", value="AAPL")

if ticker_symbol:
    try:
        st.subheader(f"📊 {ticker_symbol.upper()} 주가 데이터")
        
        # 야후 파이낸스에서 데이터 불러오기
        stock_data = yf.Ticker(ticker_symbol)
        df = stock_data.history(period="1y")
        
        if not df.empty:
            # 현재가 및 기본 정보 표시
            current_price = df['Close'].iloc[-1]
            st.metric(label=f"{ticker_symbol.upper()} 최근 종가", value=f"${current_price:,.2f}")
            
            # 최근 데이터 표로 보여주기
            st.write("최근 거래 데이터 (상위 5개)")
            st.dataframe(df.tail());
            
            # 간단한 차트 그리기
            st.write("1년간 주가 추이 그래프")
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(df.index, df['Close'], color='blue', label='Close Price')
            ax.set_xlabel("Date")
            ax.set_ylabel("Price (USD)")
            ax.legend()
            st.pyplot(fig)
        else:
            st.warning("해당 종목의 데이터를 찾을 수 없습니다. 티커 심볼을 다시 확인해 주세요.")
            
    except Exception as e:
        st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
        else:
            st.error("해당 종목의 데이터를 찾을 수 없습니다.")
else:
    st.info("👈 왼쪽 사이드바에서 추천 목록을 고르거나 종목을 검색해 주세요!")
