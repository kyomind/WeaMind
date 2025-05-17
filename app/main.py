from fastapi import FastAPI

from app.user.router import router as user_router

app = FastAPI(title="WeaMind API", description="API for WeaMind Weather LINE BOT")


@app.get("/")
async def root():
    """
    歡迎使用 WeaMind API 的根路由
    
    Returns:
        dict: API 的歡迎訊息
    """
    return {"message": "Welcome to WeaMind API"}


# Include routers from modules
app.include_router(user_router, prefix="/api/v1", tags=["user"])
