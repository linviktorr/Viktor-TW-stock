import streamlit as st
import pandas as pd
from FinMind.data import DataLoader
from datetime import datetime, timedelta

st.set_page_config(page_title="台股強勢選股器", layout="wide")
st.title("🚀 台股強勢選股器")

# 1. 日期設定：確保範圍夠大
# 今天是 2026-02-24，我們往前抓 45 天，確保跨過過年或連假
end_dt = datetime.now().strftime('%Y-%m-%d')
start_dt = (datetime.now() - timedelta(days=45)).strftime('%Y-%m-%d')

target_stock = st.sidebar.text_input("輸入股票代碼", "2330")
vol_mult = st.sidebar.slider("成交量翻倍倍數", 1.5, 5.0, 2.0)

# 使用這招：把 DataLoader 放在 try 裡面
try:
    dl = DataLoader()
    
    # 這裡加入一個 loading 進度條，讓使用者知道正在抓資料
    with st.spinner('正在從資料庫搬運食材中...'):
        df = dl.taiwan_stock_daily_adj(
            stock_id=target_stock, 
            start_date=start_dt,
            end_date=end_dt
        )

    # 關鍵檢查：不僅檢查 df，還檢查裡面是否有我們需要的欄位
    if df is not None and not df.empty and 'close' in df.columns:
        df = df.sort_values('date')
        
        # 計算 MA5
        df['MA5'] = df['close'].rolling(window=5).mean()
        
        if len(df) >= 5:
            today = df.iloc[-1]
            yesterday = df.iloc[-2]
            
            # 判斷邏輯
            is_above_ma5 = today['close'] > today['MA5']
            is_vol_double = today['Trading_Volume'] >= (yesterday['Trading_Volume'] * vol_mult)
            
            st.subheader(f"分析結果：{target_stock} ({today['date']})")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("今日收盤", f"{today['close']} 元")
            col2.metric("今日成交量", f"{int(today['Trading_Volume'])} 張")
            col3.metric("昨日成交量", f"{int(yesterday['Trading_Volume'])} 張")

            if is_above_ma5 and is_vol_double:
                st.success(f"🔥 強勢訊號：成交量暴增 {round(today['Trading_Volume']/yesterday['Trading_Volume'], 2)} 倍！")
                st.balloons()
            else:
                st.info("💡 尚未達標。條件：股價需在 MA5 之上且成交量翻倍。")
                
            # 展示圖表
            st.line_chart(df.set_index('date')[['close', 'MA5']])
        else:
            st.warning("抓到的天數不足 5 天，無法計算均線。請確認今日是否為交易日。")
    else:
        st.error("⚠️ 無法讀取資料包。")
        st.write("這通常是因為 API 伺服器正在維護，或該股票代碼在目前日期區間沒有資料。")

except Exception as e:
    # 如果抓到 'data' 錯誤，顯示更白話的提示
    if 'data' in str(e):
        st.error("❌ API 回傳格式錯誤 (KeyError: 'data')")
        st.info("這通常是 FinMind API 暫時性的問題。建議：1. 檢查代碼是否正確 2. 稍等 5 分鐘再試。")
    else:
        st.error(f"捕捉到未知錯誤: {e}")
