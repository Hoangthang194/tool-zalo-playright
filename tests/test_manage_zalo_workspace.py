from browser_automation.application.use_cases.manage_zalo_workspace import (
    ZaloAccountUpsertRequest,
    ZaloWorkspaceManagerUseCase,
)
from browser_automation.domain.exceptions import (
    SavedZaloAccountConflictError,
    SavedZaloAccountNotFoundError,
)
from browser_automation.domain.zalo_workspace import ZaloWorkspaceLibrary


class InMemoryZaloWorkspaceStore:
    def __init__(self) -> None:
        self.library = ZaloWorkspaceLibrary()

    def load(self) -> ZaloWorkspaceLibrary:
        return self.library

    def save(self, library: ZaloWorkspaceLibrary) -> None:
        self.library = library


def test_workspace_use_case_saves_and_updates_accounts() -> None:
    store = InMemoryZaloWorkspaceStore()
    use_case = ZaloWorkspaceManagerUseCase(store)

    created_state = use_case.save_account(
        ZaloAccountUpsertRequest(
            name="Profile One",
            profile_id="profile-1",
            proxy="127.0.0.1:8080",
        )
    )
    created_account = created_state.accounts[0]

    updated_state = use_case.save_account(
        ZaloAccountUpsertRequest(
            account_id=created_account.id,
            name="Profile One",
            profile_id="profile-1",
            proxy="user:pass@10.0.0.2:9000",
        )
    )

    assert len(updated_state.accounts) == 1
    assert updated_state.accounts[0].id == created_account.id
    assert updated_state.accounts[0].name == "Profile One"
    assert updated_state.accounts[0].profile_id == "profile-1"
    assert updated_state.accounts[0].proxy == "user:pass@10.0.0.2:9000"
    assert updated_state.accounts[0].mode == "send"
    assert updated_state.accounts[0].listener_token
    assert updated_state.selected_account_id == created_account.id


def test_workspace_use_case_rejects_duplicate_profile_links() -> None:
    store = InMemoryZaloWorkspaceStore()
    use_case = ZaloWorkspaceManagerUseCase(store)

    use_case.save_account(
        ZaloAccountUpsertRequest(
            name="Profile One",
            profile_id="profile-1",
            proxy="127.0.0.1:8000",
        )
    )

    try:
        use_case.save_account(
            ZaloAccountUpsertRequest(
                name="Profile One Duplicate",
                profile_id="profile-1",
                proxy="127.0.0.1:9000",
            )
        )
    except SavedZaloAccountConflictError as exc:
        assert "already exists" in str(exc)
    else:
        raise AssertionError("Expected duplicate linked profile conflict")


def test_workspace_use_case_requires_linked_profile() -> None:
    store = InMemoryZaloWorkspaceStore()
    use_case = ZaloWorkspaceManagerUseCase(store)

    try:
        use_case.save_account(
            ZaloAccountUpsertRequest(
                name="Missing Profile",
                proxy="127.0.0.1:8080",
            )
        )
    except SavedZaloAccountConflictError as exc:
        assert "linked profile is required" in str(exc).lower()
    else:
        raise AssertionError("Expected missing profile conflict")


def test_workspace_use_case_deletes_and_selects_accounts() -> None:
    store = InMemoryZaloWorkspaceStore()
    use_case = ZaloWorkspaceManagerUseCase(store)

    first_state = use_case.save_account(
        ZaloAccountUpsertRequest(name="Profile A", profile_id="profile-a", proxy="10.0.0.1:9000")
    )
    second_state = use_case.save_account(
        ZaloAccountUpsertRequest(name="Profile B", profile_id="profile-b", proxy="")
    )

    selected_state = use_case.select_account(first_state.selected_account_id)
    state_after_delete = use_case.delete_account(second_state.selected_account_id)

    assert selected_state.selected_account_id == first_state.selected_account_id
    assert len(state_after_delete.accounts) == 1
    assert state_after_delete.accounts[0].profile_id == "profile-a"

    try:
        use_case.delete_account("missing")
    except SavedZaloAccountNotFoundError:
        pass
    else:
        raise AssertionError("Expected account not found")


def test_workspace_use_case_persists_listener_mode_and_token_on_update() -> None:
    store = InMemoryZaloWorkspaceStore()
    use_case = ZaloWorkspaceManagerUseCase(store)

    created_state = use_case.save_account(
        ZaloAccountUpsertRequest(
            name="Profile Listen",
            profile_id="profile-listen",
            proxy="",
            mode="listen",
        )
    )
    created_account = created_state.accounts[0]

    updated_state = use_case.save_account(
        ZaloAccountUpsertRequest(
            account_id=created_account.id,
            name="Profile Listen",
            profile_id="profile-listen",
            proxy="127.0.0.1:8080",
            mode="listen",
        )
    )

    updated_account = updated_state.accounts[0]
    assert updated_account.mode == "listen"
    assert updated_account.listener_token == created_account.listener_token


def test_workspace_use_case_rejects_invalid_account_mode() -> None:
    store = InMemoryZaloWorkspaceStore()
    use_case = ZaloWorkspaceManagerUseCase(store)

    try:
        use_case.save_account(
            ZaloAccountUpsertRequest(
                name="Profile One",
                profile_id="profile-1",
                mode="invalid",
            )
        )
    except SavedZaloAccountConflictError as exc:
        assert "mode" in str(exc).lower()
    else:
        raise AssertionError("Expected invalid mode conflict")
