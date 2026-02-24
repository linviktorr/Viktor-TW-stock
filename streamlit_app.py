import streamlit as st
import pandas as pd
from FinMind.data import DataLoader
from datetime import datetime, timedelta

st.set_page_config(page_title="台股籌碼選股器", layout="wide")
st.title("🔍 台股籌碼過濾器")

# 側邊欄設定
target = st.sidebar.text_input("輸入股票代碼", "2330")
st.sidebar.info("條件：券資比 < 30% 且 法人賣超")

dl = DataLoader()

# 設定抓取日期（抓最近 10 天確保有資料）
end_dt = datetime.now().strftime('%Y-%m-%d')
start_dt = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')

try:
    with st.spinner('籌碼資料讀取中...'):
        # 1. 抓取融資融券
        df_margin = dl.taiwan_stock_margin_purchase_short_sale(
            stock_id=target, start_date=start_dt, end_date=end_dt
        )
        # 2. 抓取法人買賣超
        df_inst = dl.taiwan_stock_institutional_investors(
            stock_id=target, start_date=start_dt, end_date=end_dt
        )

    # 檢查資料是否存在
    if df_margin is not None and not df_margin.empty and df_inst is not None and not df_inst.empty:
        
        # --- 邏輯計算 ---
        last_margin = df_margin.iloc[-1]
        # 券資比 = (融券餘額 / 融資餘額) * 100
        short_ratio = (last_margin['Short_Sale_Balance'] / last_margin['Margin_Purchase_Balance']) * 100
        
        # 法人合計買賣超 (三大法人相加)
        last_inst = df_inst.tail(3) # 抓最近一天的三大法人資料
        total_inst_buy = last_inst['buy'].sum() - last_inst['sell'].sum()
        
        # --- 顯示面板 ---
        st.subheader(f"籌碼分析：{target}")
        c1, c2 = st.columns(2)
        c1.metric("券資比", f"{round(short_ratio, 2)}%")
        c2.metric("法人合計買賣超", f"{int(total_inst_buy)} 股")

        # --- 判斷條件 ---
        cond1 = short_ratio < 30
        cond2 = total_inst_buy < 0 # 賣超
        
        if cond1 and cond2:
            st.warning("⚠️ 符合條件：券資比低於 30% 且法人正在賣超 (籌碼面較弱)")
        else:
            st.info("✅ 尚未完全符合篩選條件。")

        # 顯示原始資料表供參考
        with st.expander("查看詳細籌碼數據"):
            st.write("融資融券紀錄", df_margin.tail())
            st.write("法人買賣紀錄", df_inst.tail(3))
            
    else:
        st.error("無法取得該股籌碼資料，請確認代碼或今日資料是否已更新。")

except Exception as e:
    st.error(f"分析時發生錯誤: {e}")
    st.info("提示：如果出現 'data' 錯誤，代表 API 伺服器目前無法回傳該股籌碼。")
