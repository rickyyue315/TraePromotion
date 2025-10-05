# 部署配置檔案

## Streamlit Cloud 部署步驟

### 1. 準備GitHub儲存庫
```bash
# 初始化Git儲存庫
git init

# 添加所有文件
git add .

# 提交更改
git commit -m "Initial commit: Retail Promotion System v1.0"

# 連接到GitHub（需要先創建儲存庫）
git remote add origin https://github.com/your-username/retail-promotion-system.git
git push -u origin main
```

### 2. Streamlit Cloud 部署
1. 訪問 https://share.streamlit.io
2. 點擊 "New app"
3. 選擇GitHub儲存庫
4. 設置：
   - Repository: your-username/retail-promotion-system
   - Branch: main
   - Main file path: app.py
   - Requirements file: requirements.txt
5. 點擊 "Deploy"

### 3. 環境變數設置（可選）
在Streamlit Cloud的應用設置中添加：
```
APP_ENV=production
LOG_LEVEL=INFO
ENABLE_UPDATE_CHECK=true
```

## Heroku 部署（替代方案）

### 1. 創建Heroku應用
```bash
# 安裝Heroku CLI
# 登錄Heroku
heroku login

# 創建新應用
heroku create retail-promotion-system

# 設置Python構建包
heroku buildpacks:add heroku/python
```

### 2. 創建必要文件
創建 `Procfile`:
```
web: sh setup.sh && streamlit run app.py
```

創建 `setup.sh`:
```bash
mkdir -p ~/.streamlit/
echo "\[general\]" > ~/.streamlit/credentials.toml
echo "email = \"your-email@example.com\"" >> ~/.streamlit/credentials.toml
echo "\[server\]" > ~/.streamlit/config.toml
echo "headless = true" >> ~/.streamlit/config.toml
echo "port = $PORT" >> ~/.streamlit/config.toml
echo "enableCORS = false" >> ~/.streamlit/config.toml
```

### 3. 部署到Heroku
```bash
# 添加文件到Git
git add .
git commit -m "Add Heroku deployment files"

# 部署到Heroku
git push heroku main

# 打開應用
heroku open
```

## Docker 部署（進階選項）

### 創建 Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 複製需求文件
COPY requirements.txt .

# 安裝Python依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式碼
COPY . .

# 暴露端口
EXPOSE 8501

# 運行應用
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### 構建和運行
```bash
# 構建Docker映像
docker build -t retail-promotion-system .

# 運行容器
docker run -p 8501:8501 retail-promotion-system
```

## 安全性和效能優化

### 1. 安全性設置
- 設置密碼保護（可選）
- 限制檔案上傳大小
- 使用HTTPS
- 實施輸入驗證

### 2. 效能優化
- 啟用Streamlit的caching功能
- 優化數據處理邏輯
- 使用適當的資源限制

### 3. 監控和日誌
- 設置應用監控
- 配置日誌收集
- 設置錯誤警報

## 維護和更新

### 1. 自動更新檢查
應用程式碼中已包含版本檢查功能，會自動比較本地版本與遠端版本。

### 2. 日誌管理
日誌檔案會自動生成在 `app.log`，包含：
- 系統運行狀態
- 錯誤資訊
- 用戶操作記錄

### 3. 備份策略
- 定期備份重要數據
- 版本控制使用Git
- 考慮數據庫備份（如果使用）

## 故障排除

### 常見問題
1. **依賴包安裝失敗**
   - 檢查Python版本兼容性
   - 使用虛擬環境
   
2. **記憶體不足**
   - 優化數據處理邏輯
   - 增加伺服器資源
   
3. **檔案上傳問題**
   - 檢查檔案大小限制
   - 驗證檔案格式

### 支援聯繫
如有部署問題，請聯繫開發者Ricky或參考Streamlit官方文檔。