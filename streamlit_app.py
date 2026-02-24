import streamlit as st
import pandas as pd
from FinMind.data import DataLoader
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="熱門股籌碼掃描", layout="wide")
st.title("🔥 熱門股雷達：成交量前 50 名")

dl = DataLoader()

# 設定日期：往前抓 10 天，確保至少能跨過一個週末
end_dt = datetime.now().strftime('%Y-%m-%d')
start_dt = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')

if st.button("🚀 開始掃描前 50 名熱門股"):
    try:
        with st.spinner('獲取市場行情中...'):
            # 抓取全市場資料
            df_all = dl.taiwan_stock_daily(start_date=start_dt, end_date=end_dt)
            
            # 關鍵保護：檢查回傳格式
            if df_all is None or not isinstance(df_all, pd.DataFrame) or df_all.empty:
                st.error("❌ 無法取得行情資料 (KeyError: 'data')。可能是 API 伺服器正在更新。")
                st.info("建議：請在收盤後一小時 (14:30後) 再試，或檢查網路連線。")
            else:
                # 找到最新的交易日
                last_date = df_all['date'].max()
                df_ticks = df_all[df_all['date'] == last_date]
                
                # 取成交量前 50 名 (Trading_Volume)
                top_50 = df_ticks.sort_values(by='Trading_Volume', ascending=False).head(50)
                top_50_list = top_50['stock_id'].tolist()
                
                st.write(f"📅 基準日期：{last_date} (已取得 {len(top_50_list)} 檔熱門股)")

                results = []
                bar = st.progress(0)
                status = st.empty()
                
                for i, sid in enumerate(top_50_list):
                    status.text(f"分析中 ({i+1}/50): {sid}")
                    try:
                        # 抓取籌碼（資券與法人）
                        # 這裡使用最近 15 天確保有足夠樣本
                        chip_start = (datetime.now() - timedelta(days=15)).strftime('%Y-%m-%d')
                        df_m = dl.taiwan_stock_margin_purchase_short_sale(stock_id=sid, start_date=chip_start, end_date=end_dt)
                        df_i = dl.taiwan_stock_institutional_investors(stock_id=sid, start_date=chip_start, end_date=end_dt)
                        
                        if df_m is not None and not df_m.empty and df_i is not None and not df_i.empty:
                            # 券資比計算
                            m = df_m.iloc[-1]
                            ss = m.get('Short_Sale_Balance', 0)
                            mp = m.get('Margin_Purchase_Balance', 1)
                            short_ratio = (ss / mp) * 100
                            
                            # 三大法人買賣超 (最近 3 天合計)
                            inst_recent = df_i.tail(3)
                            net_buy = inst_recent['buy'].sum() - inst_recent['sell'].sum()
                            
                            if short_ratio < 30 and net_buy < 0:
                                results.append({
                                    "排名": i + 1,
                                    "代號": sid,
                                    "券資比": f"{round(short_ratio, 2)}%",
                                    "法人賣超": f"{int(net_buy // 1000)} 張",
                                    "今日量": f"{int(top_50.iloc[i]['Trading_Volume'] // 1000)} 張"
                                })
                        time.sleep(0.05) # 稍微加速但保持禮貌
                    except:
                        continue
                    bar.progress((i + 1) / 50)

                status.empty()
                if results:
                    st.warning("⚠️ 掃描完成！符合籌碼轉弱條件的股票如下：")
                    st.table(pd.DataFrame(results))
                else:
                    st.success("🎉 掃描完成！目前熱門股籌碼尚未出現集體轉弱跡象。")

    except Exception as e:
        st.error(f"掃描過程中出錯: {e}")
