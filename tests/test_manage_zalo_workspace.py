from browser_automation.application.use_cases.manage_zalo_workspace import (
    CookieUpsertRequest,
    ZaloAccountUpsertRequest,
    ZaloWorkspaceManagerUseCase,
)
from browser_automation.domain.exceptions import (
    SavedCookieConflictError,
    SavedCookieNotFoundError,
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


def test_workspace_use_case_saves_and_updates_cookie_entries() -> None:
    store = InMemoryZaloWorkspaceStore()
    use_case = ZaloWorkspaceManagerUseCase(store)

    created_state = use_case.save_cookie(
        CookieUpsertRequest(
            name="Session A",
            raw_cookie='{"sid":"abc"}',
            profile_id="profile-1",
            notes="Primary cookie",
        )
    )
    created_cookie = created_state.cookies[0]

    updated_state = use_case.save_cookie(
        CookieUpsertRequest(
            cookie_id=created_cookie.id,
            name="Session A Updated",
            raw_cookie='{"sid":"xyz"}',
            profile_id="profile-2",
            notes="Updated cookie",
        )
    )

    assert len(updated_state.cookies) == 1
    assert updated_state.cookies[0].id == created_cookie.id
    assert updated_state.cookies[0].name == "Session A Updated"
    assert updated_state.cookies[0].profile_id == "profile-2"
    assert updated_state.selected_cookie_id == created_cookie.id


def test_workspace_use_case_rejects_duplicate_cookie_names() -> None:
    store = InMemoryZaloWorkspaceStore()
    use_case = ZaloWorkspaceManagerUseCase(store)

    use_case.save_cookie(CookieUpsertRequest(name="Cookie One", raw_cookie="a=b"))

    try:
        use_case.save_cookie(CookieUpsertRequest(name="cookie one", raw_cookie="c=d"))
    except SavedCookieConflictError as exc:
        assert "already exists" in str(exc)
    else:
        raise AssertionError("Expected duplicate cookie name conflict")


def test_workspace_use_case_saves_and_updates_accounts() -> None:
    store = InMemoryZaloWorkspaceStore()
    use_case = ZaloWorkspaceManagerUseCase(store)

    created_state = use_case.save_account(
        ZaloAccountUpsertRequest(
            name="Zalo 1",
            phone_number="0900000001",
            profile_id="profile-1",
            cookie_id="cookie-1",
            notes="VIP",
        )
    )
    created_account = created_state.accounts[0]

    updated_state = use_case.save_account(
        ZaloAccountUpsertRequest(
            account_id=created_account.id,
            name="Zalo 1 Updated",
            phone_number="0900000002",
            profile_id="profile-2",
            cookie_id="cookie-2",
            notes="Updated",
        )
    )

    assert len(updated_state.accounts) == 1
    assert updated_state.accounts[0].id == created_account.id
    assert updated_state.accounts[0].name == "Zalo 1 Updated"
    assert updated_state.accounts[0].cookie_id == "cookie-2"
    assert updated_state.selected_account_id == created_account.id


def test_workspace_use_case_rejects_duplicate_account_names() -> None:
    store = InMemoryZaloWorkspaceStore()
    use_case = ZaloWorkspaceManagerUseCase(store)

    use_case.save_account(ZaloAccountUpsertRequest(name="Sales"))

    try:
        use_case.save_account(ZaloAccountUpsertRequest(name="sales"))
    except SavedZaloAccountConflictError as exc:
        assert "already exists" in str(exc)
    else:
        raise AssertionError("Expected duplicate account name conflict")


def test_workspace_use_case_deletes_cookie_and_account_entries() -> None:
    store = InMemoryZaloWorkspaceStore()
    use_case = ZaloWorkspaceManagerUseCase(store)

    cookie_state = use_case.save_cookie(CookieUpsertRequest(name="Cookie A", raw_cookie="x=y"))
    account_state = use_case.save_account(ZaloAccountUpsertRequest(name="Account A"))

    state_after_cookie_delete = use_case.delete_cookie(cookie_state.selected_cookie_id)
    state_after_account_delete = use_case.delete_account(account_state.selected_account_id)

    assert state_after_cookie_delete.cookies == ()
    assert state_after_account_delete.accounts == ()

    try:
        use_case.delete_cookie("missing")
    except SavedCookieNotFoundError:
        pass
    else:
        raise AssertionError("Expected cookie not found")

    try:
        use_case.delete_account("missing")
    except SavedZaloAccountNotFoundError:
        pass
    else:
        raise AssertionError("Expected account not found")
