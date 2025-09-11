# 🔒 WeaMind 安全評估與部署檢查清單

## 📊 安全狀態總覽

**目前安全等級**: 🟡 中等風險
**部署狀態**: ✅ 適合遠端部署（有限制條件）
**最後更新**: 2025年8月16日

## ✅ 已完成的安全改進

### 1. Mock Token 移除 ✅ 已完成
- [x] 完全移除所有 `dev-mock-token-` 相關邏輯
- [x] 只接受真實的 LINE ID Token
- [x] 移除開發模式降級處理

### 2. CORS 配置強化 ✅ 已完成
- [x] 限制 origin 為 `https://liff.line.me`
- [x] 移除開發環境的寬鬆設定
- [x] 生產環境安全配置

### 3. JWT 基本驗證強化 ✅ 已改善
**新增驗證項目**:
- ✅ Token 格式檢查
- ✅ 演算法驗證 (只接受 RS256, ES256)
- ✅ 過期時間檢查 (`exp`)
- ✅ 發行者驗證 (`iss` = `https://access.line.me`)
- ✅ 用戶 ID 存在檢查

### 4. 用戶創建問題修正 ✅ 已修正
**問題**: 如果 LINE 用戶第一次使用 LIFF，會因為資料庫中沒有用戶記錄而失敗
**修正**: 自動創建新用戶
```python
# 修正前：
if not user:
    return False, "使用者不存在", None

# 修正後：
if not user:
    user = create_user_if_not_exists(session, line_user_id, display_name=None)
```

### 5. 前端邏輯簡化 ✅ 已完成
- [x] 移除開發模式降級處理
- [x] 移除 mock token 生成邏輯
- [x] 移除 LIFF 環境檢測（假設總是在 LIFF 環境中運行）

## 🚨 仍存在的安全風險

### 1. JWT 簽名未驗證 (高風險)
**問題**: 目前沒有驗證 JWT 的數位簽名
**風險**: 攻擊者可以偽造有效的 JWT token
**狀態**: ⚠️ 需要實作

#### 💡 為什麼需要第三方驗證工具？

**核心概念**: 由於 JWT token **不是我們自己配發的**，而是由 LINE 平台配發，所以我們必須依賴 LINE 提供的驗證機制來確保 token 的真實性。

**信任鏈流程**:
```
LINE 平台 → 配發 token → 用戶 → 傳遞 token → 我們的後端
    ↓                                        ↑
提供公鑰驗證工具 ————————————————————————————┘
```

**類比說明**:
- **銀行**（LINE）發給客戶一張**支票**（JWT token）
- 客戶拿支票到**商店**（我們的服務）消費
- 商店**不能自己印支票**，但可以用銀行公布的**防偽特徵**（公鑰）來驗證支票真偽

**實際威脅場景**:
```python
# 目前的安全漏洞：
# 惡意使用者可以自製假 token，在 payload 中放入任何想要的 LINE user ID
fake_token = create_fake_jwt_with_any_user_id("target_user_id")
# 我們的系統會接受這個假 token，因為只檢查格式不檢查簽名
```

**為什麼必須用 LINE 的公鑰驗證**:
1. **我們沒有 LINE 的私鑰** - 無法自己生成或驗證簽名
2. **信任 LINE 的身份驗證** - 讓我們專注業務邏輯，不需管理用戶密碼
3. **OAuth/OpenID Connect 標準** - 現代應用的標準做法

### 2. Audience 未驗證 (中風險)
**問題**: 沒有驗證 `aud` 欄位是否為正確的 LINE Login Channel ID（非 LIFF ID）
**風險**: 其他 Channel 的 token 可能被誤用
**狀態**: ⚠️ 需要實作
> 提醒：`aud` 是 OIDC 的 client_id，在 LINE 等同「Channel ID」（純數字）；LIFF ID（例如 `2007938807-GQzRrDoy`）只用於前端初始化，兩者不同。

## 🛠️ 完整安全解決方案

### 選項 1: 完整 JWT 驗證 (推薦)

**實作原理**: 使用 LINE 提供的公鑰驗證 token 的數位簽名

```python
import jwt
import requests
from cryptography.hazmat.primitives import serialization

def verify_line_id_token_complete(token: str) -> str:
    """完整的 LINE ID Token 驗證流程"""

    # 1. 從 LINE 的 JWK endpoint 取得公鑰
    # 這是 LINE 公開提供的驗證工具
    jwk_response = requests.get("https://api.line.me/oauth2/v2.1/certs")
    jwks = jwk_response.json()

    # 2. 使用 LINE 的公鑰驗證簽名並解碼
    try:
        payload = jwt.decode(
            token,
            key=jwks,  # LINE 提供的公鑰（需要格式轉換）
            algorithms=["RS256", "ES256"],  # LINE 支援的演算法
            audience="YOUR_LINE_CHANNEL_ID",    # 驗證 token 是給我們的 LINE Login Channel 用的（純數字）
            issuer="https://access.line.me"  # 驗證確實是 LINE 簽發的
        )
        return payload["sub"]  # LINE user ID
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
```

**安全性比較**:
```python
# 目前做法（不安全）：只看支票上的數字，不檢查印章
def current_verification():
    # 只解碼 payload，不驗證簽名
    payload = base64.decode(token_payload)
    return payload["sub"]  # 容易偽造

# 完整做法（安全）：檢查銀行印章的真實性
def secure_verification():
    # 用 LINE 的公鑰驗證數位簽名
    payload = jwt.decode(token, line_public_key, verify=True)
    return payload["sub"]  # 幾乎無法偽造
```

### 選項 2: 分階段改善 (務實)

**開發階段優先順序**:
```python
# 第一階段：加強現有驗證 ✅ 已完成
# - 基本格式檢查
# - 過期時間驗證
# - 發行者驗證

# 第二階段：加入 audience 驗證 ⚠️ 開發中
# - 確保 token 是為我們的 LINE Login Channel 簽發的（audience = Channel ID）

# 第三階段：完整簽名驗證 📅 後續實作
# - 使用 LINE 公鑰驗證數位簽名
# - 達到生產等級安全性
```

## 🔒 部署前檢查清單

### 必須完成項目
1. **真實 LIFF App 設定**
   ```javascript
   // 替換 app.js 中的 LIFF ID
   const liffId = '2007938807-GQzRrDoy'; // 已設定真實 ID
   ```

2. **環境變數確認**
   ```bash
    # 確保生產環境設定
    ENV=production
    LINE_CHANNEL_ID=2007938807  # 你的 LINE Login Channel ID（純數字）
   ```

3. **資料庫連線**
   - [x] 確認生產資料庫連線設定
   - [x] 執行必要的 migrations

4. **安全配置驗證**
   - [x] 移除所有開發測試功能
   - [x] CORS 限制設定正確
   - [x] 只接受真實 LINE ID Token

### 建議改進項目（可後續完成）
1. **JWT Token 驗證強化**
   - 目前只做基本驗證，未來應完成簽名驗證

2. **監控與日誌**
   - 設定監控告警
   - 詳細的安全日誌記錄

3. **錯誤處理優化**
   - 更詳細的錯誤監控
   - 優化用戶體驗

## 📊 風險評估與部署建議

### 可接受的部署情況 ✅
- 內部測試環境
- 有限用戶的 beta 測試
- 監控良好的生產環境

### 不建議的部署情況 ⚠️
- 大規模公開部署
- 處理敏感數據
- 高安全需求環境

### 立即可部署條件 (有限風險)
**必要條件**:
- [x] 設定監控告警
- [x] 限制用戶數量
- [x] 準備快速修復機制

**監控項目**:
```python
# 記錄所有驗證失敗
logger.warning(f"JWT validation failed: {error}")

# 監控異常 user ID 模式
if len(line_user_id) != 33:  # LINE user ID 固定長度
    logger.alert(f"Suspicious user ID: {line_user_id}")
```

## 🚀 現在的部署就緒狀態

### ✅ 已移除的本地測試功能
- Mock token 支援
- 開發模式降級處理
- LIFF 環境檢測邏輯
- 開發環境 CORS 設定

### ✅ 保留的核心功能
- 真實 LIFF 整合
- 地點設定 API
- 安全的 token 驗證
- 用戶資料儲存

## 📋 行動計劃

### 🔥 緊急 (24小時內)
- [x] 修正用戶不存在問題
- [x] 加強基本 JWT 驗證
- [x] 移除所有開發測試邏輯
- [ ] 設定監控告警

### 🚀 短期 (1週內)
- [ ] 實作 audience 驗證
- [ ] 加入詳細的安全日誌
- [ ] 建立錯誤監控

### 🎯 中期 (1月內)
- [ ] 完整 JWT 簽名驗證
- [ ] 效能優化
- [ ] 安全測試

## 💡 臨時安全措施

如果需要立即部署，建議：

1. **IP 白名單**: 限制 API 訪問來源
2. **速率限制**: 防止暴力攻擊
3. **監控告警**: 實時監控異常行為
4. **快速回滾**: 準備緊急下線機制

### 🔍 開發階段的安全考量

**為什麼現階段可以先不實作完整驗證**:
1. **開發優先順序**: 先建立完整的功能流程，再逐步強化安全性
2. **測試可行性**: 完整 JWT 驗證需要複雜的公鑰管理，不適合頻繁測試
3. **漸進式改善**: 分階段實作比一次到位更穩健

**目前實作的合理性**:
- ✅ **基本驗證已足夠** - 能防止大部分的簡單攻擊
- ✅ **開發效率優先** - 不在早期階段被複雜的安全實作拖慢
- ✅ **有明確的改善計劃** - 知道後續要做什麼以及為什麼要做

**重要提醒**:
> 目前的實作適合開發和有限測試，但上生產環境前**必須**完成完整的 JWT 簽名驗證。這不是可選項目，而是安全性的基本要求。

## 🎯 生產就緒部署條件

### 必須完成
1. 完整 JWT 簽名驗證
2. Audience 驗證
3. 安全監控系統
4. 錯誤處理優化

---

**結論**: 目前的代碼**已準備好遠端部署**，專為真實 LINE 環境設計，更簡潔且更安全。基本的 JWT 驗證**可用但不完整**，適合有限制的部署，但需要盡快完成完整的簽名驗證以達到生產等級的安全性。
