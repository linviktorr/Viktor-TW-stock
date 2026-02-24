import streamlit as st
import pandas as pd
from FinMind.data import DataLoader
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="籌碼精準掃描", layout="wide")
st.title("🛡️ 專業版：籌碼動向雷達")

dl = DataLoader()

# 設定抓取範圍：往前抓 30 天，確保能抓到最近有資料的「那一天」
end_dt = datetime.now().strftime('%Y-%m-%d')
start_dt = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

popular_stocks = ["2330", "2317", "2454", "2308", "2382", "2303", "2603", "3231", "6669", "2357"]

if st.button("🚀 開始精準掃描"):
    results = []
    bar = st.progress(0)
    
    for i, sid in enumerate(popular_stocks):
        try:
            # 1. 抓取籌碼資料
            df_m = dl.taiwan_stock_margin_purchase_short_sale(stock_id=sid, start_date=start_dt, end_date=end_dt)
            df_i = dl.taiwan_stock_institutional_investors(stock_id=sid, start_date=start_dt, end_date=end_dt)
            
            if df_m is not None and not df_m.empty:
                # --- 關鍵修正：由後往前找第一筆「融資餘額 > 0」的資料 ---
                valid_m = df_m[df_m['Margin_Purchase_Balance'] > 0]
                if not valid_m.empty:
                    m = valid_m.iloc[-1] # 取得最近有數值的那天
                    ss = m.get('Short_Sale_Balance', 0)
                    mp = m.get('Margin_Purchase_Balance', 1)
                    short_ratio = (ss / mp) * 100
                    data_date = m.get('date', 'Unknown')
                else:
                    short_ratio = 0
                    data_date = "無資券資料"

                # 2. 抓取法人買賣超 (最近 3 天)
                if df_i is not None and not df_i.empty:
                    inst_recent = df_i.tail(3)
                    net_buy = inst_recent['buy'].sum() - inst_recent['sell'].sum()
                else:
                    net_buy = 0

                # 3. 判斷條件：券資比 < 30% 且 法人賣超
                if 0 < short_ratio < 50 and net_buy < 0:
                    results.append({
                        "代號": sid,
                        "資料日期": data_date,
                        "券資比": f"{round(short_ratio, 2)}%",
                        "法人買賣": f"賣超 {int(abs(net_buy)//1000)} 張"
                    })
            
            time.sleep(0.2)
        except:
            continue
        bar.progress((i + 1) / len(popular_stocks))

    if results:
        st.warning(f"🔍 掃描完成！符合條件股票：")
        st.table(pd.DataFrame(results))
    else:
        st.success("🎉 目前名單內沒有符合「券資比低於 30% 且法人賣超」的股票。")
