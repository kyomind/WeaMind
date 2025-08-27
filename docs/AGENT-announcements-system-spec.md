# AGENT-公告系統開發規格文件

## 一、問題背景與目標 (Why)

### 核心問題
LINE Bot 的 Rich Menu 有一個「其它」按鈕功能未定，需要建立與用戶的有效溝通管道，讓開發團隊能夠向用戶推送重要資訊（系統維護、新功能發布等）。

### 解決目標
1. **建立用戶溝通管道**：提供系統公告、維護通知等資訊
2. **降低維護成本**：採用單一資料源，避免重複維護
3. **提升用戶體驗**：在 LINE 對話框內提供即時、流暢的資訊查詢體驗
4. **建立擴展架構**：為後續其他「其它」功能奠定基礎

## 二、功能需求 (What)

### 主要功能
1. **Rich Menu「其它」按鈕**：觸發 Quick Reply 選單
2. **四個子功能選項**：
   - 📢 **公告**：系統維護、新功能等資訊（Flex Message + 靜態頁面）
   - 🔄 **更新**：版本迭代紀錄（連結到 GitHub CHANGELOG.md）
   - 📖 **使用說明**：產品功能操作指南（靜態頁面）
   - ℹ️ **專案介紹**：產品背景、理念與特色（靜態頁面）

### 用戶流程
```
用戶點擊 Rich Menu「其它」
↓
收到 Quick Reply 四選項選單
↓
點擊「📢 公告」→ 立即收到 Flex Message Carousel（最新1-3則）
點擊「🔄 更新」→ 開啟 GitHub CHANGELOG.md 頁面
點擊「📖 使用說明」→ 開啟功能操作指南頁面
點擊「ℹ️ 專案介紹」→ 開啟產品背景介紹頁面
```

## 三、技術方案與實作方式 (How)

### 整體架構設計
- **核心原則**：「單一資料源 + 雙重呈現」
- **公告資料源**：`/static/announcements.json`（唯一資料來源）
- **雙重呈現**：
  1. **即時體驗**：Flex Message Carousel（最新1-3則）
  2. **完整資訊**：靜態網頁（所有歷史公告）

### 檔案結構
```
/static/
├── announcements/index.html    # 完整公告頁面
├── help/index.html            # 使用說明頁面
├── about/index.html           # 專案介紹頁面
└── announcements.json         # 公告資料源
```

### 公告資料 Schema
```json
{
  "version": 1,
  "updated_at": "2025-08-27T10:00:00Z",
  "items": [
    {
      "id": "2025-09-maint",
      "title": "9/1 例行維護",
      "body": "完整的公告內容說明...",
      "level": "maintenance",
      "start_at": "2025-09-01T00:00:00+08:00",
      "end_at": "2025-09-01T02:00:00+08:00",
      "visible": true
    }
  ]
}
```

### Schema 與 Flex Message 對應關係

此 Schema 專為 LINE Flex Message 設計，每個欄位都有明確的視覺呈現目的：

#### 欄位映射規則
```
Schema 欄位           → Flex Message 組件
─────────────────────────────────────────
title (≤20字)        → Header 區域主標題
body (截斷至50字)     → Body 區域內容文字
level               → 決定整體顏色主題和標籤
start_at            → 排序依據（新→舊）
visible             → 是否出現在 Carousel
id                  → 內部識別（不顯示）
end_at              → 靜態頁面用（不顯示）
```

#### Level 視覺映射
```json
{
  "info": {
    "color": "#2196F3",      // 藍色
    "label": "一般資訊",
    "usage": "功能介紹、歡迎訊息等"
  },
  "warning": {
    "color": "#FF9800",      // 橘色
    "label": "重要提醒",
    "usage": "重要變更、注意事項等"
  },
  "maintenance": {
    "color": "#F44336",      // 紅色
    "label": "維護公告",
    "usage": "系統維護、服務中斷等"
  }
}
```

#### 技術限制考量
- **標題20字限制**：確保在手機螢幕上完整顯示
- **內容50字限制**：平衡資訊量與閱讀體驗
- **最多3則顯示**：避免 Carousel 過長影響用戶體驗
- **時間排序**：確保最新訊息優先展示

### 實作要點
1. **後端處理**：
   - 在 `app/line/service.py` 新增「其它」按鈕事件處理
   - 實作 `handle_announcements` postback 處理函式
   - 動態讀取 JSON 並生成 Flex Message Carousel

2. **前端處理**：
   - 靜態頁面使用 JavaScript fetch 同一份 `announcements.json`
   - 客戶端渲染完整公告列表

3. **靜態檔案服務**：
   - 在 FastAPI 中設定 `/static` 路由
   - 部署在現有網域 `https://api.kyomind.tw/static/`

## 四、技術決策與限制

### 已確認的決策
1. **level 欄位值**：`info`（一般資訊）/ `warning`（重要提醒）/ `maintenance`（維護公告）
2. **Flex Message 限制**：
   - 最多顯示 3 則公告
   - 標題 ≤ 20 字
   - 內容摘要 ≤ 50 字
   - 按 `start_at` 時間倒序排列
3. **不實作主動推送**：避免 LINE API 推送費用
4. **快取策略**：直接讀取檔案，不使用快取（檔案小且變動頻率低）
5. **歷史管理**：保留 6 個月，使用 `visible: false` 隱藏過期公告

### 技術限制與考量
1. **LINE API 限制**：
   - Quick Reply 最多 13 個選項（目前使用 4 個）
   - Flex Message 有字數與結構限制
   - 推送訊息需要費用

2. **部署考量**：
   - 使用現有網域避免 CORS 問題
   - 善用現有 Nginx 和 HTTPS 憑證
   - 所有資源在同一 repo 便於版本控制

3. **維護考量**：
   - 手動編輯 JSON 檔案（變動頻率低）
   - GitHub CHANGELOG.md 零維護成本
   - 靜態頁面相對穩定

## 五、實作優先順序

### 第一階段：核心功能
1. 建立靜態檔案架構與 FastAPI 路由設定
2. 設計並建立 `announcements.json` 範例資料
3. 實作 Rich Menu「其它」按鈕事件處理

### 第二階段：主要功能
1. 實作 Quick Reply 四選項選單
2. 實作公告 Flex Message 動態生成邏輯
3. 建立公告完整頁面（靜態 HTML + JavaScript）

### 第三階段：完善功能
1. 建立使用說明與專案介紹靜態頁面
2. 撰寫相關單元測試
3. 整合測試與錯誤處理

## 六、驗收標準

### 功能驗收
- [ ] 用戶點擊 Rich Menu「其它」按鈕收到 Quick Reply 四選項選單
- [ ] 點擊「📢 公告」收到最新 1-3 則公告的 Flex Message Carousel
- [ ] Flex Message 中的「查看完整內容」按鈕正確跳轉到靜態頁面
- [ ] 其他三個選項正確跳轉到對應頁面
- [ ] 公告資料僅需維護一份 JSON，兩處自動同步顯示

### 技術驗收
- [ ] 靜態檔案正確部署在 `/static/` 路由下
- [ ] JSON 讀取與 Flex Message 生成邏輯正常運作
- [ ] 靜態頁面 JavaScript 正確抓取並渲染 JSON 資料
- [ ] 錯誤處理機制完善（JSON 讀取失敗、格式錯誤等）
- [ ] 相關單元測試通過

## 七、後續擴展考量

1. **快取機制**：未來用戶量增加時可考慮加入 Redis 快取
2. **管理工具**：可開發簡單的 Web 管理介面來編輯公告
3. **推送功能**：評估成本效益後可考慮緊急公告推送
4. **分析功能**：追蹤公告查看率與用戶互動行為

---

**文件版本**：v1.0
**建立日期**：2025-08-27
**最後更新**：2025-08-27
**相關文件**：`docs/Others-spec.md`、`docs/Todo.md`
