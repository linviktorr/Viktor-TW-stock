import streamlit as st
import pandas as pd
from FinMind.data import DataLoader
from datetime import datetime, timedelta

st.set_page_config(page_title="台股強勢選股器", layout="wide")
st.title("🚀 台股強勢選股器")

# 1. 調整日期邏輯：往前多抓一點，確保有資料可算 MA5
# 如果今天是周一，往前推 30 天絕對夠用
end_dt = datetime.now().strftime('%Y-%m-%d')
start_dt = (datetime.now() - timedelta(days=40)).strftime('%Y-%m-%d')

target_stock = st.sidebar.text_input("輸入股票代碼", "2330")
vol_mult = st.sidebar.slider("成交量翻倍倍數", 1.5, 5.0, 2.0)

dl = DataLoader()

try:
    # 抓取資料
    df = dl.taiwan_stock_daily_adj(
        stock_id=target_stock, 
        start_date=start_dt,
        end_date=end_dt
    )

    # 關鍵修正：先檢查 df 是否為 None，再檢查裡面有沒有東西
    if df is not None and isinstance(df, pd.DataFrame) and not df.empty:
        # 確保欄位名稱正確且資料排序正確（由舊到新）
        df = df.sort_values('date')
        
        # 計算 MA5
        df['MA5'] = df['close'].rolling(window=5).mean()
        
        # 確保至少有兩天的資料來比較成交量
        if len(df) >= 2:
            today = df.iloc[-1]
            yesterday = df.iloc[-2]
            
            is_above_ma5 = today['close'] > today['MA5']
            is_vol_double = today['Trading_Volume'] >= (yesterday['Trading_Volume'] * vol_mult)
            
            st.subheader(f"分析結果：{target_stock} (日期: {today['date']})")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("今日收盤", f"{today['close']} 元")
            c2.metric("今日成交量", f"{int(today['Trading_Volume'])} 張")
            c3.metric("昨日成交量", f"{int(yesterday['Trading_Volume'])} 張")

            if is_above_ma5 and is_vol_double:
                st.success(f"🔥 符合條件！股價高於均線且成交量爆發 ({round(today['Trading_Volume']/yesterday['Trading_Volume'], 2)}倍)")
                st.balloons()
            else:
                st.info("💡 目前未達標。提示：可能是成交量不夠大或股價在均線下。")
                
            st.line_chart(df.set_index('date')[['close', 'MA5']])
        else:
            st.warning("資料天數不足，無法進行對比。")
    else:
        st.error("⚠️ 讀取失敗：API 未回傳有效數據。")
        st.info("常見原因：1. 代碼錯誤 2. 今日尚未收盤 3. 該股近期停牌")

except Exception as e:
    # 這邊會捕捉到具體的錯誤原因，例如 'data'
    st.error(f"系統偵測到異常: {e}")
    st.info("建議：請檢查網路連線或稍後再試。")
