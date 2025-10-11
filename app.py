import streamlit as st
import pandas as pd
import numpy as np
import openpyxl
import matplotlib.pyplot as plt
import seaborn as sns
import logging
from datetime import datetime
import io

# --- 日誌記錄設置 ---
logging.basicConfig(filename='app.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# --- 函數定義 ---
def find_sheet_name(sheet_names, candidates):
    """從候選列表中查找有效的工作表名稱。"""
    for name in candidates:
        if name in sheet_names:
            return name
    return None

def load_data(file_a, file_b):
    """載入、驗證、清理並合併兩個上傳的 Excel 檔案。"""
    try:
        # --- 檔案 A 處理 ---
        df_a = pd.read_excel(file_a, sheet_name=0, dtype={'Article': str, 'Site': str})
        required_cols_a = [
            'Article', 'Article Description', 'RP Type', 'Site', 'MOQ', 
            'SaSa Net Stock', 'Pending Received', 'Safety Stock', 
            'Last Month Sold Qty', 'MTD Sold Qty', 'Supply source', 'Description p. group'
        ]
        if not all(col in df_a.columns for col in required_cols_a):
            missing_cols = [col for col in required_cols_a if col not in df_a.columns]
            st.error(f"檔案 A 缺少必要欄位：{', '.join(missing_cols)}")
            return None, None

        # --- 檔案 B 處理 ---
        xls_b = pd.ExcelFile(file_b)
        sheet_names_b = xls_b.sheet_names

        sheet1_name = find_sheet_name(sheet_names_b, ['Sheet1', 'Sheet 1'])
        sheet2_name = find_sheet_name(sheet_names_b, ['Sheet2', 'Sheet 2'])

        if not sheet1_name or not sheet2_name:
            st.error("檔案 B 必須包含 'Sheet1' (或 'Sheet 1') 和 'Sheet2' (或 'Sheet 2')。")
            return None, None
        
        df_b1 = pd.read_excel(xls_b, sheet1_name, dtype={'Article': str})
        required_cols_b1 = ['Group No.', 'Article', 'SKU Target', 'Target Type', 'Promotion Days', 'Target Cover Days']
        if not all(col in df_b1.columns for col in required_cols_b1):
            missing_cols = [col for col in required_cols_b1 if col not in df_b1.columns]
            st.error(f"檔案 B 的 {sheet1_name} 缺少必要欄位：{', '.join(missing_cols)}")
            return None, None

        df_b2 = pd.read_excel(xls_b, sheet2_name, dtype={'Site': str})
        required_cols_b2 = ['Site', 'Shop Target(HK)', 'Shop Target(MO)', 'Shop Target(ALL)']
        if not all(col in df_b2.columns for col in required_cols_b2):
            missing_cols = [col for col in required_cols_b2 if col not in df_b2.columns]
            st.error(f"檔案 B 的 {sheet2_name} 缺少必要欄位：{', '.join(missing_cols)}")
            return None, None

        # --- 數據清理與預處理 ---
        df_a['Notes'] = ''
        
        # 清理字串欄位
        for col in ['Article', 'Site']:
            if col in df_a.columns:
                df_a[col] = df_a[col].str.strip()
        if 'Article' in df_b1.columns:
            df_b1['Article'] = df_b1['Article'].str.strip()
        if 'Site' in df_b2.columns:
            df_b2['Site'] = df_b2['Site'].str.strip()

        # 處理數值欄位
        numeric_cols_a = ['MOQ', 'SaSa Net Stock', 'Pending Received', 'Safety Stock', 'Last Month Sold Qty', 'MTD Sold Qty']
        for col in numeric_cols_a:
            if col in df_a.columns:
                df_a['Notes'] += np.where(pd.to_numeric(df_a[col], errors='coerce').isnull(), f'{col} 包含無效值; ', '')
                df_a[col] = pd.to_numeric(df_a[col], errors='coerce').fillna(0).astype(int)
                df_a['Notes'] += np.where(df_a[col] < 0, f'{col} 修正為 0; ', '')
                df_a[col] = np.where(df_a[col] < 0, 0, df_a[col])

        # 處理銷量異常
        if 'Last Month Sold Qty' in df_a.columns:
            df_a['Notes'] += np.where(df_a['Last Month Sold Qty'] > 100000, '銷量異常調整; ', '')
            df_a['Last Month Sold Qty'] = np.where(df_a['Last Month Sold Qty'] > 100000, 100000, df_a['Last Month Sold Qty'])

        # --- 合併數據 ---
        df_merged = pd.merge(df_a, df_b1, on='Article', how='left')
        df_merged = pd.merge(df_merged, df_b2, on='Site', how='left')

        # 填充合併後產生的 NaN
        fill_cols = list(df_b1.columns) + list(df_b2.columns)
        fill_cols = [c for c in fill_cols if c not in ['Article', 'Site']]
        
        for col in fill_cols:
            if col in df_merged.columns:
                if pd.api.types.is_numeric_dtype(df_merged[col]):
                    df_merged[col] = df_merged[col].fillna(0)
                else:
                    df_merged[col] = df_merged[col].fillna('')
        
        if 'Group No.' in df_merged.columns:
             df_merged['Notes'] += np.where(df_merged['Group No.'].fillna('') == '', '未匹配到推廣目標; ', '')

        return df_merged, None

    except Exception as e:
        st.error(f"處理檔案時發生錯誤：{e}")
        logging.error(f"File processing error: {e}", exc_info=True)
        return None, None

def calculate_demand(df, lead_time):
    """計算推廣貨量需求。"""
    try:
        if df is None or df.empty:
            return pd.DataFrame(), pd.DataFrame()

        # 複製數據框以避免修改原始數據
        df_calc = df.copy()

        # 1. 計算每日銷售率
        df_calc['Daily Sales Rate'] = (df_calc['Last Month Sold Qty'] / 30).apply(lambda x: max(0, x))

        # 2. 確定推廣目標係數
        df_calc['Site Target %'] = df_calc.apply(
            lambda row: row['Shop Target(HK)'] if row['Target Type'] == 'HK'
            else (row['Shop Target(MO)'] if row['Target Type'] == 'MO'
                  else (row['Shop Target(ALL)'] if row['Target Type'] == 'ALL' else 0)),
            axis=1
        )

        # 3. 計算日常銷售需求
        df_calc['Regular Demand'] = df_calc['Daily Sales Rate'] * (df_calc['Target Cover Days'] + lead_time)

        # 4. 計算推廣特定需求
        df_calc['Promo Demand'] = df_calc['SKU Target'] * df_calc['Site Target %']

        # 5. 計算總需求
        # 對於多 SKU 組，需要先聚合
        group_sku_counts = df_calc.groupby('Group No.')['Article'].nunique()
        multi_sku_groups = group_sku_counts[group_sku_counts > 1].index

        # 初始化 Total Demand
        df_calc['Total Demand'] = 0

        # 單 SKU 組
        single_sku_mask = ~df_calc['Group No.'].isin(multi_sku_groups)
        df_calc.loc[single_sku_mask, 'Total Demand'] = df_calc.loc[single_sku_mask, 'Regular Demand'] + df_calc.loc[single_sku_mask, 'Promo Demand']

        # 多 SKU 組
        if not multi_sku_groups.empty:
            # 按 Group No. 和 Site 聚合 Regular Demand
            agg_regular_demand = df_calc[df_calc['Group No.'].isin(multi_sku_groups)].groupby(['Group No.', 'Site'])['Regular Demand'].sum().reset_index()
            agg_regular_demand.rename(columns={'Regular Demand': 'Aggregated Regular Demand'}, inplace=True)

            # 將聚合後的需求合併回主數據框
            df_calc = pd.merge(df_calc, agg_regular_demand, on=['Group No.', 'Site'], how='left')
            df_calc['Aggregated Regular Demand'].fillna(0, inplace=True)

            # 計算多 SKU 組的 Total Demand
            multi_sku_mask = df_calc['Group No.'].isin(multi_sku_groups)
            df_calc.loc[multi_sku_mask, 'Total Demand'] = df_calc.loc[multi_sku_mask, 'Aggregated Regular Demand'] + df_calc.loc[multi_sku_mask, 'Promo Demand']
            df_calc.drop(columns=['Aggregated Regular Demand'], inplace=True)


        # 6. 計算淨需求
        df_calc['Net Demand'] = df_calc['Total Demand'] - (df_calc['SaSa Net Stock'] + df_calc['Pending Received']) + df_calc['Safety Stock']

        # 7. 計算派貨建議
        # 新邏輯: 派貨數量需為 MOQ 的倍數，且不小於 MOQ
        
        # 步驟 1: 確定基礎派貨量，至少為 Net Demand 和 MOQ 中的較大者
        base_dispatch_qty = np.maximum(df_calc['Net Demand'], df_calc['MOQ'])
        
        # 步驟 2: 將基礎派貨量向上取整至 MOQ 的最接近倍數
        moq = df_calc['MOQ']
        # 為避免除以零的錯誤，只在 MOQ > 0 時執行計算
        final_dispatch_qty = np.where(
            moq > 0,
            np.ceil(base_dispatch_qty / moq) * moq,
            base_dispatch_qty # 若 MOQ 為 0，則回退到基礎派貨量
        )
        
        # 步驟 3: 僅對 RP Type 為 'RF' 的項目應用此邏輯
        df_calc['Suggested Dispatch Qty'] = np.where(
            df_calc['RP Type'] == 'RF',
            final_dispatch_qty,
            0
        )
        
        # 步驟 4: 清理數據，確保為非負整數
        df_calc['Suggested Dispatch Qty'] = df_calc['Suggested Dispatch Qty'].clip(lower=0).fillna(0).astype(int)

        # 8. 確定派貨類型
        df_calc['Dispatch Type'] = np.where(
            df_calc['Site'] == 'D001',
            'D001',
            np.where(
                df_calc['RP Type'] == 'ND',
                'ND',
                np.where(
                    df_calc['Supply source'].isin([1, 4]),
                    'Buyer需要訂貨',
                    np.where(df_calc['Supply source'] == 2, '需生成 DN', '')
                )
            )
        )
        
        # 更新 Notes
        df_calc['Notes'] += f'Lead Time={lead_time}日; '

        # 9. 聚合摘要表 (按 Group No. 和 SKU)
        # 1. 分離 D001 和非 D001 數據
        df_non_d001 = df_calc[df_calc['Site'] != 'D001'].copy()
        df_d001 = df_calc[df_calc['Site'] == 'D001'].copy()

        # 2. 從非 D001 數據創建基礎總結
        summary_base = df_non_d001.groupby(['Group No.', 'Article']).agg(
            Total_Demand=('Total Demand', 'sum'),
            Total_Stock=('SaSa Net Stock', 'sum'),
            Total_Pending=('Pending Received', 'sum'),
            Total_Dispatch=('Suggested Dispatch Qty', 'sum')
        ).reset_index()

        # 3. 創建 D001 庫存總結
        if not df_d001.empty:
            d001_stock_cols = ['SaSa Net Stock', 'In Quality Insp.', 'Blocked', 'Pending Received']
            for col in d001_stock_cols:
                if col not in df_d001.columns:
                    df_d001[col] = 0
            
            d001_summary = df_d001.groupby(['Group No.', 'Article']).agg(
                D001_SaSa_Net_Stock=('SaSa Net Stock', 'sum'),
                D001_In_Quality_Insp=('In Quality Insp.', 'sum'),
                D001_Blocked=('Blocked', 'sum'),
                D001_Pending_Received=('Pending Received', 'sum')
            ).reset_index()
        else:
            d001_summary = pd.DataFrame(columns=['Group No.', 'Article', 'D001_SaSa_Net_Stock', 'D001_In_Quality_Insp', 'D001_Blocked', 'D001_Pending_Received'])

        # 4. 合併基礎總結和 D001 庫存
        summary_final = pd.merge(summary_base, d001_summary, on=['Group No.', 'Article'], how='left')

        # 5. 填充 NaN 並設置數據類型
        fill_cols = ['D001_SaSa_Net_Stock', 'D001_In_Quality_Insp', 'D001_Blocked', 'D001_Pending_Received']
        for col in fill_cols:
            summary_final[col] = summary_final[col].fillna(0).astype(int)

        # 6. 添加計算欄位
        summary_final['Total_Stock_Available'] = summary_final['Total_Stock'] + summary_final['Total_Pending']
        
        # 更新 Out_of_Stock_Warning 邏輯
        # 優先級 1: 檢查 D001 是否有足夠的庫存來應對總派貨量
        # 優先級 2: 如果 D001 庫存充足，再檢查非 D001 門市的庫存是否滿足其需求
        summary_final['Out_of_Stock_Warning'] = np.where(
            summary_final['Total_Dispatch'] > summary_final['D001_SaSa_Net_Stock'],
            'D001 缺貨',
            np.where(summary_final['Total_Demand'] > summary_final['Total_Stock_Available'], 'Y', 'N')
        )

        # 將 'Article' 重命名為 'SKU'
        summary_final.rename(columns={'Article': 'SKU'}, inplace=True)

        # 重新排序欄位
        final_cols = [
            'Group No.', 'SKU', 'Total_Demand', 'Total_Stock', 'Total_Pending', 'Total_Stock_Available', 'Total_Dispatch',
            'D001_SaSa_Net_Stock', 'D001_In_Quality_Insp', 'D001_Blocked', 'D001_Pending_Received', 'Out_of_Stock_Warning'
        ]
        summary_final = summary_final[final_cols]

        return df_calc, summary_final
    except Exception as e:
        st.error(f"計算需求時發生錯誤：{e}")
        logging.error(f"Demand calculation error: {e}", exc_info=True)
        return pd.DataFrame(), pd.DataFrame()


# --- Streamlit UI ---
st.set_page_config(layout="wide", page_title="零售推廣目標檢視及派貨系統")

# --- 側邊欄 ---
with st.sidebar:
    st.header("開發者資訊")
    st.write("姓名：Ricky")
    st.write("當前版本：v1.0")
    
    st.header("參數設定")
    lead_time = st.slider("自訂 Lead Time (日)", min_value=2.0, max_value=5.0, value=2.0, step=0.5)

    st.header("檔案上傳注意事項")
    st.info("請確保上傳的檔案符合以下格式要求：")
    with st.expander("檔案 A (庫存與銷售) 注意事項", expanded=False):
        st.markdown("""
        - **必要欄位**: 必須包含 `Article`, `Site`, `SaSa Net Stock`, `Pending Received`, `MOQ`, `RP Type`, `Last Month Sold Qty` 等。
        - **資料格式**: 
            - `Article` 和 `Site` 會自動清除前後空格。
            - 數值欄位 (如庫存、銷量) 中的非數字或負數會被視為 0。
        """)
    with st.expander("檔案 B (推廣目標) 注意事項", expanded=False):
        st.markdown("""
        - **工作表**: 必須包含 `Sheet1` 和 `Sheet2`。
        - **Sheet1 欄位**: 需有 `Group No.`, `Article`, `SKU Target` 等。
        - **Sheet2 欄位**: 需有 `Site`, `Shop Target(HK)` 等。
        """)

# --- 主區域 ---
st.title("零售推廣目標檢視及派貨系統")

# --- 檔案上傳 ---
uploaded_file_a = st.file_uploader("上傳庫存與銷售檔案 (A)", type=["xlsx"])
uploaded_file_b = st.file_uploader("上傳推廣目標檔案 (B)", type=["xlsx"])

# 初始化 session state
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
    st.session_state.df_merged = None
    st.session_state.results = None
    st.session_state.summary = None

if uploaded_file_a and uploaded_file_b:
    df_merged, _ = load_data(uploaded_file_a, uploaded_file_b)
    if df_merged is not None:
        st.session_state.df_merged = df_merged
        st.session_state.data_loaded = True

# --- 資料預覽 ---
with st.expander("資料預覽 (前 10 行)", expanded=False):
    if st.session_state.data_loaded:
        st.dataframe(st.session_state.df_merged.head(10), use_container_width=True)
    else:
        st.info("請上傳兩個檔案以預覽資料。")

# --- 分析觸發 ---
if st.button("開始分析"):
    if st.session_state.data_loaded:
        progress_bar = st.progress(0, text="分析中，請稍候...")
        
        # 執行計算
        results, summary = calculate_demand(st.session_state.df_merged, lead_time)
        st.session_state.results = results
        st.session_state.summary = summary
        
        progress_bar.progress(100, text="分析完成！")
        st.success("✅ 分析完成！")
    else:
        st.error("錯誤：請先上傳兩個必要的 Excel 檔案。")

# --- 結果顯示 ---
with st.expander("詳細計算結果", expanded=True):
    if st.session_state.results is not None:
        st.dataframe(st.session_state.results, use_container_width=True)
    else:
        st.info("點擊「開始分析」以生成結果。")

with st.expander("總結報告", expanded=True):
    if st.session_state.summary is not None:
        st.dataframe(st.session_state.summary, use_container_width=True)
    else:
        st.info("點擊「開始分析」以生成總結報告。")

def create_visualizations(results_df, summary_df):
    """根據分析結果創建並顯示多個視覺化圖表。"""
    st.header("Visualization Analysis")

    if results_df.empty:
        st.info("No data available for visualization.")
        return

    # --- 過濫器 ---
    group_options = ["All"] + sorted(results_df['Group No.'].unique().tolist())
    selected_group = st.selectbox("Select Group No. to analyze", options=group_options)

    # 根據選擇過濫數據
    if selected_group != "All":
        filtered_results = results_df[results_df['Group No.'] == selected_group]
        filtered_summary = summary_df[summary_df['Group No.'] == selected_group]
    else:
        filtered_results = results_df
        filtered_summary = summary_df

    if filtered_results.empty:
        st.warning("No data to display for the selected group.")
        return

    # --- 圖表生成 ---
    # 1. 柱狀圖 (SKU 需求 vs 庫存, 不含 D001)
    st.subheader("SKU Demand vs. Stock (excluding D001)")
    
    # 過濫掉 D001
    chart_data = filtered_results[filtered_results['Site'] != 'D001'].copy()
    
    if not chart_data.empty:
        # 計算每個 SKU 的總需求和總庫存
        chart_data['Stock Available'] = chart_data['SaSa Net Stock'] + chart_data['Pending Received']
        sku_plot_data = chart_data.groupby('Article').agg({
            'Total Demand': 'sum',
            'Stock Available': 'sum'
        }).reset_index()

        fig1, ax1 = plt.subplots()
        sku_plot_data.plot(x='Article', y=['Total Demand', 'Stock Available'], kind='bar', ax=ax1)
        ax1.set_title(f"Group: {selected_group}")
        ax1.set_ylabel("Quantity")
        ax1.tick_params(axis='x', rotation=90)
        st.pyplot(fig1)
        st.caption("This chart compares total demand vs. available stock for each SKU (D001 excluded).")
    else:
        st.info("No data available for this chart after excluding D001.")

    # 2. 淨需求熱圖
    st.subheader("Net Demand Heatmap (by Site and Article, excluding D001)")
    heatmap_filtered_results = filtered_results[filtered_results['Site'] != 'D001']
    heatmap_data = heatmap_filtered_results.pivot_table(index='Site', columns='Article', values='Net Demand', aggfunc='sum')
    if not heatmap_data.empty:
        # 如果數據點太多，進行抽樣
        if heatmap_data.size > 1000:
            st.warning("Data points exceed 1000. Showing a sample of the data.")
            sampled_cols = np.random.choice(heatmap_data.columns, size=min(50, len(heatmap_data.columns)), replace=False)
            heatmap_data = heatmap_data[sampled_cols]

        fig3, ax3 = plt.subplots(figsize=(12, max(6, len(heatmap_data.index) * 0.5)))
        sns.heatmap(heatmap_data, annot=True, fmt=".0f", cmap="viridis", ax=ax3)
        ax3.set_title(f"Group: {selected_group}")
        st.pyplot(fig3)
        st.caption("This heatmap shows the net demand for each article at each site (D001 excluded). Higher values indicate greater demand.")
    else:
        st.info("No net demand data available to generate a heatmap for this group (D001 excluded).")

def export_to_excel(raw_df, results_df, summary_df):
    """將數據導出到一個多工作表的 Excel 檔案中。"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        raw_df.to_excel(writer, sheet_name='Raw Data', index=False)
        results_df.to_excel(writer, sheet_name='Calculation Results', index=False)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
    
    processed_data = output.getvalue()
    return processed_data

# --- 視覺化圖表 ---
with st.expander("視覺化圖表", expanded=True):
    if st.session_state.results is not None:
        create_visualizations(st.session_state.results, st.session_state.summary)
    else:
        st.info("點擊「開始分析」以生成圖表。")

# --- 匯出功能 ---
with st.expander("匯出分析結果", expanded=False):
    if st.session_state.results is not None:
        current_date = datetime.now().strftime("%Y%m%d")
        file_name = f"Promotion_Demand_Report_{current_date}.xlsx"
        
        excel_data = export_to_excel(
            st.session_state.df_merged,
            st.session_state.results,
            st.session_state.summary
        )
        
        st.download_button(
            label="📥 下載 Excel 報告",
            data=excel_data,
            file_name=file_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("點擊「開始分析」以生成可匯出的報告。")

# --- 依賴檢查 ---
try:
    import openpyxl
    import matplotlib
    import seaborn
except ImportError:
    st.error("缺少必要套件，請根據 requirements.txt 檔案安裝。")