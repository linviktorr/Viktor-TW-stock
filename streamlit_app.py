import streamlit as st
import pandas as pd
from FinMind.data import DataLoader
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="熱門股籌碼掃描", layout="wide")
st.title("🔥 熱門股雷達：成交量前 50 名籌碼分析")
st.caption("條件：券資比 < 30% 且 法人賣超")

dl = DataLoader()

# 設定日期範圍
end_dt = datetime.now().strftime('%Y-%m-%d')
start_dt = (datetime.now() - timedelta(days=20)).strftime('%Y-%m-%d')

if st.button("🚀 開始掃描熱門股"):
    try:
        with st.spinner('正在獲取今日行情並排序...'):
            # 1. 取得今日全市場行情
            df_ticks = dl.taiwan_stock_daily_adj(
                start_date=end_dt, 
                end_date=end_dt
            )
            
            # 若今日尚未收盤或無資料，改抓昨日
            if df_ticks is None or df_ticks.empty:
                yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                df_ticks = dl.taiwan_stock_daily_adj(start_date=yesterday, end_date=yesterday)

            # 2. 依照成交量 (Trading_Volume) 排序，取前 50 名
            top_50 = df_ticks.sort_values(by='Trading_Volume', ascending=False).head(50)
            top_50_list = top_50['stock_id'].tolist()

        results = []
        bar = st.progress(0)
        status_text = st.empty()

        for i, sid in enumerate(top_50_list):
            status_text.text(f"分析中 ({i+1}/50): {sid}")
            
            try:
                # 抓取籌碼資料
                df_m = dl.taiwan_stock_margin_purchase_short_sale(stock_id=sid, start_date=start_dt, end_date=end_dt)
                df_i = dl.taiwan_stock_institutional_investors(stock_id=sid, start_date=start_dt, end_date=end_dt)
                
                if not df_m.empty and not df_i.empty:
                    # 計算券資比
                    m = df_m.iloc[-1]
                    ss = m.get('Short_Sale_Balance', 0)
                    mp = m.get('Margin_Purchase_Balance', 1)
                    short_ratio = (ss / mp) * 100
                    
                    # 法人近期買賣 (最近 3 天合計)
                    inst_sum = df_i.tail(3)['buy'].sum() - df_i.
