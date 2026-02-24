import streamlit as st
import pandas as pd
from FinMind.data import DataLoader
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="0050 籌碼雷達", layout="wide")

# --- 介面頂部：選股邏輯說明 ---
st.title("📡 0050 成分股：籌碼動向雷達")
with st.expander("ℹ️ 點擊查看選股邏輯與篩選範圍", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        ### 🔍 篩選邏輯
        1. **券資比 < 30%**：
           - 代表市場放空力道弱，缺乏「軋空」動能。
           - 若股價下跌，較無空頭回補的支撐。
        2. **法人賣超 (近 3 日合計)**：
           - 三大法人（外資、投信、自營商）呈現淨賣出狀態。
           - 代表聰明錢正撤離該標的。
        """)
    with col2:
        st.markdown("""
        ### 🎯 篩選範圍
        - **元大台灣 50 (0050)**：
           - 包含台灣市值最大的 50 檔公司。
           - 這些股票流動性最高，是法人主要進出的戰場。
        """)

# --- 初始化 API ---
dl = DataLoader()
end_dt = datetime.now().strftime('%Y-%m-%d')
start_dt = (datetime.now() - timedelta(days=20)).strftime('%Y-%m-%d')

if st.button("🚀 開始全自動掃描 0050 成分股"):
    try:
        with st.spinner('正在獲取 0050 最新成分股名單...'):
            # 自動抓取 0050 成分股
            df_0050 = dl.taiwan_stock_holding_shares(
                stock_id='0050', 
                start_date=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            )
            # 取得最新的成分股清單
            latest_date = df_0050['date'].max()
            stock_list = df_0050[df_0050['date'] == latest_date]['holding_stock_id'].unique().tolist()
            # 確保只取前 50 檔（排除現金等）
            stock_list = [s for s in stock_list if len(s) == 4][:50]
        
        st.write(f"✅ 已成功抓取 **{len(stock_list)}** 檔成分股名單 (基準日: {latest_date})")

        results = []
        bar = st.progress(0)
        status = st.empty()
        
        for i, sid in enumerate(stock_list):
            status.text(f"正在分析第 {i+1}/50 檔：{sid}")
            try:
                # 抓取資券與法人資料
                df_m = dl.taiwan_stock_margin_purchase_short_sale(stock_id=sid, start_date=start_dt, end_date=end_dt)
                df_i = dl.taiwan_stock_institutional_investors(stock_id=sid, start_date=start_dt, end_date=end_dt)
                
                if df_m is not None and not df_m.empty and df_i is not None and not df_i.empty:
                    # 抓取最近一筆有意義的資券數字
                    valid_m = df_m[df_m['Margin_Purchase_Balance'] > 0]
                    if not valid_m.empty:
                        m_row = valid_m.iloc[-1]
                        short_ratio = (m_row['Short_Sale_Balance'] / m_row['Margin_Purchase_Balance']) * 100
                        m_date = m_row['date']
                    else:
                        short_ratio, m_date = 0, "無資料"

                    # 計算法人近 3 日合計
                    net_buy = df_i.tail(3)['buy'].sum() - df_i.tail(3)['sell'].sum()
                    
                    # 篩選條件
                    if short_ratio < 30 and net_buy < 0:
                        results.append({
                            "代號": sid,
                            "資券日期": m_date,
                            "券資比": f"{round(short_ratio, 2)}%",
                            "法人賣超 (張)": int(abs(net_buy)//1000)
                        })
                time.sleep(0.1)
            except:
                continue
            bar.progress((i + 1) / len(stock_list))

        status.empty()
        if results:
            st.warning(f"🔍 掃描完成！符合「籌碼偏弱」條件的股票如下：")
            st.dataframe(pd.DataFrame(results), use_container_width=True)
        else:
            st.success("🎉 掃描完成！0050 成分股目前籌碼面尚無集體轉弱跡象。")

    except Exception as e:
        st.error(f"系統發生錯誤: {e}")
