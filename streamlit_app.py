import streamlit as st
import pandas as pd
from FinMind.data import DataLoader
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="記憶體強勢軋空雷達", layout="wide")

# --- 介面說明與選股邏輯 ---
st.title("📈 記憶體產業：強勢軋空雷達")

with st.expander("ℹ️ 點擊查看【強勢選股邏輯】", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        ### 🚀 多頭核心指標
        1. **券資比 > 30%**：
           - 市場空單比例高，具備潛在「軋空」動能。
           - 當股價上漲，空頭回補將助長漲勢。
        2. **法人買超 (近 3 日合計)**：
           - 三大法人站在買方，代表大戶看好未來產業走勢。
        """)
    with col2:
        st.markdown("""
        ### 🎯 篩選族群：記憶體與模組
        - 包含：南亞科、華邦電、旺宏、群聯、威剛等。
        - 記憶體族群具備高波動特性，最容易出現軋空行情。
        """)

# --- 初始化 ---
dl = DataLoader()
today_dt = datetime.now().strftime('%Y-%m-%d')
start_dt = (datetime.now() - timedelta(days=20)).strftime('%Y-%m-%d')

# 記憶體族群清單
stocks_memory = [
    "2408", "2344", "2337", "3260", "8299", 
    "3006", "4967", "6239", "8110", "2451", 
    "3532", "6485", "6573", "5289"
]

if st.button("🚀 開始掃描記憶體族群"):
    res_both = []   # 強勢軋空 (兩項皆符合)
    res_margin = [] # 具備軋空潛力 (僅券資比高)
    res_inst = []   # 法人看好 (僅法人買超)
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, sid in enumerate(stocks_memory):
        status_text.text(f"分析中 ({i+1}/{len(stocks_memory)}): {sid}")
        try:
            df_m = dl.taiwan_stock_margin_purchase_short_sale(stock_id=sid, start_date=start_dt, end_date=today_dt)
            df_i = dl.taiwan_stock_institutional_investors(stock_id=sid, start_date=start_dt, end_date=today_dt)
            
            if df_m is not None and not df_m.empty and df_i is not None and not df_i.empty:
                # 1. 計算券資比 (取最新有效資料)
                valid_m = df_m[df_m['Margin_Purchase_Balance'] > 0]
                m_row = valid_m.iloc[-1] if not valid_m.empty else df_m.iloc[-1]
                short_ratio = round((m_row.get('Short_Sale_Balance', 0) / m_row.get('Margin_Purchase_Balance', 1)) * 100, 2)
                
                # 2. 計算法人近 3 日買賣 (張數)
                net_buy = int((df_i.tail(3)['buy'].sum() - df_i.tail(3)['sell'].sum()) // 1000)
                
                # 3. 分類邏輯 (新：多頭策略)
                cond_margin = short_ratio > 30
                cond_inst = net_buy > 0
                
                data_item = {"代號": sid, "券資比": f"{short_ratio}%", "法人買超(張)": net_buy, "更新日期": m_row['date']}
                
                if cond_margin and cond_inst:
                    res_both.append(data_item)
                elif cond_margin:
                    res_margin.append({"代號": sid, "券資比": f"{short_ratio}%", "更新日期": m_row['date']})
                elif cond_inst:
                    res_inst.append({"代號": sid, "法人買超(張)": net_buy, "更新日期": m_row['date']})
            
            time.sleep(0.1)
        except:
            continue
        progress_bar.progress((i + 1) / len(stocks_memory))

    status_text.empty()

    # --- 顯示結果 ---
    tab1, tab2, tab3 = st.tabs(["🔥 強勢軋空區 (雙重符合)", "📈 高券資比 (潛在軋空)", "💎 法人佈局 (純買超)"])

    with tab1:
        if res_both:
            st.success(f"發現 {len(res_both)} 檔標的符合【強勢軋空】條件！")
            st.table(pd.DataFrame(res_both))
            st.balloons()
        else:
            st.info("目前記憶體族群中尚無標的同時符合【券資比>30%】與【法人買超】。")

    with tab2:
        if res_margin:
            st.warning(f"共有 {len(res_margin)} 檔標的【券資比 > 30%】，具備軋空動能。")
            st.dataframe(pd.DataFrame(res_margin), use_container_width=True)
        else:
            st.write("查無資料")

    with tab3:
        if res_inst:
            st.info(f"共有 {len(res_inst)} 檔標的【法人近期買超】，大戶進場。")
            st.dataframe(pd.DataFrame(res_inst).sort_values("法人買超(張)", ascending=False), use_container_width=True)
        else:
            st.write("查無資料")

st.divider()
st.caption("⚠️ 警語：軋空行情波動劇烈，請務必配合技術面（如股價站上 5 日線）進行操作。")
