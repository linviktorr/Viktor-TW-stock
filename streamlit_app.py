import streamlit as st
import pandas as pd
from FinMind.data import DataLoader
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="記憶體籌碼全掃描", layout="wide")

# --- 介面說明 ---
st.title("💾 記憶體產業：籌碼全方位雷達")

with st.expander("ℹ️ 選股邏輯說明 (多頭導向)", expanded=True):
    st.markdown("""
    **本工具篩選【法人買超】之標的，並依「券資比」分為兩大類：**
    1. **強勢軋空區 (券資比 > 30%)**：大戶買進 + 空頭受壓，最具噴發潛力。
    2. **穩健佈局區 (券資比 < 30%)**：大戶買進 + 散戶未進場，適合中長線觀察。
    - *若今日資券尚未更新，系統會自動追溯至最新有資料的交易日。*
    """)

dl = DataLoader()
# 抓取過去 30 天資料確保穩定
end_dt = datetime.now().strftime('%Y-%m-%d')
start_dt = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

# 記憶體族群核心名單
stocks_memory = [
    "2408", "2344", "2337", "3260", "8299", 
    "3006", "4967", "6239", "8110", "2451",
    "3532", "6485", "5289"
]

if st.button("🚀 開始全維度掃描"):
    res_high_margin = [] # 條件 A: 券資比 > 30% & 法人買超
    res_low_margin = []  # 條件 B: 券資比 < 30% & 法人買超
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, sid in enumerate(stocks_memory):
        status_text.text(f"分析中 ({i+1}/{len(stocks_memory)}): {sid}")
        try:
            # 1. 抓取資券與法人
            df_m = dl.taiwan_stock_margin_purchase_short_sale(stock_id=sid, start_date=start_dt, end_date=end_dt)
            df_i = dl.taiwan_stock_institutional_investors(stock_id=sid, start_date=start_dt, end_date=end_dt)
            
            if df_m is not None and not df_m.empty and df_i is not None and not df_i.empty:
                # 取得最近一筆「非零」的資券資料 (自動追溯機制)
                valid_m = df_m[df_m['Margin_Purchase_Balance'] > 0]
                m_row = valid_m.iloc[-1] if not valid_m.empty else df_m.iloc[-1]
                
                ss = m_row.get('Short_Sale_Balance', 0)
                mp = m_row.get('Margin_Purchase_Balance', 1)
                short_ratio = round((ss / mp) * 100, 2)
                
                # 法人買賣合計 (近 3 日)
                net_buy = int((df_i.tail(3)['buy'].sum() - df_i.tail(3)['sell'].sum()) // 1000)
                
                # 統一多頭前提：法人必須是買超 (net_buy > 0)
                if net_buy > 0:
                    data_item = {
                        "代號": sid,
                        "券資比": f"{short_ratio}%",
                        "法人買超(張)": net_buy,
                        "資券日期": m_row['date']
                    }
                    
                    if short_ratio >= 30:
                        res_high_margin.append(data_item)
                    else:
                        res_low_margin.append(data_item)
            
            time.sleep(0.1)
        except:
            continue
        progress_bar.progress((i + 1) / len(stocks_memory))

    status_text.empty()

    # --- 顯示結果 ---
    tab1, tab2 = st.tabs(["🔥 強勢軋空區 (券資比 > 30%)", "🛡️ 穩健佈局區 (券資比 < 30%)"])

    with tab1:
        st.subheader("大戶買進 + 空頭待宰")
        if res_high_margin:
            st.success(f"發現 {len(res_high_margin)} 檔具備軋空動能")
            st.table(pd.DataFrame(res_high_margin))
        else:
            st.info("目前無標的同時符合「法人買超」且「券資比 > 30%」。")

    with tab2:
        st.subheader("大戶買進 + 散戶冷淡")
        if res_low_margin:
            st.warning(f"發現 {len(res_low_margin)} 檔法人悄悄吸貨")
            st.dataframe(pd.DataFrame(res_low_margin).sort_values("法人買超(張)", ascending=False), use_container_width=True)
        else:
            st.info("目前無標的符合「法人買超」且「券資比 < 30%」。")

st.divider()
st.caption("💡 提示：若兩個分頁都沒股票，代表法人近三日對記憶體族群主要持賣出或觀望態度。")
