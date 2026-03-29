---
description: "Guide for managing WeaMind LINE Rich Menus"
---

# WeaMind Rich Menu Guide

## Goal

Use this prompt when the user asks to create, upload, list, delete, or debug a LINE Rich Menu for WeaMind. Prefer the existing script and Makefile targets. Keep the layout and payloads consistent unless the user asks for a redesign.

## Rules

1. Use `scripts/rich_menu_manager.py` and the Makefile targets first.
2. Keep the preset 2x3 layout unless the user asks for a new design.
3. Do not recalculate coordinates when the preset layout already fits the request.
4. If the request is missing the image path, menu ID, or action, ask one short question and stop.
5. If the task can be done with the existing script, use it instead of manual LINE API calls.
6. Report the exact command used, the result, and any files changed.

## Workflow

1. Identify the task.
   - upload or create
   - list
   - delete
   - debug a failed upload or a missing menu
2. Check the required inputs.
   - upload: image path and whether it should become the default menu
   - delete: rich menu ID
   - debug: error message or failed command output
3. Verify the image before uploading.
   - Size: 2500 x 1686
   - Format: PNG or JPEG
   - File size: under 1 MB
4. Check the environment.
   - `LINE_CHANNEL_ACCESS_TOKEN` must be set
5. Run the matching command.
   - upload or create: `make upload IMAGE=...`
   - list: `make upload-list`
   - delete: `make upload-delete ID=...`
6. If the upload succeeds, verify it with `make upload-list`.
7. If the upload fails, inspect the script, input file, or environment variable first. Only edit code if the failure comes from a real bug.
8. Report back with:
   - what was done
   - the command used
   - the result
   - any remaining issue

## Button Layout

Use the existing preset 2x3 layout.

- Top left: home weather
- Top middle: office weather
- Top right: recent queries
- Bottom left: current location
- Bottom middle: location settings
- Bottom right: other

## Postback Handling

If the task adds or changes a button action, update `app/line/service.py` to handle the new `PostbackEvent` payload. Keep the handler simple and route by the `action` field.

## References

- `scripts/rich_menu_manager.py`
- `docs/rich_menu/README.md`
- `docs/rich_menu/implementation-plan.md`
