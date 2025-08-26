# LINE Bot「其它」功能設計思路與最終方案(by google gemini)

本文檔旨在總結 LINE Bot 中「其它」選單功能的設計過程，從初步構想、使用者體驗的演進，到最終的技術架構決策，並特別著重於愈後期的討論，以保留完整的決策思路。

## 一、問題背景與核心功能定義

- **問題**：LINE Bot 的 Rich Menu 有一個「其它」按鈕，其功能未定，需要設計實用、易於維護且體驗良好的功能。
- **決策**：經過討論，此選單應包含三個核心功能：
  - 📢 **服務公告**：發布系統維護、新功能等資訊。
  - 📄 **更新日誌 (Changelog)**：提供版本迭代的紀錄。
  - ℹ️ **產品介紹與使用說明**：幫助新用戶快速上手。

## 二、互動流程的演進與決策

功能的互動流程經過了數次迭代，最終在「即時性」、「流暢度」與「維護成本」之間取得了平衡。

### 1. 初步構想：直接顯示內容 vs. 提供選單

- **討論點**：點擊「其它」後，是直接顯示某個預設內容，還是先提供一個選單讓使用者選擇？
- **最終決策**：**使用 Quick Reply 選單**。
- **決策思路**：
  - **使用者控制權**：點擊後先提供選項（公告、日誌、說明），能給予使用者明確的控制權，避免呈現非預期的資訊。
  - **最佳反應速度**：Quick Reply 是 LINE 中反應最快、最輕量的互動元件，幾乎沒有延遲，體驗遠優於載入一個複雜的 Flex Message 或等待網頁跳轉。

### 2. 內容呈現方式的探討：Flex Message vs. 外部網頁

這是整個設計過程中最核心的討論，直接影響了使用者體驗與開發複雜度。

#### (1) 服務公告

- **初期想法**：建立一個靜態網頁來顯示所有公告。
- **體驗考量**：開啟外部網頁會中斷對話流程，使用者需要跳離 LINE App，體驗不夠流暢。
- **進階想法**：在對話框內使用 Flex Message 呈現，以提供更原生的體驗。
- **疑慮與澄清**：
  - *「Flex Message 是否必須有圖片？」* → **澄清：不需要**。可以設計純文字、無圖片的 Flex Message，排版依然比純文字訊息豐富。
  - *「體驗優劣？」* → **結論：Flex Message 優於開網頁**。在對話框內完成操作的即時性與一致性，是提升使用者體驗的關鍵。
- **最終方案 (混合模式)**：
  - **主要體驗 (門面)**：在 LINE 對話框內使用 **Flex Message (Carousel)** 顯示最新的 1-3 則公告。這提供了最佳的即時性和原生體驗。
  - **完整內容 (後路)**：若公告內容過長或使用者想查看歷史紀錄，可在 Flex Message 中提供一個「查看完整內容」的按鈕，連結到一個**靜態網頁**。
  - **優點**：此方案完美兼顧了「即時體驗」與「完整資訊呈現」兩個需求。

#### (2) 更新日誌 (Changelog)

- **最終方案**：**直接連結到 GitHub 上的 `CHANGELOG.md` 渲染頁面**。
- **決策思路**：這是**零成本、零維護**的最佳實踐。開發者本來就會在版本控制中維護 `CHANGELOG.md`，而 GitHub 會自動將其渲染成美觀的網頁，無需任何額外開發。

#### (3) 介紹與說明

- **最終方案**：**建立一個靜態網頁**。
- **決策思路**：這部分內容相對固定，變動頻率低。使用靜態網頁最容易進行內容排版和長期維護。

## 三、技術實現與架構決策

技術選型的核心目標是**降低長期維護成本**。

### 1. 資料來源：單一真相原則 (Single Source of Truth)

這是後段討論中最關鍵的技術決策，旨在解決「一份公告資料，如何同時供應給 Flex Message 和靜態網頁」的問題。

- **決策**：在專案的 `/static` 目錄下，維護一份**原始資料 `announcements.json`**。
- **決策思路 (極為重要)**：
  - **動態組裝 Flex Message**：Bot 後端程式讀取 `announcements.json` 的原始資料，並**在執行期 (Runtime) 動態地**將最新的幾則公告組裝成 LINE Flex Message 所需的 JSON 結構後，再回傳給 LINE Platform。**開發者絕不應該手動去編寫複雜的 Flex Message JSON**。
  - **前端渲染靜態頁**：公告的靜態網頁 (`/static/announcements/index.html`) 則透過 JavaScript `fetch` **同一份 `announcements.json`**，並在客戶端將其渲染成完整的公告列表。
- **架構優點**：此方法實現了**「一份資料，兩處使用」**，維護成本降至最低。未來無論是想調整 Flex Message 的樣式還是網頁的排版，都只需要修改對應的「轉換邏輯」或「渲染腳本」，而不需要更動原始資料 `announcements.json`。

### 2. 部署與託管

- **決策**：將所有靜態資源（說明頁、公告頁、`announcements.json`）都放在 Bot 專案的 `/static` 目錄下，並透過現有的網域 (`https://api.kyomind.tw`) 提供服務。
- **決策思路**：
  - **簡化管理**：所有資源都在同一個程式庫 (Repo) 中，方便版本控制與統一一部署。
  - **避免 CORS**：由於靜態頁面和其抓取的 `announcements.json` 檔案同源，完全不存在跨域資源共用 (CORS) 的問題。
  - **善用現有設施**：無需引入新的託管服務 (如 Netlify, Vercel)，直接使用現有的 Nginx 和 HTTPS 憑證即可，零額外成本。

## 四、最終方案總結

| 元件                        | 設計方案                                                                                                                                                                                                                                  |
| --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Rich Menu「其它」按鈕**   | 觸發一個 **Quick Reply** 選單。                                                                                                                                                                                                           |
| **Quick Reply 選單**        | 包含三個選項：<br>1. `[📢 公告]` (Postback Action)<br>2. `[📄 Changelog]` (URI Action)<br>3. `[ℹ️ 介紹與說明]` (URI Action)                                                                                                                  |
| **`[📢 公告]` 的行為**       | 1. 觸發後端邏輯。<br>2. 後端讀取 `/static/announcements.json`。<br>3. 動態生成 **Flex Message Carousel** (顯示最新 1-3 則)。<br>4. 回傳 Flex Message 給使用者。<br>5. Flex Message 內含按鈕，可連結至 `/static/announcements/` 完整頁面。 |
| **`[📄 Changelog]` 的行為**  | 直接開啟 **GitHub** 上的 `CHANGELOG.md` 渲染頁面。                                                                                                                                                                                        |
| **`[ℹ️ 介紹與說明]` 的行為** | 直接開啟 `/static/help/` **靜態頁面**。                                                                                                                                                                                                   |
| **日常維護流程**            | - **發布公告**：僅需修改 `/static/announcements.json` 檔案。<br>- **更新日誌**：僅需修改 `CHANGELOG.md` 檔案。<br>- **修改說明**：修改 `/static/help/index.html` 檔案。                                                                   |
# 摘要：其他功能討論(by claude)

## 核心問題與解答

### 用戶關鍵提問：
1. **「其它」Rich Menu 按鈕應該放什麼功能？**
2. **公告功能如何實作？需要驗證嗎？**
3. **靜態頁面部署在哪裡最適合？**
4. **Flex Message 是否強制要圖片？**
5. **公告來源 JSON 應該放在哪裡？**

## 最終解決方案

### Rich Menu「其它」設計
- **實作方式**：Quick Reply 三鍵（最快速、體驗最佳）
- **三個選項**：
  1. 📢 公告 → Flex Message（來源：`static/announcements.json`）
  2. 📄 Changelog → 直接開 GitHub 的 CHANGELOG.md 頁面
  3. ℹ️ 介紹與說明 → 內建靜態頁面（`https://api.kyomind.tw/static/help/`）

### 公告系統架構
- **資料來源**：單一 `static/announcements.json` 檔案
- **呈現方式**：
  - Flex Message 顯示最新 1-3 則（標題 + 摘要 + 完整內容按鈕）
  - 靜態頁面顯示完整歷史（JS 抓取同一份 JSON 渲染）
- **重大公告**：額外發送簡短文字訊息直接提醒

### 技術細節

#### Flex Message 規格
```json
{
  "type": "flex",
  "altText": "WeaMind 公告",
  "contents": {
    "type": "carousel",
    "contents": [
      {
        "type": "bubble",
        "body": {
          "type": "box",
          "layout": "vertical",
          "contents": [
            {"type": "text", "text": "📢 標題", "weight": "bold"},
            {"type": "text", "text": "內容摘要", "size": "sm", "wrap": true}
          ]
        },
        "footer": {
          "type": "box",
          "layout": "vertical",
          "contents": [
            {
              "type": "button",
              "style": "link",
              "action": {"type": "uri", "label": "查看完整內容", "uri": "..."}
            }
          ]
        }
      }
    ]
  }
}
```

#### 公告 JSON Schema
```json
{
  "version": 1,
  "updated_at": "2025-08-26T07:00:00Z",
  "items": [
    {
      "id": "2025-09-maint",
      "title": "9/1 例行維護",
      "body": "9/1 00:00–02:00 服務暫停。",
      "level": "info",
      "start_at": "2025-09-01T00:00:00+08:00",
      "end_at": "2025-09-01T02:00:00+08:00",
      "visible": true
    }
  ]
}
```

#### 部署建議
- **靜態檔案**：部署在 Bot API 同域名（`https://api.kyomind.tw/static/`）
- **優點**：免 CORS、HTTPS 免費、維護統一
- **檔案結構**：
  ```
  /static/
  ├─ announcements/index.html
  ├─ help/index.html
  └─ announcements.json
  ```

## 重要技術觀點

### Flex Message 特性
- **不強制圖片**：可做純文字版面
- **Carousel 滑動**：最新公告放最左邊
- **字數限制**：標題 ≤30 字、摘要 ≤60 字

### 維護策略
- **單一資料源**：只需維護 `announcements.json`
- **雙向同步**：Flex 和靜態頁自動同步
- **快取策略**：JSON 短快取，HTML/CSS/JS 長快取

### 用戶體驗考量
- **體驗優先順序**：Flex > 靜態頁 > 跳外部連結
- **Quick Reply 優於 Flex 子選單**：響應速度更快
- **重大公告直送聊天室**：避免用戶錯過重要資訊

## 實用範例

### Quick Reply 模板
```json
{
  "type": "text",
  "text": "要看哪一個？",
  "quickReply": {
    "items": [
      {"type":"action","action":{"type":"postback","label":"📢 公告","data":"type=OTHER_ANNOUNCEMENTS"}},
      {"type":"action","action":{"type":"uri","label":"📄 Changelog","uri":"https://github.com/<user>/<repo>/blob/main/CHANGELOG.md"}},
      {"type":"action","action":{"type":"uri","label":"ℹ️ 使用說明","uri":"https://api.kyomind.tw/static/help/"}}
    ]
  }
}
```

### 後端轉換邏輯
```python
def announcements_to_flex(items, limit=3):
    bubbles = []
    for ann in sorted(items, key=lambda x: x["start_at"], reverse=True)[:limit]:
        bubbles.append({
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": f"📢 {ann['title']}", "weight": "bold"},
                    {"type": "text", "text": ann['body'][:60], "size": "sm", "wrap": True}
                ]
            }
        })
    return {"type": "flex", "altText": "WeaMind 公告", "contents": {"type": "carousel", "contents": bubbles}}
```

## 結論
此設計方案達到了：
- **最小維護成本**（單一 JSON 檔案）
- **最佳使用體驗**（Quick Reply + Flex）
- **完整功能覆蓋**（公告、說明、版本資訊）
- **技術可行性高**（同域部署、免驗證）
