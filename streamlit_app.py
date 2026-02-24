import streamlit as st
import pandas as pd
from FinMind.data import DataLoader
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="台股全市場籌碼掃描", layout="wide")
st.title("📡 全市場掃描器：券資比 < 30% 且 法人賣超")

dl = DataLoader()

# 設定日期
end_dt = datetime.now().strftime('%Y-%m-%d')
start_dt = (datetime.now() - timedelta(days=15)).strftime('%Y-%m-%d')

if st.button("🚀 開始全市場掃描 (示範前 20 檔)"):
    try:
        # 1. 取得所有股票清單
        stock_info = dl.taiwan_stock_info()
        # 篩選出普通的股票 (排除權證、ETF)
        stock_list = stock_info[stock_info['type'] == 'twstock']['stock_id'].tolist()
        
        # 為了測試，我們先取前 20 檔，避免 App 跑太久當機
        test_list = stock_list[:20] 
        
        results = []
        progress_text = st.empty()
        bar = st.progress(0)

        for i, sid in enumerate(test_list):
            progress_text.text(f"正在分析第 {i+1}/{len(test_list)} 檔：{sid}")
            
            try:
                # 抓取資券
                df_m = dl.taiwan_stock_margin_purchase_short_sale(stock_id=sid, start_date=start_dt, end_date=end_dt)
                # 抓取法人
                df_i = dl.taiwan_stock_institutional_investors(stock_id=sid, start_date=start_dt, end_date=end_dt)
                
                if not df_m.empty and not df_i.empty:
                    m = df_m.iloc[-1]
                    # 安全計算券資比
                    ss = m.get('Short_Sale_Balance', 0)
                    mp = m.get('Margin_Purchase_Balance', 1) # 避免除以0
                    short_ratio = (ss / mp) * 100
                    
                    # 法人買賣超 (最近三天加總)
                    inst_sum = df_i.tail(3)['buy'].sum() - df_i.tail(3)['sell'].sum()
                    
                    # 符合條件：券資比 < 30% 且 法人賣超
                    if short_ratio < 30 and inst_sum < 0:
                        results.append({
                            "代號": sid,
                            "券資比": f"{round(short_ratio, 2)}%",
                            "法人賣超量": int(inst_sum),
                            "狀態": "⚠️ 籌碼轉弱"
                        })
                
                # 稍微停頓避免被 API 封鎖
                time.sleep(0.1)
                
            except:
                continue
            
            bar.progress((i + 1) / len(test_list))

        progress_text.text("✅ 掃描完成！")

        if results:
            st.write(f"🔍 掃描完畢，共有 {len(results)} 檔符合條件：")
            st.table(pd.DataFrame(results))
        else:
            st.info("符合條件的股票目前為 0 檔。")

    except Exception as e:
        st.error(f"掃描失敗: {e}")

st.info("💡 註：由於全市場有 1,700 檔，正式版建議分產業或分權重掃描，以確保執行速度。")
