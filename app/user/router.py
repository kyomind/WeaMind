from fastapi import APIRouter, HTTPException, status

router = APIRouter()

@router.get("/users", response_model=dict)
async def get_users():
    """
    用戶資料檢索端點的佔位符
    
    Returns:
        dict: 端點的佔位符訊息
    """
    return {"message": "用戶資料檢索端點（佔位符）"}

@router.post("/users", response_model=dict)
async def create_user():
    """
    創建新用戶的佔位符
    
    Returns:
        dict: 端點的佔位符訊息
    """
    return {"message": "用戶創建端點（佔位符）"}

@router.get("/users/{user_id}/quota", response_model=dict)
async def get_user_quota(user_id: str):
    """
    檢索用戶額度資訊的佔位符
    
    Args:
        user_id (str): 用戶的ID，用於檢索額度資訊
    
    Returns:
        dict: 包含用戶額度資訊的佔位符訊息
    """
    return {"message": f"用戶 {user_id} 的額度資訊（佔位符）"}
