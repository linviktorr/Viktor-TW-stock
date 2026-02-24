import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

st.set_page_config(page_title="台股強勢選股器", layout="wide")
st.title("🚀 台股強勢選股器 (穩定版)")

# 側邊欄設定
target = st.sidebar.text_input("輸入股票代碼 (例如: 2330)", "2330")
vol_mult = st.sidebar.slider("成交量翻倍倍數", 1.5, 5.0, 2.0)

# 台股代碼轉換：yfinance 需要在代碼後加 .TW
stock_id = f"{target}.TW"

# 設定抓取範圍 (抓過去 60 天確保有足夠資料)
end_dt = datetime.now()
start_dt = end_dt - timedelta(days=60)

try:
    with st.spinner('正在從全球資料庫抓取台股數據...'):
        # 抓取資料
        ticker = yf.Ticker(stock_id)
        df = ticker.history(start=start_dt, end=end_dt)

    if not df.empty:
        # 計算 5 日均線
        df['MA5'] = df['Close'].rolling(window=5).mean()
        
        # 取得最新與昨日資料
        today = df.iloc[-1]
        yesterday = df.iloc[-2]
        
        # 判斷邏輯
        is_above_ma5 = today['Close'] > today['MA5']
        is_vol_double = today['Volume'] >= (yesterday['Volume'] * vol_mult)
        
        # 顯示結果介面
        st.subheader(f"分析結果：{target} (日期: {df.index[-1].strftime('%Y-%m-%d')})")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("今日收盤", f"{round(today['Close'], 2)} 元")
        c2.metric("今日成交張數", f"{int(today['Volume'] // 1000)} 張") # yfinance 單位是股，除以 1000 變張
        c3.metric("昨日成交張數", f"{int(yesterday['Volume'] // 1000)} 張")

        if is_above_ma5 and is_vol_double:
            st.success(f"🔥 強勢訊號：成交量暴增 {round(today['Volume']/yesterday['Volume'], 2)} 倍！")
            st.balloons()
        else:
            st.info("💡 尚未達標。條件：股價需在 MA5 之上且成交量翻倍。")
            
        # 畫出美化圖表
        st.line_chart(df[['Close', 'MA5']])
    else:
        st.error(f"⚠️ 找不到股票代碼 {stock_id} 的資料。請確認代碼是否正確。")

except Exception as e:
    st.error(f"系統偵測到異常: {e}")
    st.info("提示：台股請輸入數字代碼即可，系統會自動轉換。")
