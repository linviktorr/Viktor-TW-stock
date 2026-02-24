import streamlit as st
import pandas as pd
from FinMind.data import DataLoader
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="熱門股籌碼掃描", layout="wide")
st.title("🔥 熱門股雷達：成交量前 50 名")

dl = DataLoader()

# 設定日期範圍
today_str = datetime.now().strftime('%Y-%m-%d')
start_str = (datetime.now() - timedelta(days=20)).strftime('%Y-%m-%d')

if st.button("🚀 開始掃描前 50 名熱門股"):
    try:
        with st.spinner('抓取今日行情...'):
            # 1. 抓取今日行情
            df_ticks = dl.taiwan_stock_daily_adj(start_date=today_str, end_date=today_str)
            if df_ticks is None or df_ticks.empty:
                # 若今日無資料則抓昨日
                old_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                df_ticks = dl.taiwan_stock_daily_adj(start_date=old_date, end_date=old_date)

            # 2. 取成交量前 50 名
            top_50 = df_ticks.sort_values(by='Trading_Volume', ascending=False).head(50)
            top_50_list = top_50['stock_id'].tolist()

        results = []
        bar = st.progress(0)
        
        for i, sid in enumerate(top_50_list):
            try:
                # 3. 抓取籌碼
                df_m = dl.taiwan_stock_margin_purchase_short_sale(stock_id=sid, start_date=start_str, end_date=today_str)
                df_i = dl.taiwan_stock_institutional_investors(stock_id=sid, start_date=start_str, end_date=today_str)
                
                if not df_m.empty and not df_i.empty:
                    # 計算券資比
                    m = df_m.iloc[-1]
                    s_ratio = (m.get('Short_Sale_Balance', 0) / m.get('Margin_Purchase_Balance', 1)) * 100
                    
                    # 法人買賣超 (最近3天加總)
                    inst_recent = df_i.tail(3)
                    net_buy = inst_recent['buy'].sum() - inst_recent['sell'].sum()
                    
                    # 篩選條件：券資比 < 30% 且 法人賣超 (net_buy < 0)
                    if s_ratio < 30 and net_buy < 0:
                        results.append({
                            "排名": i + 1,
                            "代號": sid,
                            "券資比": f"{round(s_ratio, 2)}%",
                            "法人賣超": f"{int(net_buy // 1000)} 張"
                        })
                time.sleep(0.1)
            except:
                continue
            bar.progress((i + 1) / 50)

        if results:
            st.warning("⚠️ 以下股票符合「券資比低、法人撤退」條件：")
            st.table(pd.DataFrame(results))
        else:
            st.success("🎉 目前熱門股籌碼尚稱穩健。")

    except Exception as e:
        st.error(f"掃描失敗: {e}")
