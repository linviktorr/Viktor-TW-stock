import streamlit as st
import pandas as pd
from FinMind.data import DataLoader
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="記憶體籌碼全能雷達", layout="wide")

st.title("💾 記憶體產業：籌碼全維度掃描")

# --- 介面說明 ---
with st.expander("ℹ️ 選股邏輯與資料說明", expanded=True):
    st.markdown("""
    **本工具將資料完全拆解，確保您能看到每一檔股票的最新狀態：**
    - **券資比**：> 30% 具軋空潛力；< 30% 走勢較平穩。
    - **法人買賣**：正數為買超，負數為賣超。
    - **自動追溯**：若今日資券尚未更新，系統會自動顯示最近一個交易日的正確數據。
    """)

dl = DataLoader()
end_dt = datetime.now().strftime('%Y-%m-%d')
start_dt = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

stocks_memory = [
    "2408", "2344", "2337", "3260", "8299", 
    "3006", "4967", "6239", "8110", "2451",
    "3532", "6485", "5289"
]

if st.button("🚀 執行全量數據掃描"):
    all_data = []
    progress_bar = st.progress(0)
    
    for i, sid in enumerate(stocks_memory):
        try:
            df_m = dl.taiwan_stock_margin_purchase_short_sale(stock_id=sid, start_date=start_dt, end_date=end_dt)
            df_i = dl.taiwan_stock_institutional_investors(stock_id=sid, start_date=start_dt, end_date=end_dt)
            
            if df_m is not None and not df_m.empty and df_i is not None and not df_i.empty:
                # 追溯最新有意義的資券資料
                valid_m = df_m[df_m['Margin_Purchase_Balance'] > 0]
                m_row = valid_m.iloc[-1] if not valid_m.empty else df_m.iloc[-1]
                
                ss = m_row.get('Short_Sale_Balance', 0)
                mp = m_row.get('Margin_Purchase_Balance', 1)
                short_ratio = round((ss / mp) * 100, 2)
                
                # 法人近 3 日合計 (不論正負)
                net_buy = int((df_i.tail(3)['buy'].sum() - df_i.tail(3)['sell'].sum()) // 1000)
                
                all_data.append({
                    "代號": sid,
                    "券資比(%)": short_ratio,
                    "法人買賣(張)": net_buy,
                    "券資比日期": m_row['date'],
                    "狀態": "🔥 高券資比" if short_ratio > 30 else "❄️ 低券資比"
                })
            time.sleep(0.1)
        except:
            continue
        progress_bar.progress((i + 1) / len(stocks_memory))

    if all_data:
        df_final = pd.DataFrame(all_data)
        
        # --- 顯示分頁 ---
        tab1, tab2, tab3 = st.tabs(["📊 全體清單", "📈 券資比排行", "🏢 法人買賣榜"])
