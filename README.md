# 零售推廣目標檢視及派貨系統

## 系統簡介
這是一個基於Streamlit的零售推廣目標檢視庫存及派貨建議系統，專為零售業務設計，用於分析推廣活動的庫存需求和派貨建議。

## 開發者資訊
- 開發者：Ricky
- 版本：v1.0

## 技術要求
- Python 3.8+
- Streamlit 1.28.0+
- Pandas 2.0.0+
- NumPy 1.24.0+
- OpenPyXL 3.1.0+
- Matplotlib 3.7.0+
- Seaborn 0.12.0+

## 安裝指南

### 1. 環境設置
```bash
# 創建虛擬環境（推薦）
python -m venv venv

# 激活虛擬環境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 2. 安裝依賴
```bash
pip install -r requirements.txt
```

### 3. 運行應用
```bash
streamlit run app.py
```

## 使用說明

### 系統功能
1. **檔案上傳**：支援上傳兩個Excel檔案
   - 檔案A：庫存與銷售數據
   - 檔案B：推廣目標數據

2. **數據預覽**：顯示上傳數據的前10行

3. **分析計算**：基於業務邏輯計算派貨需求

4. **視覺化**：提供多種圖表展示分析結果

5. **匯出功能**：將分析結果匯出為Excel檔案

### 輸入檔案格式要求

#### 檔案A（庫存與銷售數據）
| 欄位名稱 | 類型 | 說明 |
|----------|------|------|
| Article | string | 產品編號 |
| Article Description | string | 產品描述 |
| RP Type | string | 補貨類型：ND（不補貨）或 RF（補貨） |
| Site | string | 店鋪編號 |
| MOQ | integer | 最低派貨數量 |
| SaSa Net Stock | integer | 現有庫存數量 |
| Pending Received | integer | 在途訂單數量 |
| Safety Stock | integer | 安全庫存數量 |
| Last Month Sold Qty | integer | 上月銷量 |
| MTD Sold Qty | integer | 本月至今銷量 |

#### 檔案B（推廣目標數據）
**Sheet 1：產品推廣目標**
| 欄位名稱 | 類型 | 說明 |
|----------|------|------|
| Group No. | string | 產品組別 |
| Article | string | 產品編號 |
| SKU Target | integer | 推廣目標數量 |
| Target Type | string | 目標類別 (HK/MO/ALL) |
| Promotion Days | integer | 推廣日數 |
| Target Cover Days | integer | 推廣目標安全覆蓋日數 |

**Sheet 2：店鋪推廣目標**
| 欄位名稱 | 類型 | 說明 |
|----------|------|------|
| Site | string | 店鋪編號 |
| Shop Target(HK) | integer | 香港店鋪推廣目標 |
| Shop Target(MO) | integer | 澳門店鋪推廣目標 |
| Shop Target(ALL) | integer | 所有店鋪推廣目標 |

### 系統限制
1. 僅支援Excel檔案格式（.xlsx）
2. 檔案大小建議不超過50MB
3. 數據處理在記憶體中完成，不會儲存到伺服器
4. 支援多語言（英文/中文）

## 測試
運行單元測試：
```bash
python -m unittest tests.py
```

## 部署

### 本地部署
按照上述安裝指南運行即可。

### 雲端部署
支援部署到Streamlit Sharing、Heroku等雲端平台。

## 更新日誌
詳見VERSION.md檔案。

## 支援與聯繫
如有問題，請聯繫開發者Ricky。