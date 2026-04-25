# Security Scanning Configuration

WeaMind 使用多層安全檢查來確保程式碼和依賴的安全性。

## 工具說明

### Bandit
- **功能**：Python 程式碼靜態安全分析
- **配置檔案**：`bandit.yaml`
- **執行命令**：`make security-bandit`

### pip-audit
- **功能**：Python 依賴弱點掃描
- **執行命令**：`make security-audit`

## 已忽略的弱點

基於風險評估，以下弱點已被標記為忽略：

### GHSA-58qw-9mgm-455v (pip <= 26.0.1)
- **風險等級**：中
- **描述**：pip 對同時可被判讀為 tar 與 ZIP 的封包存在解析衝突，可能導致安裝內容與檔名暗示不一致。
- **忽略原因**：
  - GitHub Advisory 目前尚未提供 `first_patched_version`
  - 專案已鎖定到目前可用的新版 pip
  - `uv.lock` 鎖定依賴來源，CI 不從任意未知來源安裝套件
  - 已新增定期檢查，當 advisory withdrawn 或出現修正版時會提醒移除 ignore

## 安全掃描流程

### Pre-commit/Pre-push Hooks
```bash
# 安裝 hooks（首次設定）
uv run pre-commit install
uv run pre-commit install --hook-type pre-push

# 每次 commit 前自動執行：
# - detect-secrets（偵測秘密資訊）
# - 程式碼格式與品質檢查

# 每次 push 前自動執行：
# - bandit（程式碼安全掃描）
```

### 本機開發
```bash
# 完整安全掃描
make security-all

# 個別工具
make security-bandit
make security-audit
```

### CI/CD 整合
安全掃描已整合到 GitHub Actions CI 流程中：
1. 程式碼格式化與 lint 檢查
2. 型別檢查
3. **Bandit 安全掃描**
4. **pip-audit 依賴弱點掃描**
5. 單元測試與覆蓋率檢查

## 報告檔案

安全掃描會產生以下報告檔案（統一輸出到 `security-reports/` 目錄）：
- `security-reports/bandit-report.json`：Bandit 掃描結果
- `security-reports/pip-audit-report.json`：pip-audit 掃描結果

## 維護指南

### 更新忽略清單
如需調整忽略的弱點：

1. 更新 `Makefile` 中的 `--ignore-vuln` 參數
2. 更新 `.github/workflows/ci.yml` 中的相同參數
3. 在此文件中記錄忽略原因

### 定期檢查
GitHub Actions 每週執行 `Check pip-audit ignores`，檢查已忽略的 GHSA 是否已 withdrawn 或出現 `first_patched_version`。若已可處理，workflow 會失敗並提示升級依賴後移除 ignore。

## 最佳實踐

1. **定期更新依賴**：使用 `uv lock --upgrade` 定期更新套件
2. **最小權限原則**：避免給予應用程式不必要的系統權限
3. **容器隔離**：使用 Docker 容器運行應用程式
4. **環境變數保護**：敏感資訊透過環境變數管理，不寫入程式碼
5. **輸入驗證**：對所有外部輸入進行適當的驗證和清理
