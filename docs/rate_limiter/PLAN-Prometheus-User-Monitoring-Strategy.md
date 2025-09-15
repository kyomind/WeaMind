# PLAN - 基於 Prometheus 的用戶行為監控策略

## 📝 文件說明

> **⚠️ 注意**：這是一份**規劃文件**，記錄基於 Prometheus 的用戶監控防護方案設計
>
> **🎯 目的**：為未來可能的實作需求提供完整的技術方案和實作指引
>
> **📅 預計時程**：配合 WeaMind V2.0 Prometheus 監控架構（2025-10-15）
>
> **🔗 前置依賴**：需要完成 V2.0 的 Prometheus + Grafana + AlertManager 基礎建設

---

## 💡 核心設計理念

### 問題背景
在討論是否為「地圖查詢」和「其它選單」功能實作 Redis 鎖機制時，發現了更優雅的解決方案：

**與其針對個別功能實作防護機制，不如建立全域的用戶行為監控系統**

### 設計哲學
- **避免重複造輪子**：利用 V2.0 既定的 Prometheus 監控基礎設施
- **最小程式碼變更**：只需幾行 metrics 埋點，不需要新系統
- **零額外資源消耗**：完全依托現有監控架構
- **更全面的防護**：覆蓋所有用戶行為，而非單點功能

---

## 🏗️ 技術架構設計

### 整體防護層次

```
┌─────────────────────────────────────────────────────────────┐
│                    LINE PostBack Event                     │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│               1. Prometheus Metrics 埋點                   │
│              記錄用戶行為到 metrics 系統                    │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│             2. AlertManager 即時監控                       │
│           基於 PromQL 規則檢測異常行為模式                 │
└─────────────────────┬───────────────────────────────────────┘
                      │ (異常觸發)
┌─────────────────────▼───────────────────────────────────────┐
│             3. Webhook 自動化防護                          │
│              自動將異常用戶加入 Redis 黑名單               │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│             4. 既有 Redis 鎖機制                           │
│              保護核心 DB + API 查詢功能                    │
└─────────────────────────────────────────────────────────────┘
```

### 與現有系統整合

**優勢**：
- ✅ **黑名單機制**：全域防護，覆蓋所有功能
- ✅ **Redis 鎖機制**：深度防護，保護重要資源
- ✅ **互補協作**：黑名單過濾惡意用戶，Redis 鎖處理正常頻率控制

---

## 🔧 實作技術細節

### 1. Prometheus Metrics 設計

```python
from prometheus_client import Counter, Histogram, Gauge

# 用戶操作計數器（按類型分組）
user_action_counter = Counter(
    'weamind_user_actions_total',
    'Total user actions by type',
    ['user_id', 'action_type', 'source']
)

# 用戶操作頻率直方圖
user_action_rate = Histogram(
    'weamind_user_action_rate_per_minute',
    'User action rate per minute',
    ['user_id'],
    buckets=[1, 5, 10, 30, 60, 120, float('inf')]
)

# 當前被封鎖用戶數
banned_users_gauge = Gauge(
    'weamind_banned_users_current',
    'Current number of banned users',
    ['ban_type']  # temporary, extended, permanent
)
```

### 2. 程式碼整合點

**在現有 PostBack 處理中埋點**：
```python
@webhook_handler.add(PostbackEvent)
def handle_postback_event(event: PostbackEvent) -> None:
    # === 現有邏輯 ===
    if not event.reply_token or not user_id:
        return

    postback_data = parse_postback_data(event.postback.data)

    # === 新增：Prometheus Metrics 埋點 ===
    user_action_counter.labels(
        user_id=user_id,
        action_type=postback_data.get('action', 'unknown'),
        source='rich_menu'
    ).inc()

    # === 新增：黑名單檢查 ===
    if redis_client.exists(f"banned:{user_id}"):
        ban_info = redis_client.hgetall(f"banned:{user_id}")
        send_ban_notification(event.reply_token, ban_info)
        return

    # === 現有的 Redis 鎖機制和業務邏輯 ===
    needs_lock = should_use_processing_lock(postback_data)
    # ... 既有邏輯保持不變 ...
```

### 3. AlertManager 告警規則

```yaml
# /etc/prometheus/alerts/user_behavior.yml
groups:
- name: user_behavior_monitoring
  rules:
  # 臨時警告：1分鐘內操作過頻
  - alert: UserHighFrequencyActivity
    expr: rate(weamind_user_actions_total[1m]) > 0.5  # 每分鐘 > 30次
    for: 30s
    labels:
      severity: warning
      ban_type: temporary
    annotations:
      summary: "User {{ $labels.user_id }} high frequency activity"
      description: "User performing {{ $value }} actions per second"

  # 嚴重警告：1分鐘內操作異常頻繁
  - alert: UserMaliciousActivity
    expr: rate(weamind_user_actions_total[1m]) > 1.0   # 每分鐘 > 60次
    for: 10s
    labels:
      severity: critical
      ban_type: extended
    annotations:
      summary: "User {{ $labels.user_id }} malicious activity detected"
      description: "Suspected bot behavior: {{ $value }} actions per second"

  # 長期監控：1小時內總操作量異常
  - alert: UserExcessiveDailyUsage
    expr: increase(weamind_user_actions_total[1h]) > 300
    for: 5m
    labels:
      severity: warning
      ban_type: review_required
    annotations:
      summary: "User {{ $labels.user_id }} excessive daily usage"
      description: "{{ $value }} actions in the last hour"
```

### 4. AlertManager Webhook 整合

```python
from pydantic import BaseModel
from typing import List, Dict, Any

class PrometheusAlert(BaseModel):
    status: str
    labels: Dict[str, str]
    annotations: Dict[str, str]
    startsAt: str
    endsAt: str = None

class AlertManagerWebhook(BaseModel):
    receiver: str
    status: str
    alerts: List[PrometheusAlert]
    groupLabels: Dict[str, str]
    commonLabels: Dict[str, str]
    commonAnnotations: Dict[str, str]

@app.post("/webhooks/alertmanager/user-behavior")
async def handle_user_behavior_alert(
    webhook_data: AlertManagerWebhook,
    redis_client: Redis = Depends(get_redis_client)
) -> Dict[str, str]:
    """
    處理來自 AlertManager 的用戶行為告警

    自動將異常用戶加入黑名單，實現防護自動化
    """
    for alert in webhook_data.alerts:
        if alert.status != "firing":
            continue

        user_id = alert.labels.get('user_id')
        ban_type = alert.labels.get('ban_type', 'temporary')
        severity = alert.labels.get('severity')

        if not user_id:
            logger.warning("Alert without user_id", extra={"alert": alert.dict()})
            continue

        # 根據告警嚴重程度設置不同的封鎖時間
        ban_duration = {
            'temporary': 300,      # 5分鐘
            'extended': 3600,      # 1小時
            'review_required': 86400  # 24小時，需人工審查
        }.get(ban_type, 300)

        # 記錄封鎖信息到 Redis
        ban_info = {
            "banned_until": (datetime.utcnow() + timedelta(seconds=ban_duration)).isoformat(),
            "ban_reason": alert.annotations.get('summary', 'excessive_activity'),
            "ban_type": ban_type,
            "alert_severity": severity,
            "banned_at": datetime.utcnow().isoformat()
        }

        # 設置黑名單記錄
        redis_client.hset(f"banned:{user_id}", mapping=ban_info)
        redis_client.expire(f"banned:{user_id}", ban_duration)

        # 更新 Prometheus 指標
        banned_users_gauge.labels(ban_type=ban_type).inc()

        logger.warning(
            f"User {user_id} banned for {ban_duration}s due to {ban_type}",
            extra={"ban_info": ban_info}
        )

    return {"status": "processed", "alerts_count": len(webhook_data.alerts)}

def send_ban_notification(reply_token: str, ban_info: Dict[str, str]) -> None:
    """發送人性化的限制通知"""
    ban_type = ban_info.get('ban_type', 'temporary')

    messages = {
        'temporary': "⏳ 您的操作過於頻繁，請稍作休息再試",
        'extended': "🛑 檢測到異常使用模式，暫時限制使用功能",
        'review_required': "🚫 使用行為需要審查，如有疑問請聯絡客服"
    }

    message = messages.get(ban_type, "操作受到限制，請稍後再試")
    send_text_response(reply_token, message)
```

---

## 📊 監控可視化設計

### Grafana Dashboard 面板

```json
{
  "dashboard": {
    "title": "WeaMind 用戶行為監控",
    "panels": [
      {
        "title": "用戶操作頻率分布",
        "type": "histogram",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(weamind_user_action_rate_per_minute_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "高頻用戶排行榜",
        "type": "table",
        "targets": [
          {
            "expr": "topk(10, rate(weamind_user_actions_total[1h]))",
            "legendFormat": "{{ user_id }}"
          }
        ]
      },
      {
        "title": "被封鎖用戶統計",
        "type": "stat",
        "targets": [
          {
            "expr": "weamind_banned_users_current",
            "legendFormat": "{{ ban_type }}"
          }
        ]
      },
      {
        "title": "告警觸發次數",
        "type": "graph",
        "targets": [
          {
            "expr": "increase(prometheus_notifications_total{instance=\"alertmanager\"}[1h])",
            "legendFormat": "Alerts sent"
          }
        ]
      }
    ]
  }
}
```

---

## ⚙️ 配置參數調優

### 閾值設計建議

| 監控維度      | 警告閾值   | 嚴重閾值   | 封鎖時間     | 說明         |
| ------------- | ---------- | ---------- | ------------ | ------------ |
| **1分鐘頻率** | 30次/分鐘  | 60次/分鐘  | 5分鐘/1小時  | 即時防護     |
| **1小時總量** | 300次/小時 | 600次/小時 | 1小時/24小時 | 持續監控     |
| **功能分布**  | 單功能>50% | 單功能>80% | 動態調整     | 行為模式分析 |
| **錯誤回應**  | >10次/分鐘 | >20次/分鐘 | 30分鐘       | 故障保護     |

### 動態調整策略

```python
# 基於系統負載動態調整閾值
class DynamicThresholdManager:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.base_thresholds = {
            'warning_per_minute': 30,
            'critical_per_minute': 60,
            'warning_per_hour': 300
        }

    def get_current_threshold(self, metric_name: str) -> float:
        """根據當前系統負載調整閾值"""
        # 獲取系統指標
        current_load = self._get_system_load()
        user_count = self._get_active_user_count()

        # 負載高時降低閾值，負載低時提高閾值
        base_threshold = self.base_thresholds[metric_name]

        if current_load > 0.8:  # 高負載
            return base_threshold * 0.7
        elif current_load < 0.3:  # 低負載
            return base_threshold * 1.3
        else:
            return base_threshold
```

---

## 🔄 實作階段規劃

### Phase 1: 基礎 Metrics 埋點（V2.0 配合實作）
**時程**：與 V2.0 Prometheus 架構同步（2025-10-15）
- ✅ 在 PostBack 處理中加入基本 metrics
- ✅ 設定 Prometheus 收集配置
- ✅ 建立基礎 Grafana Dashboard

### Phase 2: 告警規則設定（V2.0 後續優化）
**時程**：V2.0 基礎架構穩定後（2025-10-30）
- ✅ 配置 AlertManager 告警規則
- ✅ 設定 Webhook 接收端點
- ✅ 實作基礎黑名單機制

### Phase 3: 進階監控分析（視需求啟動）
**時程**：根據實際使用情況決定
- ✅ 動態閾值調整機制
- ✅ 行為模式深度分析
- ✅ 自動化運維響應

---

## 💡 決策依據與價值分析

### 為什麼選擇這個方案？

1. **技術債務最小化**
   - 利用既有 V2.0 監控基礎設施
   - 避免重複建設專用監控系統
   - 代碼變更量極小（< 50 行）

2. **資源效率最大化**
   - 零額外計算資源消耗
   - 零額外存儲系統需求
   - 維護成本接近於零

3. **防護效果最優化**
   - 全域用戶行為監控
   - 實時告警和自動化響應
   - 分級防護策略

4. **架構一致性**
   - 符合現代可觀測性最佳實踐
   - 與 WeaMind 演進式架構理念一致
   - 為後續 K8s 階段提供監控基礎

### 與專用監控系統對比

| 評估維度   | 專用監控系統 | Prometheus 整合方案       |
| ---------- | ------------ | ------------------------- |
| 開發工作量 | 大量新代碼   | **幾行埋點代碼**          |
| 系統複雜度 | 高（新系統） | **低（擴展現有）**        |
| 資源消耗   | 額外資源     | **零額外消耗**            |
| 維護成本   | 高           | **極低**                  |
| 查詢分析   | 自建界面     | **Grafana 原生支持**      |
| 告警機制   | 自建邏輯     | **AlertManager 成熟方案** |
| 擴展性     | 有限         | **Prometheus 生態**       |

---

## 🚨 注意事項與風險評估

### 實作風險

1. **數據隱私考量**
   - Metrics 中包含 user_id 標籤
   - 需要考慮 GDPR 和隱私法規
   - 建議：使用 hash 後的 user_id 或脫敏處理

2. **Prometheus 存儲壓力**
   - 高頻用戶可能產生大量時序數據
   - 需要設定合理的數據保留策略
   - 建議：7天詳細數據 + 30天聚合數據

3. **告警風暴風險**
   - 大量用戶同時觸發告警
   - AlertManager 需要設定合理的抑制規則
   - 建議：設定告警頻率限制和分組策略

### 緩解策略

```yaml
# AlertManager 配置示例
route:
  group_by: ['alertname', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 1h

inhibit_rules:
- source_match:
    severity: 'critical'
  target_match:
    severity: 'warning'
  equal: ['user_id']
```

---

## 📚 相關文件與參考

### WeaMind 專案文件
- `WeaMind 架構與 Roadmap.md` - V2.0 監控架構規劃
- `AGENT-Redis-Lock-1sec-Timeout-Optimization.md` - 現有 Redis 鎖機制
- `docs/rate_limiter/` - 頻率限制相關文件

### 技術參考
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [AlertManager Configuration](https://prometheus.io/docs/alerting/latest/configuration/)
- [Grafana Dashboard Design](https://grafana.com/docs/grafana/latest/dashboards/)

---

## 📋 實作檢查清單

### V2.0 階段（基礎埋點）
- [ ] 在 `app/line/service.py` 中加入 Prometheus metrics 導入
- [ ] 在 PostBack 處理函數中埋點計數器
- [ ] 配置 Prometheus 收集 WeaMind metrics
- [ ] 建立基礎 Grafana Dashboard 面板

### 後續階段（完整防護）
- [ ] 設計 AlertManager 告警規則檔案
- [ ] 實作 `/webhooks/alertmanager/user-behavior` 端點
- [ ] 實作黑名單檢查和通知邏輯
- [ ] 設定動態閾值調整機制
- [ ] 建立運維監控和故障處理流程

---

*這份文件記錄了基於 Prometheus 的用戶行為監控策略完整設計，為未來可能的實作需求提供詳細的技術方案和實作指引。*
