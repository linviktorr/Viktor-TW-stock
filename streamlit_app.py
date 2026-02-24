import streamlit as st
import pandas as pd
from FinMind.data import DataLoader
from datetime import datetime, timedelta

st.set_page_config(page_title="台股強勢選股器", layout="wide")
st.title("🚀 台股強勢選股器")

# 1. 設定時間
end_dt = datetime.now().strftime('%Y-%m-%d')
start_dt = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

target_stock = st.sidebar.text_input("輸入股票代碼", "2330")
vol_mult = st.sidebar.slider("成交量翻倍倍數", 1.5, 5.0, 2.0)

dl = DataLoader()

try:
    # 這裡補上了 end_date
    df = dl.taiwan_stock_daily_adj(
        stock_id=target_stock, 
        start_date=start_dt,
        end_date=end_dt
    )

    if df is not None and not df.empty:
        df['MA5'] = df['close'].rolling(window=5).mean()
        today = df.iloc[-1]
        yesterday = df.iloc[-2]
        
        is_above_ma5 = today['close'] > today['MA5']
        is_vol_double = today['Trading_Volume'] >= (yesterday['Trading_Volume'] * vol_mult)
        
        st.subheader(f"分析結果：{target_stock}")
        c1, c2, c3 = st.columns(3)
        c1.metric("今日收盤", f"{today['close']} 元")
        c2.metric("今日成交量", f"{int(today['Trading_Volume'])} 張")
        c3.metric("昨日成交量", f"{int(yesterday['Trading_Volume'])} 張")

        if is_above_ma5 and is_vol_double:
            st.success("✅ 符合強勢條件！")
            st.balloons()
        else:
            st.info("💡 條件尚未達成。")
            
        st.line_chart(df.set_index('date')[['close', 'MA5']])
    else:
        st.warning("查無資料，請確認代碼或今日是否為休市日。")

except Exception as e:
    st.error(f"錯誤訊息：{e}")
