# Git Worktree 管理使用說明

## 📋 概述

WeaMind 專案整合了 Git worktree 管理功能，讓您可以輕鬆進行平行開發。透過 Makefile 指令，您可以方便地創建、管理和移除 worktree，實現同時開發多個分支的需求。

## 🎯 什麼是 Git Worktree？

Git worktree 允許您在同一個倉庫中同時 checkout 多個分支到不同的目錄，每個目錄都是獨立的工作區，但共享同一個 Git 歷史記錄。

### 優勢
- ✅ 同時開發多個功能分支
- ✅ 快速切換不同版本進行測試
- ✅ 避免頻繁的 `git stash` 和分支切換
- ✅ 每個 worktree 有獨立的工作狀態

## 🚀 快速開始

### 可用指令

```bash
make worktree-add     # 創建新的 worktree
make worktree-list    # 列出所有 worktree
make worktree-remove  # 移除指定的 worktree
make worktree-clean   # 清理過期的 worktree 引用
```

## 📖 詳細使用說明

### 1. 創建 Worktree

```bash
make worktree-add
```

執行後會顯示互動介面：

```
🌳 Git Worktree 創建工具

📋 現有分支：
  feature/add-wea-net
  feature/location-input-parsing
  feature/quick-reply
  feature/rich-menu
* feature/worktree-management

💡 請輸入要創建 worktree 的分支名稱：
```

#### 情況 1：為現有分支創建 worktree
```
輸入：feature/rich-menu

🌳 為現有分支 'feature/rich-menu' 創建 worktree...
📁 路徑: ../WeaMind-feature/rich-menu
✅ 成功創建 worktree!
📂 cd ../WeaMind-feature/rich-menu
```

#### 情況 2：創建新分支和 worktree
```
輸入：feature/new-feature

🌱 分支 'feature/new-feature' 不存在，將創建新分支...
📁 路徑: ../WeaMind-feature/new-feature
✅ 成功創建新分支和 worktree!
📂 cd ../WeaMind-feature/new-feature
```

#### 情況 3：錯誤處理 - 分支正在使用中
```
輸入：feature/worktree-management

❌ 錯誤：目標分支 'feature/worktree-management' 正在當前目錄中被使用
💡 解決方案：
   1. 切換到其他分支: git checkout main
   2. 然後再執行: make worktree-add
```

### 2. 列出 Worktree

```bash
make worktree-list
```

輸出範例：
```
📋 當前 worktrees：
/Users/kyo/Code/WeaMind                          6c2e2b0 [feature/worktree-management]
/Users/kyo/Code/WeaMind-feature/rich-menu        68f9d5f [feature/rich-menu]
/Users/kyo/Code/WeaMind-feature/new-feature      6c2e2b0 [feature/new-feature]
```

### 3. 移除 Worktree

```bash
make worktree-remove
```

互動選擇介面：
```
📋 可移除的 worktrees：
  1) /Users/kyo/Code/WeaMind-feature/rich-menu
  2) /Users/kyo/Code/WeaMind-feature/new-feature

🗑️  請選擇要移除的 worktree 編號 (1-2)：
```

選擇後會要求確認：
```
輸入：1

⚠️  確定要移除 worktree: /Users/kyo/Code/WeaMind-feature/rich-menu？ (y/N)
輸入：y

✅ 成功移除 worktree: /Users/kyo/Code/WeaMind-feature/rich-menu
```

### 4. 清理過期引用

```bash
make worktree-clean
```

```
🧹 清理過期的 worktree 引用...
✅ 清理完成
```

## 💡 實際使用場景

### 場景 1：平行開發兩個功能

```bash
# 1. 開發第一個功能
git checkout -b feature/user-authentication
# 在主目錄開發...

# 2. 需要同時開發第二個功能
make worktree-add
# 輸入：feature/payment-integration

# 3. 現在有兩個獨立的工作環境
# 主目錄：/Users/kyo/Code/WeaMind (feature/user-authentication)
# Worktree：../WeaMind-feature/payment-integration
```

### 場景 2：Bug 修復而不影響當前開發

```bash
# 當前在開發功能分支
git checkout feature/new-dashboard

# 緊急 bug 需要修復
make worktree-add
# 輸入：hotfix/critical-bug

cd ../WeaMind-hotfix/critical-bug
# 修復 bug...
git add . && git commit -m "Fix critical bug"
git push origin hotfix/critical-bug

# 回到原功能開發
cd /Users/kyo/Code/WeaMind
# 繼續開發...
```

### 場景 3：測試不同版本

```bash
# 為現有分支創建 worktree 進行測試
make worktree-add
# 輸入：feature/experimental-ui

cd ../WeaMind-feature/experimental-ui
# 測試實驗性功能...

# 同時在主目錄保持穩定版本進行對比
```

## 📂 目錄結構

使用 worktree 後的目錄結構：

```
~/Code/
├── WeaMind/                                    # 主目錄
│   ├── .git/                                   # 主 Git 倉庫
│   ├── app/
│   ├── docs/
│   └── ...
├── WeaMind-feature/
│   ├── rich-menu/                              # worktree 1
│   │   ├── .git                                # Git 檔案（指向主倉庫）
│   │   ├── app/
│   │   └── ...
│   ├── new-feature/                            # worktree 2
│   │   ├── .git
│   │   ├── app/
│   │   └── ...
│   └── payment-integration/                    # worktree 3
│       ├── .git
│       ├── app/
│       └── ...
└── WeaMind-hotfix/
    └── critical-bug/                           # worktree 4
        ├── .git
        ├── app/
        └── ...
```

## ⚠️  重要注意事項

### Git Worktree 限制
1. **一個分支只能被一個 worktree checkout**
   - 如果分支已在使用中，必須先切換到其他分支才能創建該分支的 worktree

2. **主目錄也是一個 worktree**
   - 主目錄會出現在 `git worktree list` 中
   - 不能移除主目錄本身

3. **分支切換限制**
   - 在 worktree 中不能切換到其他 worktree 正在使用的分支

### 最佳實務

1. **命名規範**
   ```bash
   feature/功能名稱        # 功能開發
   hotfix/修復名稱         # 緊急修復
   bugfix/錯誤名稱         # 一般錯誤修復
   ```

2. **工作流程建議**
   ```bash
   # 1. 先確定當前分支狀態
   git status
   
   # 2. 如果需要為當前分支創建 worktree，先切換
   git checkout main
   
   # 3. 創建 worktree
   make worktree-add
   
   # 4. 移動到 worktree 目錄
   cd ../WeaMind-feature/your-branch
   ```

3. **清理建議**
   - 定期執行 `make worktree-clean` 清理過期引用
   - 完成開發後記得移除不需要的 worktree
   - 保持 worktree 數量在合理範圍（建議不超過 3-4 個）

## 🔧 故障排除

### 問題：無法創建 worktree
```
❌ 創建失敗：分支 'feature/xxx' 可能已在使用中
```

**解決方案：**
1. 檢查分支是否在其他地方被 checkout：`make worktree-list`
2. 切換到不同的分支：`git checkout main`
3. 重新嘗試創建

### 問題：路徑已存在
```
❌ 錯誤：worktree 路徑已存在: ../WeaMind-feature/xxx
```

**解決方案：**
1. 移除現有目錄：`rm -rf ../WeaMind-feature/xxx`
2. 或使用 `make worktree-remove` 正確移除
3. 重新創建

### 問題：意外刪除了 worktree 目錄
如果直接刪除了 worktree 目錄而不是用 `git worktree remove`：

```bash
# 清理過期引用
make worktree-clean
```

## 🎯 總結

Git worktree 功能讓 WeaMind 專案的平行開發變得簡單高效。透過簡潔的 Makefile 指令，您可以：

- 🚀 快速創建和管理多個工作環境
- 🔄 無縫切換不同功能的開發
- 🛡️ 避免因頻繁切換分支造成的狀態丟失
- 📈 提升開發效率和程式碼品質

開始使用 `make worktree-add` 體驗平行開發的便利性吧！
