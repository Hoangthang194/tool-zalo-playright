from pathlib import Path

import pytest

from browser_automation.application.use_cases.manage_zalo_profiles import (
    SavedProfileUpsertRequest,
    ZaloProfileManagerUseCase,
)
from browser_automation.domain.exceptions import (
    SavedProfileConflictError,
    SavedProfileNotFoundError,
)
from browser_automation.domain.zalo_launcher import DEFAULT_ZALO_URL, SavedProfileLibrary, WindowPlacement


class FakeChromeDiscovery:
    def __init__(self, executable_path: Path | None = None, user_data_dir: Path | None = None) -> None:
        self.executable_path = executable_path
        self.user_data_dir = user_data_dir

    def discover_executable(self) -> Path | None:
        return self.executable_path

    def discover_user_data_dir(self) -> Path | None:
        return self.user_data_dir


class InMemorySavedProfileLibraryStore:
    def __init__(self) -> None:
        self.library = SavedProfileLibrary()

    def load(self) -> SavedProfileLibrary:
        return self.library

    def save(self, library: SavedProfileLibrary) -> None:
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
        self.wait_requests: list[tuple[set[int], float]] = []
        self.tiled_handles: list[int] = []
        self.tiled_columns: int | None = None
        self.tiled_rows: int | None = None
        self.applied_window_placements: list[tuple[int, WindowPlacement]] = []

    def snapshot_window_handles(self) -> frozenset[int]:
        return frozenset(self.initial_handles)

    def calculate_grid_placements(self, *, count: int, columns: int, rows: int) -> tuple[WindowPlacement, ...]:
        if self.placements:
            return self.placements[:count]
        return tuple(
            WindowPlacement(
                left=index * 100,
                top=index * 10,
                width=400,
                height=500,
            )
            for index in range(count)
        )

    def wait_for_new_window(self, existing_window_handles, timeout_seconds: float) -> int | None:
        self.wait_requests.append((set(existing_window_handles), timeout_seconds))
        if not self.new_handles:
            return None
        return self.new_handles.pop(0)

    def apply_window_placement(self, window_handle: int, placement: WindowPlacement) -> None:
        self.applied_window_placements.append((window_handle, placement))

    def tile_windows(self, window_handles, *, columns: int, rows: int) -> int:
        self.tiled_handles = list(window_handles)
        self.tiled_columns = columns
        self.tiled_rows = rows
        return len(window_handles)


def test_manager_use_case_creates_and_updates_saved_profiles(tmp_path) -> None:
    chrome_executable = tmp_path / "chrome.exe"
    chrome_executable.write_text("", encoding="utf-8")
    work_profile_path = tmp_path / "User Data" / "Profile 1"
    work_profile_path.mkdir(parents=True)
    sales_profile_path = tmp_path / "User Data" / "Profile 9"
    sales_profile_path.mkdir(parents=True)

    store = InMemorySavedProfileLibraryStore()
    use_case = ZaloProfileManagerUseCase(
        library_store=store,
        chrome_discovery=FakeChromeDiscovery(executable_path=chrome_executable),
        chrome_launcher=FakeChromeLauncher(),
    )

    created_state = use_case.save_profile(
        SavedProfileUpsertRequest(
            name="Work",
            chrome_executable=str(chrome_executable),
            profile_path=str(work_profile_path),
        )
    )
    created_profile = created_state.profiles[0]

    updated_state = use_case.save_profile(
        SavedProfileUpsertRequest(
            profile_id=created_profile.id,
            name="Work Updated",
            chrome_executable=str(chrome_executable),
            profile_path=str(sales_profile_path),
        )
    )

    assert len(updated_state.profiles) == 1
    updated_profile = updated_state.profiles[0]
    assert updated_profile.id == created_profile.id
    assert updated_profile.name == "Work Updated"
    assert updated_profile.profile_path == str(sales_profile_path.resolve(strict=False))
    assert updated_state.selected_profile_id == updated_profile.id


def test_manager_use_case_rejects_duplicate_profile_names(tmp_path) -> None:
    chrome_executable = tmp_path / "chrome.exe"
    chrome_executable.write_text("", encoding="utf-8")
    profile_one = tmp_path / "User Data" / "Profile 1"
    profile_two = tmp_path / "User Data" / "Profile 2"
    profile_one.mkdir(parents=True)
    profile_two.mkdir(parents=True)

    store = InMemorySavedProfileLibraryStore()
    use_case = ZaloProfileManagerUseCase(
        library_store=store,
        chrome_discovery=FakeChromeDiscovery(executable_path=chrome_executable),
        chrome_launcher=FakeChromeLauncher(),
    )

    use_case.save_profile(
        SavedProfileUpsertRequest(
            name="Work",
            chrome_executable=str(chrome_executable),
            profile_path=str(profile_one),
        )
    )

    with pytest.raises(SavedProfileConflictError, match="already exists"):
        use_case.save_profile(
            SavedProfileUpsertRequest(
                name="work",
                chrome_executable=str(chrome_executable),
                profile_path=str(profile_two),
            )
        )


def test_manager_use_case_rejects_duplicate_profile_paths(tmp_path) -> None:
    chrome_executable = tmp_path / "chrome.exe"
    chrome_executable.write_text("", encoding="utf-8")
    profile_one = tmp_path / "User Data" / "Profile 1"
    profile_two = tmp_path / "User Data" / "Profile 2"
    profile_one.mkdir(parents=True)
    profile_two.mkdir(parents=True)

    store = InMemorySavedProfileLibraryStore()
    use_case = ZaloProfileManagerUseCase(
        library_store=store,
        chrome_discovery=FakeChromeDiscovery(executable_path=chrome_executable),
        chrome_launcher=FakeChromeLauncher(),
    )

    use_case.save_profile(
        SavedProfileUpsertRequest(
            name="Work",
            chrome_executable=str(chrome_executable),
            profile_path=str(profile_one),
        )
    )

    with pytest.raises(SavedProfileConflictError, match="different Chrome profile path"):
        use_case.save_profile(
            SavedProfileUpsertRequest(
                name="Sales",
                chrome_executable=str(chrome_executable),
                profile_path=str(profile_one),
            )
        )

    use_case.save_profile(
        SavedProfileUpsertRequest(
            name="Sales",
            chrome_executable=str(chrome_executable),
            profile_path=str(profile_two),
        )
    )


def test_manager_use_case_launches_selected_profile_and_builds_launch_config(tmp_path) -> None:
    chrome_executable = tmp_path / "chrome.exe"
    chrome_executable.write_text("", encoding="utf-8")
    work_profile = tmp_path / "User Data" / "Profile 1"
    sales_profile = tmp_path / "User Data" / "Profile 2"
    work_profile.mkdir(parents=True)
    sales_profile.mkdir(parents=True)

    store = InMemorySavedProfileLibraryStore()
    launcher = FakeChromeLauncher()
    window_arranger = FakeChromeWindowArranger(new_handles=(801,))
    use_case = ZaloProfileManagerUseCase(
        library_store=store,
        chrome_discovery=FakeChromeDiscovery(executable_path=chrome_executable),
        chrome_launcher=launcher,
        chrome_window_arranger=window_arranger,
    )

    first_state = use_case.save_profile(
        SavedProfileUpsertRequest(
            name="Work",
            chrome_executable=str(chrome_executable),
            profile_path=str(work_profile),
        )
    )
    second_state = use_case.save_profile(
        SavedProfileUpsertRequest(
            name="Sales",
            chrome_executable=str(chrome_executable),
            profile_path=str(sales_profile),
        )
    )

    first_profile_id = first_state.profiles[0].id
    launch_result = use_case.launch_profile(first_profile_id)

    assert launch_result.profile_id == first_profile_id
    assert launch_result.profile_name == "Work"
    assert launch_result.launch_result.target_url == DEFAULT_ZALO_URL
    assert store.library.selected_profile_id == first_profile_id
    assert launcher.launched_config is not None
    assert launcher.launched_config.user_data_dir == work_profile.parent
    assert launcher.launched_config.profile_directory == "Profile 1"
    assert launcher.launched_config.new_window is True
    assert launcher.launched_config.window_placement == WindowPlacement(
        left=0,
        top=0,
        width=400,
        height=500,
    )
    assert window_arranger.applied_window_placements == [
        (801, WindowPlacement(left=0, top=0, width=400, height=500))
    ]
    assert second_state.selected_profile_id != first_profile_id


def test_manager_use_case_launches_next_single_profile_beside_existing_window(tmp_path) -> None:
    chrome_executable = tmp_path / "chrome.exe"
    chrome_executable.write_text("", encoding="utf-8")
    work_profile = tmp_path / "User Data" / "Profile 1"
    work_profile.mkdir(parents=True)

    store = InMemorySavedProfileLibraryStore()
    launcher = FakeChromeLauncher()
    window_arranger = FakeChromeWindowArranger(
        initial_handles=(901,),
        new_handles=(902,),
        placements=(
            WindowPlacement(left=0, top=0, width=300, height=400),
            WindowPlacement(left=300, top=0, width=300, height=400),
        ),
    )
    use_case = ZaloProfileManagerUseCase(
        library_store=store,
        chrome_discovery=FakeChromeDiscovery(executable_path=chrome_executable),
        chrome_launcher=launcher,
        chrome_window_arranger=window_arranger,
    )

    state = use_case.save_profile(
        SavedProfileUpsertRequest(
            name="Work",
            chrome_executable=str(chrome_executable),
            profile_path=str(work_profile),
        )
    )

    result = use_case.launch_profile(state.selected_profile_id)

    assert result.launch_result.window_placement == WindowPlacement(
        left=300,
        top=0,
        width=300,
        height=400,
    )
    assert launcher.launched_config.window_placement == WindowPlacement(
        left=300,
        top=0,
        width=300,
        height=400,
    )
    assert window_arranger.applied_window_placements == [
        (902, WindowPlacement(left=300, top=0, width=300, height=400))
    ]


def test_manager_use_case_deletes_profile_and_updates_selection(tmp_path) -> None:
    chrome_executable = tmp_path / "chrome.exe"
    chrome_executable.write_text("", encoding="utf-8")
    work_profile = tmp_path / "User Data" / "Profile 1"
    sales_profile = tmp_path / "User Data" / "Profile 2"
    work_profile.mkdir(parents=True)
    sales_profile.mkdir(parents=True)

    store = InMemorySavedProfileLibraryStore()
    use_case = ZaloProfileManagerUseCase(
        library_store=store,
        chrome_discovery=FakeChromeDiscovery(executable_path=chrome_executable),
        chrome_launcher=FakeChromeLauncher(),
    )

    first_state = use_case.save_profile(
        SavedProfileUpsertRequest(
            name="Work",
            chrome_executable=str(chrome_executable),
            profile_path=str(work_profile),
        )
    )
    second_state = use_case.save_profile(
        SavedProfileUpsertRequest(
            name="Sales",
            chrome_executable=str(chrome_executable),
            profile_path=str(sales_profile),
        )
    )

    remaining_state = use_case.delete_profile(second_state.selected_profile_id)

    assert len(remaining_state.profiles) == 1
    assert remaining_state.profiles[0].name == "Work"
    assert remaining_state.selected_profile_id == first_state.selected_profile_id

    with pytest.raises(SavedProfileNotFoundError):
        use_case.delete_profile("missing-profile")


def test_manager_use_case_launches_multiple_profiles_in_requested_grid_order(tmp_path) -> None:
    chrome_executable = tmp_path / "chrome.exe"
    chrome_executable.write_text("", encoding="utf-8")
    first_profile = tmp_path / "User Data" / "Profile 1"
    second_profile = tmp_path / "User Data" / "Profile 2"
    third_profile = tmp_path / "User Data" / "Profile 3"
    first_profile.mkdir(parents=True)
    second_profile.mkdir(parents=True)
    third_profile.mkdir(parents=True)

    store = InMemorySavedProfileLibraryStore()
    launcher = FakeChromeLauncher()
    window_arranger = FakeChromeWindowArranger(
        initial_handles=(500,),
        new_handles=(601, 602, 603),
        placements=(
            WindowPlacement(left=10, top=20, width=300, height=400),
            WindowPlacement(left=310, top=20, width=300, height=400),
            WindowPlacement(left=610, top=20, width=300, height=400),
        ),
    )
    use_case = ZaloProfileManagerUseCase(
        library_store=store,
        chrome_discovery=FakeChromeDiscovery(executable_path=chrome_executable),
        chrome_launcher=launcher,
        chrome_window_arranger=window_arranger,
    )

    work_state = use_case.save_profile(
        SavedProfileUpsertRequest(
            name="Work",
            chrome_executable=str(chrome_executable),
            profile_path=str(first_profile),
        )
    )
    sales_state = use_case.save_profile(
        SavedProfileUpsertRequest(
            name="Sales",
            chrome_executable=str(chrome_executable),
            profile_path=str(second_profile),
        )
    )
    support_state = use_case.save_profile(
        SavedProfileUpsertRequest(
            name="Support",
            chrome_executable=str(chrome_executable),
            profile_path=str(third_profile),
        )
    )

    requested_profile_ids = [
        support_state.selected_profile_id,
        work_state.selected_profile_id,
        sales_state.selected_profile_id,
    ]
    result = use_case.launch_profiles_grid(requested_profile_ids)

    assert [profile.profile_id for profile in result.profiles] == requested_profile_ids
    assert [profile.profile_name for profile in result.profiles] == ["Support", "Work", "Sales"]
    assert [config.profile_directory for config in launcher.launched_configs] == [
        "Profile 3",
        "Profile 1",
        "Profile 2",
    ]
    assert [config.window_placement for config in launcher.launched_configs] == [
        WindowPlacement(left=10, top=20, width=300, height=400),
        WindowPlacement(left=310, top=20, width=300, height=400),
        WindowPlacement(left=610, top=20, width=300, height=400),
    ]
    assert window_arranger.tiled_handles == [601, 602, 603]
    assert window_arranger.tiled_columns == 4
    assert window_arranger.tiled_rows == 2
    assert result.tiled_window_count == 3
    assert result.omitted_profile_count == 0
    assert store.library.selected_profile_id == requested_profile_ids[0]
    assert result.profiles[0].launch_result.window_placement == WindowPlacement(
        left=10,
        top=20,
        width=300,
        height=400,
    )


def test_manager_use_case_caps_grid_launch_to_first_eight_profiles(tmp_path) -> None:
    chrome_executable = tmp_path / "chrome.exe"
    chrome_executable.write_text("", encoding="utf-8")

    store = InMemorySavedProfileLibraryStore()
    launcher = FakeChromeLauncher()
    window_arranger = FakeChromeWindowArranger(
        new_handles=(701, 702, 703, 704, 705, 706, 707, 708),
    )
    use_case = ZaloProfileManagerUseCase(
        library_store=store,
        chrome_discovery=FakeChromeDiscovery(executable_path=chrome_executable),
        chrome_launcher=launcher,
        chrome_window_arranger=window_arranger,
    )

    selected_profile_ids: list[str] = []
    for index in range(1, 11):
        profile_path = tmp_path / "User Data" / f"Profile {index}"
        profile_path.mkdir(parents=True, exist_ok=True)
        state = use_case.save_profile(
            SavedProfileUpsertRequest(
                name=f"Profile {index}",
                chrome_executable=str(chrome_executable),
                profile_path=str(profile_path),
            )
        )
        selected_profile_ids.append(state.selected_profile_id)

    result = use_case.launch_profiles_grid(selected_profile_ids)

    assert len(result.profiles) == 8
    assert result.omitted_profile_count == 2
    assert len(launcher.launched_configs) == 8
    assert [config.profile_directory for config in launcher.launched_configs] == [
        f"Profile {index}" for index in range(1, 9)
    ]
    assert launcher.launched_configs[0].window_placement == WindowPlacement(
        left=0,
        top=0,
        width=400,
        height=500,
    )
    assert window_arranger.tiled_handles == [701, 702, 703, 704, 705, 706, 707, 708]
    assert result.tiled_window_count == 8
