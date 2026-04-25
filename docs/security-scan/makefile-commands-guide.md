# WeaMind Makefile 安全掃描指令完整使用說明

## 概述

WeaMind 專案透過 Makefile 提供了便利的安全掃描指令介面。本文檔詳細說明所有與安全掃描相關的指令使用方法、參數選項和最佳實踐。

## 指令總覽

```bash
# 安全掃描相關指令
make security-bandit    # Bandit 程式碼安全掃描
make security-audit     # pip-audit 依賴弱點掃描
make security-all       # 執行完整安全掃描
```

## 詳細指令說明

### 1. security-bandit

**功能**：執行 Bandit 靜態程式碼安全分析

```bash
make security-bandit
```

**執行流程**：
1. 建立 `security-reports/` 目錄（如不存在）
2. 使用 `bandit.yaml` 配置檔掃描 `app/` 目錄
3. 生成 JSON 格式報告到 `security-reports/bandit-report.json`
4. 在控制台顯示人類可讀的掃描結果

**輸出範例**：
```
🔒 執行 Bandit 安全掃描...
[main]  INFO    using config: bandit.yaml
[main]  INFO    running on Python 3.12.10
Run started:2025-10-02 03:18:29.759126

Test results:
        No issues identified.

Code scanned:
        Total lines of code: 2123
        Total lines skipped (#nosec): 0
```

**報告檔案**：
- **位置**：`security-reports/bandit-report.json`
- **格式**：JSON
- **內容**：詳細的掃描結果、問題分級、程式碼位置等

### 2. security-audit

**功能**：執行 pip-audit 依賴弱點掃描

```bash
make security-audit
```

**執行流程**：
1. 建立 `security-reports/` 目錄（如不存在）
2. 掃描當前環境中的所有 Python 套件
3. 檢查已知的 CVE 弱點資料庫
4. 生成 JSON 格式報告到 `security-reports/pip-audit-report.json`
5. 在控制台顯示掃描摘要

**忽略的弱點**：
- `GHSA-58qw-9mgm-455v`：pip 目前尚無修正版的中風險問題

**輸出範例**：
```
🔍 執行 pip-audit 依賴弱點掃描...
No known vulnerabilities found, 1 ignored
```

**報告檔案**：
- **位置**：`security-reports/pip-audit-report.json`
- **格式**：JSON
- **內容**：弱點詳情、受影響套件版本、修復建議等

### 3. security-all

**功能**：執行完整的安全掃描流程

```bash
make security-all
```

**執行順序**：
1. 執行 `make security-bandit`
2. 執行 `make security-audit`
3. 顯示完成訊息

**輸出範例**：
```
🛡️ 執行完整安全掃描...
🔒 執行 Bandit 安全掃描...
[Bandit 輸出...]
🔍 執行 pip-audit 依賴弱點掃描...
[pip-audit 輸出...]
✅ 安全掃描完成！
```

## 配置檔案說明

### bandit.yaml

Bandit 的主要配置檔案，包含：

```yaml
# 排除目錄
exclude_dirs:
  - migrations    # 資料庫遷移檔案
  - tests        # 測試檔案
  - .venv        # 虛擬環境
  - __pycache__  # Python 快取
  - coverage_html_report  # 覆蓋率報告

# 掃描檔案類型
include:
  - "*.py"

# 測試項目（僅包含高/中風險項目）
tests:
  - B102  # exec_used
  - B103  # set_bad_file_permissions
  # ... 更多測試項目
```

**自訂配置**：
- 修改 `exclude_dirs` 來排除特定目錄
- 調整 `tests` 清單來啟用/停用特定檢查
- 設定 `confidence` 和 `severity` 級別

## 進階使用技巧

### 1. 查看詳細報告

```bash
# 查看 Bandit JSON 報告
cat security-reports/bandit-report.json | jq '.'

# 查看 pip-audit JSON 報告
cat security-reports/pip-audit-report.json | jq '.'
```

### 2. 自訂掃描範圍

```bash
# 僅掃描特定目錄
uv run bandit -c bandit.yaml -r app/specific_module

# 掃描特定檔案
uv run bandit -c bandit.yaml app/main.py
```

### 3. 調整輸出格式

```bash
# 生成 HTML 報告
uv run bandit -c bandit.yaml -r app -f html -o security-reports/bandit-report.html

# 生成 CSV 報告
uv run bandit -c bandit.yaml -r app -f csv -o security-reports/bandit-report.csv
```

### 4. 臨時忽略特定問題

```bash
# 在程式碼中使用 # nosec 註解
password = "temp_password"  # nosec B105  # pragma: allowlist secret

# 或在 bandit.yaml 中新增 skips
skips:
  - B105  # hardcoded_password_string
```

## 故障排除

### 常見問題與解決方案

#### 1. Bandit 找不到配置檔案
```bash
# 錯誤訊息
ERROR: Could not read config file bandit.yaml

# 解決方案
# 確保在專案根目錄執行指令
cd /path/to/WeaMind
make security-bandit
```

#### 2. pip-audit 掃描時間過長
```bash
# 使用本地快取加速
uv run pip-audit --cache-dir ~/.cache/pip-audit

# 或跳過特定套件
uv run pip-audit --skip-deps
```

#### 3. 記憶體不足問題
```bash
# 增加掃描時的記憶體限制
BANDIT_MAX_MEMORY=2G make security-bandit
```

## 整合到開發工作流程

### Pre-commit Hooks

Bandit 已整合到 pre-push hooks 中，在每次推送前自動執行：

```yaml
# .pre-commit-config.yaml
- repo: https://github.com/PyCQA/bandit
  rev: 1.8.6
  hooks:
    - id: bandit
      args: ['-c', 'bandit.yaml', '-r', 'app']
      types: [python]
      stages: [pre-push]  # 僅在推送前執行
```

**啟用 pre-commit 和 pre-push**：
```bash
# 安裝 pre-commit hooks（commit 前檢查）
uv run pre-commit install

# 安裝 pre-push hooks（推送前檢查）
uv run pre-commit install --hook-type pre-push

# 手動執行所有 hooks
uv run pre-commit run --all-files

# 僅執行 Bandit（需指定 pre-push stage）
uv run pre-commit run --hook-stage pre-push bandit
```

**工作流程**：
- **每次 commit**：detect-secrets、格式檢查等快速檢查
- **每次 push**：Bandit 安全掃描（較完整但耗時的檢查）

### GitHub Actions 範例

```yaml
- name: Security scan (Bandit)
  run: uv run bandit -c bandit.yaml -r app

- name: Dependency vulnerability scan (pip-audit)
  run: uv run pip-audit --progress-spinner=off --ignore-vuln=GHSA-58qw-9mgm-455v
```

### 本機 pre-commit hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/PyCQA/bandit
    rev: 1.8.6
    hooks:
      - id: bandit
        args: ['-c', 'bandit.yaml', '-r', 'app']
```

## 效能考量

### 掃描時間預估

| 指令            | 程式碼行數 | 預估時間 | 記憶體使用 |
| --------------- | ---------- | -------- | ---------- |
| security-bandit | 2,123 行   | ~5 秒    | ~50MB      |
| security-audit  | 99 套件    | ~10 秒   | ~100MB     |
| security-all    | 全部       | ~15 秒   | ~150MB     |

### 最佳化建議

1. **本機開發**：使用 `security-all` 進行完整檢查
2. **功能分支**：針對修改的模組使用特定掃描
3. **CI/CD**：設定快取機制減少重複掃描時間

## 維護指南

### 定期更新檢查清單

- [ ] 每月檢查工具版本更新
- [ ] 每季檢討忽略的弱點是否仍然合理
- [ ] 每半年評估新的安全檢查工具
- [ ] 年度檢視整體安全掃描策略

### 配置檔案版本控制

所有配置檔案都應納入版本控制：
- `bandit.yaml`
- `Makefile` 中的安全掃描區段
- `.github/workflows/ci.yml` 中的安全檢查步驟

## 相關資源

### 官方文檔
- [Bandit 文檔](https://bandit.readthedocs.io/)
- [pip-audit 文檔](https://pypi.org/project/pip-audit/)

### WeaMind 專案文檔
- [安全性配置說明](../Security.md)
- [實作重點總結](./implementation-highlights.md)
- [專案架構文檔](../Architecture.md)

---

**提示**：建議開發者將本文檔加入書籤，在執行安全掃描時可快速查閱相關指令和參數說明。
