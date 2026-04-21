import pytest

from browser_automation.application.use_cases.launch_zalo_chat import (
    LaunchZaloChatRequest,
    LaunchZaloChatUseCase,
)
from browser_automation.domain.exceptions import LauncherValidationError, SettingsPersistenceError
from browser_automation.domain.zalo_launcher import DEFAULT_ZALO_URL, LauncherSettings


class FakeChromeDiscovery:
    def __init__(self, executable_path=None, user_data_dir=None) -> None:
        self.executable_path = executable_path
        self.user_data_dir = user_data_dir

    def discover_executable(self):
        return self.executable_path

    def discover_user_data_dir(self):
        return self.user_data_dir


class FakeChromeLauncher:
    def __init__(self) -> None:
        self.launched_config = None

    def launch(self, config) -> None:
        self.launched_config = config


class FakeSettingsStore:
    def __init__(self, loaded_settings=None, fail_on_save: bool = False) -> None:
        self.loaded_settings = loaded_settings or LauncherSettings()
        self.fail_on_save = fail_on_save
        self.saved_settings = None

    def load(self) -> LauncherSettings:
        return self.loaded_settings

    def save(self, settings: LauncherSettings) -> None:
        if self.fail_on_save:
            raise SettingsPersistenceError("save failed")
        self.saved_settings = settings


def test_zalo_use_case_loads_saved_form_state_before_discovery(tmp_path) -> None:
    saved_executable = tmp_path / "saved-chrome.exe"
    saved_user_data = tmp_path / "Saved User Data"

    use_case = LaunchZaloChatUseCase(
        chrome_discovery=FakeChromeDiscovery(),
        chrome_launcher=FakeChromeLauncher(),
        settings_store=FakeSettingsStore(
            loaded_settings=LauncherSettings(
                chrome_executable=str(saved_executable),
                user_data_dir=str(saved_user_data),
                profile_directory="Profile 7",
            )
        ),
    )

    form_state = use_case.load_form_state()

    assert form_state.chrome_executable == str(saved_executable)
    assert form_state.user_data_dir == str(saved_user_data)
    assert form_state.profile_directory == "Profile 7"
    assert form_state.target_url == DEFAULT_ZALO_URL


def test_zalo_use_case_executes_with_discovered_paths_and_saves_settings(tmp_path) -> None:
    chrome_executable = tmp_path / "chrome.exe"
    chrome_executable.write_text("", encoding="utf-8")
    user_data_dir = tmp_path / "User Data"
    profile_directory = user_data_dir / "Profile 1"
    profile_directory.mkdir(parents=True)

    launcher = FakeChromeLauncher()
    settings_store = FakeSettingsStore()
    use_case = LaunchZaloChatUseCase(
        chrome_discovery=FakeChromeDiscovery(
            executable_path=chrome_executable,
            user_data_dir=user_data_dir,
        ),
        chrome_launcher=launcher,
        settings_store=settings_store,
    )

    result = use_case.execute(
        LaunchZaloChatRequest(
            chrome_executable="",
            user_data_dir="",
            profile_directory="Profile 1",
        )
    )

    assert launcher.launched_config is not None
    assert launcher.launched_config.chrome_executable == chrome_executable
    assert launcher.launched_config.user_data_dir == user_data_dir
    assert launcher.launched_config.profile_directory == "Profile 1"
    assert launcher.launched_config.target_url == DEFAULT_ZALO_URL
    assert settings_store.saved_settings == LauncherSettings(
        chrome_executable=str(chrome_executable),
        user_data_dir=str(user_data_dir),
        profile_directory="Profile 1",
    )
    assert result.chrome_executable == chrome_executable
    assert result.settings_persisted is True


def test_zalo_use_case_rejects_missing_profile_directory(tmp_path) -> None:
    chrome_executable = tmp_path / "chrome.exe"
    chrome_executable.write_text("", encoding="utf-8")
    user_data_dir = tmp_path / "User Data"
    user_data_dir.mkdir()

    launcher = FakeChromeLauncher()
    use_case = LaunchZaloChatUseCase(
        chrome_discovery=FakeChromeDiscovery(
            executable_path=chrome_executable,
            user_data_dir=user_data_dir,
        ),
        chrome_launcher=launcher,
        settings_store=FakeSettingsStore(),
    )

    with pytest.raises(LauncherValidationError, match="Chrome profile directory not found"):
        use_case.execute(
            LaunchZaloChatRequest(
                chrome_executable=str(chrome_executable),
                user_data_dir=str(user_data_dir),
                profile_directory="Profile 404",
            )
        )

    assert launcher.launched_config is None


def test_zalo_use_case_reports_launch_success_even_if_settings_save_fails(tmp_path) -> None:
    chrome_executable = tmp_path / "chrome.exe"
    chrome_executable.write_text("", encoding="utf-8")
    user_data_dir = tmp_path / "User Data"
    profile_directory = user_data_dir / "Default"
    profile_directory.mkdir(parents=True)

    use_case = LaunchZaloChatUseCase(
        chrome_discovery=FakeChromeDiscovery(
            executable_path=chrome_executable,
            user_data_dir=user_data_dir,
        ),
        chrome_launcher=FakeChromeLauncher(),
        settings_store=FakeSettingsStore(fail_on_save=True),
    )

    result = use_case.execute(
        LaunchZaloChatRequest(
            chrome_executable=str(chrome_executable),
            user_data_dir=str(user_data_dir),
            profile_directory="Default",
        )
    )

    assert result.settings_persisted is False
