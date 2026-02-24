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
    st.info("💡 邏輯：若今日(2/24)資券尚未結算，系統會自動追溯至 2/23 或更早。")

# --- 選股邏輯看板 ---
st.info("### 📋 篩選邏輯標註\n"
        "1. **分組顯示**：依「券資比 30%」為界線分開列表。\n"
        "2. **法人動向**：觀測近 3 日三大法人買賣超張數合計。\n"
        "3. **資料日期**：顯示該筆資券數據的實際產出日期，確保非空值。")

dl = DataLoader()

if user_token:
    try:
        dl.login(token=user_token)
    except:
        st.sidebar.error("Token 驗證失敗")

# 記憶體核心清單
stocks_memory = ["2408", "2344", "2337", "3260", "8299", "6239", "3006", "4967"]

if st.button("🚀 執行強力掃描 (含自動回溯)"):
    if not user_token:
        st.error("❌ 請輸入 Token。API 需要驗證才能提供完整的資券歷史資料。")
    else:
        results = []
        progress_bar = st.progress(0)
        status = st.empty()
        
        # 設定日期：往前抓足 40 天，確保能跨過農曆年或長假
        end_dt = datetime.now().strftime('%Y-%m-%d')
        start_dt = (datetime.now() - timedelta(days=40)).strftime('%Y-%m-%d')
        
        for i, sid in enumerate(stocks_memory):
            status.text(f"📡 正在深度分析: {sid}...")
            try:
                # 抓取資料
                df_m = dl.taiwan_stock_margin_purchase_short_sale(stock_id=sid, start_date=start_dt, end_date=end_dt)
                df_i = dl.taiwan_stock_institutional_investors(stock_id=sid, start_date=start_dt, end_date=end_dt)
                
                # 關鍵邏輯：檢查 DataFrame 且必須有實質內容
                if isinstance(df_m, pd.DataFrame) and not df_m.empty and \
                   isinstance(df_i, pd.DataFrame) and not df_i.empty:
                    
                    # 排除融資餘額為 0 的無效天數（通常是當天尚未結算）
                    valid_m = df_m[df_m['Margin_Purchase_Balance'] > 0]
                    
                    if not valid_m.empty:
                        m_row = valid_m.iloc[-1] # 抓取最近有數字的那一天
                        
                        ss = m_row.get('Short_Sale_Balance', 0)
                        mp = m_row.get('Margin_Purchase_Balance', 1) # 防呆除以一
                        short_ratio = round((ss / mp) * 100, 2)
                        
                        # 計算法人合計
                        net_buy = int((df_i.tail(3)['buy'].sum() - df_i.tail(3)['sell'].sum()) // 1000)
                        
                        results.append({
                            "代號": sid,
                            "券資比(%)": short_ratio,
                            "法人買賣(張)": net_buy,
                            "資料日期": m_row['date']
                        })
                
                time.sleep(0.2) # 適度延遲
            except:
                continue
            
            progress_bar.progress((i + 1) / len(stocks_memory))

        status.empty()

        if results:
            df = pd.DataFrame(results)
            
            # --- 依照要求：分開顯示 ---
            col_high, col_low = st.columns(2)
            
            with col_high:
                st.subheader("🔥 券資比 > 30%")
                high_df = df[df["券資比(%)"] > 30]
                if not high_df.empty:
                    st.table(high_df.sort_values("券資比(%)", ascending=False))
                else:
                    st.write("目前無高券資比標的")

            with col_low:
                st.subheader("❄️ 券資比 < 30%")
                low_df = df[df["券資比(%)"] <= 30]
                if not low_df.empty:
                    st.table(low_df.sort_values("法人買賣(張)", ascending=False))
                else:
                    st.write("目前無低券資比標的")
                    
            # 加碼：法人買超清單
            st.divider()
            st.success("💎 法人買超焦點標的")
            st.dataframe(df[df["法人買賣(張)"] > 0].sort_values("法人買賣(張)", ascending=False), use_container_width=True)
            
        else:
            st.error("😭 依舊抓不到資料。這通常代表 Token 無法在伺服器端通過驗證。")
            st.info("建議檢查：1. Token 是否包含空格？ 2. FinMind 帳號是否已完成 Email 驗證？")
