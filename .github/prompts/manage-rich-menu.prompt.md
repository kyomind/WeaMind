---
description: "管理 LINE 圖文選單：建立、單帳號驗收、正式切換與回復"
---

# Manage LINE Rich Menus

## Goal and Boundaries

Manage rich menus through LINE's API using `scripts/rich_menu_manager.py` first. The configuration lives in `docs/rich_menu/rich_menu_config.json`; uploading it changes LINE-side state, not the k3s deployment. Merging configuration changes or redeploying the backend does not update an existing LINE menu.

- Preserve the existing image, labels, layout, bounds, and unrelated actions unless a redesign is requested. Read the JSON for actual positions; do not infer them from old diagrams.
- Distinguish URI actions from Postback actions. Only a Postback payload change may require updates in `app/line/postback.py`; location messages continue through the existing webhook flow.
- Get explicit authorization for the intended mutation: creating a menu, binding a test account, switching the global default, unlinking, or deleting. Authorization to edit files is not authorization to update LINE.
- Never log or commit tokens. Ask for missing image paths, menu IDs, or test user IDs only when the chosen operation needs them.

## Inspect and Prepare

1. Read `AGENTS.md`, the current JSON, `docs/rich_menu/README.md`, and the manager script.
2. Use `make upload-list` to list existing menus. Separately retrieve the current default and any test account's current per-user menu; the list command does not show those associations. Record their IDs for restoration. Distinguish an absent association from an API or authorization failure.
3. For uploads, verify the image matches the configured size (currently 2500×1686), is under 1 MB, and uses PNG for the existing script, which sends `image/png`. Do not redesign or regenerate an existing image unnecessarily.
4. Confirm the environment loads the required settings, including `LINE_CHANNEL_ACCESS_TOKEN`, without exposing credentials.

## Create Without Global Rollout

Use the existing CLI without `--set-default`:

```sh
uv run python -m scripts.rich_menu_manager create --image PATH_TO_EXISTING_IMAGE.png
```

Record the new menu ID and verify its configuration and image on LINE. **Do not use `make upload` for staging or personal testing:** it passes `--set-default` and immediately changes the global default.

## Single-Account Acceptance Test

The CLI does not implement per-user binding. For this step, consult the official API documentation and use a minimal authenticated request with credentials loaded from settings; do not invent CLI subcommands or add a management framework.

Relevant endpoints under `https://api.line.me/v2/bot`:

| Operation | Method and path |
| --- | --- |
| Read global default | `GET /user/all/richmenu` |
| Read a user's menu | `GET /user/{userId}/richmenu` |
| Bind a user's menu | `POST /user/{userId}/richmenu/{richMenuId}` |
| Remove a user's override | `DELETE /user/{userId}/richmenu` |
| Set global default | `POST /user/all/richmenu/{richMenuId}` |
| Remove API default | `DELETE /user/all/richmenu` |

1. After authorization, bind the new menu only to the designated test user. Leave the global default unchanged.
2. Have the user test in mobile LINE: open the menu, tap the changed action, send a location, and confirm the weather reply. Check other buttons remain usable. JSON validation or successful upload is not proof of client behavior.
3. The test uses the production webhook and may create normal Query History. No separate k3s environment is needed for a menu-only change, but it is not an isolated backend test.
4. Restore the previous per-user menu after testing. If there was no override, remove the test override. Confirm restoration; do not silently leave a personal override that hides later default changes.

## Global Rollout and Recovery

- Report acceptance results and wait for explicit approval before global rollout. If mobile testing is unavailable, report that gap rather than claiming verification.
- Reuse the tested menu ID. The existing `set_default_rich_menu()` helper can set it as default; do not recreate the menu just to enable it.
- Verify the default via the API and have the user confirm it on mobile LINE. Existing per-user overrides take precedence over the default and are not changed by this operation.
- Keep the previous menu and image available. If validation fails, restore the previous default; if no API default existed, remove the new API default to restore that state. Verify the result.
- Delete menus only with explicit approval and after checking they are not needed for active users or rollback. `make upload-delete ID=...` is destructive.

## Report

Report files changed, commands or API operations used (without credentials), old/new menu IDs, personal versus global scope, test results, restoration status, and remaining risks. A failed API request must not be reported as an empty menu list or a successful update.

## References

- `scripts/rich_menu_manager.py`
- `docs/rich_menu/README.md`
- [LINE Rich Menu API](https://developers.line.biz/en/reference/messaging-api/#rich-menu)
- [Per-user rich menus](https://developers.line.biz/en/docs/messaging-api/use-per-user-rich-menus/)
