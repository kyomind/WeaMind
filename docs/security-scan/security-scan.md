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

目前沒有忽略中的 pip-audit 弱點。

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
GitHub Actions 每週執行 `Check pip-audit ignores`，避免暫時性的安全例外永久留在 repo 中。

- **執行時間**：每週一 03:00 UTC（台灣時間每週一 11:00），也可從 GitHub Actions 手動執行。
- **執行內容**：workflow 會執行 `python3 scripts/check_pip_audit_ignores.py`。
- **掃描範圍**：script 會 repo-wide 掃描文字檔中的 `--ignore-vuln=GHSA-...`，但會跳過 `.git`、`.venv`、cache、coverage 與 `security-reports/` 等目錄。
- **判斷方式**：對每個被 ignore 的 GHSA，script 會查 GitHub Advisory API，確認 advisory 是否已 withdrawn，或是否已出現 `first_patched_version`。
- **成功代表**：沒有找到 GHSA ignore，或找到的 ignore 目前仍沒有可處理的修正版，也沒有 withdrawn。
- **失敗代表**：至少一個 ignore 可能已經可以移除。這不是 production 故障，而是維護提醒。

這個檢查不會自動修改檔案、升級依賴或開 PR。當 workflow 失敗時，依照 failed log 中列出的 GHSA 與檔案位置處理：

1. 查明受影響套件與修正版。
2. 更新 `pyproject.toml` 與 `uv.lock`，必要時執行 `uv lock --upgrade-package <package>`。
3. 移除 `Makefile`、`.github/workflows/ci.yml` 與相關文件中的 `--ignore-vuln=GHSA-...`。
4. 執行 `uv run pip-audit --progress-spinner=off`。
5. 執行 `python3 scripts/check_pip_audit_ignores.py`，確認沒有 stale ignore。

## 最佳實踐

1. **定期更新依賴**：使用 `uv lock --upgrade` 定期更新套件
2. **最小權限原則**：避免給予應用程式不必要的系統權限
3. **容器隔離**：使用 Docker 容器運行應用程式
4. **環境變數保護**：敏感資訊透過環境變數管理，不寫入程式碼
5. **輸入驗證**：對所有外部輸入進行適當的驗證和清理
