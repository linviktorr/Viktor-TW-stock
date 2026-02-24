import streamlit as st
import pandas as pd
from FinMind.data import DataLoader
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="熱門股籌碼掃描", layout="wide")
st.title("🔥 熱門股雷達：成交量前 50 名")

dl = DataLoader()

# 設定日期範圍 (考慮到週末，往前推 5 天確保抓得到最近一日行情)
today_str = datetime.now().strftime('%Y-%m-%d')
start_str = (datetime.now() - timedelta(days=20)).strftime('%Y-%m-%d')
market_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')

if st.button("🚀 開始掃描前 50 名熱門股"):
    try:
        with st.spinner('獲取全市場行情中...'):
            # 修正處：使用 taiwan_stock_daily 抓取全市場資料 (不傳入 stock_id)
            df_all = dl.taiwan_stock_daily(
                start_date=market_date, 
                end_date=today_str
            )
            
            if df_all is None or df_all.empty:
                st.error("無法取得市場行情，請確認 API 連線。")
            else:
                # 取得最近一個交易日的全部資料
                last_date = df_all['date'].max()
                df_ticks = df_all[df_all['date'] == last_date]

                # 2. 取成交量前 50 名
                top_50 = df_ticks.sort_values(by='Trading_Volume', ascending=False).head(50)
                top_50_list = top_50['stock_id'].tolist()

                results = []
                bar = st.progress(0)
                
                for i, sid in enumerate(top_50_list):
                    try:
                        # 3. 抓取籌碼資料 (這部分需要 stock_id)
                        df_m = dl.taiwan_stock_margin_purchase_short_sale(stock_id=sid, start_date=start_str, end_date=today_str)
                        df_i = dl.taiwan_stock_institutional_investors(stock_id=sid, start_date=start_str, end_date=today_str)
                        
                        if not df_m.empty and not df_i.empty:
                            m = df_m.iloc[-1]
                            # 券資比計算
                            s_ratio = (m.get('Short_Sale_Balance', 0) / m.get('Margin_Purchase_Balance', 1)) * 100
                            
                            # 三大法人買賣超 (最近 3 天合計)
                            inst_recent = df_i.tail(3)
                            net_buy = inst_recent['buy'].sum() - inst_recent['sell'].sum()
                            
                            # 篩選：券資比 < 30% 且 法人賣超
                            if s_ratio < 30 and net_buy < 0:
                                results.append({
                                    "排名": i + 1,
                                    "代號": sid,
                                    "券資比": f"{round(s_ratio, 2)}%",
                                    "法人賣超": f"{int(net_buy // 1000)} 張",
                                    "今日量": f"{int(top_50.iloc[i]['Trading_Volume'] // 1000)} 張"
                                })
                        time.sleep(0.1)
                    except:
                        continue
                    bar.progress((i + 1) / 50)

                if results:
                    st.warning(f"💡 掃描完成！以下 {len(results)} 檔熱門股籌碼偏弱：")
                    st.table(pd.DataFrame(results))
                else:
                    st.success(f"🎉 掃描完成！前 50 名熱門股中（日期：{last_date}），目前沒有符合籌碼偏弱條件的股票。")

    except Exception as e:
        st.error(f"掃描失敗: {e}")
