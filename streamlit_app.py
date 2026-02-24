import streamlit as st
import pandas as pd
from FinMind.data import DataLoader
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="記憶體強勢軋空雷達", layout="wide")

st.title("📈 記憶體產業：強勢軋空雷達")

# --- 介面說明 ---
with st.expander("ℹ️ 選股邏輯說明", expanded=True):
    st.markdown("""
    - **強勢軋空**：券資比 > 30% 且 法人買超。
    - **資料修正**：若今日資券尚未更新，系統將自動追溯至前一交易日。
    """)

dl = DataLoader()
# 增加抓取天數，確保跨過週末與空窗期
end_dt = datetime.now().strftime('%Y-%m-%d')
start_dt = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

stocks_memory = ["2408", "2344", "2337", "3260", "8299", "3006", "4967", "6239", "8110", "2451"]

if st.button("🚀 開始深度掃描"):
    res_both, res_margin, res_inst = [], [], []
    bar = st.progress(0)
    status = st.empty()
    
    for i, sid in enumerate(stocks_memory):
        status.text(f"分析中: {sid}")
        try:
            # 1. 抓取資料
            df_m = dl.taiwan_stock_margin_purchase_short_sale(stock_id=sid, start_date=start_dt, end_date=end_dt)
            df_i = dl.taiwan_stock_institutional_investors(stock_id=sid, start_date=start_dt, end_date=end_dt)
            
            # 2. 核心修正：找出「最近一個」融資餘額大於 0 的日期
            if df_m is not None and not df_m.empty:
                valid_m = df_m[df_m['Margin_Purchase_Balance'] > 0]
                if not valid_m.empty:
                    m_row = valid_m.iloc[-1] # 這就是最近有資券數據的那天
                    ss = m_row.get('Short_Sale_Balance', 0)
                    mp = m_row.get('Margin_Purchase_Balance', 1)
                    short_ratio = round((ss / mp) * 100, 2)
                    m_date = m_row['date']
                else:
                    short_ratio, m_date = 0, "無有效資券"
            else:
                short_ratio, m_date = 0, "連線錯誤"

            # 3. 法人買賣超 (取最後 3 筆有資料的加總)
            if df_i is not None and not df_i.empty:
                net_buy = int(df_i.tail(3)['buy'].sum() - df_i.tail(3)['sell'].sum()) // 1000
            else:
                net_buy = 0

            # 4. 分類邏輯 (強勢多頭)
            data_item = {"代號": sid, "券資比": f"{short_ratio}%", "法人買超(張)": net_buy, "資券日期": m_date}
            
            if short_ratio > 30 and net_buy > 0:
                res_both.append(data_item)
            elif short_ratio > 30:
                res_margin.append(data_item)
            elif net_buy > 0:
                res_inst.append(data_item)
                
            time.sleep(0.1)
        except Exception as e:
            continue
        bar.progress((i + 1) / len(stocks_memory))

    status.empty()
    t1, t2, t3 = st.tabs(["🔥 強勢軋空", "📈 高券資比", "💎 法人買超"])
    
    with t1:
        if res_both: st.table(pd.DataFrame(res_both))
        else: st.info("目前無雙重符合標的")
    with t2:
        if res_margin: st.dataframe(pd.DataFrame(res_margin))
        else: st.write("無高券資比標的")
    with t3:
        if res_inst: st.dataframe(pd.DataFrame(res_inst))
        else: st.write("無法人買超標的")
