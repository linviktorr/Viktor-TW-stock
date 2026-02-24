import streamlit as st
import pandas as pd
from FinMind.data import DataLoader
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="記憶體籌碼分析儀", layout="wide")

st.title("💾 記憶體產業：籌碼全維度雷達")

# --- API 登入區 ---
with st.sidebar:
    st.header("🔑 權限設定")
    user_token = st.text_input("請輸入 FinMind Token", type="password")
    st.info("💡 修正：使用 dl.login(token=...) 進行驗證")

# --- 邏輯標註 ---
with st.expander("📝 選股邏輯說明", expanded=True):
    st.markdown("""
    **本頁面將記憶體族群依「券資比」分開列出，並觀測法人動向：**
    1. **券資比 > 30%**：高券資比，具備潛在軋空動能。
    2. **券資比 < 30%**：低券資比，籌碼結構較單純。
    3. **共通核心**：需注意 **法人買賣超** 是否同步轉向。
    """)

dl = DataLoader()

# --- 修正後的登入邏輯 ---
if user_token:
    try:
        dl.login(token=user_token) # 這裡修正了方法名稱
    except Exception as e:
        st.sidebar.error(f"登入失敗: {e}")

# 記憶體清單
stocks_memory = ["2408", "2344", "2337", "3260", "8299", "6239", "3006", "4967"]

if st.button("🚀 執行強力掃描"):
    if not user_token:
        st.error("❌ 請在左側輸入 FinMind Token。未登入狀態下頻繁抓取會導致 'data' 錯誤。")
    else:
        all_data = []
        progress_bar = st.progress(0)
        status = st.empty()
        
        # 設定日期
        end_dt = datetime.now().strftime('%Y-%m-%d')
        start_dt = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        for i, sid in enumerate(stocks_memory):
            status.text(f"📡 掃描中: {sid}...")
            try:
                # 抓取資券 (Margin) 與 法人 (Institutional)
                df_m = dl.taiwan_stock_margin_purchase_short_sale(stock_id=sid, start_date=start_dt, end_date=end_dt)
                df_i = dl.taiwan_stock_institutional_investors(stock_id=sid, start_date=start_dt, end_date=end_dt)
                
                # 嚴謹檢查：確保回傳的是含有資料的 DataFrame
                if isinstance(df_m, pd.DataFrame) and not df_m.empty and isinstance(df_i, pd.DataFrame) and not df_i.empty:
                    # 追溯最新有意義的資券日期
                    valid_m = df_m[df_m['Margin_Purchase_Balance'] > 0]
                    m_row = valid_m.iloc[-1] if not valid_m.empty else df_m.iloc[-1]
                    
                    short_ratio = round((m_row['Short_Sale_Balance'] / m_row['Margin_Purchase_Balance']) * 100, 2)
                    net_buy = int((df_i.tail(3)['buy'].sum() - df_i.tail(3)['sell'].sum()) // 1000)
                    
                    all_data.append({
                        "代號": sid,
                        "券資比(%)": short_ratio,
                        "法人買賣(張)": net_buy,
                        "最後日期": m_row['date']
                    })
                
                time.sleep(0.3)
            except Exception as e:
                # 即使某一檔失敗也繼續執行，不崩潰
                continue
            
            progress_bar.progress((i + 1) / len(stocks_memory))

        status.empty()

        if all_data:
            df = pd.DataFrame(all_data)
            
            # --- 分開列出邏輯 ---
            st.divider()
            high_col, low_col = st.columns(2)
            
            with high_col:
                st.subheader("🔥 券資比 > 30%")
                high_df = df[df["券資比(%)"] > 30]
                if not high_df.empty:
                    st.table(high_df.sort_values("券資比(%)", ascending=False))
                else:
                    st.info("目前無標的券資比 > 30%")

            with low_col:
                st.subheader("❄️ 券資比 < 30%")
                low_df = df[df["券資比(%)"] <= 30]
                if not low_df.empty:
                    st.table(low_df.sort_values("法人買賣(張)", ascending=False))
                else:
                    st.info("目前無標的券資比 < 30%")
                    
            # 額外分析法人方向
            st.divider()
            st.subheader("💎 法人買超焦點 Top 3")
            top_buy = df[df["法人買賣(張)"] > 0].sort_values("法人買賣(張)", ascending=False).head(3)
            if not top_buy.empty:
                st.dataframe(top_buy, use_container_width=True)
            else:
                st.warning("⚠️ 法人目前對記憶體族群無明顯買超。")
        else:
            st.error("無法抓取到資料。請檢查 Token 是否過期或網路狀態。")
