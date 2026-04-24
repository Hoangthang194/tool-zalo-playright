from browser_automation.domain.zalo_workspace import (
    SavedZaloAccount,
    SavedZaloClickTarget,
    ZaloWorkspaceLibrary,
)
from browser_automation.infrastructure.chrome_launcher.json_zalo_workspace_store import (
    JsonZaloWorkspaceStore,
)


def test_json_zalo_workspace_store_round_trips_account_proxy_data(tmp_path) -> None:
    store = JsonZaloWorkspaceStore(path=tmp_path / "zalo-workspace.json")
    upload_file = tmp_path / "image.png"
    upload_file.write_text("data", encoding="utf-8")
    library = ZaloWorkspaceLibrary(
        accounts=(
            SavedZaloAccount(
                id="account-1",
                name="Profile One",
                profile_id="profile-1",
                proxy="user:pass@127.0.0.1:9000",
                mode="listen",
                listener_token="token-1",
            ),
        ),
        click_targets=(
            SavedZaloClickTarget(
                id="target-1",
                name="Open Menu",
                selector_kind="class",
                selector_value="menu-item active",
                upload_file_path=str(upload_file),
            ),
        ),
        selected_account_id="account-1",
        selected_click_target_id="target-1",
    )

    store.save(library)
    loaded = store.load()

    assert loaded == library


def test_json_zalo_workspace_store_skips_invalid_entries(tmp_path) -> None:
    workspace_path = tmp_path / "zalo-workspace.json"
    workspace_path.write_text(
        """
        {
          "selected_account_id": "account-1",
          "accounts": [
            {"id": "account-1", "name": "Profile One", "profile_id": "profile-1", "proxy": "1.2.3.4:80"},
            {"id": "", "name": "Broken", "profile_id": "profile-2"}
          ]
        }
        """,
        encoding="utf-8",
    )

    loaded = JsonZaloWorkspaceStore(path=workspace_path).load()

    assert len(loaded.accounts) == 1
    assert loaded.accounts[0].id == "account-1"
    assert loaded.accounts[0].mode == "send"
    assert loaded.accounts[0].listener_token == ""


def test_json_zalo_workspace_store_loads_accounts_from_legacy_payload_shape(tmp_path) -> None:
    workspace_path = tmp_path / "zalo-workspace.json"
    workspace_path.write_text(
        """
        {
          "selected_cookie_id": "cookie-1",
          "selected_account_id": "account-legacy",
          "cookies": [
            {"id": "cookie-1", "name": "Cookie A", "raw_cookie": "a=b"}
          ],
          "accounts": [
            {"id": "account-legacy", "name": "Legacy Account", "profile_id": "profile-legacy", "phone_number": "0901", "notes": "old"}
          ]
        }
        """,
        encoding="utf-8",
    )

    loaded = JsonZaloWorkspaceStore(path=workspace_path).load()

    assert len(loaded.accounts) == 1
    assert loaded.accounts[0].name == "Legacy Account"
    assert loaded.accounts[0].profile_id == "profile-legacy"
    assert loaded.accounts[0].proxy == ""


def test_json_zalo_workspace_store_loads_click_targets_when_present(tmp_path) -> None:
    upload_file = tmp_path / "image.png"
    upload_file.write_text("data", encoding="utf-8")
    escaped_upload_file = str(upload_file).replace("\\", "\\\\")
    workspace_path = tmp_path / "zalo-workspace.json"
    workspace_path.write_text(
        f"""
        {{
          "selected_account_id": "account-1",
          "selected_click_target_id": "target-1",
          "accounts": [
            {{"id": "account-1", "name": "Profile One", "profile_id": "profile-1", "proxy": ""}}
          ],
          "click_targets": [
            {{"id": "target-1", "name": "Open Menu", "selector_kind": "class", "selector_value": "menu-item", "upload_file_path": "{escaped_upload_file}"}},
            {{"id": "", "name": "Broken", "selector_kind": "id", "selector_value": "submit"}}
          ]
        }}
        """,
        encoding="utf-8",
    )

    loaded = JsonZaloWorkspaceStore(path=workspace_path).load()

    assert len(loaded.click_targets) == 1
    assert loaded.click_targets[0].id == "target-1"
    assert loaded.click_targets[0].selector_kind == "class"
    assert loaded.click_targets[0].upload_file_path == str(upload_file)
    assert loaded.selected_click_target_id == "target-1"
