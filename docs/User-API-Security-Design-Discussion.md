# User API 安全性設計探討

## 背景

在 WeaMind LINE Bot 專案的 `feature/liff-location-settings` 分支開發過程中，發現 User 相關 API 存在重大安全漏洞。本文件記錄了針對這些問題的深入討論、解決方案分析，以及最終的設計決策。

## 核心問題識別

### 問題 1: User CRUD API 不當對外暴露

**現狀**：
```python
# 目前暴露的 5 個 User API
POST   /users              # 創建用戶
GET    /users/{user_id}    # 查詢用戶
PATCH  /users/{user_id}    # 更新用戶
DELETE /users/{user_id}    # 刪除用戶
POST   /users/locations    # 設定位置 (有認證)
```

**安全風險**：
- 前 4 個 API 完全沒有認證保護
- 任何人都可以創建、查詢、修改、刪除任意用戶
- 攻擊者可以遍歷 `user_id` 獲取所有用戶資料
- 可能造成資料洩露、未授權修改、惡意刪除等安全事件

### 問題 2: Primary Key 設計的安全隱患

**現狀**：
```python
id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
```

**安全風險**：
- 自增整數 ID (1, 2, 3, 4...) 完全可預測
- 攻擊者可以推測用戶數量和遍歷所有用戶
- 典型的 IDOR (Insecure Direct Object Reference) 漏洞

## 解決方案分析

### 針對問題 1 的解決方案

#### 方案 A: 為所有 API 加入認證
**描述**：為 4 個 CRUD API 都加上 LINE ID Token 驗證

**優點**：
- 保留完整 CRUD 功能
- 符合 RESTful 設計原則
- 為未來擴展保留彈性

**缺點**：
- 增加實作複雜度
- 需要重新設計認證機制
- 違反最小權限原則

#### 方案 B: 移除不必要的公開 API ⭐ (採用)
**描述**：分析業務需求，移除不必要的對外 API

**從 PRD 分析真實需求**：
- **用戶創建**：應通過 LINE Bot 互動自動觸發 → 內部邏輯，不需外部 API
- **用戶查詢**：用戶只需查看自己資料 → 內部邏輯，不需外部 API
- **用戶更新**：主要是地點設定 → 已有 `/locations` API
- **用戶刪除**：LINE Bot 場景下極少需要 → 不需外部 API

**設計原則**：
> "不需要的功能就不要暴露，這比加任何認證都更安全"

**最終架構**：
```
🌐 公開 API (對外)
├── POST /users/locations  ← LIFF 地點設定 (已有認證)

🔒 內部 Service (不對外)
├── create_user()          ← LINE webhook 觸發
├── get_user()             ← LINE Bot 內部使用
├── update_user()          ← 內部使用
└── delete_user()          ← 管理功能，內部使用
```

**優點**：
- 最小攻擊面，根本性解決安全問題
- 符合業務邏輯和 LINE Bot 生態
- 簡化架構，降低維護成本
- 遵循 YAGNI (You Aren't Gonna Need It) 原則

#### 方案 C: 區分內部/外部 API
**描述**：將 API 分為內部和外部兩套，使用不同的安全策略

**優點**：
- 最大靈活性
- 符合微服務最佳實踐

**缺點**：
- 實作複雜度最高
- 需要更多基礎設施支援
- 對當前需求來說過度工程

### 針對問題 2 的解決方案

#### 方案 A: 改用 UUID 作為 Primary Key
```python
id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
```

**優點**：
- 完全不可預測
- 標準的安全實踐

**缺點**：
- 性能較差（字串比較 vs 整數比較）
- 佔用更多存儲空間
- 需要遷移現有資料

#### 方案 B: 雙 ID 設計模式 ⭐ (採用)
```python
class User(Base):
    # 內部 Primary Key - 效能最佳
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # LINE 平台的唯一識別 - 對外使用
    line_user_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    
    # 未來如需額外公開 ID
    # public_id: Mapped[str] = mapped_column(String, unique=True, index=True, default=lambda: str(uuid4()))
```

**設計原則**：
- **內部使用 int id**：JOIN 查詢效能最佳，記憶體使用最少
- **對外使用 line_user_id**：不可預測，安全且符合 LINE 生態
- **隔離性**：內部 ID 永不洩露，外部 ID 安全暴露

**優點**：
- 兼顧效能和安全性
- 最小改動成本
- 業界最佳實踐
- 符合當前架構

## 達成的重要結論

### 1. 安全設計的根本原則
**"安全的核心不是加更多認證，而是不暴露不需要的功能"**

從業務需求出發思考，比從技術角度添加保護措施更有效。

### 2. 架構設計的指導原則
- **YAGNI (You Aren't Gonna Need It)**：不實作當前不需要的功能
- **最小權限原則**：只暴露必要的 API
- **最小攻擊面**：減少對外暴露的端點

### 3. LINE Bot 生態的特殊性
- 用戶身份完全依賴 LINE ID
- 大部分互動通過 Rich Menu 點擊完成
- 用戶管理應該是封閉的內部邏輯

### 4. 效能與安全的平衡
雙 ID 設計模式是業界成熟的解決方案，能夠同時滿足：
- 內部查詢的高效能需求
- 對外暴露的安全性需求

## 實施計劃

### 階段 1: 立即安全措施 (高優先級)
```
□ 移除危險的公開 API：
  - DELETE /users/{user_id}  ← 立即移除
  - PATCH /users/{user_id}   ← 立即移除  
  - GET /users/{user_id}     ← 立即移除
  - POST /users             ← 立即移除

□ 保留必要的 API：
  - POST /users/locations   ← 保留 (LIFF 使用)
```

### 階段 2: 架構優化 (中優先級)
```
□ 確保所有用戶操作通過內部 Service 層
□ 完善 LINE webhook 中的用戶自動創建邏輯
□ 建立內部用戶管理的最佳實踐文件
```

### 階段 3: 長期規劃 (低優先級)
```
□ 如有需要，考慮加入 public_id 欄位
□ 建立審計日誌機制
□ 考慮引入 RBAC (角色權限控制)
```

## 尚未解決的問題

### 1. 現有資料遷移
- 如何處理已暴露的 API 端點？
- 是否需要通知前端/客戶端移除對這些 API 的調用？

### 2. 監控與告警
- 如何監控是否有人仍在嘗試存取被移除的 API？
- 是否需要建立安全事件的告警機制？

### 3. 文件更新
- 需要更新 API 文件
- 需要更新開發者指南，說明正確的用戶操作方式

## 後續思考方向

### 1. 安全稽核
定期檢視所有對外 API 的必要性和安全性

### 2. 最佳實踐建立
為團隊建立 API 設計的安全檢查清單：
- [ ] API 是否真的需要對外暴露？
- [ ] 如果需要，是否有適當的認證？
- [ ] 是否使用了可預測的識別符？
- [ ] 是否遵循最小權限原則？

### 3. 自動化檢測
考慮在 CI/CD 流程中加入安全掃描，自動檢測：
- 新增的公開 API 是否有認證
- 是否使用了自增 ID 作為對外識別符
- 是否違反了最小暴露原則

## 參考資料

- [OWASP Top 10 - Broken Access Control](https://owasp.org/Top10/A01_2021-Broken_Access_Control/)
- [OWASP IDOR Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Insecure_Direct_Object_Reference_Prevention_Cheat_Sheet.html)
- WeaMind PRD v1.0 - 了解真實業務需求的重要依據

---

**文件建立時間**: 2025年8月17日  
**討論參與者**: 開發團隊  
**決策狀態**: 已達成共識，待實施  
**下次檢視**: 實施完成後
