#!/usr/bin/env python3
"""
Rich Menu management script for LINE Bot.

This script automates Rich Menu operations for WeaMind LINE Bot, implementing
the complete LINE Rich Menu API workflow. Rich Menus provide persistent
interactive buttons at the bottom of the LINE chat interface.

Key Features:
- Create Rich Menu with JSON configuration
- Upload PNG images (max 1MB, specific dimensions)
- Set default Rich Menu for all users
- List and delete existing Rich Menus

LINE API Constraints:
- Rich Menu JSON configuration cannot be modified once created
- Images can be updated independently without recreating the Rich Menu
- Only one Rich Menu can be set as default at a time
- Maximum 1000 Rich Menus per LINE Bot account

Usage:
    python scripts/rich_menu_manager.py create --image path/to/image.png
    python scripts/rich_menu_manager.py list
    python scripts/rich_menu_manager.py delete --rich-menu-id MENU_ID
"""

import json
import logging
from pathlib import Path

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# LINE Bot API endpoints
LINE_API_BASE = "https://api.line.me/v2/bot"
LINE_DATA_API_BASE = "https://api-data.line.me/v2/bot"
RICH_MENU_API = f"{LINE_API_BASE}/richmenu"

# Headers for LINE API
HEADERS = {
    "Authorization": f"Bearer {settings.LINE_CHANNEL_ACCESS_TOKEN}",
    "Content-Type": "application/json",
}

# Rich Menu 配置檔案路徑
RICH_MENU_CONFIG_PATH = (
    Path(__file__).parent.parent / "docs" / "rich_menu" / "rich_menu_config.json"
)


def load_rich_menu_config() -> dict:
    """
    Load Rich Menu configuration from JSON file.

    Reads the Rich Menu structure, button areas, and PostBack actions from
    the configuration file. This JSON defines the interactive regions and
    their corresponding actions (weather, other menu, announcements).

    Returns:
        Rich Menu configuration dictionary
    """
    with open(RICH_MENU_CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def create_rich_menu() -> str | None:
    """
    Create Rich Menu with JSON configuration.

    Step 1 of the LINE Rich Menu API workflow. Creates a Rich Menu object
    with the configuration from rich_menu_config.json. Note that LINE API
    does not allow modification of existing Rich Menu settings - a new Rich
    Menu must be created for any JSON configuration changes.

    Returns:
        Rich Menu ID if successful, None otherwise
    """
    try:
        config = load_rich_menu_config()
        with httpx.Client() as client:
            response = client.post(RICH_MENU_API, headers=HEADERS, json=config)
            response.raise_for_status()

            rich_menu_id = response.json().get("richMenuId")
            logger.info(f"Rich Menu created successfully: {rich_menu_id}")
            return rich_menu_id

    except httpx.HTTPError:
        logger.exception("Failed to create Rich Menu")
        return None


def upload_rich_menu_image(rich_menu_id: str, image_path: Path) -> bool:
    """
    Upload Rich Menu image to existing Rich Menu.

    Step 2 of the LINE Rich Menu API workflow. Uploads an image to an
    existing Rich Menu ID. Unlike JSON configuration, images can be updated
    independently without recreating the Rich Menu object.

    Args:
        rich_menu_id: Rich Menu ID from create_rich_menu()
        image_path: Path to PNG image file (max 1MB, 2500x1686px or 2500x843px)

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
                    f"{LINE_DATA_API_BASE}/richmenu/{rich_menu_id}/content",
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
    Set Rich Menu as default for all users.

    Step 3 of the LINE Rich Menu API workflow. Makes the Rich Menu
    visible to all users. Only one Rich Menu can be set as default at a time.
    This replaces any previously set default Rich Menu.

    Args:
        rich_menu_id: Rich Menu ID to set as default

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
    List all Rich Menus on the LINE platform.

    Retrieves all Rich Menus associated with the LINE Bot account.
    Useful for debugging and cleanup operations to see existing Rich Menus
    before creating new ones or deleting old ones.

    Returns:
        List of Rich Menu objects with their IDs and configurations
    """
    try:
        with httpx.Client() as client:
            response = client.get(
                f"{RICH_MENU_API}/list",
                headers={"Authorization": f"Bearer {settings.LINE_CHANNEL_ACCESS_TOKEN}"},
            )
            response.raise_for_status()

            return response.json().get("richmenus", [])

    except httpx.HTTPError:
        logger.exception("Failed to list Rich Menus")
        return []


def delete_rich_menu(rich_menu_id: str) -> bool:
    """
    Delete Rich Menu from LINE platform.

    Permanently removes a Rich Menu. This is typically used to clean up
    old Rich Menus after deploying a new one. Cannot be undone.
    Best practice: always list existing Rich Menus before deletion.

    Args:
        rich_menu_id: Rich Menu ID to delete

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
    """
    Main execution function for Rich Menu management.

    Provides command-line interface for Rich Menu operations. Supports the
    complete LINE Rich Menu API workflow:

    1. create: Full 3-step process (create → upload image → set default)
    2. list: Display all Rich Menus
    3. delete: Remove specific Rich Menu by ID

    Update Rules:
    - JSON config changes: Must create new Rich Menu (cannot modify existing)
    - Image only changes: Can update existing Rich Menu image
    - Both changes: Full recreation required
    """
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
