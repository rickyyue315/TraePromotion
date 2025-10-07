import os
from datetime import datetime

# 系統配置
class Config:
    """系統配置類"""
    
    # 應用配置
    APP_NAME = "Retail Promotion System"
    APP_VERSION = "v1.0"
    DEVELOPER = "Ricky"
    PAGE_ICON = "📊"
    LAYOUT = "wide"
    INITIAL_SIDEBAR_STATE = "expanded"
    PAGE_TITLE = "Retail Promotion Target Inventory & Distribution System"
    
    # 文件配置
    SUPPORTED_FILE_TYPES = ['xlsx']
    MAX_FILE_SIZE_MB = 50
    MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
    
    # 數據處理配置
    MAX_ABNORMAL_VALUE = 100000
    DEFAULT_LEAD_TIME = 2.5
    LEAD_TIME_MIN = 0.1
    LEAD_TIME_MAX = 3.0
    LEAD_TIME_STEP = 0.1
    LEAD_TIME_HELP = "Adjust lead time for demand calculation"
    
    # 業務邏輯配置
    TARGET_COEFFICIENTS = {
        'HK': 1,
        'MO': 1,
        'ALL': 2
    }
    
    DAYS_IN_MONTH = 30
    TARGET_TYPE_MULTIPLIERS = {
        'HK': 1,
        'MO': 1,
        'ALL': 2
    }
    RP_TYPE_RF = 'RF'
    
    # 日誌配置
    LOG_FILE = "app.log"
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    
    # 匯出配置
    EXPORT_FILE_PREFIX = "Promotion_Demand_Report"
    EXPORT_DATE_FORMAT = "%Y%m%d_%H%M%S"
    EXCEL_ENGINE = 'openpyxl'
    EXCEL_SHEET_ANALYSIS = 'Analysis Results'
    EXCEL_SHEET_SUMMARY = 'Summary'
    EXCEL_SHEET_ORIGINAL = 'Original Data'
    
    # 視覺化配置
    VISUALIZATION_FIGSIZE = (15, 12)
    VISUALIZATION_TITLE_FONT_SIZE = 16
    VISUALIZATION_TITLE_FONT_WEIGHT = 'bold'
    BAR_CHART_WIDTH = 0.35
    CHART_COLORS = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
    PIE_CHART_COLORS = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#ff99cc', '#c2c2f0']
    HEATMAP_COLORMAP = "viridis"
    MAX_HEATMAP_DATA_POINTS = 20
    MAX_SCATTER_POINTS = 100
    SCATTER_ALPHA = 0.6
    SCATTER_COLOR = '#1f77b4'
    SCATTER_SIZE = 50
    TRENDLINE_ALPHA = 0.8
    GRID_ALPHA = 0.3
    
    # 快取配置
    CACHE_TTL = 3600  # 1小時
    
    # 資料處理配置
    QUANTITY_COLUMNS = ['SaSa Net Stock', 'Pending Received', 'Safety Stock', 'Last Month Sold Qty', 'MTD Sold Qty', 'SKU Target', 'Shop Target(HK)', 'Shop Target(MO)', 'Shop Target(ALL)']
    OUTLIER_THRESHOLD = 10000
    STRING_COLUMNS = ['Article', 'Article Description', 'RP Type', 'Site', 'Group No.', 'Target Type']
    
    # 供應來源配置
    VALID_SUPPLY_SOURCES = ['1', '2', '4']
    SUPPLY_SOURCE_BUYER_NOTIFICATION = ['1', '4']  # 需要通知Buyer的供應來源
    SUPPLY_SOURCE_RP_TEAM = ['2']  # 需要RP team建議的供應來源
    INVALID_SOURCE_DEFAULT = "無效來源"
    
    # 安全配置
    ENABLE_FILE_VALIDATION = True
    ENABLE_DATA_CLEANING = True
    ENABLE_ERROR_LOGGING = True
    
    @classmethod
    def get_export_filename(cls):
        """生成匯出文件名"""
        timestamp = datetime.now().strftime(cls.EXPORT_DATE_FORMAT)
        return f"{cls.EXPORT_FILE_PREFIX}_{timestamp}.xlsx"
    
    @classmethod
    def get_log_file_path(cls):
        """獲取日誌文件路徑"""
        return os.path.join(os.path.dirname(__file__), cls.LOG_FILE)

# 多語言配置
TRANSLATIONS = {
    'en': {
        'title': 'Retail Promotion Target Inventory & Distribution System',
        'developer': 'Developer: Ricky',
        'version': 'Version: v1.0',
        'upload_inventory': 'Upload Inventory File (A)',
        'upload_promotion': 'Upload Promotion Target File (B)',
        'start_analysis': 'Start Analysis',
        'analysis_complete': 'Analysis Complete',
        'upload_valid_excel': 'Please upload valid Excel files',
        'missing_fields': 'Missing required fields',
        'no_valid_data': 'No valid data to calculate',
        'data_preview': 'Data Preview (First 10 rows)',
        'analysis_results': 'Analysis Results',
        'visualization': 'Data Visualization',
        'export_results': 'Export Results',
        'lead_time_setting': 'Lead Time Setting (Days)',
        'select_group': 'Select Product Group',
        'total_demand_vs_inventory': 'Total Demand vs Inventory by Product Group',
        'distribution_recommendations': 'Distribution Recommendations Distribution',
        'net_demand_heatmap': 'Net Demand Intensity Heatmap',
        'no_visualization_data': 'No visualization data available',
        'download_report': 'Download Analysis Report',
        'file_a_missing': 'File A is missing',
        'file_b_missing': 'File B is missing',
        'system_info': 'System Information',
        'quick_navigation': 'Quick Navigation',
        'file_upload': 'File Upload',
        'analysis_result': 'Analysis Result',
        'check_update': 'Check for Updates',
        'current_version': 'Current Version',
        'latest_version': 'Latest Version',
        'update_available': 'Update Available',
        'up_to_date': 'Up to Date',
        'error_file_too_large': 'File size exceeds maximum allowed size',
        'error_invalid_file_type': 'Invalid file type. Only Excel files are supported',
        'error_data_validation': 'Data validation error',
        'success_file_loaded': 'File loaded successfully',
        'out_of_stock_notification': 'Out of Stock Notification',
        'buyer_notification': 'Buyer Notification',
        'rp_team_suggestion': 'RP Team Suggestion',
        'stock_out_qty': 'Out of Stock Qty',
        'supply_source': 'Supply Source',
        'buyer_group': 'Buyer Group',
        'invalid_supply_source': 'Invalid Supply Source',
        'check_d001_availability': 'Please check D001 availability',
        'processing_data': 'Processing data...',
        'calculating_results': 'Calculating results...',
        'generating_visualizations': 'Generating visualizations...',
        'exporting_data': 'Exporting data...'
    },
    'zh': {
        'title': '零售推廣目標檢視及派貨系統',
        'developer': '開發者：Ricky',
        'version': '版本：v1.0',
        'upload_inventory': '上傳庫存檔案 (A)',
        'upload_promotion': '上傳推廣目標檔案 (B)',
        'start_analysis': '開始分析',
        'analysis_complete': '分析完成',
        'upload_valid_excel': '請上傳有效Excel檔案',
        'missing_fields': '缺少必需欄位',
        'no_valid_data': '無有效資料可計算',
        'data_preview': '資料預覽（前10行）',
        'analysis_results': '分析結果',
        'visualization': '資料視覺化',
        'export_results': '匯出結果',
        'lead_time_setting': 'Lead Time 設定（天）',
        'select_group': '選擇產品組別',
        'total_demand_vs_inventory': '按產品組別顯示總需求 vs 總庫存',
        'distribution_recommendations': '派貨建議分佈',
        'net_demand_heatmap': '淨需求強度熱力圖',
        'no_visualization_data': '無視覺化資料可用',
        'download_report': '下載分析報告',
        'file_a_missing': '缺少檔案A',
        'file_b_missing': '缺少檔案B',
        'system_info': '系統資訊',
        'quick_navigation': '快速導航',
        'file_upload': '檔案上傳',
        'analysis_result': '分析結果',
        'check_update': '檢查更新',
        'current_version': '目前版本',
        'latest_version': '最新版本',
        'update_available': '有可用更新',
        'up_to_date': '已是最新版本',
        'error_file_too_large': '檔案大小超過最大限制',
        'error_invalid_file_type': '無效的檔案類型。只支援Excel檔案',
        'error_data_validation': '資料驗證錯誤',
        'success_file_loaded': '檔案載入成功',
        'out_of_stock_notification': '缺貨通知',
        'buyer_notification': '買家通知',
        'rp_team_suggestion': 'RP團隊建議',
        'stock_out_qty': '缺貨數量',
        'supply_source': '補貨來源',
        'buyer_group': '買家組別',
        'invalid_supply_source': '無效補貨來源',
        'check_d001_availability': '請檢查D001可用性',
        'processing_data': '處理資料中...',
        'calculating_results': '計算結果中...',
        'generating_visualizations': '生成視覺化中...',
        'exporting_data': '匯出資料中...'
    }
}

# 錯誤訊息配置
ERROR_MESSAGES = {
    'file_validation': {
        'en': 'File validation failed. Please check the file format and required fields.',
        'zh': '檔案驗證失敗。請檢查檔案格式和必需欄位。'
    },
    'data_processing': {
        'en': 'Data processing error occurred. Please check your data and try again.',
        'zh': '資料處理時發生錯誤。請檢查您的資料後重試。'
    },
    'calculation_error': {
        'en': 'Calculation error. Please verify your input data.',
        'zh': '計算錯誤。請驗證您的輸入資料。'
    },
    'visualization_error': {
        'en': 'Visualization generation failed.',
        'zh': '視覺化生成失敗。'
    },
    'export_error': {
        'en': 'Export failed. Please try again.',
        'zh': '匯出失敗。請重試。'
    }
}

# 成功訊息配置
SUCCESS_MESSAGES = {
    'file_loaded': {
        'en': 'File loaded and validated successfully.',
        'zh': '檔案載入並驗證成功。'
    },
    'analysis_complete': {
        'en': 'Analysis completed successfully.',
        'zh': '分析成功完成。'
    },
    'export_complete': {
        'en': 'Export completed successfully.',
        'zh': '匯出成功完成。'
    }
}

# 依賴包配置
REQUIRED_PACKAGES = {
    'streamlit': 'streamlit>=1.28.0',
    'pandas': 'pandas>=2.0.0',
    'numpy': 'numpy>=1.24.0',
    'openpyxl': 'openpyxl>=3.1.0',
    'matplotlib': 'matplotlib>=3.7.0',
    'seaborn': 'seaborn>=0.12.0'
}

# 欄位配置
REQUIRED_COLUMNS = {
    'file_a': [
        'Article', 'Article Description', 'RP Type', 'Site', 'MOQ',
        'SaSa Net Stock', 'Pending Received', 'Safety Stock',
        'Last Month Sold Qty', 'MTD Sold Qty', 'Supply source', 'Description p. group'
    ],
    'file_b_sheet1': [
        'Group No.', 'Article', 'SKU Target', 'Target Type',
        'Promotion Days', 'Target Cover Days'
    ],
    'file_b_sheet2': [
        'Site', 'Shop Target(HK)', 'Shop Target(MO)', 'Shop Target(ALL)'
    ]
}