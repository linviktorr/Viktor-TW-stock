import streamlit as st
import pandas as pd
from FinMind.data import DataLoader
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="0050 籌碼雷達", layout="wide")

# --- 介面說明 ---
st.title("📡 0050 籌碼雙指標雷達")
st.markdown("針對 **0050 成分股** 進行多維度籌碼掃描")

# --- 初始化 ---
dl = DataLoader()
today_dt = datetime.now().strftime('%Y-%m-%d')
start_dt = (datetime.now() - timedelta(days=20)).strftime('%Y-%m-%d')

stocks_0050 = [
    "2330", "2317", "2454", "2308", "2382", "2412", "2303", "2881", "2882", "2603",
    "2891", "3711", "2357", "2886", "1301", "2609", "1216", "2884", "2880", "2301",
    "2892", "2885", "5880", "2324", "1303", "2002", "2912", "3008", "2379", "6669",
    "3034", "3037", "3231", "2395", "1101", "4904", "2890", "2615", "5871", "4938",
    "2408", "2345", "1326", "2207", "1402", "2105", "5876", "9904", "1605", "2354"
]

if st.button("🚀 開始雙指標同步掃描"):
    res_both = []   # 同時符合
    res_margin = [] # 僅符合券資比 < 30%
    res_inst = []   # 僅符合法人賣超
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, sid in enumerate(stocks_0050):
        status_text.text(f"掃描中 ({i+1}/50): {sid}")
        try:
            df_m = dl.taiwan_stock_margin_purchase_short_sale(stock_id=sid, start_date=start_dt, end_date=today_dt)
            df_i = dl.taiwan_stock_institutional_investors(stock_id=sid, start_date=start_dt, end_date=today_dt)
            
            if df_m is not None and not df_m.empty and df_i is not None and not df_i.empty:
                # 1. 計算券資比
                valid_m = df_m[df_m['Margin_Purchase_Balance'] > 0]
                m_row = valid_m.iloc[-1] if not valid_m.empty else df_m.iloc[-1]
                short_ratio = round((m_row.get('Short_Sale_Balance', 0) / m_row.get('Margin_Purchase_Balance', 1)) * 100, 2)
                
                # 2. 計算法人近 3 日買賣
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
            
            time.sleep(0.05)
        except:
            continue
        progress_bar.progress((i + 1) / len(stocks_0050))

    status_text.empty()

    # --- 顯示結果 (使用 Tabs) ---
    tab1, tab2, tab3 = st.tabs(["🔥 雙重警示 (符合兩項)", "📉 僅券資比低", "🏢 僅法人賣超"])

    with tab1:
        if res_both:
            st.warning(f"共有 {len(res_both)} 檔同時符合條件")
            st.table(pd.DataFrame(res_both))
        else:
            st.success("目前沒有標的同時符合兩項條件")

    with tab2:
        if res_margin:
            st.info(f"共有 {len(res_margin)} 檔券資比低於 30%")
            st.dataframe(pd.DataFrame(res_margin), use_container_width=True)
        else:
            st.write("查無資料")

    with tab3:
        if res_inst:
            st.error(f"共有 {len(res_inst)} 檔法人近期連續賣超")
            st.dataframe(pd.DataFrame(res_inst).sort_values("法人賣超(張)", ascending=False), use_container_width=True)
        else:
            st.write("查無資料")

st.divider()
st.caption("註：券資比低代表缺乏軋空力道；法人賣超代表大戶資金流出。")
