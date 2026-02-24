import streamlit as st
import pandas as pd
from FinMind.data import DataLoader
from datetime import datetime, timedelta

# 第一行必須緊貼左邊，不能有空格
st.set_page_config(page_title="台股籌碼掃描器", layout="wide")
st.title("📡 籌碼雷達：0050 核心股掃描")

# 設定掃描目標：台積電、鴻海、聯發科
target_list = ["2330", "2317", "2454"]

dl = DataLoader()
end_dt = datetime.now().strftime('%Y-%m-%d')
start_dt = (datetime.now() - timedelta(days=20)).strftime('%Y-%m-%d')

if st.button("開始掃描"):
    results = []
    progress_bar = st.progress(0)
    
    for i, sid in enumerate(target_list):
        try:
            # 抓取資料
            df_margin = dl.taiwan_stock_margin_purchase_short_sale(stock_id=sid, start_date=start_dt, end_date=end_dt)
            df_inst = dl.taiwan_stock_institutional_investors(stock_id=sid, start_date=start_dt, end_date=end_dt)
            
            if not df_margin.empty and not df_inst.empty:
                # 計算券資比
                m_last = df_margin.iloc[-1]
                # 自動搜尋欄位名稱 (防呆)
                ss = m_last.filter(like='Short_Sale_Balance').values[0]
                mp = m_last.filter(like='Margin_Purchase_Balance').values[0]
                short_ratio = (ss / mp) * 100
                
                # 計算法人買賣超 (最近 1 天)
                inst_last = df_inst.tail(3)
                net_buy = inst_last['buy'].sum() - inst_last['sell'].sum()
                
                # 判斷條件：券資比 < 30% 且 法人賣超
                status = "⚠️ 符合 (弱勢)" if (short_ratio < 30 and net_buy < 0) else "✅ 安全"
                
                results.append({
                    "股票代碼": sid,
                    "券資比": f"{round(short_ratio, 2)}%",
                    "法人買賣": "賣超" if net_buy < 0 else "買超",
                    "掃描結果": status
                })
        except:
            continue
        progress_bar.progress((i + 1) / len(target_list))

    # 顯示表格結果
    if results:
        st.table(pd.DataFrame(results))
    else:
        st.error("暫時抓不到資料，請稍後再試。")
