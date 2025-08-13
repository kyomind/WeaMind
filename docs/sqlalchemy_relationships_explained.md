# SQLAlchemy 外鍵與關係 (Relationship) 指南

本文件旨在解說 SQLAlchemy ORM 中外鍵 (Foreign Key) 與關係 (Relationship) 的核心概念與寫法。我們將以 `app/weather/models.py` 中的 `Location` 與 `Weather` model 作為實際範例。

在 SQLAlchemy 中，建立兩個表格之間的關聯主要涉及三個部分：
1.  `ForeignKey()`: **資料庫層級**的「外鍵約束」。
2.  `relationship()`: **Python/ORM 層級**的「導覽屬性」，讓我們能方便地在物件之間移動。
3.  `back_populates`: **同步雙向關係**的「黏著劑」。

---

## 完整範例程式碼

為了方便參考，以下是 `Location` 與 `Weather` 兩個 Model 中與關係設定最相關的部分：

```python
# app/weather/models.py

from typing import List
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class Location(Base):
    __tablename__ = "location"

    id: Mapped[int] = mapped_column(primary_key=True)
    # ... 其他欄位 ...

    # 建立一個名為 'forecasts' 的屬性，它會是一個包含 Weather 物件的 List
    # back_populates 指向 Weather model 中對應的關係屬性 'location'
    forecasts: Mapped[List["Weather"]] = relationship(back_populates="location")


class Weather(Base):
    __tablename__ = "weather"

    id: Mapped[int] = mapped_column(primary_key=True)

    # 建立 location_id 欄位，並設定其為指向 location.id 的外鍵
    location_id: Mapped[int] = mapped_column(ForeignKey("location.id"))

    # ... 其他欄位 ...

    # 建立一個名為 'location' 的屬性，它會是一個 Location 物件
    # back_populates 指向 Location model 中對應的關係屬性 'forecasts'
    location: Mapped["Location"] = relationship(back_populates="forecasts")
```

---

## 1. `ForeignKey`：定義資料庫的連結

我們來看 `Weather` model 的這一行：

```python
# in class Weather:
location_id: Mapped[int] = mapped_column(
    ForeignKey("location.id"), nullable=False
)
```

- **作用**: 這行程式碼直接對應到資料庫的 `FOREIGN KEY` 約束。
- `location_id: Mapped[int]`: 這定義了一個名為 `location_id` 的欄位，它的型別是整數。在資料庫中，它就是 `weather` 表格裡的 `location_id` 欄位。
- `ForeignKey("location.id")`: 這是最關鍵的部分。它告訴 SQLAlchemy：
    - `"location"`: 這個欄位要參考的**表格名稱** (也就是 `Location` model 的 `__tablename__`)。
    - `".id"`: 參考該表格中的 `id` **欄位**。

簡單來說，**`ForeignKey` 是一個純粹的資料庫概念**。它確保了 `weather.location_id` 欄位中的每一個值，都必須是 `location` 表格中某個存在的 `id`。

---

## 2. `relationship`：建立 Python 物件的橋樑

光有資料庫約束還不夠，我們希望在程式碼中能很直觀地操作，例如：`某個天氣預報物件.地點` 或 `某個地點物件.所有天氣預報`。這就是 `relationship` 的功用。

#### a) 在 `Weather` Model 中 (多對一的「多」方)

```python
# in class Weather:
location: Mapped["Location"] = relationship(back_populates="forecasts")
```

- **作用**: 這行**不會在資料庫中建立任何欄位**。它是一個純粹由 SQLAlchemy ORM 管理的「魔法屬性」。
- `location: Mapped["Location"]`: 我們定義了一個名為 `location` 的屬性，它的型別會是一個 `Location` 物件。
- `relationship(...)`: 告訴 SQLAlchemy 這個屬性是一個「關係」。當你在 Python 中存取 `my_weather.location` 時，SQLAlchemy 會：
    1.  查看 `my_weather` 物件的 `location_id` 值。
    2.  自動去 `location` 表格中查詢對應的 `Location` 物件。
    3.  將查到的 `Location` 物件回傳給你。
- **回傳值**: 一個**單一的 `Location` 物件**。因為一筆天氣預報只會屬於一個地點，所以這個屬性回傳的是單一物件，而不是列表。

#### b) 在 `Location` Model 中 (多對一的「一」方)

```python
# in class Location:
forecasts: Mapped[List["Weather"]] = relationship(back_populates="location")
```

- **作用**: 這是反向的關係，同樣也是一個「魔法屬性」。
- `forecasts: Mapped[List["Weather"]]`: 我們定義了一個 `forecasts` 屬性，它的型別是**一個包含 `Weather` 物件的 List**。
- `relationship(...)`: 當你存取 `my_location.forecasts` 時，SQLAlchemy 會自動去 `weather` 表格中，查詢所有 `location_id` 等於 `my_location.id` 的天氣預報紀錄，並將它們作為一個 List 回傳。
- **回傳值**: 一個**包含 `Weather` 物件的 Python `List`**。因為一個地點可以擁有多筆天氣預報，所以回傳的是一個列表。如果該地點沒有任何預報，則回傳一個空列表 `[]`。

---

## 3. `back_populates`：讓關係保持同步

- `back_populates="forecasts"` (在 `Weather` model 中)
- `back_populates="location"` (在 `Location` model 中)

這兩行就像是「黏著劑」，它們告訴 SQLAlchemy：`Weather.location` 這個關係和 `Location.forecasts` 這個關係是**一對互相呼應的關係**。

它的好處是，當你操作其中一方時，另一方會自動更新。例如：

```python
# 假設 some_location 是一個 Location 物件
# 假設 new_weather 是一個新的 Weather 物件

# 你只需要做這一步
new_weather.location = some_location

# SQLAlchemy 會自動幫你完成下面這一步！
# some_location.forecasts 這個 list 中會自動加入 new_weather
print(new_weather in some_location.forecasts)  # --> True
```

---

## 4. 實際使用範例

讓我們看看在程式碼中如何使用這些屬性，以及它們的值是什麼。

```python
# 假設我們已經從資料庫查詢到一個地點和它的一筆天氣預報
# (此為示意程式碼，需在實際的 session 中運行)
yonghe_location: Location = db.query(Location).filter(Location.full_name == "新北市永和區").one()

# --- 從 Location 物件存取多筆 Weather ---

# 存取 .forecasts 屬性
all_forecasts = yonghe_location.forecasts

# all_forecasts 的「值」是什麼？
# 它是一個 Python List，裡面裝滿了 Weather 物件
print(type(all_forecasts)) # <class 'list'>

# 假設資料庫中有 9 筆永和區的預報
print(len(all_forecasts))  # --> 9

# List 中的每一個元素都是一個 Weather 物件
if all_forecasts:
    some_forecast = all_forecasts[0]
    print(type(some_forecast)) # <class 'app.weather.models.Weather'>
    print(some_forecast.weather_condition) # "短暫陣雨或雷雨"


# --- 從 Weather 物件存取單一 Location ---

# 存取 .location 屬性
linked_location = some_forecast.location

# linked_location 的「值」是什麼？
# 它是一個 Location 物件，與 yonghe_location 是同一個
print(type(linked_location))  # <class 'app.weather.models.Location'>
print(linked_location.full_name) # "新北市永和區"

# 驗證它們是同一個 Python 物件
print(linked_location is yonghe_location) # True
```

---

## 總結

| 語法 | 層級 | 目的 |
| :--- | :--- | :--- |
| `ForeignKey` | **資料庫** | 建立欄位與外鍵約束，保證資料的完整性。 |
| `relationship` | **Python/ORM** | 建立物件導覽屬性，讓我們寫程式時能方便地在關聯物件間移動。 |
| `back_populates` | **Python/ORM** | 將兩個 `relationship` 綁定在一起，實現雙向同步，簡化操作。 |
