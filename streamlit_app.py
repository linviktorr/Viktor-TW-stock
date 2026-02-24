import streamlit as st
import pandas as pd
from FinMind.data import DataLoader
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="熱門股籌碼掃描器", layout="wide")
st.title("🛡️ 穩定版：熱門股籌碼雷達")

dl = DataLoader()

# 抓取範圍
end_dt = datetime.now().strftime('%Y-%m-%d')
start_dt = (datetime.now() - timedelta(days=20)).strftime('%Y-%m-%d')

# 模擬熱門股清單 (包含台灣 50 與 中型 100 核心股，確保分析有意義)
popular_stocks = ["2330", "2317", "2454", "2308", "2382", "2412", "2303", "2881", "2882", "2603", "2609", "2615", "3231", "6669", "2357"]

if st.button("🚀 開始穩定掃描 (熱門標的)"):
    results = []
    progress_bar = st.progress(0)
    status_msg = st.empty()
    
    for i, sid in enumerate(popular_stocks):
        status_msg.text(f"正在檢查：{sid} ({i+1}/{len(popular_stocks)})")
        try:
            # 1. 抓取籌碼資料
            df_m = dl.taiwan_stock_margin_purchase_short_sale(stock_id=sid, start_date=start_dt, end_date=end_dt)
            df_i = dl.taiwan_stock_institutional_investors(stock_id=sid, start_date=start_dt, end_date=end_dt)
            
            # 2. 只有在資料完整時才進行計算
            if df_m is not None and not df_m.empty and df_i is not None and not df_i.empty:
                # 取得最新一筆
                m = df_m.iloc[-1]
                # 券資比
                ss = m.get('Short_Sale_Balance', 0)
                mp = m.get('Margin_Purchase_Balance', 1)
                short_ratio = (ss / mp) * 100
                
                # 法人買賣超 (最近 3 天加總)
                inst_recent = df_i.tail(3)
                net_buy = inst_recent['buy'].sum() - inst_recent['sell'].sum()
                
                # 篩選：券資比 < 30% 且 法人賣超
                if short_ratio < 30 and net_buy < 0:
                    results.append({
                        "代號": sid,
                        "券資比": f"{round(short_ratio, 2)}%",
                        "法人買賣": f"賣超 {int(abs(net_buy)//1000)} 張",
                        "狀態": "⚠️ 籌碼轉弱"
                    })
            
            # 3. 避免 API 過載
            time.sleep(0.2)
            
        except Exception as e:
            # 個別股票出錯跳過，不影響整台機器
            continue
            
        progress_bar.progress((i + 1) / len(popular_stocks))

    status_msg.empty()
    if results:
        st.warning(f"🔍 掃描完成！發現 {len(results)} 檔符合「籌碼轉弱」條件：")
        st.table(pd.DataFrame(results))
    else:
        st.success("🎉 掃描完成！名單內暫無符合籌碼偏弱條件的股票。")

st.info("💡 穩定版說明：此版本針對 15 檔高權值熱門股進行精確掃描，有效避開全市場資料抓取時的 'data' 報錯。")
