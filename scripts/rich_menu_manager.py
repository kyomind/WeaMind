#!/usr/bin/env python3
"""
Rich Menu upload script.

Script for automating Rich Menu image and configuration uploads to LINE platform.
"""

import logging
from pathlib import Path

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# LINE Bot API endpoints
LINE_API_BASE = "https://api.line.me/v2/bot"
RICH_MENU_API = f"{LINE_API_BASE}/richmenu"

# Headers for LINE API
HEADERS = {
    "Authorization": f"Bearer {settings.LINE_CHANNEL_ACCESS_TOKEN}",
    "Content-Type": "application/json",
}

# Rich Menu 配置
RICH_MENU_CONFIG = {
    "size": {"width": 2500, "height": 1686},
    "selected": False,
    "name": "WeaMind Main Menu",
    "chatBarText": "選單",
    "areas": [
        {
            "bounds": {"x": 0, "y": 0, "width": 833, "height": 843},
            "action": {
                "type": "postback",
                "data": "action=weather&type=home",
                "displayText": "查住家",
            },
        },
        {
            "bounds": {"x": 833, "y": 0, "width": 833, "height": 843},
            "action": {
                "type": "postback",
                "data": "action=weather&type=office",
                "displayText": "查公司",
            },
        },
        {
            "bounds": {"x": 1666, "y": 0, "width": 834, "height": 843},
            "action": {
                "type": "postback",
                "data": "action=recent_queries",
                "displayText": "最近查過",
            },
        },
        {
            "bounds": {"x": 0, "y": 843, "width": 833, "height": 843},
            "action": {
                "type": "postback",
                "data": "action=weather&type=current",
                "displayText": "目前位置",
            },
        },
        {
            "bounds": {"x": 833, "y": 843, "width": 833, "height": 843},
            "action": {
                "type": "postback",
                "data": "action=settings&type=location",
                "displayText": "設定地點",
            },
        },
        {
            "bounds": {"x": 1666, "y": 843, "width": 834, "height": 843},
            "action": {"type": "postback", "data": "action=menu&type=more", "displayText": "其它"},
        },
    ],
}


def create_rich_menu() -> str | None:
    """
    Create Rich Menu and return rich_menu_id.

    Returns:
        Rich Menu ID if successful, None otherwise
    """
    try:
        with httpx.Client() as client:
            response = client.post(RICH_MENU_API, headers=HEADERS, json=RICH_MENU_CONFIG)
            response.raise_for_status()

            rich_menu_id = response.json().get("richMenuId")
            logger.info(f"Rich Menu created successfully: {rich_menu_id}")
            return rich_menu_id

    except httpx.HTTPError:
        logger.exception("Failed to create Rich Menu")
        return None


def upload_rich_menu_image(rich_menu_id: str, image_path: Path) -> bool:
    """
    Upload Rich Menu image.

    Args:
        rich_menu_id: Rich Menu ID
        image_path: Image file path

    Returns:
        True if successful, False otherwise
    """
    if not image_path.exists():
        logger.error(f"Image file not found: {image_path}")
        return False

    try:
        with httpx.Client() as client:
            with open(image_path, "rb") as image_file:
                response = client.post(
                    f"{RICH_MENU_API}/{rich_menu_id}/content",
                    headers={
                        "Authorization": f"Bearer {settings.LINE_CHANNEL_ACCESS_TOKEN}",
                        "Content-Type": "image/png",
                    },
                    content=image_file.read(),
                )
                response.raise_for_status()

            logger.info("Rich Menu image uploaded successfully")
            return True

    except httpx.HTTPError:
        logger.exception("Failed to upload Rich Menu image")
        return False


def set_default_rich_menu(rich_menu_id: str) -> bool:
    """
    Set default Rich Menu.

    Args:
        rich_menu_id: Rich Menu ID

    Returns:
        True if successful, False otherwise
    """
    try:
        with httpx.Client() as client:
            response = client.post(
                f"{LINE_API_BASE}/user/all/richmenu/{rich_menu_id}",
                headers={"Authorization": f"Bearer {settings.LINE_CHANNEL_ACCESS_TOKEN}"},
            )
            response.raise_for_status()

            logger.info("Rich Menu set as default successfully")
            return True

    except httpx.HTTPError:
        logger.exception("Failed to set default Rich Menu")
        return False


def list_rich_menus() -> list[dict]:
    """
    List all Rich Menus.

    Returns:
        List of Rich Menu objects
    """
    try:
        with httpx.Client() as client:
            response = client.get(
                RICH_MENU_API,
                headers={"Authorization": f"Bearer {settings.LINE_CHANNEL_ACCESS_TOKEN}"},
            )
            response.raise_for_status()

            return response.json().get("richmenus", [])

    except httpx.HTTPError:
        logger.exception("Failed to list Rich Menus")
        return []


def delete_rich_menu(rich_menu_id: str) -> bool:
    """
    Delete Rich Menu.

    Args:
        rich_menu_id: Rich Menu ID

    Returns:
        True if successful, False otherwise
    """
    try:
        with httpx.Client() as client:
            response = client.delete(
                f"{RICH_MENU_API}/{rich_menu_id}",
                headers={"Authorization": f"Bearer {settings.LINE_CHANNEL_ACCESS_TOKEN}"},
            )
            response.raise_for_status()

            logger.info(f"Rich Menu deleted successfully: {rich_menu_id}")
            return True

    except httpx.HTTPError:
        logger.exception("Failed to delete Rich Menu")
        return False


def main() -> None:
    """Main execution function."""
    import argparse

    parser = argparse.ArgumentParser(description="Rich Menu 管理工具")
    parser.add_argument("action", choices=["create", "list", "delete"], help="執行動作")
    parser.add_argument("--image", type=str, help="圖片檔案路徑 (用於 create)")
    parser.add_argument("--rich-menu-id", type=str, help="Rich Menu ID (用於 delete)")
    parser.add_argument("--set-default", action="store_true", help="設定為預設 Rich Menu")

    args = parser.parse_args()

    if args.action == "create":
        if not args.image:
            print("錯誤：建立 Rich Menu 需要指定 --image 參數")
            return

        image_path = Path(args.image)

        # 1. 建立 Rich Menu
        rich_menu_id = create_rich_menu()
        if not rich_menu_id:
            print("建立 Rich Menu 失敗")
            return

        # 2. 上傳圖片
        if not upload_rich_menu_image(rich_menu_id, image_path):
            print("上傳圖片失敗")
            delete_rich_menu(rich_menu_id)  # 清理失敗的 Rich Menu
            return

        # 3. 設定為預設（如果指定）
        if args.set_default:
            if not set_default_rich_menu(rich_menu_id):
                print("設定預設 Rich Menu 失敗")
                return

        print(f"✅ Rich Menu 建立成功！ID: {rich_menu_id}")

    elif args.action == "list":
        rich_menus = list_rich_menus()
        if rich_menus:
            print("📋 現有 Rich Menu 列表：")
            for menu in rich_menus:
                print(f"- ID: {menu['richMenuId']}")
                print(f"  名稱: {menu['name']}")
                print(f"  聊天欄文字: {menu['chatBarText']}")
                print()
        else:
            print("沒有找到 Rich Menu")

    elif args.action == "delete":
        if not args.rich_menu_id:
            print("錯誤：刪除 Rich Menu 需要指定 --rich-menu-id 參數")
            return

        if delete_rich_menu(args.rich_menu_id):
            print(f"✅ Rich Menu 刪除成功！ID: {args.rich_menu_id}")
        else:
            print("刪除 Rich Menu 失敗")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
