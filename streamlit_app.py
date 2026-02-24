import streamlit as st
import pandas as pd
from FinMind.data import DataLoader
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="0050 籌碼雷達", layout="wide")

# --- 介面頂部：說明看板 ---
st.title("📡 0050 成分股：籌碼動向雷達")
with st.expander("ℹ️ 查看選股邏輯與篩選範圍", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🔍 篩選邏輯\n1. **券資比 < 30%**：缺乏軋空動能。\n2. **法人賣超 (近 3 日)**：大戶撤出。")
    with col2:
        st.markdown("### 🎯 篩選範圍\n- **元大台灣 50 (0050)**：市值前 50 大企業。")

# --- 初始化 ---
dl = DataLoader()
today_dt = datetime.now().strftime('%Y-%m-%d')
start_dt = (datetime.now() - timedelta(days=20)).strftime('%Y-%m-%d')

# 修正變數名稱：不能以數字開頭
stocks_0050 = [
    "2330", "2317", "2454", "2308", "2382", "2412", "2303", "2881", "2882", "2603",
    "2891", "3711", "2357", "2886", "1301", "2609", "1216", "2884", "2880", "2301",
    "2892", "2885", "5880", "2324", "1303", "2002", "2912", "3008", "2379", "6669",
    "3034", "3037", "3231", "2395", "1101", "4904", "2890", "2615", "5871", "4938",
    "2408", "2345", "1326", "2207", "1402", "2105", "5876", "9904", "1605", "2354"
]

if st.button("🚀 開始掃描 0050 成分股"):
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, sid in enumerate(stocks_0050):
        status_text.text(f"分析中 ({i+1}/50): {sid}")
        try:
            df_m = dl.taiwan_stock_margin_purchase_short_sale(stock_id=sid, start_date=start_dt, end_date=today_dt)
            df_i = dl.taiwan_stock_institutional_investors(stock_id=sid, start_date=start_dt, end_date=today_dt)
            
            if df_m is not None and not df_m.empty and df_i is not None and not df_i.empty:
                valid_m = df_m[df_m['Margin_Purchase_Balance'] > 0]
                m_row = valid_m.iloc[-1] if not valid_m.empty else df_m.iloc[-1]
                
                ss = m_row.get('Short_Sale_Balance', 0)
                mp = m_row.get('Margin_Purchase_Balance', 1)
                short_ratio = (ss / mp) * 100
                
                net_buy = df_i.tail(3)['buy'].sum() - df_i.tail(3)['sell'].sum()
                
                if short_ratio < 30 and net_buy < 0:
                    results.append({
                        "代號": sid,
                        "券資比日期": m_row['date'],
                        "券資比": round(short_ratio, 2),
                        "法人賣超(張)": int(abs(net_buy)//1000)
                    })
            time.sleep(0.05)
        except:
            continue
        progress_bar.progress((i + 1) / len(stocks_0050))

    status_text.empty()
    
    if results:
        # 轉換為 DataFrame 並排序 (依賣超張數排序)
        df_res = pd.DataFrame(results).sort_values("法人賣超(張)", ascending=False)
        
        # --- 警告牆功能 ---
        st.subheader("⚠️ 籌碼轉弱警告牆")
        top_3 = df_res.head(3)
        cols = st.columns(len(top_3))
        for idx, row in enumerate(top_3.itertuples()):
            with cols[idx]:
                st.error(f"**{row.代號}**")
                st.metric("法人賣超", f"{row.法人賣超(張)} 張")
                st.caption(f"券資比: {row.券資比}%")

        st.divider()
        st.write("🔍 詳細掃描清單：")
        st.dataframe(df_res, use_container_width=True)
    else:
        st.success("🎉 掃描完成！目前 0050 成分股籌碼面表現穩健。")
