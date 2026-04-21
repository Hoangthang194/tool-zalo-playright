from browser_automation.domain.zalo_launcher import (
    DEFAULT_ZALO_URL,
    LauncherSettings,
    SavedChromeProfile,
    SavedProfileLibrary,
)
from browser_automation.infrastructure.chrome_launcher.json_launcher_settings_store import (
    JsonLauncherSettingsStore,
)
from browser_automation.infrastructure.chrome_launcher.json_saved_profile_library_store import (
    JsonSavedProfileLibraryStore,
)


def test_saved_profile_library_store_round_trips_profiles(tmp_path) -> None:
    store = JsonSavedProfileLibraryStore(path=tmp_path / "zalo-profiles.json")
    library = SavedProfileLibrary(
        profiles=(
            SavedChromeProfile(
                id="profile-1",
                name="Work",
                chrome_executable=r"C:\Chrome\chrome.exe",
                profile_path=r"C:\Users\demo\AppData\Local\Google\Chrome\User Data\Profile 1",
            ),
            SavedChromeProfile(
                id="profile-2",
                name="Sales",
                chrome_executable=r"C:\Chrome\chrome.exe",
                profile_path=r"C:\Users\demo\AppData\Local\Google\Chrome\User Data\Profile 2",
            ),
        ),
        selected_profile_id="profile-2",
    )

    store.save(library)
    loaded_library = store.load()

    assert loaded_library == library


def test_saved_profile_library_store_migrates_legacy_single_profile_settings(tmp_path) -> None:
    legacy_store = JsonLauncherSettingsStore(path=tmp_path / "zalo-launcher.json")
    legacy_store.save(
        LauncherSettings(
            chrome_executable=r"C:\Chrome\chrome.exe",
            user_data_dir=r"C:\Users\demo\AppData\Local\Google\Chrome\User Data",
            profile_directory="Default",
        )
    )
    store = JsonSavedProfileLibraryStore(
        path=tmp_path / "zalo-profiles.json",
        legacy_settings_store=legacy_store,
    )

    loaded_library = store.load()

    assert len(loaded_library.profiles) == 1
    migrated_profile = loaded_library.profiles[0]
    assert migrated_profile.name == "Imported Default"
    assert migrated_profile.chrome_executable == r"C:\Chrome\chrome.exe"
    assert (
        migrated_profile.profile_path
        == r"C:\Users\demo\AppData\Local\Google\Chrome\User Data\Default"
    )
    assert migrated_profile.target_url == DEFAULT_ZALO_URL
    assert loaded_library.selected_profile_id == migrated_profile.id
