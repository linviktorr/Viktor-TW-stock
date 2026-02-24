import streamlit as st
import pandas as pd
from FinMind.data import DataLoader
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="記憶體族群籌碼雷達", layout="wide")

# --- 介面說明 ---
st.title("💾 記憶體產業：籌碼動向雷達")
st.markdown("針對 **台灣記憶體與模組大廠** 進行多維度籌碼掃描")

# --- 初始化 ---
dl = DataLoader()
today_dt = datetime.now().strftime('%Y-%m-%d')
start_dt = (datetime.now() - timedelta(days=20)).strftime('%Y-%m-%d')

# 記憶體類股清單 (包含 DRAM、Flash、模組廠)
stocks_memory = [
    "2408", "2344", "2337", "3260", "8299", # 核心製造 (南亞科、華邦電、旺宏、威剛、群聯)
    "3006", "4967", "6239", "8110", "2451", # 模組與週邊 (創見、十銓、力成、華東、創見)
    "3532", "6485", "6573", "5289"          # 矽晶圓與設計 (台勝科、點序、虹冠電、宜鼎)
]

if st.button("🚀 開始記憶體族群掃描"):
    res_both = []   # 同時符合
    res_margin = [] # 僅符合券資比 < 30%
    res_inst = []   # 僅符合法人賣超
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, sid in enumerate(stocks_memory):
        status_text.text(f"分析中 ({i+1}/{len(stocks_memory)}): {sid}")
        try:
            # 抓取資料
            df_m = dl.taiwan_stock_margin_purchase_short_sale(stock_id=sid, start_date=start_dt, end_date=today_dt)
            df_i = dl.taiwan_stock_institutional_investors(stock_id=sid, start_date=start_dt, end_date=today_dt)
            
            if df_m is not None and not df_m.empty and df_i is not None and not df_i.empty:
                # 1. 計算券資比 (取最新有效資料)
                valid_m = df_m[df_m['Margin_Purchase_Balance'] > 0]
                m_row = valid_m.iloc[-1] if not valid_m.empty else df_m.iloc[-1]
                short_ratio = round((m_row.get('Short_Sale_Balance', 0) / m_row.get('Margin_Purchase_Balance', 1)) * 100, 2)
                
                # 2. 計算法人近 3 日買賣 (張數)
                net_buy = int((df_i.tail(3)['buy'].sum() - df_i.tail(3)['sell'].sum()) // 1000)
                
                # 3. 分類邏輯
                cond_margin = short_ratio < 30
                cond_inst = net_buy < 0
                
                data_item = {"代號": sid, "券資比": f"{short_ratio}%", "法人賣超(張)": abs(net_buy), "日期": m_row['date']}
                
                if cond_margin and cond_inst:
                    res_both.append(data_item)
                elif cond_margin:
                    res_margin.append({"代號": sid, "券資比": f"{short_ratio}%", "日期": m_row['date']})
                elif cond_inst:
                    res_inst.append({"代號": sid, "法人賣超(張)": abs(net_buy), "日期": m_row['date']})
            
            time.sleep(0.1)
        except:
            continue
        progress_bar.progress((i + 1) / len(stocks_memory))

    status_text.empty()

    # --- 顯示結果 (使用 Tabs) ---
    tab1, tab2, tab3 = st.tabs(["🔥 雙重警示 (符合兩項)", "📉 僅券資比低", "🏢 僅法人賣超"])

    with tab1:
        if res_both:
            st.warning(f"記憶體族群中有 {len(res_both)} 檔同時符合條件")
            st.table(pd.DataFrame(res_both))
        else:
            st.success("記憶體類股中目前沒有標的同時符合兩項條件")

    with tab2:
        if res_margin:
            st.info(f"共有 {len(res_margin)} 檔券資比低於 30%")
            st.dataframe(pd.DataFrame(res_margin), use_container_width=True)
        else:
            st.write("查無資料")

    with tab3:
        if res_inst:
            st.error(f"共有 {len(res_inst)} 檔法人近期賣超")
            st.dataframe(pd.DataFrame(res_inst).sort_values("法人賣超(張)", ascending=False), use_container_width=True)
        else:
            st.write("查無資料")

st.divider()
st.info("💡 **產業知識**：記憶體類股通常與國際報價（如現貨價、合約價）高度相關。當法人持續賣超時，應密切注意產業庫存或跌價風險。")
