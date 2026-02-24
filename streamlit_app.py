import streamlit as st
import pandas as pd
from FinMind.data import DataLoader
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="0050 籌碼雷達", layout="wide")

# --- 介面頂部：選股邏輯說明 ---
st.title("📡 0050 成分股：籌碼動向雷達")
with st.expander("ℹ️ 查看選股邏輯與篩選範圍", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        ### 🔍 篩選邏輯
        1. **券資比 < 30%**：缺乏軋空動能，支撐較弱。
        2. **法人賣超 (近 3 日)**：三大法人同步撤出。
        """)
    with col2:
        st.markdown("""
        ### 🎯 篩選範圍
        - **元大台灣 50 (0050)**：台灣市值最大的 50 檔公司，法人進出指標。
        """)

# --- 初始化 API ---
dl = DataLoader()
# 2026-02-24 資料設定
today_dt = datetime.now().strftime('%Y-%m-%d')
start_dt = (datetime.now() - timedelta(days=20)).strftime('%Y-%m-%d')

# 0050 成分股清單 (2026最新版快取，避免 API 函數找不到報錯)
# 這樣做最穩，且不用每次都去抓名單浪費時間
0050_list = [
    "2330", "2317", "2454", "2308", "2382", "2412", "2303", "2881", "2882", "2603",
    "2891", "3711", "2357", "2886", "1301", "2609", "1216", "2884", "2880", "2301",
    "2892", "2885", "5880", "2324", "1303", "2002", "2912", "3008", "2379", "6669",
    "3034", "3037", "3231", "2395", "1101", "4904", "2890", "2615", "5871", "4938",
    "2408", "2345", "1326", "2207", "1402", "2105", "2002", "5876", "9904", "1605"
]

if st.button("🚀 開始掃描 0050 成分股"):
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # 建立一個容器來顯示掃描中的進度
    for i, sid in enumerate(0050_list):
        status_text.text(f"分析中 ({i+1}/50): {sid}")
        try:
            # 抓取資券與法人
            df_m = dl.taiwan_stock_margin_purchase_short_sale(stock_id=sid, start_date=start_dt, end_date=today_dt)
            df_i = dl.taiwan_stock_institutional_investors(stock_id=sid, start_date=start_dt, end_date=today_dt)
            
            if df_m is not None and not df_m.empty and df_i is not None and not df_i.empty:
                # 取得最近一筆非零資券
                valid_m = df_m[df_m['Margin_Purchase_Balance'] > 0]
                m_row = valid_m.iloc[-1] if not valid_m.empty else df_m.iloc[-1]
                
                ss = m_row.get('Short_Sale_Balance', 0)
                mp = m_row.get('Margin_Purchase_Balance', 1)
                short_ratio = (ss / mp) * 100
                
                # 法人買賣合計 (近 3 日)
                net_buy = df_i.tail(3)['buy'].sum() - df_i.tail(3)['sell'].sum()
                
                if short_ratio < 30 and net_buy < 0:
                    results.append({
                        "代號": sid,
                        "券資比日期": m_row['date'],
                        "券資比": f"{round(short_ratio, 2)}%",
                        "法人賣超 (張)": int(abs(net_buy)//1000)
                    })
            
            # 調整 sleep 確保不會被 API 封鎖但維持速度
            time.sleep(0.05)
            
        except:
            continue
        
        progress_bar.progress((i + 1) / len(0050_list))

    status_text.empty()
    if results:
        st.warning(f"🔍 掃描完成！共 {len(results)} 檔符合條件：")
        st.dataframe(pd.DataFrame(results), use_container_width=True)
    else:
        st.success("🎉 掃描完成！目前 0050 成分股籌碼面表現穩健。")
