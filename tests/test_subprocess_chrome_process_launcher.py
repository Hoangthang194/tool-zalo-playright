from pathlib import Path

import pytest

from browser_automation.domain.exceptions import ChromeLaunchError
from browser_automation.domain.zalo_launcher import ChromeLaunchConfig, WindowPlacement
from browser_automation.infrastructure.chrome_launcher import (
    subprocess_chrome_process_launcher as launcher_module,
)
from browser_automation.infrastructure.chrome_launcher.subprocess_chrome_process_launcher import (
    SubprocessChromeProcessLauncher,
)


def test_subprocess_chrome_process_launcher_builds_expected_command() -> None:
    launcher = SubprocessChromeProcessLauncher()
    config = ChromeLaunchConfig(
        chrome_executable=Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        user_data_dir=Path(r"C:\ChromeProfiles\sales"),
    )

    assert launcher.build_command(config) == [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "--new-window",
        r"--user-data-dir=C:\ChromeProfiles\sales",
        "https://chat.zalo.me",
    ]


def test_subprocess_chrome_process_launcher_builds_legacy_profile_directory_command() -> None:
    launcher = SubprocessChromeProcessLauncher()
    config = ChromeLaunchConfig(
        chrome_executable=Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        user_data_dir=Path(r"C:\Users\demo\AppData\Local\Google\Chrome\User Data"),
        profile_directory="Profile 1",
    )

    assert launcher.build_command(config) == [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "--new-window",
        r"--user-data-dir=C:\Users\demo\AppData\Local\Google\Chrome\User Data",
        "--profile-directory=Profile 1",
        "https://chat.zalo.me",
    ]


def test_subprocess_chrome_process_launcher_includes_window_size_and_position() -> None:
    launcher = SubprocessChromeProcessLauncher()
    config = ChromeLaunchConfig(
        chrome_executable=Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        user_data_dir=Path(r"C:\Users\demo\AppData\Local\Google\Chrome\User Data"),
        profile_directory="Profile 2",
        window_placement=WindowPlacement(left=12, top=34, width=456, height=789),
    )

    assert launcher.build_command(config) == [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "--new-window",
        "--window-position=12,34",
        "--window-size=456,789",
        r"--user-data-dir=C:\Users\demo\AppData\Local\Google\Chrome\User Data",
        "--profile-directory=Profile 2",
        "https://chat.zalo.me",
    ]


def test_subprocess_chrome_process_launcher_includes_proxy_server() -> None:
    launcher = SubprocessChromeProcessLauncher()
    config = ChromeLaunchConfig(
        chrome_executable=Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        user_data_dir=Path(r"C:\Users\demo\AppData\Local\Google\Chrome\User Data"),
        profile_directory="Profile 3",
        proxy_server="127.0.0.1:8080",
    )

    assert launcher.build_command(config) == [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "--new-window",
        "--proxy-server=127.0.0.1:8080",
        r"--user-data-dir=C:\Users\demo\AppData\Local\Google\Chrome\User Data",
        "--profile-directory=Profile 3",
        "https://chat.zalo.me",
    ]


def test_subprocess_chrome_process_launcher_builds_headless_command() -> None:
    launcher = SubprocessChromeProcessLauncher()
    config = ChromeLaunchConfig(
        chrome_executable=Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        user_data_dir=Path(r"C:\Users\demo\AppData\Local\Google\Chrome\User Data"),
        profile_directory="Profile 4",
        headless=True,
        proxy_server="127.0.0.1:8080",
    )

    assert launcher.build_command(config) == [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "--headless=new",
        "--disable-gpu",
        "--proxy-server=127.0.0.1:8080",
        r"--user-data-dir=C:\Users\demo\AppData\Local\Google\Chrome\User Data",
        "--profile-directory=Profile 4",
        "https://chat.zalo.me",
    ]


def test_subprocess_chrome_process_launcher_wraps_os_errors(monkeypatch) -> None:
    launcher = SubprocessChromeProcessLauncher()
    config = ChromeLaunchConfig(
        chrome_executable=Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        user_data_dir=Path(r"C:\ChromeProfiles\work"),
    )

    def fake_popen(**_kwargs):
        raise OSError("boom")

    monkeypatch.setattr(launcher_module.subprocess, "Popen", fake_popen)

    with pytest.raises(ChromeLaunchError, match="Could not start Google Chrome"):
        launcher.launch(config)
