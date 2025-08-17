## 🐛 LIFF Token 過期問題調試指南

### 📋 問題現象
用戶立刻登入後再次提交表單，仍然出現 "Token expired" 錯誤，並跳回登入頁面。

### 🔧 已加入的調試功能

#### 後端調試
1. **放寬時間容忍度**: 加入 5 分鐘緩衝時間處理時鐘偏差
2. **詳細日誌**: 記錄 Token 過期的具體時間差
3. **成功驗證日誌**: 記錄成功驗證的用戶 ID

#### 前端調試
1. **Token 資訊記錄**: 顯示 Token 的過期時間和剩餘時間
2. **API 錯誤詳情**: 記錄完整的 API 回應錯誤
3. **Token 解碼檢查**: 在提交前檢查 Token 是否即將過期

### 📊 調試步驟

1. **重新部署** 包含調試資訊的版本
2. **開啟瀏覽器開發者工具**
3. **嘗試提交表單** 並查看 Console 輸出
4. **檢查後端日誌** 查看 Token 驗證的詳細資訊

### 🔍 預期的調試輸出

#### 前端 Console
```javascript
ID Token obtained: eyJhbGciOiJSUzI1Ni...
Token info: {
  currentTime: 1692259200,
  exp: 1692262800,
  timeToExpiry: 3600,
  sub: "U1234567890abcdef"
}
```

#### 後端日誌
```
INFO: Token verified successfully for user: U1234567890abcdef
或
WARNING: Token expired: current_time=1692259200, exp=1692258000, diff=1200
```

### 🚨 可能的原因

1. **時鐘同步問題**: 伺服器和 LINE 服務器時間不同步
2. **Token 生命週期**: LIFF Token 的實際有效期比預期短
3. **重新登入邏輯**: 重新登入後沒有正確獲取新的 Token
4. **LIFF App 設定**: Scope 或其他設定可能影響 Token 有效性

### 🔧 臨時解決方案

如果調試後發現是時間同步問題，可以暫時移除過期檢查：

```python
# 在 app/core/auth.py 中暫時註解掉過期檢查
# if current_time > (exp + time_buffer):
#     logger.warning(...)
#     raise ValueError("Token expired")
```

### ⚡ 快速測試

1. 部署調試版本
2. 測試並查看 Console 和日誌
3. 回報具體的時間差數據
4. 根據數據調整解決方案
