import streamlit as st
import pandas as pd
from FinMind.data import DataLoader
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="記憶體籌碼分析儀", layout="wide")

st.title("💾 記憶體族群：籌碼動向雷達")

# --- API 登入區 ---
with st.sidebar:
    st.header("🔑 權限設定")
    user_token = st.text_input("請輸入 FinMind Token (必填)", type="password")
    st.info("註冊 FinMind 官網即可免費取得 Token，解決 'data' 報錯問題。")

# --- 邏輯標註 ---
with st.expander("📝 選股邏輯說明", expanded=True):
    st.markdown("""
    - **強勢區**：券資比 > 30%（具軋空動能）。
    - **穩健區**：券資比 < 30%（籌碼相對安定）。
    - **核心條件**：皆需搭配 **法人買賣超** 進行觀察。
    """)

dl = DataLoader()
if user_token:
    dl.login_token(user_token)

# 記憶體清單
stocks_memory = ["2408", "2344", "2337", "3260", "8299", "6239", "3006"]

if st.button("🚀 執行深度掃描"):
    if not user_token:
        st.error("❌ 請先在左側輸入 Token，否則 API 會拒絕連線並顯示 'data' 錯誤。")
    else:
        all_data = []
        progress_bar = st.progress(0)
        status = st.empty()
        
        for i, sid in enumerate(stocks_memory):
            status.text(f"正在連線抓取: {sid}...")
            try:
                # 抓取資料並增加檢查
                df_m = dl.taiwan_stock_margin_purchase_short_sale(stock_id=sid, start_date=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
                df_i = dl.taiwan_stock_institutional_investors(stock_id=sid, start_date=(datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d'))
                
                # 防禦性檢查：確保回傳的是有資料的 DataFrame
                if isinstance(df_m, pd.DataFrame) and not df_m.empty and isinstance(df_i, pd.DataFrame) and not df_i.empty:
                    # 追溯有效資券
                    valid_m = df_m[df_m['Margin_Purchase_Balance'] > 0]
                    m_row = valid_m.iloc[-1] if not valid_m.empty else df_m.iloc[-1]
                    
                    short_ratio = round((m_row['Short_Sale_Balance'] / m_row['Margin_Purchase_Balance']) * 100, 2)
                    net_buy = int((df_i.tail(3)['buy'].sum() - df_i.tail(3)['sell'].sum()) // 1000)
                    
                    all_data.append({
                        "代號": sid,
                        "券資比(%)": short_ratio,
                        "法人買賣(張)": net_buy,
                        "最後更新日期": m_row['date']
                    })
                else:
                    st.warning(f"⚠️ {sid}: API 未回傳有效數據，請確認 Token 是否正確或額度是否用完。")
                
                time.sleep(0.5) # 延長間隔避免被封鎖
            except Exception as e:
                st.error(f"❌ 抓取 {sid} 時發生預期外錯誤: {e}")
            
            progress_bar.progress((i + 1) / len(stocks_memory))

        status.empty()

        if all_data:
            df = pd.DataFrame(all_data)
            
            # --- 依照你的要求：分開顯示券資比大於與小於 30% ---
            st.divider()
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🔥 券資比 > 30% (高能量)")
                high_df = df[df["券資比(%)"] > 30]
                if not high_df.empty:
                    st.dataframe(high_df.sort_values("券資比(%)", ascending=False))
                else:
                    st.write("目前無高券資比標的")

            with col2:
                st.subheader("❄️ 券資比 < 30% (穩健區)")
                low_df = df[df["券資比(%)"] <= 30]
                if not low_df.empty:
                    st.dataframe(low_df.sort_values("法人買賣(張)", ascending=False))
                else:
                    st.write("目前無低券資比標的")
                    
            # 加碼顯示法人買超專區
            st.success("💎 法人買超焦點 (不分券資比)")
            st.dataframe(df[df["法人買賣(張)"] > 0].sort_values("法人買賣(張)", ascending=False))
