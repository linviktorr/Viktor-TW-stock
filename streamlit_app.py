 import streamlit as st
import pandas as pd
from FinMind.data import DataLoader
from datetime import datetime, timedelta

st.set_page_config(page_title="台股籌碼過濾器", layout="wide")
st.title("🔍 台股籌碼過濾器 (自動偵測版)")

target = st.sidebar.text_input("輸入股票代碼", "2330")
dl = DataLoader()

# 設定抓取日期
end_dt = datetime.now().strftime('%Y-%m-%d')
start_dt = (datetime.now() - timedelta(days=20)).strftime('%Y-%m-%d')

try:
    with st.spinner('正在分析籌碼數據...'):
        df_margin = dl.taiwan_stock_margin_purchase_short_sale(
            stock_id=target, start_date=start_dt, end_date=end_dt
        )
        df_inst = dl.taiwan_stock_institutional_investors(
            stock_id=target, start_date=start_dt, end_date=end_dt
        )

    # 檢查是否有資料
    if df_margin is not None and not df_margin.empty:
        # --- 自動找欄位 (不論大小寫) ---
        cols = df_margin.columns.tolist()
        # 找融券餘額
        ss_col = next((c for c in cols if 'Short' in c and 'Balance' in c), None)
        # 找融資餘額
        mp_col = next((c for c in cols if 'Margin' in c and 'Balance' in c), None)

        if ss_col and mp_col:
            last_m = df_margin.iloc[-1]
            short_ratio = (last_m[ss_col] / last_m[mp_col]) * 100
            st.metric("券資比", f"{round(short_ratio, 2)}%")
            
            # 判斷法人賣超
            if df_inst is not None and not df_inst.empty:
                # 三大法人買賣超通常是 'buy' 和 'sell' 欄位
                last_3 = df_inst.tail(3)
                net_buy = last_3['buy'].sum() - last_3['sell'].sum()
                st.metric("法人合計買賣超", f"{int(net_buy)} 股")

                # 最終判斷條件
                if short_ratio < 30 and net_buy < 0:
                    st.warning("⚠️ 符合條件：券資比 < 30% 且法人賣超")
                else:
                    st.info("✅ 尚未符合篩選條件")
        else:
            st.error(f"找不到正確的資券欄位。目前的欄位有：{cols}")
    else:
        st.error("API 未回傳資料，請確認代碼。")

except Exception as e:
    st.error(f"發生意外錯誤: {e}")
