import streamlit as st
import pandas as pd
from FinMind.data import DataLoader
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="籌碼精準掃描", layout="wide")
st.title("🛡️ 專業版：籌碼動向雷達 (修正顯示邏輯)")

dl = DataLoader()

# 設定抓取範圍：確保包含過去兩週
end_dt = datetime.now().strftime('%Y-%m-%d')
start_dt = (datetime.now() - timedelta(days=20)).strftime('%Y-%m-%d')

# 擴充名單到 20 檔，增加篩選到股票的機率
popular_stocks = [
    "2330", "2317", "2454", "2308", "2382", "2303", "2603", "2609", 
    "3231", "6669", "2357", "2881", "2882", "2886", "2301", "2408"
]

if st.button("🚀 開始掃描"):
    results = []
    bar = st.progress(0)
    
    for i, sid in enumerate(popular_stocks):
        try:
            # 1. 抓取資料
            df_m = dl.taiwan_stock_margin_purchase_short_sale(stock_id=sid, start_date=start_dt, end_date=end_dt)
            df_i = dl.taiwan_stock_institutional_investors(stock_id=sid, start_date=start_dt, end_date=end_dt)
            
            # 2. 處理資券資料 (找最近一筆不為 0 的)
            if df_m is not None and not df_m.empty:
                # 篩選掉 Margin_Purchase_Balance 為 0 的日子
                valid_m = df_m[df_m['Margin_Purchase_Balance'] > 0]
                
                if not valid_m.empty:
                    m_row = valid_m.iloc[-1]
                    ss = m_row.get('Short_Sale_Balance', 0)
                    mp = m_row.get('Margin_Purchase_Balance', 1)
                    short_ratio = (ss / mp) * 100
                    m_date = m_row.get('date', '')
                else:
                    # 如果真的找不到非 0 資料，就給它最新的一筆（即使是 0）
                    m_row = df_m.iloc[-1]
                    short_ratio = 0
                    m_date = m_row.get('date', '無資料')
            else:
                short_ratio = 0
                m_date = "N/A"

            # 3. 處理法人資料
            if df_i is not None and not df_i.empty:
                inst_recent = df_i.tail(3)
                net_buy = inst_recent['buy'].sum() - inst_recent['sell'].sum()
            else:
                net_buy = 0

            # 4. 判斷條件：只要券資比 < 30% 且 法人賣超 (不再強制券資比要 > 0)
            if short_ratio < 30 and net_buy < 0:
                results.append({
                    "代號": sid,
                    "券資比日期": m_date,
                    "券資比": f"{round(short_ratio, 2)}%",
                    "法人買賣(3日)": f"賣超 {int(abs(net_buy)//1000)} 張"
                })
            
            time.sleep(0.1)
        except:
            continue
        bar.progress((i + 1) / len(popular_stocks))

    if results:
        st.warning(f"🔍 掃描完成！符合條件股票（券資比 < 30% 且 法人賣超）：")
        st.table(pd.DataFrame(results))
    else:
        st.info("🎉 目前名單內無符合條件的股票。可能是法人轉為買超，或是券資比突然大幅攀升。")
