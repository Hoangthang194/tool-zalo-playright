from browser_automation.domain.zalo_workspace import (
    SavedCookieEntry,
    SavedZaloAccount,
    ZaloWorkspaceLibrary,
)
from browser_automation.infrastructure.chrome_launcher.json_zalo_workspace_store import (
    JsonZaloWorkspaceStore,
)


def test_json_zalo_workspace_store_round_trips_cookie_and_account_data(tmp_path) -> None:
    store = JsonZaloWorkspaceStore(path=tmp_path / "zalo-workspace.json")
    library = ZaloWorkspaceLibrary(
        cookies=(
            SavedCookieEntry(
                id="cookie-1",
                name="Cookie A",
                raw_cookie='{"sid":"abc"}',
                profile_id="profile-1",
                notes="note a",
            ),
        ),
        accounts=(
            SavedZaloAccount(
                id="account-1",
                name="Account A",
                phone_number="0901",
                profile_id="profile-1",
                cookie_id="cookie-1",
                notes="note b",
            ),
        ),
        selected_cookie_id="cookie-1",
        selected_account_id="account-1",
    )

    store.save(library)
    loaded = store.load()

    assert loaded == library


def test_json_zalo_workspace_store_skips_invalid_entries(tmp_path) -> None:
    workspace_path = tmp_path / "zalo-workspace.json"
    workspace_path.write_text(
        """
        {
          "selected_cookie_id": "cookie-1",
          "selected_account_id": "account-1",
          "cookies": [
            {"id": "cookie-1", "name": "Cookie A", "raw_cookie": "a=b"},
            {"id": "", "name": "Broken", "raw_cookie": "c=d"}
          ],
          "accounts": [
            {"id": "account-1", "name": "Account A"},
            {"id": "account-2", "phone_number": "0902"}
          ]
        }
        """,
        encoding="utf-8",
    )

    loaded = JsonZaloWorkspaceStore(path=workspace_path).load()

    assert len(loaded.cookies) == 1
    assert loaded.cookies[0].id == "cookie-1"
    assert len(loaded.accounts) == 1
    assert loaded.accounts[0].id == "account-1"
