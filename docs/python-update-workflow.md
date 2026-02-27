# Python 環境更新流程

## 完整更新流程

當需要檢查並更新 Python 版本時，按照以下順序執行：

### 1. 更新 UV 本身

```bash
uv self update
```

UV 需要先更新才能知道最新的 Python 版本。

### 2. 檢查可用的 Python 版本

```bash
uv python list | grep "3.14"
```

這會顯示所有 Python 3.14.x 版本，包括：
- 已安裝的版本
- 可下載的新版本（標示為 `<download available>`）

### 3. 安裝新版本（如果有）

假設發現 3.14.3 可用：

```bash
uv python install 3.14.3
```

### 4. 移除舊版本（可選）

```bash
uv python uninstall 3.14.2
```

### 5. 重建虛擬環境

```bash
rm -rf .venv
uv sync
```

由於 `.python-version` 檔案寫的是 `3.14`，UV 會自動使用最新的 3.14.x 版本。

### 6. 驗證版本

```bash
uv run python --version
```

## 快速檢查指令

```bash
# 一次性檢查所有資訊
uv --version && echo "---" && uv python list | grep "3.14" && echo "---" && uv run python --version
```

## 版本檔案說明

- `.python-version`: 寫 `3.14` 表示使用最新的 3.14.x patch 版本
- `pyproject.toml`: 定義專案依賴和 Python 版本要求

## 注意事項

- 更新不是自動的，需要手動執行上述流程
- patch 版本（如 3.14.2 → 3.14.3）通常只包含 bug 修復，很安全
- minor 版本（如 3.14 → 3.15）可能有破壞性變更，需謹慎
