# AGENT - Redis 鎖機制優化：固定1秒超時實作

## 📝 Memory Hooks (關鍵記憶點)

> **🎯 核心目標**：將動態解鎖改為固定1秒TTL，簡化實作並增強防護效果
>
> **⚡ 關鍵洞察**：0.3-0.5秒的查詢時間讓動態解鎖失去防護意義，1秒內仍可發送2-3次請求
>
> **🔧 核心變更**：移除 `release_lock()` 方法和所有手動釋放邏輯，完全依賴Redis TTL
>
> **💡 技術重點**：`SET key "1" EX 1 NX` - 固定1秒，無需參數化timeout

---

## WHY - 問題背景與動機

### 現有問題分析
目前的動態鎖機制存在防護漏洞：
- **處理時間過短**：DB查詢僅需0.3-0.5秒
- **防護效果有限**：1秒內惡意用戶仍可發送2-3次請求
- **程式碼複雜**：需要 try-finally 確保鎖釋放
- **故障風險**：手動釋放失敗可能導致死鎖

### 業務需求重新評估
WeaMind 作為天氣查詢服務的特性：
- 天氣查詢本質上不是高頻操作需求
- 正常用戶很少需要1秒內多次查詢
- **防範惡意使用** > **毫秒級響應優化**
- 系統穩定性優於極致性能

## WHAT - 功能需求規格

### 核心功能目標
1. **絕對頻率控制**：每用戶每秒最多1次請求
2. **程式碼簡化**：移除手動鎖管理複雜性
3. **系統穩定性**：更好保護downstream服務
4. **故障恢復**：完全依賴Redis TTL機制

### 具體變更範圍
- **修改檔案**：`app/core/processing_lock.py`
- **影響範圍**：`app/line/service.py` 中的鎖使用邏輯
- **移除內容**：`release_lock()` 方法和所有手動釋放邏輯
- **簡化參數**：`try_acquire_lock()` 不再需要timeout參數

## HOW - 技術實作方案

### Redis 鎖機制核心變更

**之前（動態解鎖）：**
```python
# 複雜的雙方法設計
try_acquire_lock(key, timeout_seconds)  # 動態timeout
release_lock(key)                       # 手動釋放

# 使用模式需要 try-finally
if try_acquire_lock(key, 5):
    try:
        process()
    finally:
        release_lock(key)
```

**現在（固定1秒TTL）：**
```python
# 簡化的單一方法
try_acquire_lock(key)  # 固定1秒TTL，無需手動釋放

# 使用模式大幅簡化
if try_acquire_lock(key):
    process()  # 無需 try-finally
```

### 核心實作要點

1. **Redis操作簡化**：
   ```python
   # 固定使用：SET key "1" EX 1 NX
   result = self.redis_client.set(key, "1", ex=1, nx=True)
   ```

2. **方法簽名變更**：
   ```python
   # 之前：def try_acquire_lock(self, key: str, timeout_seconds: int) -> bool
   # 現在：def try_acquire_lock(self, key: str) -> bool
   ```

3. **完全移除**：
   - `release_lock()` 方法
   - 所有 `try-finally` 區塊
   - timeout參數傳遞邏輯

### 使用端變更模式

**在 `app/line/service.py` 中：**
```python
# 移除複雜的 try-finally 包裝
# 改為簡潔的單一判斷流程

if needs_lock and PROCESSING_LOCK_ENABLED:
    if not processing_lock_service.try_acquire_lock(lock_key):
        reply("⏳ 正在為您查詢天氣，請稍候...")
        return

# 直接處理業務邏輯，無需擔心鎖釋放
_dispatch_postback(event, user_id, postback_data)
```

## 技術限制與考量因素

### 設計權衡
- **犧牲**：極致的響應速度（處理完成後仍需等待至1秒）
- **獲得**：更強的防護效果、更簡潔的程式碼、更好的系統穩定性

### 技術約束
- **Redis依賴**：完全依賴Redis TTL機制，無手動釋放backup
- **固定時間**：1秒是硬編碼，未來如需調整需修改程式碼
- **容錯策略**：維持既有的 fail-open 設計

### 相容性考量
- **向下相容**：不影響現有的鎖判斷邏輯（`should_use_processing_lock`）
- **測試影響**：簡化測試，只需驗證鎖取得，無需測試釋放邏輯
- **監控影響**：Redis操作量減半（只有SET，沒有DELETE）

## 重要共識與決策記錄

### 核心決策
1. **防護優先於性能**：選擇固定1秒鎖，即使犧牲部分響應速度
2. **簡化優於功能**：移除手動釋放，完全依賴TTL自動釋放
3. **穩定優於靈活**：硬編碼1秒超時，避免參數複雜性

### 技術共識
- **單一責任**：鎖服務只負責取得鎖，釋放交給Redis TTL
- **原子操作**：繼續使用 `SET NX EX` 確保競爭條件安全
- **故障策略**：維持fail-open，Redis故障時不影響主功能

### 業務共識
- **用戶體驗**：1秒等待對天氣查詢服務是可接受的
- **防護目標**：重點防範惡意高頻使用，而非優化正常使用體驗
- **系統定位**：WeaMind是穩定的天氣服務，不是即時互動應用

---

## 📋 實作檢查清單

- [ ] 修改 `ProcessingLockService.try_acquire_lock()` 移除timeout參數
- [ ] 移除 `ProcessingLockService.release_lock()` 方法
- [ ] 更新 `app/line/service.py` 中的鎖使用邏輯
- [ ] 移除所有 try-finally 區塊
- [ ] 更新相關測試案例
- [ ] 驗證鎖機制在實際環境的防護效果

---

*這份文件記錄了從動態鎖到固定1秒TTL鎖的關鍵設計決策，為未來的AI agent提供完整的實作脈絡和技術記憶。*
