from pathlib import Path

import pytest

from browser_automation.application.use_cases.launch_zalo_account import (
    LaunchZaloAccountUseCase,
)
from browser_automation.domain.exceptions import (
    SavedProfileNotFoundError,
    SavedZaloAccountConflictError,
)
from browser_automation.domain.zalo_launcher import (
    SavedChromeProfile,
    SavedProfileLibrary,
    WindowPlacement,
)
from browser_automation.domain.zalo_workspace import (
    SavedZaloAccount,
    SavedZaloClickTarget,
    ZaloWorkspaceLibrary,
)


class FakeChromeDiscovery:
    def __init__(self, executable_path: Path | None = None) -> None:
        self.executable_path = executable_path

    def discover_executable(self) -> Path | None:
        return self.executable_path

    def discover_user_data_dir(self) -> Path | None:
        return None


class InMemorySavedProfileLibraryStore:
    def __init__(self, library: SavedProfileLibrary | None = None) -> None:
        self.library = SavedProfileLibrary() if library is None else library

    def load(self) -> SavedProfileLibrary:
        return self.library

    def save(self, library: SavedProfileLibrary) -> None:
        self.library = library


class InMemoryZaloWorkspaceStore:
    def __init__(self, library: ZaloWorkspaceLibrary | None = None) -> None:
        self.library = ZaloWorkspaceLibrary() if library is None else library

    def load(self) -> ZaloWorkspaceLibrary:
        return self.library

    def save(self, library: ZaloWorkspaceLibrary) -> None:
        self.library = library


class FakeChromeLauncher:
    def __init__(self) -> None:
        self.launched_config = None
        self.launched_configs = []

    def launch(self, config) -> None:
        self.launched_config = config
        self.launched_configs.append(config)


class FakeChromeWindowArranger:
    def __init__(
        self,
        *,
        initial_handles: tuple[int, ...] = (),
        new_handles: tuple[int | None, ...] = (),
        placements: tuple[WindowPlacement, ...] = (),
    ) -> None:
        self.initial_handles = initial_handles
        self.new_handles = list(new_handles)
        self.placements = placements
        self.applied_window_placements: list[tuple[int, WindowPlacement]] = []

    def snapshot_window_handles(self) -> frozenset[int]:
        return frozenset(self.initial_handles)

    def calculate_grid_placements(self, *, count: int, columns: int, rows: int) -> tuple[WindowPlacement, ...]:
        if self.placements:
            return self.placements[:count]
        return tuple(
            WindowPlacement(
                left=index * 100,
                top=0,
                width=400,
                height=500,
            )
            for index in range(count)
        )

    def wait_for_new_window(self, existing_window_handles, timeout_seconds: float) -> int | None:
        if not self.new_handles:
            return None
        return self.new_handles.pop(0)

    def apply_window_placement(self, window_handle: int, placement: WindowPlacement) -> None:
        self.applied_window_placements.append((window_handle, placement))


class FakeClickAutomationRunner:
    def __init__(self, clicked_target_names: tuple[str, ...] = ()) -> None:
        self.clicked_target_names = clicked_target_names
        self.remote_debugging_port = None
        self.target_url = None
        self.click_targets = None
        self.timeout_seconds = None

    def run(self, *, remote_debugging_port: int, target_url: str, click_targets, timeout_seconds: float):
        self.remote_debugging_port = remote_debugging_port
        self.target_url = target_url
        self.click_targets = click_targets
        self.timeout_seconds = timeout_seconds

        class Result:
            def __init__(self, clicked_target_names: tuple[str, ...]) -> None:
                self.clicked_target_names = clicked_target_names

        return Result(self.clicked_target_names)


def test_launch_zalo_account_uses_linked_profile_and_proxy(tmp_path) -> None:
    chrome_executable = tmp_path / "chrome.exe"
    chrome_executable.write_text("", encoding="utf-8")
    profile_one_path = tmp_path / "User Data" / "Profile 1"
    profile_two_path = tmp_path / "User Data" / "Profile 2"
    profile_one_path.mkdir(parents=True)
    profile_two_path.mkdir(parents=True)

    first_profile = SavedChromeProfile(
        id="profile-1",
        name="Profile One",
        chrome_executable=str(chrome_executable),
        profile_path=str(profile_one_path),
    )
    second_profile = SavedChromeProfile(
        id="profile-2",
        name="Profile Two",
        chrome_executable=str(chrome_executable),
        profile_path=str(profile_two_path),
    )
    first_account = SavedZaloAccount(
        id="account-1",
        name="Profile One",
        profile_id="profile-1",
        proxy="",
    )
    second_account = SavedZaloAccount(
        id="account-2",
        name="Profile Two",
        profile_id="profile-2",
        proxy="171.236.172.8:50455:danggiang7:danggiang7",
    )

    library_store = InMemorySavedProfileLibraryStore(
        SavedProfileLibrary(
            profiles=(first_profile, second_profile),
            selected_profile_id=first_profile.id,
        )
    )
    workspace_store = InMemoryZaloWorkspaceStore(
        ZaloWorkspaceLibrary(
            accounts=(first_account, second_account),
            selected_account_id=first_account.id,
        )
    )
    launcher = FakeChromeLauncher()
    window_arranger = FakeChromeWindowArranger(
        initial_handles=(901,),
        new_handles=(902,),
        placements=(
            WindowPlacement(left=0, top=0, width=300, height=400),
            WindowPlacement(left=300, top=0, width=300, height=400),
        ),
    )
    use_case = LaunchZaloAccountUseCase(
        workspace_store=workspace_store,
        library_store=library_store,
        chrome_discovery=FakeChromeDiscovery(executable_path=chrome_executable),
        chrome_launcher=launcher,
        chrome_window_arranger=window_arranger,
    )

    result = use_case.launch_account(second_account.id)

    assert result.account_id == second_account.id
    assert result.profile_id == second_profile.id
    assert result.profile_name == "Profile Two"
    assert result.proxy == "171.236.172.8:50455:danggiang7:danggiang7"
    assert workspace_store.library.selected_account_id == second_account.id
    assert launcher.launched_config is not None
    assert launcher.launched_config.user_data_dir == profile_two_path.parent
    assert launcher.launched_config.profile_directory == "Profile 2"
    assert launcher.launched_config.proxy_server == "171.236.172.8:50455"
    assert launcher.launched_config.window_placement == WindowPlacement(
        left=300,
        top=0,
        width=300,
        height=400,
    )
    assert result.launch_result.proxy_server == "171.236.172.8:50455"
    assert window_arranger.applied_window_placements == [
        (902, WindowPlacement(left=300, top=0, width=300, height=400))
    ]


def test_launch_zalo_account_allows_blank_proxy(tmp_path) -> None:
    chrome_executable = tmp_path / "chrome.exe"
    chrome_executable.write_text("", encoding="utf-8")
    profile_path = tmp_path / "User Data" / "Default"
    profile_path.mkdir(parents=True)

    library_store = InMemorySavedProfileLibraryStore(
        SavedProfileLibrary(
            profiles=(
                SavedChromeProfile(
                    id="profile-1",
                    name="Default",
                    chrome_executable=str(chrome_executable),
                    profile_path=str(profile_path),
                ),
            ),
            selected_profile_id="profile-1",
        )
    )
    workspace_store = InMemoryZaloWorkspaceStore(
        ZaloWorkspaceLibrary(
            accounts=(
                SavedZaloAccount(
                    id="account-1",
                    name="Default",
                    profile_id="profile-1",
                    proxy="",
                ),
            ),
            selected_account_id="account-1",
        )
    )
    launcher = FakeChromeLauncher()
    use_case = LaunchZaloAccountUseCase(
        workspace_store=workspace_store,
        library_store=library_store,
        chrome_discovery=FakeChromeDiscovery(executable_path=chrome_executable),
        chrome_launcher=launcher,
    )

    result = use_case.launch_account()

    assert result.proxy == ""
    assert launcher.launched_config.proxy_server is None
    assert result.launch_result.proxy_server is None


def test_launch_zalo_account_rejects_missing_linked_profile(tmp_path) -> None:
    chrome_executable = tmp_path / "chrome.exe"
    chrome_executable.write_text("", encoding="utf-8")

    library_store = InMemorySavedProfileLibraryStore(SavedProfileLibrary())
    workspace_store = InMemoryZaloWorkspaceStore(
        ZaloWorkspaceLibrary(
            accounts=(
                SavedZaloAccount(
                    id="account-1",
                    name="Broken",
                    profile_id="missing-profile",
                    proxy="127.0.0.1:8080",
                ),
            ),
            selected_account_id="account-1",
        )
    )
    use_case = LaunchZaloAccountUseCase(
        workspace_store=workspace_store,
        library_store=library_store,
        chrome_discovery=FakeChromeDiscovery(executable_path=chrome_executable),
        chrome_launcher=FakeChromeLauncher(),
    )

    with pytest.raises(SavedProfileNotFoundError, match="Linked saved Chrome profile not found"):
        use_case.launch_account()


def test_launch_zalo_account_requires_linked_profile_reference(tmp_path) -> None:
    chrome_executable = tmp_path / "chrome.exe"
    chrome_executable.write_text("", encoding="utf-8")

    workspace_store = InMemoryZaloWorkspaceStore(
        ZaloWorkspaceLibrary(
            accounts=(
                SavedZaloAccount(
                    id="account-1",
                    name="Missing Link",
                    profile_id=None,
                    proxy="127.0.0.1:8080",
                ),
            ),
            selected_account_id="account-1",
        )
    )
    use_case = LaunchZaloAccountUseCase(
        workspace_store=workspace_store,
        library_store=InMemorySavedProfileLibraryStore(SavedProfileLibrary()),
        chrome_discovery=FakeChromeDiscovery(executable_path=chrome_executable),
        chrome_launcher=FakeChromeLauncher(),
    )

    with pytest.raises(SavedZaloAccountConflictError, match="requires a linked profile"):
        use_case.launch_account()


def test_launch_zalo_account_exposes_remote_debugging_port_for_follow_up_clicks(tmp_path) -> None:
    chrome_executable = tmp_path / "chrome.exe"
    chrome_executable.write_text("", encoding="utf-8")
    profile_path = tmp_path / "User Data" / "Default"
    profile_path.mkdir(parents=True)

    workspace_store = InMemoryZaloWorkspaceStore(
        ZaloWorkspaceLibrary(
            accounts=(
                SavedZaloAccount(
                    id="account-1",
                    name="Default",
                    profile_id="profile-1",
                    proxy="",
                ),
            ),
            selected_account_id="account-1",
        )
    )
    click_runner = FakeClickAutomationRunner()
    use_case = LaunchZaloAccountUseCase(
        workspace_store=workspace_store,
        library_store=InMemorySavedProfileLibraryStore(
            SavedProfileLibrary(
                profiles=(
                    SavedChromeProfile(
                        id="profile-1",
                        name="Default",
                        chrome_executable=str(chrome_executable),
                        profile_path=str(profile_path),
                    ),
                ),
                selected_profile_id="profile-1",
            )
        ),
        chrome_discovery=FakeChromeDiscovery(executable_path=chrome_executable),
        chrome_launcher=FakeChromeLauncher(),
        click_automation_runner=click_runner,
    )

    result = use_case.launch_account()

    assert result.launch_result.remote_debugging_port is not None
    assert click_runner.remote_debugging_port is None


def test_launch_zalo_account_does_not_run_saved_click_targets_during_launch(tmp_path) -> None:
    chrome_executable = tmp_path / "chrome.exe"
    chrome_executable.write_text("", encoding="utf-8")
    profile_path = tmp_path / "User Data" / "Default"
    profile_path.mkdir(parents=True)

    click_runner = FakeClickAutomationRunner(clicked_target_names=("Open Menu",))
    use_case = LaunchZaloAccountUseCase(
        workspace_store=InMemoryZaloWorkspaceStore(
            ZaloWorkspaceLibrary(
                accounts=(
                    SavedZaloAccount(
                        id="account-1",
                        name="Default",
                        profile_id="profile-1",
                        proxy="",
                    ),
                ),
                click_targets=(
                    SavedZaloClickTarget(
                        id="target-1",
                        name="Open Menu",
                        selector_kind="id",
                        selector_value="btnSubmit",
                    ),
                ),
                selected_account_id="account-1",
                selected_click_target_id="target-1",
            )
        ),
        library_store=InMemorySavedProfileLibraryStore(
            SavedProfileLibrary(
                profiles=(
                    SavedChromeProfile(
                        id="profile-1",
                        name="Default",
                        chrome_executable=str(chrome_executable),
                        profile_path=str(profile_path),
                    ),
                ),
                selected_profile_id="profile-1",
            )
        ),
        chrome_discovery=FakeChromeDiscovery(executable_path=chrome_executable),
        chrome_launcher=FakeChromeLauncher(),
        click_automation_runner=click_runner,
    )

    result = use_case.launch_account()

    assert result.launch_result.remote_debugging_port is not None
    assert click_runner.click_targets is None
    assert click_runner.remote_debugging_port is None
