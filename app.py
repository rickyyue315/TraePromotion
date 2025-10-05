import streamlit as st
import pandas as pd
import numpy as np
import openpyxl
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, date
import logging
import io
import sys
import os
from config import Config, TRANSLATIONS, ERROR_MESSAGES, SUCCESS_MESSAGES, REQUIRED_PACKAGES, REQUIRED_COLUMNS

# 設置日誌
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format=Config.LOG_FORMAT,
    handlers=[
        logging.FileHandler(Config.get_log_file_path()),
        logging.StreamHandler()
    ]
)

def get_text(key, lang='en'):
    """獲取翻譯文本"""
    return TRANSLATIONS.get(lang, TRANSLATIONS['en']).get(key, key)

def check_dependencies():
    """檢查依賴包是否安裝"""
    missing_packages = []
    for package, requirement in REQUIRED_PACKAGES.items():
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(requirement)
    
    return missing_packages

def load_excel_file(file, sheet_name=None):
    """載入Excel檔案"""
    try:
        if sheet_name:
            return pd.read_excel(file, sheet_name=sheet_name)
        else:
            return pd.read_excel(file)
    except Exception as e:
        logging.error(f"Error loading Excel file: {str(e)}")
        return None

def validate_inventory_file(df):
    """驗證庫存檔案"""
    missing_columns = [col for col in REQUIRED_COLUMNS['inventory'] if col not in df.columns]
    return missing_columns

def validate_file_b(df1, df2):
    """驗證檔案B的必需欄位"""
    missing_sheet1 = [col for col in REQUIRED_COLUMNS['promotion_sheet1'] if col not in df1.columns] if df1 is not None else []
    missing_sheet2 = [col for col in REQUIRED_COLUMNS['promotion_sheet2'] if col not in df2.columns] if df2 is not None else []
    
    return missing_sheet1, missing_sheet2

def preprocess_data(df):
    """數據預處理"""
    df_processed = df.copy()
    notes = []
    
    # Article欄位處理
    if 'Article' in df_processed.columns:
        df_processed['Article'] = df_processed['Article'].astype(str).str.strip()
    
    # 數值欄位處理
    numeric_columns = Config.QUANTITY_COLUMNS
    
    for col in numeric_columns:
        if col in df_processed.columns:
            # 轉換為數值類型，無效值填充為0
            df_processed[col] = pd.to_numeric(df_processed[col], errors='coerce').fillna(0)
            
            # 負值修正為0
            negative_mask = df_processed[col] < 0
            if negative_mask.any():
                df_processed.loc[negative_mask, col] = 0
                notes.append(f"{col}: 修正了{negative_mask.sum()}個負值")
            
            # 異常值處理（>100000）
            if col in ['Last Month Sold Qty', 'MTD Sold Qty']:
                abnormal_mask = df_processed[col] > Config.OUTLIER_THRESHOLD
                if abnormal_mask.any():
                    df_processed.loc[abnormal_mask, col] = Config.OUTLIER_THRESHOLD
                    notes.append(f"{col}: 調整了{abnormal_mask.sum()}個異常值（>{Config.OUTLIER_THRESHOLD}）")
    
    # 字串欄位空值處理
    string_columns = Config.STRING_COLUMNS
    for col in string_columns:
        if col in df_processed.columns:
            df_processed[col] = df_processed[col].fillna('').astype(str)
    
    # 添加Notes欄位
    df_processed['Notes'] = '; '.join(notes) if notes else 'No data corrections needed'
    
    return df_processed

def calculate_business_logic(df_inventory, df_promotion_sku, df_promotion_shop, lead_time=None):
    """核心業務邏輯計算"""
    try:
        if df_inventory.empty or df_promotion_sku.empty or df_promotion_shop.empty:
            return pd.DataFrame(), "No valid data to calculate"
        
        # 使用默認lead time如果未提供
        if lead_time is None:
            lead_time = Config.DEFAULT_LEAD_TIME
        
        # 合併數據
        df_merged = df_inventory.merge(
            df_promotion_sku, 
            on='Article', 
            how='left',
            suffixes=('', '_promo')
        )
        
        df_merged = df_merged.merge(
            df_promotion_shop,
            on='Site',
            how='left',
            suffixes=('', '_shop')
        )
        
        # 填充缺失值
        fill_columns = ['SKU Target', 'Promotion Days', 'Target Cover Days', 
                       'Shop Target(HK)', 'Shop Target(MO)', 'Shop Target(ALL)']
        for col in fill_columns:
            if col in df_merged.columns:
                df_merged[col] = df_merged[col].fillna(0)
        
        # 計算日常銷售率
        current_day = date.today().day
        
        df_merged['Daily Sales Rate'] = np.where(
            (df_merged['Last Month Sold Qty'] > 0) | (df_merged['MTD Sold Qty'] > 0),
            (df_merged['Last Month Sold Qty'] / Config.DAYS_IN_MONTH + df_merged['MTD Sold Qty'] / current_day) / 2,
            0
        )
        
        # 計算目標類型調整係數
        df_merged['Target Coefficient'] = df_merged['Target Type'].map(Config.TARGET_TYPE_MULTIPLIERS).fillna(1)
        
        # 計算日常銷售需求
        df_merged['Daily Sales Demand'] = df_merged['Daily Sales Rate'] * (
            df_merged['Promotion Days'] + df_merged['Target Cover Days'] + lead_time
        )
        
        # 計算推廣特定需求
        df_merged['Promotion Specific Demand'] = (
            df_merged['SKU Target'] * df_merged['Target Coefficient']
        )
        
        # 添加店鋪目標
        df_merged['Shop Target'] = np.where(
            df_merged['Target Type'] == 'HK', df_merged['Shop Target(HK)'],
            np.where(df_merged['Target Type'] == 'MO', df_merged['Shop Target(MO)'],
                    df_merged['Shop Target(ALL)'])
        )
        
        # 總需求
        df_merged['Total Demand'] = (
            df_merged['Daily Sales Demand'] + 
            df_merged['Promotion Specific Demand'] + 
            df_merged['Shop Target']
        )
        
        # 可用庫存
        df_merged['Available Stock'] = (
            df_merged['SaSa Net Stock'] + df_merged['Pending Received']
        )
        
        # 淨需求
        df_merged['Net Demand'] = np.maximum(
            0,
            df_merged['Total Demand'] - df_merged['Available Stock'] + df_merged['Safety Stock']
        )
        
        # 派貨建議
        df_merged['Suggested Dispatch Qty'] = np.where(
            df_merged['RP Type'] == Config.RP_TYPE_RF,
            np.maximum(df_merged['Net Demand'], df_merged['MOQ']),
            0
        )
        
        # 添加計算日誌
        df_merged['Calculation Notes'] = (
            f"Lead Time: {lead_time} days; "
            f"Calculation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        return df_merged, "Calculation completed successfully"
        
    except Exception as e:
        logging.error(f"Error in business logic calculation: {str(e)}")
        return pd.DataFrame(), f"Calculation error: {str(e)}"

def create_visualizations(df, lang='en'):
    """創建視覺化圖表"""
    if df.empty:
        return None
    
    fig, axes = plt.subplots(2, 2, figsize=Config.VISUALIZATION_FIGSIZE)
    fig.suptitle(get_text('visualization', lang), fontsize=Config.VISUALIZATION_TITLE_FONT_SIZE)
    
    # 1. 柱狀圖：按Group No.顯示總需求 vs 總庫存
    if 'Group No.' in df.columns:
        group_summary = df.groupby('Group No.').agg({
            'Total Demand': 'sum',
            'Available Stock': 'sum'
        }).reset_index()
        
        x = range(len(group_summary))
        width = Config.BAR_CHART_WIDTH
        
        axes[0, 0].bar([i - width/2 for i in x], group_summary['Total Demand'], 
                      width, label=get_text('total_demand_vs_inventory', lang), color=Config.CHART_COLORS[0])
        axes[0, 0].bar([i + width/2 for i in x], group_summary['Available Stock'], 
                      width, label='Total Inventory', color=Config.CHART_COLORS[1])
        
        axes[0, 0].set_xlabel('Group No.')
        axes[0, 0].set_ylabel('Quantity')
        axes[0, 0].set_title('Total Demand vs Inventory by Group')
        axes[0, 0].legend()
        axes[0, 0].set_xticks(x)
        axes[0, 0].set_xticklabels(group_summary['Group No.'], rotation=45)
    
    # 2. 餅圖：派貨建議分佈
    if 'RP Type' in df.columns and 'Suggested Dispatch Qty' in df.columns:
        dispatch_summary = df.groupby('RP Type')['Suggested Dispatch Qty'].sum()
        
        axes[0, 1].pie(dispatch_summary.values, labels=dispatch_summary.index, 
                      autopct='%1.1f%%', startangle=90, colors=Config.PIE_CHART_COLORS)
        axes[0, 1].set_title('Distribution Recommendations Distribution')
    
    # 3. 熱力圖：按Site和Article顯示淨需求強度
    if 'Site' in df.columns and 'Article' in df.columns and 'Net Demand' in df.columns:
        # 取前20個數據點以避免圖表過於擁擠
        heatmap_data = df.nlargest(Config.MAX_HEATMAP_DATA_POINTS, 'Net Demand')[['Site', 'Article', 'Net Demand']]
        heatmap_pivot = heatmap_data.pivot_table(
            values='Net Demand', 
            index='Site', 
            columns='Article', 
            aggfunc='sum',
            fill_value=0
        )
        
        sns.heatmap(heatmap_pivot, annot=True, fmt='.0f', cmap=Config.HEATMAP_COLORMAP, 
                   ax=axes[1, 0], cbar_kws={'label': 'Net Demand'})
        axes[1, 0].set_title('Net Demand Intensity Heatmap')
        axes[1, 0].set_xlabel('Article')
        axes[1, 0].set_ylabel('Site')
    
    # 4. 散點圖：總需求 vs 建議派貨量
    if 'Total Demand' in df.columns and 'Suggested Dispatch Qty' in df.columns:
        # 限制資料點數避免效能問題
        if len(df) > Config.MAX_SCATTER_POINTS:
            df_sample = df.sample(n=Config.MAX_SCATTER_POINTS, random_state=42)
        else:
            df_sample = df
        
        axes[1, 1].scatter(df_sample['Total Demand'], df_sample['Suggested Dispatch Qty'], 
                          alpha=Config.SCATTER_ALPHA, color=Config.SCATTER_COLOR, s=Config.SCATTER_SIZE)
        axes[1, 1].set_xlabel('Total Demand')
        axes[1, 1].set_ylabel('Suggested Dispatch Qty')
        axes[1, 1].set_title('Total Demand vs Suggested Dispatch')
        
        # 添加趨勢線
        z = np.polyfit(df_sample['Total Demand'], df_sample['Suggested Dispatch Qty'], 1)
        p = np.poly1d(z)
        axes[1, 1].plot(df_sample['Total Demand'], p(df_sample['Total Demand']), "r--", alpha=Config.TRENDLINE_ALPHA)
    
    plt.tight_layout()
    return fig

def export_to_excel(df_results, df_summary):
    """匯出結果到Excel"""
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine=Config.EXCEL_ENGINE) as writer:
        # 主要結果
        df_results.to_excel(writer, sheet_name=Config.EXCEL_SHEET_ANALYSIS, index=False)
        
        # 摘要數據
        if not df_summary.empty:
            df_summary.to_excel(writer, sheet_name=Config.EXCEL_SHEET_SUMMARY, index=False)
    
    output.seek(0)
    return output

@st.cache_data(ttl=Config.CACHE_TTL)
def load_data_cached(file, file_type):
    """快取資料載入"""
    return pd.read_excel(file, sheet_name=0)

def main():
    # 設置頁面配置
    st.set_page_config(
        page_title=Config.APP_NAME,
        page_icon=Config.PAGE_ICON,
        layout=Config.LAYOUT,
        initial_sidebar_state=Config.INITIAL_SIDEBAR_STATE
    )
    
    # 初始化會話狀態
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'summary_results' not in st.session_state:
        st.session_state.summary_results = None
    
    # 檢查依賴包
    missing_deps = check_dependencies()
    if missing_deps:
        st.error(f"Missing required packages: {', '.join(missing_deps)}")
        st.info("Please install missing packages using: pip install -r requirements.txt")
        return
    
    # 語言選擇
    lang = st.sidebar.selectbox("Language / 語言", ["English", "中文"])
    lang_code = "en" if lang == "English" else "zh"
    
    # 側邊欄
    with st.sidebar:
        st.title(get_text('system_info', lang_code))
        st.info(f"{get_text('developer', lang_code)}\n{get_text('version', lang_code)}")
        
        st.subheader(get_text('quick_navigation', lang_code))
        page = st.radio("", [
            get_text('file_upload', lang_code),
            get_text('analysis_result', lang_code)
        ])
        
        # 參數設置
        st.subheader("Parameters")
        lead_time = st.slider(
            get_text('lead_time_setting', lang_code),
            min_value=Config.LEAD_TIME_MIN,
            max_value=Config.LEAD_TIME_MAX,
            value=Config.DEFAULT_LEAD_TIME,
            step=Config.LEAD_TIME_STEP
        )
    
    # 主標題
    st.title(get_text('title', lang_code))
    
    # 初始化session state
    if 'df_inventory' not in st.session_state:
        st.session_state.df_inventory = None
    if 'df_promotion_sku' not in st.session_state:
        st.session_state.df_promotion_sku = None
    if 'df_promotion_shop' not in st.session_state:
        st.session_state.df_promotion_shop = None
    if 'df_results' not in st.session_state:
        st.session_state.df_results = None
    
    if page == get_text('file_upload', lang_code):
        # 檔案上傳區域
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader(get_text('upload_inventory', lang_code))
            file_a = st.file_uploader(
                get_text('upload_inventory', lang_code),
                type=['xlsx'],
                key='file_a'
            )
        
        with col2:
            st.subheader(get_text('upload_promotion', lang_code))
            file_b = st.file_uploader(
                get_text('upload_promotion', lang_code),
                type=['xlsx'],
                key='file_b'
            )
        
        if file_a and file_b:
            # 載入檔案A
            df_inventory_raw = load_excel_file(file_a)
            if df_inventory_raw is not None:
                # 驗證檔案A
                missing_cols_a = validate_file_a(df_inventory_raw)
                if missing_cols_a:
                    st.error(f"{get_text('missing_fields', lang_code)} in File A: {', '.join(missing_cols_a)}")
                else:
                    # 預處理檔案A
                    st.session_state.df_inventory = preprocess_data(df_inventory_raw)
                    st.success("File A loaded and validated successfully")
            
            # 載入檔案B（兩個sheet）
            try:
                df_promotion_sku_raw = load_excel_file(file_b, sheet_name=0)
                df_promotion_shop_raw = load_excel_file(file_b, sheet_name=1)
                
                if df_promotion_sku_raw is not None and df_promotion_shop_raw is not None:
                    # 驗證檔案B
                    missing_sheet1, missing_sheet2 = validate_file_b(df_promotion_sku_raw, df_promotion_shop_raw)
                    
                    if missing_sheet1 or missing_sheet2:
                        error_msg = f"{get_text('missing_fields', lang_code)} in File B: "
                        if missing_sheet1:
                            error_msg += f"Sheet1: {', '.join(missing_sheet1)}; "
                        if missing_sheet2:
                            error_msg += f"Sheet2: {', '.join(missing_sheet2)}"
                        st.error(error_msg)
                    else:
                        # 預處理檔案B
                        st.session_state.df_promotion_sku = preprocess_data(df_promotion_sku_raw)
                        st.session_state.df_promotion_shop = preprocess_data(df_promotion_shop_raw)
                        st.success("File B loaded and validated successfully")
            except Exception as e:
                st.error(f"Error loading File B: {str(e)}")
        
        # 顯示數據預覽
        if st.session_state.df_inventory is not None:
            st.subheader(get_text('data_preview', lang_code))
            st.dataframe(st.session_state.df_inventory.head(10))
        
        # 分析按鈕
        if (st.session_state.df_inventory is not None and 
            st.session_state.df_promotion_sku is not None and 
            st.session_state.df_promotion_shop is not None):
            
            if st.button(get_text('start_analysis', lang_code), type="primary"):
                with st.spinner("Processing..."):
                    progress_bar = st.progress(0)
                    
                    # 執行分析
                    progress_bar.progress(30)
                    df_results, message = calculate_business_logic(
                        st.session_state.df_inventory,
                        st.session_state.df_promotion_sku,
                        st.session_state.df_promotion_shop,
                        lead_time
                    )
                    
                    progress_bar.progress(70)
                    st.session_state.df_results = df_results
                    
                    progress_bar.progress(100)
                    
                    if not df_results.empty:
                        st.success(get_text('analysis_complete', lang_code))
                        st.info(f"Processed {len(df_results)} records")
                    else:
                        st.warning(get_text('no_valid_data', lang_code))
    
    else:  # Analysis Result page
        if st.session_state.df_results is not None and not st.session_state.df_results.empty:
            st.subheader(get_text('analysis_results', lang_code))
            
            # 顯示結果表格
            display_columns = [
                'Article', 'Site', 'Group No.', 'RP Type', 'Daily Sales Rate',
                'Total Demand', 'Net Demand', 'Suggested Dispatch Qty', 'Notes'
            ]
            
            available_columns = [col for col in display_columns if col in st.session_state.df_results.columns]
            st.dataframe(st.session_state.df_results[available_columns])
            
            # 創建摘要統計
            st.subheader("Summary Statistics")
            summary_stats = pd.DataFrame({
                'Metric': ['Total Records', 'Total Demand', 'Total Suggested Dispatch', 'Average Daily Sales Rate'],
                'Value': [
                    len(st.session_state.df_results),
                    st.session_state.df_results['Total Demand'].sum(),
                    st.session_state.df_results['Suggested Dispatch Qty'].sum(),
                    st.session_state.df_results['Daily Sales Rate'].mean()
                ]
            })
            st.table(summary_stats)
            
            # 視覺化
            st.subheader(get_text('visualization', lang_code))
            
            # 產品組別選擇器
            if 'Group No.' in st.session_state.df_results.columns:
                unique_groups = ['All'] + sorted(st.session_state.df_results['Group No.'].unique().tolist())
                selected_group = st.selectbox(get_text('select_group', lang_code), unique_groups)
                
                # 過濾數據
                if selected_group != 'All':
                    viz_data = st.session_state.df_results[st.session_state.df_results['Group No.'] == selected_group]
                else:
                    viz_data = st.session_state.df_results
                
                # 創建圖表
                fig = create_visualizations(viz_data, lang_code)
                if fig:
                    st.pyplot(fig)
                else:
                    st.info(get_text('no_visualization_data', lang_code))
            
            # 匯出功能
            st.subheader(get_text('export_results', lang_code))
            
            # 創建摘要數據
            summary_data = st.session_state.df_results.groupby(['Group No.', 'Site']).agg({
                'Total Demand': 'sum',
                'Available Stock': 'sum',
                'Suggested Dispatch Qty': 'sum'
            }).reset_index()
            
            excel_file = export_to_excel(st.session_state.df_results, summary_data)
            
            st.download_button(
                label=get_text('download_report', lang_code),
                data=excel_file,
                file_name=f"Promotion_Demand_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
        else:
            st.warning(get_text('no_valid_data', lang_code))
    
    # 更新檢查（側邊欄底部）
    st.sidebar.markdown("---")
    if st.sidebar.button(get_text('check_update', lang_code)):
        st.sidebar.info(f"{get_text('current_version', lang_code)}: v1.0")
        st.sidebar.success(get_text('up_to_date', lang_code))

if __name__ == "__main__":
    main()