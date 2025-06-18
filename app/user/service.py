from app.user import constants, schemas

_fake_db: dict[int, dict] = {}


def create_user(data: schemas.UserCreate) -> dict:
    """
    建立新用戶並儲存於記憶體

    Returns:
        新建立的用戶資料
    """
    user_id = max(_fake_db) + 1 if _fake_db else 1
    record = {
        "id": user_id,
        "line_user_id": data.line_user_id,
        "display_name": data.display_name,
        "quota": constants.DAILY_QUOTA_LIMIT,
        "quota_used": 0,
    }
    _fake_db[user_id] = record
    return record


def get_user(user_id: int) -> dict | None:
    """
    取得指定用戶
    """
    return _fake_db.get(user_id)


def update_user(user_id: int, data: schemas.UserUpdate) -> dict | None:
    """
    更新用戶資料
    """
    record = _fake_db.get(user_id)
    if not record:
        return None
    if data.display_name is not None:
        record["display_name"] = data.display_name
    return record


def delete_user(user_id: int) -> bool:
    """
    刪除指定用戶
    """
    return _fake_db.pop(user_id, None) is not None


def list_users() -> list[dict]:
    """
    列出所有用戶
    """
    return list(_fake_db.values())


def get_user_quota(user_id: int) -> dict | None:
    """
    回傳指定用戶的額度資訊
    """
    record = _fake_db.get(user_id)
    if not record:
        return None
    return {
        "line_user_id": record["line_user_id"],
        "quota": record["quota"],
        "quota_used": record["quota_used"],
    }
