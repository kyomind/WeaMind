#!/bin/bash
# WeaMind CHANGELOG 管理腳本
# 作者：WeaMind 開發團隊
# 用途：簡化版本發布流程

set -e  # 遇到錯誤立即退出

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 輔助函式
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 顯示使用方法
show_usage() {
    cat << EOF
WeaMind CHANGELOG 管理工具

用法:
  $0 prepare [version]     準備 CHANGELOG 資料（收集 commits）
  $0 update <version>      更新版本號並發布
  $0 release <version>     驗證並發布版本（含參數檢查）
  $0 status               顯示目前狀態
  $0 help                 顯示此幫助
  $0 guide                顯示完整使用指南
  $0 quick-help           顯示簡化指南（for Makefile）

範例:
  $0 prepare              # 準備下一版本的資料
  $0 prepare 0.2.0        # 準備指定版本的資料
  $0 release 0.2.0        # 發布 v0.2.0（含驗證）

EOF
}

# 顯示簡化指南（給 Makefile 使用）
show_quick_help() {
    cat << 'EOF'
📝 CHANGELOG 維護指南 (簡化版)：

🔍 基本操作：
   make changelog-status                    # 查看目前狀態
   make changelog-prepare [VERSION=x.y.z]   # 準備 commits 資料
   make changelog-release VERSION=x.y.z     # 發布新版本

📋 完整流程：
   1. make changelog-prepare               # 收集 commits
   2. 用 Copilot Chat 產生 CHANGELOG 內容
   3. 手動編輯 CHANGELOG.md 加入新版本
   4. make changelog-release VERSION=x.y.z # 更新版本並發布

💡 Copilot Chat 提示範本已內建在 prepare 指令中
EOF
}

# 顯示完整使用指南
show_guide() {
    cat << 'EOF'
📝 CHANGELOG 維護指南 (簡化版)：

🔍 基本操作：
   make changelog-status                    # 查看目前狀態
   make changelog-prepare [VERSION=x.y.z]   # 準備 commits 資料
   make changelog-release VERSION=x.y.z     # 發布新版本

📋 完整流程：
   1. make changelog-prepare               # 收集 commits
   2. 用 Copilot Chat 產生 CHANGELOG 內容
   3. 手動編輯 CHANGELOG.md 加入新版本
   4. make changelog-release VERSION=x.y.z # 更新版本並發布

💡 Copilot Chat 提示範本已內建在 prepare 指令中
EOF
}

# 帶參數驗證的發布函式
release_with_validation() {
    local version=$1

    if [[ -z "$version" ]]; then
        log_error "請指定版本號: make changelog-release VERSION=0.2.0"
        exit 1
    fi

    update_version "$version"
}

# 檢查 Git 狀態
check_git_status() {
    if ! git diff-index --quiet HEAD --; then
        log_error "工作目錄有未提交的變更，請先提交或暫存"
        exit 1
    fi

    local current_branch=$(git rev-parse --abbrev-ref HEAD)
    if [[ "$current_branch" != "main" ]]; then
        log_error "版本發布必須在 main 分支進行，目前在 ${current_branch} 分支"
        log_info "請切換到 main 分支後再執行：git checkout main"
        exit 1
    fi
}

# 檢查 Git 狀態（發布專用，允許 CHANGELOG.md 有變更）
check_git_status_for_release() {
    local current_branch=$(git rev-parse --abbrev-ref HEAD)
    if [[ "$current_branch" != "main" ]]; then
        log_error "版本發布必須在 main 分支進行，目前在 ${current_branch} 分支"
        log_info "請切換到 main 分支後再執行：git checkout main"
        exit 1
    fi

    # 檢查除了 CHANGELOG.md 之外是否有其他未提交變更
    local changed_files=$(git diff --name-only HEAD)
    local non_changelog_changes=$(echo "$changed_files" | grep -v "^CHANGELOG\.md$" | wc -l | tr -d ' ')

    if [[ "$non_changelog_changes" -gt 0 ]]; then
        log_error "除了 CHANGELOG.md 之外還有其他未提交的變更："
        echo "$changed_files" | grep -v "^CHANGELOG\.md$"
        log_info "請先提交或暫存這些變更"
        exit 1
    fi

    # 檢查是否有 CHANGELOG.md 變更
    if ! git diff --quiet HEAD -- CHANGELOG.md; then
        log_info "✅ 發現 CHANGELOG.md 變更，將包含在版本 commit 中"
        return 0
    else
        log_warning "⚠️  CHANGELOG.md 沒有變更，請確認是否已更新版本內容"
        read -p "是否繼續？(y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "發布已取消"
            exit 0
        fi
    fi
}

# 獲取最新標籤
get_latest_tag() {
    git describe --tags --abbrev=0 2>/dev/null || echo "v0.1.0"
}

# 收集 commits
collect_commits() {
    local latest_tag=$(get_latest_tag)
    local range="${latest_tag}..HEAD"

    log_info "從 ${latest_tag} 到現在的變更："
    echo
    git log ${range} --oneline --pretty=format:"- %s (%h)" 2>/dev/null || {
        log_warning "沒有找到新的 commits"
        return 1
    }
    echo
}

# 顯示狀態
show_status() {
    log_info "=== WeaMind 版本狀態 ==="
    echo
    echo "📂 專案目錄: $(pwd)"
    echo "🌿 當前分支: $(git rev-parse --abbrev-ref HEAD)"
    echo "🏷️  最新標籤: $(get_latest_tag)"
    echo "📝 當前版本: $(grep '^version = ' pyproject.toml | cut -d'"' -f2)"
    echo

    local latest_tag=$(get_latest_tag)
    local commit_count=$(git rev-list ${latest_tag}..HEAD --count 2>/dev/null || echo "0")

    if [[ "$commit_count" -gt 0 ]]; then
        log_info "📊 自 ${latest_tag} 以來有 ${commit_count} 個新 commits"
        echo
        collect_commits
    else
        log_success "✨ 沒有未發布的變更"
    fi
}

# 準備 CHANGELOG 資料
prepare_changelog() {
    local target_version=$1

    log_info "=== 準備 CHANGELOG 資料 ==="

    # 檢查 Git 狀態（包含分支檢查）
    check_git_status

    # 顯示基本資訊
    show_status
    echo

    # 收集 commits
    log_info "🔍 正在收集 commit 訊息..."
    if ! collect_commits; then
        log_warning "沒有新的變更可以發布"
        exit 0
    fi

    echo
    log_info "📋 請複製上述 commits 內容到 Copilot Chat，使用以下提示詞："
    echo
    cat << 'EOF'
根據以下 git commits 為 WeaMind 產生 CHANGELOG 內容：

[貼上上述 commits]

要求：
- 繁體中文，Keep a Changelog 格式
- 簡潔明瞭，面向一般用戶而非開發者
- 突出產品價值和用戶體驗
- 避免過多技術細節
- 不要包含「即將推出」或「技術亮點」區塊
- 每項功能一行描述，重點功能可用粗體

格式範例：
## [版本號] - 日期

### 新增
- **核心功能名稱**: 簡潔的功能描述，說明對用戶的價值
- 次要功能描述

### 修正
- 修復具體問題，說明影響和改善

### 改進
- 現有功能的優化說明
EOF

    if [[ -n "$target_version" ]]; then
        echo
        log_info "🎯 目標版本: v${target_version}"
    fi
}

# 更新版本並發布
update_version() {
    local version=$1

    if [[ -z "$version" ]]; then
        log_error "請指定版本號"
        show_usage
        exit 1
    fi

    # 驗證版本格式
    if ! [[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        log_error "版本格式錯誤，請使用語意化版本 (如: 1.0.0)"
        exit 1
    fi

    log_info "=== 發布版本 v${version} ==="

    # 檢查 Git 狀態（允許 CHANGELOG.md 有未提交變更）
    check_git_status_for_release

    # 更新 pyproject.toml
    log_info "📝 更新 pyproject.toml 版本號..."
    sed -i '' "s/^version = .*/version = \"${version}\"/" pyproject.toml

    # 確認更新
    local current_version=$(grep '^version = ' pyproject.toml | cut -d'"' -f2)
    if [[ "$current_version" != "$version" ]]; then
        log_error "版本更新失敗"
        exit 1
    fi

    log_success "版本號已更新為 ${version}"

    # 更新依賴鎖定檔案
    log_info "🔒 更新 uv.lock 檔案..."
    if ! uv lock; then
        log_error "uv lock 執行失敗"
        exit 1
    fi

    log_success "依賴鎖定檔案已更新"

    # 先獨立提交 CHANGELOG.md 變更（如果有的話）
    if ! git diff --quiet HEAD -- CHANGELOG.md; then
        log_info "📝 提交 CHANGELOG 更新..."
        git add CHANGELOG.md
        git commit -m "Update CHANGELOG for v${version}"
        log_success "✅ CHANGELOG 已獨立提交"
    else
        log_warning "⚠️  CHANGELOG.md 沒有變更"
    fi

    # 提交版本相關變更（pyproject.toml + uv.lock）
    log_info "📤 提交版本發布變更..."
    git add pyproject.toml uv.lock

    # 檢查是否有版本變更需要提交
    if git diff --cached --quiet; then
        log_error "沒有版本變更可以提交"
        exit 1
    fi

    git commit -m "Release WeaMind v${version}"

    log_success "✅ 版本發布變更已提交"

    # 在所有本地操作完成後建立標籤
    log_info "🏷️  創建版本標籤..."
    git tag -a "v${version}" -m "Release v${version}"
    log_success "✅ 版本標籤已建立"

    # 一次性推送所有內容（commit + tag）
    log_info "🚀 推送所有變更到遠端..."
    if ! git push origin main --tags; then
        log_error "推送失敗，版本發布中止"
        log_info "💡 提示：可能需要先 git pull 或解決衝突"
        log_warning "⚠️  本地已完成 commit 和 tag，可稍後手動推送"
        exit 1
    fi

    log_success "🎉 版本 v${version} 發布完成！"
    log_info "💡 GitHub Actions 將自動建立 Release"
}

# 主邏輯
main() {
    case "${1:-help}" in
        "prepare")
            prepare_changelog "$2"
            ;;
        "update")
            update_version "$2"
            ;;
        "release")
            release_with_validation "$2"
            ;;
        "status")
            show_status
            ;;
        "guide")
            show_guide
            ;;
        "quick-help")
            show_quick_help
            ;;
        "help"|"-h"|"--help")
            show_usage
            ;;
        *)
            log_error "未知命令: $1"
            show_usage
            exit 1
            ;;
    esac
}

# 執行主邏輯
main "$@"
