import streamlit as st
import pandas as pd
from FinMind.data import DataLoader
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="籌碼除錯雷達", layout="wide")

st.title("🛡️ 籌碼雷達：終極除錯版")

# --- 側邊欄：設定區 ---
st.sidebar.header("⚙️ API 設定")
api_token = st.sidebar.text_input("輸入 FinMind Token (選填)", type="password")
st.sidebar.info("💡 若沒資料，請至 FinMind 官網註冊並取得免費 Token。")

# --- 介面說明 ---
with st.expander("📝 選股邏輯標註 (目前條件：分開並列)", expanded=True):
    st.markdown("""
    1. **券資比 > 30%**：高券資比，具備軋空潛能。
    2. **券資比 < 30%**：低券資比，籌碼相對冷靜。
    3. **法人買賣超**：反映大戶最新動態 (今日顯示所有買賣數值)。
    """)

# --- 初始化 ---
dl = DataLoader()
if api_token:
    dl.login_token(api_token)

# 讓使用者可以自訂要掃描的代號
default_stocks = "2408,2344,2337,3260,8299,6239"
input_stocks = st.text_input("請輸入要掃描的股票代號 (逗號隔開)", default_stocks)
stocks_list = [s.strip() for s in input_stocks.split(",")]

# 日期設定 (往前推 30 天確保有舊資料可以對比)
end_dt = datetime.now().strftime('%Y-%m-%d')
start_dt = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

if st.button("🚀 開始強力掃描"):
    all_results = []
    progress_bar = st.progress(0)
    msg = st.empty()
    
    for i, sid in enumerate(stocks_list):
        msg.text(f"📡 正在嘗試聯繫 API 抓取: {sid}...")
        try:
            # 抓取資料
            df_m = dl.taiwan_stock_margin_purchase_short_sale(stock_id=sid, start_date=start_dt, end_date=end_dt)
            df_i = dl.taiwan_stock_institutional_investors(stock_id=sid, start_date=start_dt, end_date=end_dt)
            
            # 檢查資料是否存在
            if df_m is not None and not df_m.empty and df_i is not None and not df_i.empty:
                # 取得最新一筆非零資券
                valid_m = df_m[df_m['Margin_Purchase_Balance'] > 0]
                m_row = valid_m.iloc[-1] if not valid_m.empty else df_m.iloc[-1]
                
                ss = m_row.get('Short_Sale_Balance', 0)
                mp = m_row.get('Margin_Purchase_Balance', 1)
                short_ratio = round((ss / mp) * 100, 2)
                
                # 法人買賣合計 (近 3 日)
                net_buy = int((df_i.tail(3)['buy'].sum() - df_i.tail(3)['sell'].sum()) // 1000)
                
                all_results.append({
                    "股票代號": sid,
                    "券資比(%)": short_ratio,
                    "法人買賣(張)": net_buy,
                    "最後更新日": m_row['date'],
                    "類別": "🔥 高券資比" if short_ratio > 30 else "❄️ 低券資比"
                })
            else:
                st.warning(f"⚠️ {sid}: API 回傳空資料，可能該標的今日尚未結算。")
            
            time.sleep(0.3) # 增加延遲避免被擋
        except Exception as e:
            st.error(f"❌ 抓取 {sid} 時出錯: {e}")
        
        progress_bar.progress((i + 1) / len(stocks_list))

    msg.empty()

    if all_results:
        df = pd.DataFrame(all_results)
        
        # --- 分開列出 ---
        t1, t2, t3 = st.tabs(["📊 全部結果", "🚀 券資比 > 30%", "📉 券資比 < 30%"])
        
        with t1:
            st.write("### 所有監控標的一覽")
            st.dataframe(df, use_container_width=True)
            
        with t2:
            high_m = df[df["券資比(%)"] > 30]
            if not high_m.empty:
                st.success(f"發現 {len(high_m)} 檔高券資比股票")
                st.table(high_m)
            else:
                st.info("目前沒有券資比 > 30% 的標的。")
                
        with t3:
            low_m = df[df["券資比(%)"] <= 30]
            if not low_m.empty:
                st.write(f"共有 {len(low_m)} 檔低券資比股票")
                st.dataframe(low_m, use_container_width=True)
                
        # 加強分析：法人買超分開顯示
        st.divider()
        st.subheader("🏢 法人資金額外分析")
        buy_df = df[df["法人買賣(張)"] > 0]
        sell_df = df[df["法人買賣(張)"] < 0]
        
        c1, c2 = st.columns(2)
        c1.metric("法人買超標的數", len(buy_df))
        c2.metric("法人賣超標的數", len(sell_df))
        
        if not buy_df.empty:
            st.write("✅ **法人正在買進的標的：**")
            st.dataframe(buy_df)
    else:
        st.error("😭 還是沒有資料。請檢查：1. 是否為休市日？ 2. 是否需要申請 FinMind Token？")
