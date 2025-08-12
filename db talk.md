# FastAPI 確實一堆用 db 作為參數名！
要認真？好。**答案是：會，用 `db` 的一堆。** 但現在 **官方文件偏好 `session`**。兩派並存，不是你的錯覺。
[Truth Hurts](https://chatgpt.com/g/g-xhP25Gb8Y-truth-hurts/c/6899c2e6-a730-832f-8ddb-8041e792dd88)
| 命名      | 在社群/專案中的可見度                                                  | 代表性證據                                                                                                                                                                                                                                                                                       |
| --------- | ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `db`      | 高（大量教學、問答、範本文章都直接寫 `db: Session = Depends(get_db)`） | PropelAuth 教學用 `db: Session = Depends(get_db)`；FastAPI‑RESTful 文件同樣用 `db`；Stack Overflow 問答範例也都是 `db`；甚至 FastAPI 自家「依賴 + yield」示例函式名稱就是 `get_db`、內部變數叫 `db`。 ([propelauth.com][1], [fastapi-restful.netlify.app][2], [Stack Overflow][3], [FastAPI][4]) |
| `session` | 官方文件近年趨勢（特別是跟著 SQLModel/SQLAlchemy 2.0 風格）            | FastAPI 官方「SQL Databases」教學整套示例都用 `get_session`、`SessionDep`、參數名 `session`。TestDriven.io 的 SQLModel 教學也用 `session`。 ([FastAPI][5], [testdriven.io][6])                                                                                                                   |

我的結論很簡單、也夠狠：

* **既有專案**：別作死改名。團隊已經習慣 `db`，一致性勝過語義潔癖。
* **新碼 / 要跟 FastAPI 官方風格走**：用 `session`，因為 SQLModel / SA 2.0 生態都往這個方向。

你要的是事實，不是宗教戰：**社群真的大量用 `db`**（上面看得到活生生的例子），**官方現在示例主推 `session`**。兩種都對，挑一個在你團隊裡最省腦、最少改動的就好。

[1]: https://www.propelauth.com/post/a-practical-guide-to-dependency-injection-with-fastapis-depends?utm_source=chatgpt.com "Guide to Dependency Injection with FastAPI's Depends"
[2]: https://fastapi-restful.netlify.app/user-guide/session/?utm_source=chatgpt.com "SQLAlchemy Sessions"
[3]: https://stackoverflow.com/questions/76358355/fastapi-depends-w-get-db-failing-for-put-endpoint?utm_source=chatgpt.com "FastAPI Depends w/ get_db failing for PUT endpoint"
[4]: https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/?utm_source=chatgpt.com "Dependencies with yield - FastAPI"
[5]: https://fastapi.tiangolo.com/tutorial/sql-databases/ "SQL (Relational) Databases - FastAPI"
[6]: https://testdriven.io/blog/fastapi-sqlmodel/ "FastAPI with Async SQLAlchemy, SQLModel, and Alembic | TestDriven.io"

#程式
