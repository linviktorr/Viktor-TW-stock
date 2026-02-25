import streamlit as st
import pandas as pd
from FinMind.data import DataLoader
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="記憶體籌碼全效版", layout="wide")

st.title("💾 記憶體產業：籌碼全方位雷達")

# --- 側邊欄設定 ---
with st.sidebar:
    st.header("🔑 權限設定")
    user_token = st.text_input("請輸入 FinMind Token", type="password")
    st.info("💡 提醒：請確保 GitHub 內的 requirements.txt 已加入 tqdm")

# --- 選股邏輯看板 ---
st.info("### 📋 選股邏輯標註\n"
        "1. **分組顯示**：依「券資比 30%」為界線分開列表。\n"
        "2. **法人動向**：觀測近 3 日三大法人買賣超張數合計（正數買超 / 負數賣超）。\n"
        "3. **自動回溯**：若今日數據未出，自動抓取最近一個有效交易日。")

dl = DataLoader()

if user_token:
    try:
        dl.login(token=user_token)
    except:
        st.sidebar.error("Token 驗證失敗")

# 記憶體核心名單
stocks_memory = ["2408", "2344", "2337", "3260", "8299", "6239", "3006", "4967"]

if st.button("🚀 執行強力掃描"):
    if not user_token:
        st.error("❌ 請輸入 Token。未登入狀態下頻繁抓取會導致 API 報錯。")
    else:
        results = []
        progress_bar = st.progress(0)
        status = st.empty()
        
        # 設定日期：抓取過去 30 天
        end_dt = datetime.now().strftime('%Y-%m-%d')
        start_dt = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        for i, sid in enumerate(stocks_memory):
            status.text(f"📡 正在掃描: {sid}...")
            try:
                # 抓取資券與法人
                df_m = dl.taiwan_stock_margin_purchase_short_sale(stock_id=sid, start_date=start_dt, end_date=end_dt)
                df_i = dl.taiwan_stock_institutional_investors(stock_id=sid, start_date=start_dt, end_date=end_dt)
                
                if isinstance(df_m, pd.DataFrame) and not df_m.empty and \
                   isinstance(df_i, pd.DataFrame) and not df_i.empty:
                    
                    # 追溯最新有資券餘額的日子
                    valid_m = df_m[df_m['Margin_Purchase_Balance'] > 0]
                    if not valid_m.empty:
                        m_row = valid_m.iloc[-1]
                        short_ratio = round((m_row['Short_Sale_Balance'] / m_row['Margin_Purchase_Balance']) * 100, 2)
                        
                        # 計算法人近 3 日合計
                        net_buy = int((df_i.tail(3)['buy'].sum() - df_i.tail(3)['sell'].sum()) // 1000)
                        
                        results.append({
                            "代號": sid,
                            "券資比(%)": short_ratio,
                            "法人買賣(張)": net_buy,
                            "資料日期": m_row['date']
                        })
                time.sleep(0.2)
            except:
                continue
            progress_bar.progress((i + 1) / len(stocks_memory))

        status.empty()

        if results:
            df = pd.DataFrame(results)
            col_high, col_low = st.columns(2)
            
            with col_high:
                st.subheader("🔥 券資比 > 30% (潛在軋空區)")
                high_df = df[df["券資比(%)"] > 30]
                if not high_df.empty:
                    st.table(high_df.sort_values("券資比(%)", ascending=False))
                else:
                    st.write("目前名單中無高券資比標的")

            with col_low:
                st.subheader("❄️ 券資比 < 30% (籌碼穩健區)")
                low_df = df[df["券資比(%)"] <= 30]
                if not low_df.empty:
                    st.table(low_df.sort_values("法人買賣(張)", ascending=False))
                else:
                    st.write("目前名單中無低券資比標的")
        else:
            st.error("還是抓不到資料，可能是 Token 沒寫對，或是 API 伺服器正在打瞌睡。")

st.divider()
st.caption("現在時間：2026-02-25。建議於收盤後晚間 10 點再次執行以獲取當日最新數據。")
