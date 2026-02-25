import streamlit as st
import pandas as pd
from FinMind.data import DataLoader
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="記憶體籌碼分析", layout="wide")

st.title("💾 記憶體產業：籌碼雷達 (穩定版)")

with st.sidebar:
    st.header("🔑 帳號設定")
    user_token = st.text_input("輸入 Token (若無請留空)", type="password")
    if not user_token:
        st.warning("⚠️ 未輸入 Token，抓取次數將受限，可能導致報錯。")

# --- 介面說明 ---
st.markdown("""
### 📊 選股邏輯
- **左側列表**：券資比 **> 30%** (觀察是否有軋空動能)。
- **右側列表**：券資比 **< 30%** (觀察籌碼是否安定)。
- **法人買賣超**：合計近 3 日張數，幫助確認大戶方向。
""")

dl = DataLoader()
if user_token:
    try:
        dl.login(token=user_token)
    except:
        st.sidebar.error("Token 無效")

# 縮減清單，在沒 Token 的情況下增加成功率
stocks_memory = ["2408", "2344", "2337", "3260", "8299", "6239"]

if st.button("🚀 開始掃描"):
    results = []
    bar = st.progress(0)
    
    # 日期設定
    end_dt = datetime.now().strftime('%Y-%m-%d')
    start_dt = (datetime.now() - timedelta(days=40)).strftime('%Y-%m-%d')

    for i, sid in enumerate(stocks_memory):
        try:
            # 抓取資料
            df_m = dl.taiwan_stock_margin_purchase_short_sale(stock_id=sid, start_date=start_dt, end_date=end_dt)
            df_i = dl.taiwan_stock_institutional_investors(stock_id=sid, start_date=start_dt, end_date=end_dt)
            
            # 檢查是否有資料 (排除 None 或空值)
            if df_m is not None and not df_m.empty and df_i is not None and not df_i.empty:
                # 取得最近一次有效的資券數據
                valid_m = df_m[df_m['Margin_Purchase_Balance'] > 0]
                if not valid_m.empty:
                    m_row = valid_m.iloc[-1]
                    short_ratio = round((m_row['Short_Sale_Balance'] / m_row['Margin_Purchase_Balance']) * 100, 2)
                    net_buy = int((df_i.tail(3)['buy'].sum() - df_i.tail(3)['sell'].sum()) // 1000)
                    
                    results.append({
                        "代號": sid,
                        "券資比(%)": short_ratio,
                        "法人買賣(張)": net_buy,
                        "資料日期": m_row['date']
                    })
            
            # 重要：沒 Token 時，每次抓取間隔要拉長，否則會被 API 踢掉
            time.sleep(1.0 if not user_token else 0.2)
        except Exception as e:
            st.write(f"⚠️ {sid} 抓取受限")
            continue
        
        bar.progress((i + 1) / len(stocks_memory))

    if results:
        df = pd.DataFrame(results)
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔥 券資比 > 30%")
            high_df = df[df["券資比(%)"] > 30]
            st.table(high_df) if not high_df.empty else st.write("無資料")

        with col2:
            st.subheader("❄️ 券資比 < 30%")
            low_df = df[df["券資比(%)"] <= 30]
            st.table(low_df) if not low_df.empty else st.write("無資料")
    else:
        st.error("❌ 抓取失敗。這通常是 API 偵測到頻繁存取，請稍後再試或使用 Token。")

st.divider()
st.caption("提示：記憶體類股波動大，券資比升高時應注意是否伴隨法人買超。")
