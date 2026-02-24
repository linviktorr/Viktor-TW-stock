import streamlit as st
import pandas as pd
from FinMind.data import DataLoader

# 設定網頁標題
st.title("🚀 台股強勢選股器")

# 側邊欄設定
st.sidebar.header("篩選條件設定")
vol_mult = st.sidebar.slider("成交量翻倍倍數", 1.5, 5.0, 2.0)
target_stock = st.sidebar.text_input("輸入股票代碼測試", "2330")

# 1. 初始化資料抓取
dl = DataLoader()

# 取得資料 (以 2330 示範，正式版可寫循環)
df = dl.taiwan_stock_daily_adj(stock_id=target_stock, start_date="2026-01-01")

if not df.empty:
    # 計算 5 日線
    df['MA5'] = df['close'].rolling(window=5).mean()
    
    # 這裡假設已經取得券資比 (FinMind 需額外 API 呼叫，此處先示意邏輯)
    # df_margin = dl.taiwan_stock_margin_purchase_short_sale(stock_id=target_stock...)
    
    today = df.iloc[-1]
    yesterday = df.iloc[-2]
    
    # 判斷邏輯
    is_above_ma5 = today['close'] > today['MA5']
    is_vol_double = today['Trading_Volume'] >= (yesterday['Trading_Volume'] * vol_mult)
    
    # 顯示結果
    st.subheader(f"分析股票：{target_stock}")
    col1, col2 = st.columns(2)
    col1.metric("今日收盤", f"{today['close']} 元")
    col2.metric("成交量", f"{int(today['Trading_Volume'])} 張")

    if is_above_ma5 and is_vol_double:
        st.success("✅ 符合強勢噴發條件！(5日線上+成交量翻倍)")
    else:
        st.warning("⏳ 尚未符合條件，持續觀察。")

    # 畫出簡單圖表
    st.line_chart(df[['close', 'MA5']])
else:
    st.error("找不到該股票資料，請檢查代碼。")
