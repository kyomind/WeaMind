# AGENT - 目前位置天氣查詢功能設計文件

## 文件概述
本文件提供給 AI Agent（如 Claude Code）作為實作「目前位置」天氣查詢功能的技術指南。

## 1. 問題背景 (Why)

### 核心問題
WeaMind LINE Bot 的 Rich Menu 中「目前位置」按鈕目前是佔位功能，用戶點擊後只會收到「功能即將推出」的訊息。這個功能是用戶日常使用頻率很高的需求，需要優先實作。

### 用戶需求
- 快速查詢當前所在位置的天氣資訊。
- 不需要記憶或輸入地名，直接使用 GPS 位置。
- 體驗直觀且快速。

### 技術現狀
- ✅ `Location` table 已有全台所有行政區的經緯度資料。
- ✅ LINE SDK v3 支援 `LocationMessageContent` 處理。
- ✅ Rich Menu `PostBack` 事件處理系統已完整。
- ✅ 天氣查詢與回應系統已完善。

## 2. 功能範圍 (What)

### 核心功能
1. **觸發機制**：用戶點擊 Rich Menu「目前位置」按鈕。
2. **位置請求**：Bot 引導用戶分享當前位置。
3. **距離計算**：計算用戶位置與各行政區的距離。
4. **最近匹配**：找出最近的行政區。
5. **天氣查詢**：查詢該行政區的天氣資訊。
6. **結果回應**：回傳天氣資訊給用戶。

### 技術邊界
- **範圍限制**：僅支援台灣地區（基於現有 `location` table）。
- **精確度**：以行政區為單位，不支援更細緻的地理位置。
- **權限要求**：需要用戶主動分享位置，無法自動取得。

## 3. 技術方案 (How)

### 3.1 架構設計

#### 用戶體驗流程
```
用戶點擊「目前位置」→ Bot 請求分享位置 → 用戶分享 GPS 座標 →
Bot 計算最近行政區 → 查詢天氣 → 回傳結果
```

#### 事件處理流程
```python
# 流程概述
PostbackEvent(action="weather", type="current")
→ handle_current_location_weather()
→ 發送「請分享位置」訊息

LocationMessageContent Event
→ handle_location_message()
→ 計算距離 → 找最近行政區 → 查詢天氣 → 回應
```

### 3.2 核心演算法

#### Haversine 距離計算
使用 Haversine 公式計算地球表面兩點間的距離（單位：公里）。
```python
def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """計算兩個經緯度座標間的距離（公里）"""
    # 地球半徑：6371 公里
    # 轉換為弧度 → 計算差值 → 應用 Haversine 公式
```

#### 最近行政區查找
**做法**：遍歷所有行政區（約 370 筆），在記憶體中計算與用戶位置的 Haversine 距離，找出距離最小者。

**台灣地理範圍驗證**：
為避免海外用戶（如日本、菲律賓）觸發無意義的結果，實作兩層地理驗證機制：

1. **第一層：邊界矩形檢查**
   - 快速排除明顯不在台灣經緯度範圍內的座標
   - 台灣大致範圍：北緯 21.9° - 25.3°，東經 119.3° - 122.0°

2. **第二層：距離閾值檢查**
   - 計算用戶與最近行政區的實際距離
   - 若距離超過 50 公里，視為不在台灣服務範圍內
   - 此設計可支援離島（綠島約 30-40km）但排除海外地區（日本 600km+）

**錯誤處理**：當檢測到用戶不在台灣時，回傳友善訊息，如「抱歉，目前僅支援台灣地區的天氣查詢 🌏」

**效能考量**：
- **遍歷計算 vs. 空間索引**：對於僅有 300-400 筆的固定資料集，直接遍歷計算的總延遲（資料庫讀取 + 記憶體計算）遠低於 15 毫秒，效能極佳，且實作簡單。引入 PostGIS 等空間索引技術屬於過早優化，反而會增加系統複雜度。
- **結論**：選擇「遍歷計算 + 雙層驗證」方案，是在當前需求下最務實且高效的選擇。

### 3.3 實作要點

#### 事件處理器擴展
- 修改 `line/service.py` 中的 `handle_current_location_weather()`，從佔位功能變為發送「請分享位置」的請求。
- 在 `line/router.py` 中新增 `LocationMessageContent` 事件的處理器，並將其導向 `line/service.py` 中新的處理函式。

#### WeatherService 重構與共用邏輯
為了同時支援「文字輸入」和「GPS座標」兩種來源，需重構 `app/weather/service.py`，將「尋找地點」與「查詢天氣並回應」的邏輯分離，提高程式碼重用性。

**建議結構**(僅供參考，ai可自行決定最佳做法)
```python
# 位於 app/weather/service.py
class WeatherService:
    # 1. 核心共用邏輯 (private)
    def _get_weather_and_create_reply(self, location: Location) -> BaseMessage:
        """給定 Location 物件，查詢天氣並產生回應。"""
        # ...

    # 2. 不同的地點查找方式 (public)
    def find_location_by_name(self, name: str) -> Location | None:
        """處理文字輸入，回傳 Location 物件。"""
        # ...

    def find_nearest_location(self, lat: float, lon: float) -> Location | None:
        """處理 GPS 座標，回傳 Location 物件。若不在台灣則回傳 None。"""
        # ...

    # 3. 供上層 (LineService) 呼叫的進入點
    def handle_text_weather_query(self, text_input: str) -> BaseMessage:
        location = self.find_location_by_name(text_input)
        # ... 處理找不到地點的情況 ...
        return self._get_weather_and_create_reply(location)

    def handle_location_weather_query(self, lat: float, lon: float) -> BaseMessage:
        location = self.find_nearest_location(lat, lon)
        # ... 處理找不到地點的情況（包含不在台灣的情況）...
        return self._get_weather_and_create_reply(location)
```

#### 訊息回應設計
- **初次點擊回應**：由 `handle_current_location_weather` 發送「請分享您的位置，我將為您查詢當地的天氣資訊 🌤️」訊息，並附上 Quick Reply 位置分享按鈕（標籤：`📍 分享我的位置`）。
- **天氣結果回應**：由 `handle_location_weather_query` 透過重構後的共用邏輯產生標準天氣 Flex Message。
- **錯誤處理**：處理使用者位置不在台灣、無法計算距離等情況，回傳友善提示。

#### 資料庫查詢
- `find_nearest_location` 會讀取所有地點，確保 `locations` 資料表能被資料庫高效快取。
- `find_location_by_name` 可考慮在 `name` 欄位上建立索引以加速文字查詢。

#### Quick Reply 位置請求實作範例(有討論過的具體方案)
```python
def create_location_request_message():
    """建立請求位置分享的訊息"""
    return {
        "type": "text",
        "text": "請分享您的位置，我將為您查詢當地的天氣資訊 🌤️",
        "quickReply": {
            "items": [
                {
                    "type": "action",
                    "action": {
                        "type": "location",
                        "label": "📍 分享我的位置"
                    }
                }
            ]
        }
    }
```

## 4. 技術限制與安全考量

### 已知限制
1. **地理範圍**：僅支援台灣地區。
2. **精確度**：以行政區為單位，可能不夠精細。
3. **使用者體驗**：需要兩次互動（點擊按鈕 + 分享位置）。
4. **位置權限**：依賴用戶主動分享，無法強制。

### 技術與安全考量
1. **隱私保護**：**不儲存**用戶分享的 GPS 座標。
2. **資料驗證**：驗證接收到的經緯度座標格式是否正確。
3. **地理範圍控制**：透過雙層驗證機制（邊界矩形 + 距離閾值）確保服務僅提供給台灣地區用戶，避免海外用戶觸發無意義的天氣查詢結果。
4. **錯誤處理**：當用戶位置在台灣以外，或發生其他計算錯誤時，應回傳友善的錯誤訊息，避免洩露系統內部資訊。
5. **資料一致性**：`location` table 的座標準確性是功能的基礎。
6. **並發處理**：目前的計算量極低，多用戶同時使用不會造成效能問題。

## 5. 重要共識與決策

1. **互動方案**：採用 `PostBack` 搭配 LINE 內建的「位置分享」功能。
   - **理由**：利用 LINE 原生功能，用戶體驗熟悉，開發成本較低。
   - **捨棄方案**：LIFF + HTML5 Geolocation，因其複雜度較高。
   - **Quick Reply 設計**：使用「📍 分享我的位置」作為按鈕標籤，直觀且親切。

2. **核心演算法**：距離計算使用 **Haversine 公式**，地點查找使用**記憶體內遍歷**。
   - **理由**：在當前資料規模下，此組合是效能與實作複雜度的最佳平衡。

3. **資料模型**：沿用現有的 `location` table。
   - **理由**：已有完整資料，滿足功能需求。

## 6. 預期效益

### 用戶體驗改善
- Rich Menu 功能完整度提升 (4/6 → 5/6)。
- 提供比手動輸入更直觀便利的天氣查詢方式。
- 減少因地名輸入錯誤導致的查詢失敗。

### 技術價值
- 建立可複用的地理位置服務基礎架構。
- 為未來開發 LBS (Location-Based Service) 相關功能奠定基礎。
- 提升 LINE Bot 的互動豐富度。

## 7. 未來擴展可能

1. **精確度提升**：引入更細緻的地理區劃或天氣觀測站資料。
2. **範圍擴展**：支援其他國家或地區。
3. **智慧推薦**：基於用戶歷史位置提供個人化天氣提醒。
4. **快取機制**：對於頻繁查詢的區域，快取天氣結果以加速回應。

---

**文件版本**：v1.1 (Refactored)
**更新日期**：2025-08-25
**目標實作時間**：45-75 分鐘
