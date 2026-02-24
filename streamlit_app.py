import streamlit as st
import pandas as pd
from FinMind.data import DataLoader
from datetime import datetime, timedelta

# 設定網頁標題
st.set_page_config(page_title="台股強勢選股器", layout="wide")
st.title("🚀 台股強勢選股器")

# 側邊欄設定
st.sidebar.header("篩選條件設定")
# 自動計算起始日期（抓過去 30 天確保有足夠資料算均線）
start_dt = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
vol_mult = st.sidebar.slider("成交量翻倍倍數", 1.5, 5.0, 2.0)
target_stock = st.sidebar.text_input("輸入股票代碼測試", "2330")

# 1. 初始化資料抓取
dl = DataLoader()

try:
    # 取得資料
    df = dl.taiwan_stock_daily_adj(
        stock_id=target_stock, 
        start_date=start_dt
    )

    # 防呆檢查：確保有抓到資料且資料量足夠
    if df is not None and len(df) >= 5:
        # 轉換日期格式以便繪圖
        df['date'] = pd.to_datetime(df['date'])
        
        # 計算 5 日線 (MA5)
        df['MA5'] = df['close'].rolling(window=5).mean()
        
        # 取得最新兩天的資料
        today = df.iloc[-1]
        yesterday = df.iloc[-2]
        
        # 判斷邏輯
        is_above_ma5 = today['close'] > today['MA5']
        is_vol_double = today['Trading_Volume'] >= (yesterday['Trading_Volume'] * vol_mult)
        
        # 顯示結果
        st.subheader(f"分析結果：{target_stock}")
        c1, c2, c3 = st.columns(3)
        c1.metric("今日收盤", f"{today['close']} 元")
        c2.metric("成交量", f"{int(today['Trading_Volume'])} 張")
        c3.metric("昨日成交量", f"{int(yesterday['Trading_Volume'])} 張")

        if is_above_ma5 and is_vol_double:
            st.success(f"✅ {target_stock} 符合強勢條件！")
            st.balloons() # 噴出慶祝氣球
        else:
            st.info("💡 尚未完全符合條件（需股價 > MA5 且量增一倍）")

        # 畫出美化的圖表
        st.line_chart(df.set_index('date')[['close', 'MA5']])
        
    else:
        st.error("❌ 抓取的資料不足（可能今日尚未開盤或代碼輸入錯誤）。")

except Exception as e:
    st.error(f"發生意外錯誤: {e}")
    st.info("提示：請確認股票代碼是否正確，例如：2330")
