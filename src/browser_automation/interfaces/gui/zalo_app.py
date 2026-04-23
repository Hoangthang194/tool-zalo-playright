from __future__ import annotations

import threading
import tkinter as tk
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from browser_automation.application.use_cases.launch_zalo_account import (
    LaunchSavedZaloAccountResult,
    LaunchZaloAccountUseCase,
)
from browser_automation.application.use_cases.click_zalo_element import (
    DEFAULT_CLICK_ELEMENT_TIMEOUT_SECONDS,
    ClickZaloElementRequest,
    ClickZaloElementResult,
    ClickZaloElementUseCase,
)
from browser_automation.application.use_cases._click_target_support import (
    looks_like_html_snippet,
)
from browser_automation.application.use_cases.manage_zalo_click_targets import (
    ZaloClickTargetManagerState,
    ZaloClickTargetManagerUseCase,
    ZaloClickTargetUpsertRequest,
)
from browser_automation.application.use_cases.test_proxy_connection import (
    TestProxyConnectionRequest,
    TestProxyConnectionResult,
    TestProxyConnectionUseCase,
)
from browser_automation.application.use_cases.manage_zalo_profiles import (
    SavedProfileUpsertRequest,
    ZaloProfileManagerState,
    ZaloProfileManagerUseCase,
)
from browser_automation.application.use_cases.manage_zalo_workspace import (
    ZaloAccountUpsertRequest,
    ZaloWorkspaceManagerUseCase,
    ZaloWorkspaceState,
)
from browser_automation.domain.exceptions import (
    BrowserAutomationError,
    ChromeLaunchError,
    LauncherValidationError,
    ProxyConnectionError,
    SavedProfileConflictError,
    SavedProfileNotFoundError,
    SavedZaloAccountConflictError,
    SavedZaloAccountNotFoundError,
    SettingsPersistenceError,
    ZaloClickAutomationError,
    ZaloClickTargetConflictError,
    ZaloClickTargetNotFoundError,
)
from browser_automation.domain.zalo_launcher import DEFAULT_ZALO_URL, SavedChromeProfile
from browser_automation.domain.zalo_workspace import SavedZaloAccount, SavedZaloClickTarget
from browser_automation.infrastructure.chrome_launcher.chrome_installation_discovery import (
    DefaultChromeInstallationDiscovery,
)
from browser_automation.infrastructure.chrome_launcher.json_saved_profile_library_store import (
    JsonSavedProfileLibraryStore,
)
from browser_automation.infrastructure.chrome_launcher.json_zalo_workspace_store import (
    JsonZaloWorkspaceStore,
)
from browser_automation.infrastructure.chrome_launcher.subprocess_chrome_process_launcher import (
    SubprocessChromeProcessLauncher,
)
from browser_automation.infrastructure.playwright_adapter.playwright_zalo_click_automation_runner import (
    PlaywrightZaloClickAutomationRunner,
)
from browser_automation.infrastructure.network.urllib_proxy_connectivity_checker import (
    UrllibProxyConnectivityChecker,
)
from browser_automation.interfaces.gui.ui_components import (
    SharedGuiFactory,
    SharedGuiTheme,
)
from browser_automation.infrastructure.chrome_launcher.windows_chrome_window_arranger import (
    WindowsChromeWindowArranger,
)


@dataclass(frozen=True, slots=True)
class ZaloGuiConfig(SharedGuiTheme):
    title: str = "Zalo Chrome Profile Manager"
    width: int = 1180
    height: int = 760


class ZaloLauncherGui:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.config = ZaloGuiConfig()
        self.ui = SharedGuiFactory(root, self.config)
        self.discovery = DefaultChromeInstallationDiscovery()
        self.library_store = JsonSavedProfileLibraryStore()
        self.workspace_store = JsonZaloWorkspaceStore()
        self.chrome_launcher = SubprocessChromeProcessLauncher()
        self.window_arranger = WindowsChromeWindowArranger()
        self.click_automation_runner = PlaywrightZaloClickAutomationRunner()
        self.use_case = ZaloProfileManagerUseCase(
            library_store=self.library_store,
            chrome_discovery=self.discovery,
            chrome_launcher=self.chrome_launcher,
            chrome_window_arranger=self.window_arranger,
        )
        self.workspace_use_case = ZaloWorkspaceManagerUseCase(self.workspace_store)
        self.click_target_use_case = ZaloClickTargetManagerUseCase(self.workspace_store)
        self.account_launch_use_case = LaunchZaloAccountUseCase(
            workspace_store=self.workspace_store,
            library_store=self.library_store,
            chrome_discovery=self.discovery,
            chrome_launcher=self.chrome_launcher,
            chrome_window_arranger=self.window_arranger,
            click_automation_runner=self.click_automation_runner,
        )
        self.click_element_use_case = ClickZaloElementUseCase(self.click_automation_runner)
        self.proxy_test_use_case = TestProxyConnectionUseCase(
            proxy_checker=UrllibProxyConnectivityChecker(),
        )

        self._launch_in_progress = False
        self._proxy_test_in_progress = False
        self._click_target_test_in_progress = False
        self._click_target_test_was_image_mode = False
        self._is_refreshing_list = False
        self._is_refreshing_account_list = False
        self._is_refreshing_click_target_list = False

        self._current_edit_profile_id: str | None = None
        self._profile_ids: list[str] = []
        self._profiles_by_id: dict[str, SavedChromeProfile] = {}
        self._state: ZaloProfileManagerState | None = None

        self._current_edit_account_id: str | None = None
        self._account_ids: list[str] = []
        self._accounts_by_id: dict[str, SavedZaloAccount] = {}
        self._workspace_state: ZaloWorkspaceState | None = None

        self._current_edit_click_target_id: str | None = None
        self._click_target_ids: list[str] = []
        self._click_targets_by_id: dict[str, SavedZaloClickTarget] = {}
        self._click_target_state: ZaloClickTargetManagerState | None = None
        self._last_account_remote_debugging_port: int | None = None
        self._last_account_target_url: str = DEFAULT_ZALO_URL

        self._profile_name_to_id: dict[str, str] = {}

        self.profile_name_var = tk.StringVar()
        self.chrome_path_var = tk.StringVar()
        self.profile_path_var = tk.StringVar()
        self.target_url_var = tk.StringVar(value=DEFAULT_ZALO_URL)
        self.status_var = tk.StringVar(
            value="Profiles stores reusable Chrome profile definitions. Launch Chrome from the Zalo Accounts tab."
        )

        self.account_profile_choice_var = tk.StringVar()
        self.account_proxy_var = tk.StringVar()
        self.account_status_var = tk.StringVar(
            value="Select a saved Zalo account to launch Chrome with its linked profile and proxy."
        )

        self.click_target_name_var = tk.StringVar()
        self.click_target_selector_kind_var = tk.StringVar(value="class")
        self.click_target_is_image_var = tk.BooleanVar(value=False)
        self.click_target_selector_value_var = tk.StringVar()
        self.click_target_upload_file_path_var = tk.StringVar()
        self.click_target_status_var = tk.StringVar(
            value="Manage saved selectors and optionally attach an upload file path for manual Test Element actions."
        )

        self.account_profile_combobox: ttk.Combobox | None = None
        self.click_target_selector_kind_combobox: ttk.Combobox | None = None
        self.click_target_is_image_checkbox: tk.Checkbutton | None = None
        self.click_target_upload_file_label: tk.Label | None = None
        self.click_target_upload_file_entry: tk.Entry | None = None
        self.click_target_upload_file_button: tk.Button | None = None
        self.click_target_hint_label: tk.Label | None = None

        self._setup_window()
        self._create_widgets()
        self.click_target_selector_kind_var.trace_add("write", self._on_click_target_selector_kind_changed)
        self.click_target_is_image_var.trace_add("write", self._on_click_target_selector_kind_changed)
        self._refresh_state()
        self._refresh_workspace_state()
        self._refresh_click_target_state()

    def _setup_window(self) -> None:
        self.ui.configure_window(
            self.root,
            title=self.config.title,
            width=self.config.width,
            height=self.config.height,
            min_width=1040,
            min_height=680,
        )

    def _create_widgets(self) -> None:
        self.ui.create_header(
            self.root,
            title=self.config.title,
            subtitle=(
                "Profiles stores reusable Chrome profile definitions. "
                "Zalo Accounts combines one linked profile with one proxy and launches Chrome from that tab. "
                "Class Manage stores selectors for manual Test Element actions after launch."
            ),
            wraplength=1040,
        )

        content_frame = self.ui.create_content_frame(self.root)

        self.notebook = ttk.Notebook(content_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        profile_tab = tk.Frame(self.notebook, bg=self.config.bg_color)
        accounts_tab = tk.Frame(self.notebook, bg=self.config.bg_color)
        click_targets_tab = tk.Frame(self.notebook, bg=self.config.bg_color)

        self.notebook.add(profile_tab, text="Profiles")
        self.notebook.add(accounts_tab, text="Zalo Accounts")
        self.notebook.add(click_targets_tab, text="Class Manage")

        self._create_profile_tab(profile_tab)
        self._create_accounts_tab(accounts_tab)
        self._create_click_targets_tab(click_targets_tab)

    def _create_profile_tab(self, parent: tk.Frame) -> None:
        parent.grid_columnconfigure(1, weight=1)
        parent.grid_rowconfigure(0, weight=1)

        library_frame = self._create_panel(parent)
        library_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 18))
        library_frame.grid_rowconfigure(3, weight=1)
        library_frame.grid_columnconfigure(0, weight=1)

        self.ui.create_section_label(library_frame, "Saved Profiles").grid(row=0, column=0, sticky="w")
        self.ui.create_muted_label(
            library_frame,
            "One saved item equals one Chrome profile folder.",
            wraplength=280,
        ).grid(row=1, column=0, sticky="w", pady=(4, 12))
        self.ui.create_muted_label(
            library_frame,
            "Use these saved profiles inside the Zalo Accounts tab, where launch also applies the account proxy.",
            wraplength=280,
        ).grid(row=2, column=0, sticky="w", pady=(0, 12))

        list_frame = tk.Frame(library_frame, bg=self.config.panel_color)
        list_frame.grid(row=3, column=0, sticky="nsew")
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        self.profile_listbox = self.ui.create_listbox(
            list_frame,
            select_background="#c7f9ed",
        )
        self.profile_listbox.grid(row=0, column=0, sticky="nsew")
        self.profile_listbox.bind("<<ListboxSelect>>", self._on_profile_selected)

        profile_scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.profile_listbox.yview)
        profile_scrollbar.grid(row=0, column=1, sticky="ns")
        self.profile_listbox.configure(yscrollcommand=profile_scrollbar.set)

        library_actions = tk.Frame(library_frame, bg=self.config.panel_color)
        library_actions.grid(row=4, column=0, sticky="ew", pady=(14, 0))
        library_actions.grid_columnconfigure(0, weight=1)
        library_actions.grid_columnconfigure(1, weight=1)

        self.new_button = self.ui.create_button(
            library_actions,
            text="New Profile",
            command=self._start_new_profile,
            variant="secondary",
        )
        self.new_button.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.delete_button = self.ui.create_button(
            library_actions,
            text="Delete",
            command=self._delete_profile,
            variant="danger",
        )
        self.delete_button.grid(row=0, column=1, sticky="ew")

        detail_frame = self._create_panel(parent)
        detail_frame.grid(row=0, column=1, sticky="nsew")
        detail_frame.grid_columnconfigure(1, weight=1)

        self.ui.create_section_label(detail_frame, "Profile Details").grid(
            row=0, column=0, columnspan=3, sticky="w"
        )
        self.ui.create_muted_label(
            detail_frame,
            "Example profile path: C:\\Users\\ThangHoang\\AppData\\Local\\Google\\Chrome\\User Data\\Profile 1",
            wraplength=640,
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(4, 14))

        self._build_entry_row(detail_frame, 2, "Profile name", self.profile_name_var)
        self._build_path_row(
            detail_frame,
            3,
            "Chrome executable",
            self.chrome_path_var,
            "Browse",
            self._browse_chrome_executable,
        )
        self._build_path_row(
            detail_frame,
            4,
            "Chrome profile path",
            self.profile_path_var,
            "Browse",
            self._browse_profile_path,
        )
        self._build_entry_row(detail_frame, 5, "Target URL", self.target_url_var, readonly=True)

        self.ui.create_muted_label(
            detail_frame,
            "Pick the actual profile folder such as 'Default' or 'Profile 1', not the parent 'User Data' folder.",
            wraplength=620,
        ).grid(row=6, column=0, columnspan=3, sticky="w", pady=(12, 8))
        self.ui.create_muted_label(
            detail_frame,
            "This tab defines reusable Chrome profiles only. Select a saved account in the Zalo Accounts tab to launch with proxy settings.",
            wraplength=620,
        ).grid(row=7, column=0, columnspan=3, sticky="w", pady=(0, 8))

        action_frame = tk.Frame(detail_frame, bg=self.config.panel_color)
        action_frame.grid(row=8, column=0, columnspan=3, sticky="ew", pady=(14, 0))

        self.save_button = self.ui.create_button(
            action_frame,
            text="Save Profile",
            command=self._save_profile,
            variant="secondary",
            padx=16,
        )
        self.save_button.grid(row=0, column=0, sticky="w")

        self.create_profile_button = self.ui.create_button(
            action_frame,
            text="Create Folder + Save",
            command=self._create_profile,
            variant="secondary",
            padx=16,
        )
        self.create_profile_button.grid(row=0, column=1, sticky="w", padx=(10, 0))

        self.status_label = self.ui.create_status_label(
            detail_frame,
            textvariable=self.status_var,
            wraplength=620,
        )
        self.status_label.grid(row=9, column=0, columnspan=3, sticky="ew", pady=(18, 0))

        self.ui.create_code_label(
            detail_frame,
            f"Saved profile library: {self.library_store.path}",
        ).grid(row=10, column=0, columnspan=3, sticky="w", pady=(14, 0))

    def _create_accounts_tab(self, parent: tk.Frame) -> None:
        parent.grid_columnconfigure(1, weight=1)
        parent.grid_rowconfigure(0, weight=1)

        library_frame = self._create_panel(parent)
        library_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 18))
        library_frame.grid_rowconfigure(2, weight=1)
        library_frame.grid_columnconfigure(0, weight=1)

        self.ui.create_section_label(library_frame, "Saved Zalo Accounts").grid(row=0, column=0, sticky="w")
        self.ui.create_muted_label(
            library_frame,
            "Each saved item links one Chrome profile to one proxy value and is the actual launch target.",
            wraplength=280,
        ).grid(row=1, column=0, sticky="w", pady=(4, 12))

        account_list_frame = tk.Frame(library_frame, bg=self.config.panel_color)
        account_list_frame.grid(row=2, column=0, sticky="nsew")
        account_list_frame.grid_rowconfigure(0, weight=1)
        account_list_frame.grid_columnconfigure(0, weight=1)

        self.account_listbox = self.ui.create_listbox(
            account_list_frame,
            select_background="#fde68a",
        )
        self.account_listbox.grid(row=0, column=0, sticky="nsew")
        self.account_listbox.bind("<<ListboxSelect>>", self._on_account_selected)

        account_scrollbar = tk.Scrollbar(account_list_frame, orient=tk.VERTICAL, command=self.account_listbox.yview)
        account_scrollbar.grid(row=0, column=1, sticky="ns")
        self.account_listbox.configure(yscrollcommand=account_scrollbar.set)

        account_actions = tk.Frame(library_frame, bg=self.config.panel_color)
        account_actions.grid(row=3, column=0, sticky="ew", pady=(14, 0))
        account_actions.grid_columnconfigure(0, weight=1)
        account_actions.grid_columnconfigure(1, weight=1)

        self.new_account_button = self.ui.create_button(
            account_actions,
            text="New Account",
            command=self._start_new_account,
            variant="secondary",
        )
        self.new_account_button.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.delete_account_button = self.ui.create_button(
            account_actions,
            text="Delete",
            command=self._delete_account,
            variant="danger",
        )
        self.delete_account_button.grid(row=0, column=1, sticky="ew")

        detail_frame = self._create_panel(parent)
        detail_frame.grid(row=0, column=1, sticky="nsew")
        detail_frame.grid_columnconfigure(1, weight=1)

        self.ui.create_section_label(detail_frame, "Account Details").grid(
            row=0, column=0, columnspan=3, sticky="w"
        )

        self._build_combobox_row(
            detail_frame,
            1,
            "Linked profile",
            self.account_profile_choice_var,
            target_name="account_profile",
        )
        self._build_entry_row(
            detail_frame,
            2,
            "Proxy",
            self.account_proxy_var,
        )
        self.ui.create_muted_label(
            detail_frame,
            "Supported formats: host:port, user:pass@host:port, or host:port:user:pass. Leave blank to use direct access.",
            wraplength=620,
        ).grid(row=3, column=0, columnspan=3, sticky="w", pady=(4, 10))

        account_action_frame = tk.Frame(detail_frame, bg=self.config.panel_color)
        account_action_frame.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(14, 0))
        account_action_frame.grid_columnconfigure(1, weight=1)

        self.save_account_button = self.ui.create_button(
            account_action_frame,
            text="Save Account",
            command=self._save_account,
            variant="secondary",
        )
        self.save_account_button.grid(row=0, column=0, sticky="w")

        self.test_proxy_button = self.ui.create_button(
            account_action_frame,
            text="Test Proxy",
            command=self._start_proxy_test,
            variant="secondary",
        )
        self.test_proxy_button.grid(row=0, column=2, sticky="e", padx=(0, 8))

        self.launch_account_button = self.ui.create_button(
            account_action_frame,
            text="Launch Account",
            command=self._start_account_launch,
            padx=18,
            variant="primary",
        )
        self.launch_account_button.grid(row=0, column=3, sticky="e")

        self.account_status_label = self.ui.create_status_label(
            detail_frame,
            textvariable=self.account_status_var,
            wraplength=620,
        )
        self.account_status_label.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(18, 0))

        self.ui.create_code_label(
            detail_frame,
            f"Account workspace: {self.workspace_store.path}",
        ).grid(row=6, column=0, columnspan=3, sticky="w", pady=(14, 0))

    def _create_click_targets_tab(self, parent: tk.Frame) -> None:
        parent.grid_columnconfigure(1, weight=1)
        parent.grid_rowconfigure(0, weight=1)

        library_frame = self._create_panel(parent)
        library_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 18))
        library_frame.grid_rowconfigure(2, weight=1)
        library_frame.grid_columnconfigure(0, weight=1)

        self.ui.create_section_label(library_frame, "Saved Click Targets").grid(row=0, column=0, sticky="w")
        self.ui.create_muted_label(
            library_frame,
            "Saved selectors are available for manual Test Element actions after a Zalo account launches.",
            wraplength=280,
        ).grid(row=1, column=0, sticky="w", pady=(4, 12))

        click_target_list_frame = tk.Frame(library_frame, bg=self.config.panel_color)
        click_target_list_frame.grid(row=2, column=0, sticky="nsew")
        click_target_list_frame.grid_rowconfigure(0, weight=1)
        click_target_list_frame.grid_columnconfigure(0, weight=1)

        self.click_target_listbox = self.ui.create_listbox(
            click_target_list_frame,
            select_background="#dbeafe",
        )
        self.click_target_listbox.grid(row=0, column=0, sticky="nsew")
        self.click_target_listbox.bind("<<ListboxSelect>>", self._on_click_target_selected)

        click_target_scrollbar = tk.Scrollbar(
            click_target_list_frame,
            orient=tk.VERTICAL,
            command=self.click_target_listbox.yview,
        )
        click_target_scrollbar.grid(row=0, column=1, sticky="ns")
        self.click_target_listbox.configure(yscrollcommand=click_target_scrollbar.set)

        click_target_actions = tk.Frame(library_frame, bg=self.config.panel_color)
        click_target_actions.grid(row=3, column=0, sticky="ew", pady=(14, 0))
        click_target_actions.grid_columnconfigure(0, weight=1)
        click_target_actions.grid_columnconfigure(1, weight=1)

        self.new_click_target_button = self.ui.create_button(
            click_target_actions,
            text="New Target",
            command=self._start_new_click_target,
            variant="secondary",
        )
        self.new_click_target_button.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.delete_click_target_button = self.ui.create_button(
            click_target_actions,
            text="Delete",
            command=self._delete_click_target,
            variant="danger",
        )
        self.delete_click_target_button.grid(row=0, column=1, sticky="ew")

        detail_frame = self._create_panel(parent)
        detail_frame.grid(row=0, column=1, sticky="nsew")
        detail_frame.grid_columnconfigure(1, weight=1)

        self.ui.create_section_label(detail_frame, "Target Details").grid(
            row=0, column=0, columnspan=3, sticky="w"
        )

        self._build_entry_row(
            detail_frame,
            1,
            "Target name",
            self.click_target_name_var,
        )
        self._build_combobox_row(
            detail_frame,
            2,
            "Selector type",
            self.click_target_selector_kind_var,
            values=("class", "id", "data-id", "anim-data-id", "css", "html"),
            target_name="click_target_selector_kind",
        )
        self.click_target_is_image_checkbox = tk.Checkbutton(
            detail_frame,
            text="Image upload target",
            variable=self.click_target_is_image_var,
            onvalue=True,
            offvalue=False,
            bg=self.config.panel_color,
            fg=self.config.text_color,
            activebackground=self.config.panel_color,
            activeforeground=self.config.text_color,
            selectcolor=self.config.input_bg,
            font=("Segoe UI", 10),
        )
        self.click_target_is_image_checkbox.grid(row=3, column=1, sticky="w", padx=(14, 12), pady=(0, 8))
        self._build_entry_row(
            detail_frame,
            4,
            "Selector value",
            self.click_target_selector_value_var,
        )
        self.click_target_upload_file_label = self.ui.grid_form_label(
            detail_frame,
            5,
            "Upload file path",
        )
        self.click_target_upload_file_entry = self.ui.create_entry(
            detail_frame,
            textvariable=self.click_target_upload_file_path_var,
        )
        self.click_target_upload_file_entry.grid(
            row=5,
            column=1,
            sticky="ew",
            padx=(14, 12),
            pady=self.config.label_pady,
            ipady=self.config.field_ipady,
        )
        self.click_target_upload_file_button = self.ui.create_button(
            detail_frame,
            text="Browse",
            command=self._browse_click_target_upload_file_path,
            variant="secondary",
        )
        self.click_target_upload_file_button.grid(row=5, column=2, sticky="ew")
        self.click_target_hint_label = self.ui.create_muted_label(
            detail_frame,
            "Examples: class => menu-item active, id => contact-search-input, data-id => div_TabMsg_ThrdChItem, anim-data-id => g1509445607335510374, css => div.chat-list button.open-chat, html => paste the Zalo element snippet and the app will resolve a clickable selector. Tick Image upload target only for file/image chooser flows.",
            wraplength=620,
        )
        self.click_target_hint_label.grid(row=6, column=0, columnspan=3, sticky="w", pady=(4, 10))

        click_target_action_frame = tk.Frame(detail_frame, bg=self.config.panel_color)
        click_target_action_frame.grid(row=7, column=0, columnspan=3, sticky="ew", pady=(14, 0))
        click_target_action_frame.grid_columnconfigure(1, weight=1)

        self.save_click_target_button = self.ui.create_button(
            click_target_action_frame,
            text="Save Target",
            command=self._save_click_target,
            variant="secondary",
            padx=18,
        )
        self.save_click_target_button.grid(row=0, column=0, sticky="w")

        self.test_click_target_button = self.ui.create_button(
            click_target_action_frame,
            text="Test Element",
            command=self._start_click_target_test,
            variant="primary",
            padx=18,
        )
        self.test_click_target_button.grid(row=0, column=2, sticky="e")

        self.click_target_status_label = self.ui.create_status_label(
            detail_frame,
            textvariable=self.click_target_status_var,
            wraplength=620,
        )
        self.click_target_status_label.grid(row=8, column=0, columnspan=3, sticky="ew", pady=(18, 0))

        self.ui.create_code_label(
            detail_frame,
            f"Selector workspace: {self.workspace_store.path}",
        ).grid(row=9, column=0, columnspan=3, sticky="w", pady=(14, 0))

    def _create_panel(self, parent: tk.Misc) -> tk.Frame:
        return self.ui.create_panel(parent)

    def _build_path_row(
        self,
        parent: tk.Frame,
        row: int,
        label: str,
        variable: tk.StringVar,
        button_text: str,
        button_command,
    ) -> None:
        self.ui.grid_path_row(
            parent,
            row=row,
            label=label,
            variable=variable,
            button_text=button_text,
            button_command=button_command,
        )

    def _build_entry_row(
        self,
        parent: tk.Frame,
        row: int,
        label: str,
        variable: tk.StringVar,
        readonly: bool = False,
    ) -> None:
        self.ui.grid_entry_row(
            parent,
            row=row,
            label=label,
            variable=variable,
            readonly=readonly,
        )

    def _build_combobox_row(
        self,
        parent: tk.Frame,
        row: int,
        label: str,
        variable: tk.StringVar,
        *,
        values: tuple[str, ...] = (),
        target_name: str,
    ) -> None:
        combo = self.ui.grid_combobox_row(
            parent,
            row=row,
            label=label,
            variable=variable,
        )
        if values:
            combo.configure(values=values)

        if target_name == "account_profile":
            self.account_profile_combobox = combo
        elif target_name == "click_target_selector_kind":
            self.click_target_selector_kind_combobox = combo

    def _refresh_state(self, preferred_profile_ids: Sequence[str] | None = None) -> None:
        self._apply_state(self.use_case.load_state(), preferred_profile_ids=preferred_profile_ids)

    def _apply_state(
        self,
        state: ZaloProfileManagerState,
        preferred_profile_ids: Sequence[str] | None = None,
    ) -> None:
        self._state = state
        self._profiles_by_id = {profile.id: profile for profile in state.profiles}
        self._profile_ids = [profile.id for profile in state.profiles]

        selected_profile_ids: list[str] = []
        for profile_id in preferred_profile_ids or ():
            if profile_id in self._profiles_by_id and profile_id not in selected_profile_ids:
                selected_profile_ids.append(profile_id)
        if not selected_profile_ids:
            fallback_profile_id = state.selected_profile_id
            if fallback_profile_id not in self._profiles_by_id:
                fallback_profile_id = self._profile_ids[0] if self._profile_ids else None
            if fallback_profile_id is not None:
                selected_profile_ids.append(fallback_profile_id)

        self._is_refreshing_list = True
        self.profile_listbox.delete(0, tk.END)
        for profile in state.profiles:
            self.profile_listbox.insert(tk.END, profile.name)
        self.profile_listbox.selection_clear(0, tk.END)
        for profile_id in selected_profile_ids:
            index = self._profile_ids.index(profile_id)
            self.profile_listbox.selection_set(index)
        self._is_refreshing_list = False

        primary_profile_id = selected_profile_ids[0] if selected_profile_ids else None
        if primary_profile_id is not None:
            index = self._profile_ids.index(primary_profile_id)
            self.profile_listbox.activate(index)
            self.profile_listbox.see(index)
            self._load_profile_into_form(self._profiles_by_id[primary_profile_id])
        else:
            self._load_new_profile_defaults()

        self._refresh_profile_choices()
        if self._workspace_state is not None:
            self._apply_workspace_state(
                self._workspace_state,
                preferred_account_id=self._current_edit_account_id,
            )
        self._update_action_states()

    def _refresh_workspace_state(
        self,
        preferred_account_id: str | None = None,
    ) -> None:
        self._apply_workspace_state(
            self.workspace_use_case.load_state(),
            preferred_account_id=preferred_account_id,
        )

    def _refresh_click_target_state(
        self,
        preferred_click_target_id: str | None = None,
    ) -> None:
        self._apply_click_target_state(
            self.click_target_use_case.load_state(),
            preferred_click_target_id=preferred_click_target_id,
        )

    def _apply_workspace_state(
        self,
        state: ZaloWorkspaceState,
        *,
        preferred_account_id: str | None = None,
    ) -> None:
        self._workspace_state = state
        self._accounts_by_id = {account.id: account for account in state.accounts}
        self._account_ids = [account.id for account in state.accounts]

        selected_account_id = (
            preferred_account_id if preferred_account_id in self._accounts_by_id else state.selected_account_id
        )
        if selected_account_id not in self._accounts_by_id:
            selected_account_id = self._account_ids[0] if self._account_ids else None

        self._is_refreshing_account_list = True
        self.account_listbox.delete(0, tk.END)
        for account in state.accounts:
            self.account_listbox.insert(tk.END, self._format_account_label(account))
        self.account_listbox.selection_clear(0, tk.END)
        if selected_account_id is not None:
            account_index = self._account_ids.index(selected_account_id)
            self.account_listbox.selection_set(account_index)
            self.account_listbox.activate(account_index)
            self.account_listbox.see(account_index)
        self._is_refreshing_account_list = False

        self._refresh_profile_choices()

        if selected_account_id is not None:
            self._load_account_into_form(self._accounts_by_id[selected_account_id])
        else:
            self._load_new_account_defaults()

        self._update_account_action_states()

    def _apply_click_target_state(
        self,
        state: ZaloClickTargetManagerState,
        *,
        preferred_click_target_id: str | None = None,
    ) -> None:
        self._click_target_state = state
        self._click_targets_by_id = {target.id: target for target in state.click_targets}
        self._click_target_ids = [target.id for target in state.click_targets]

        selected_click_target_id = (
            preferred_click_target_id
            if preferred_click_target_id in self._click_targets_by_id
            else state.selected_click_target_id
        )
        if selected_click_target_id not in self._click_targets_by_id:
            selected_click_target_id = self._click_target_ids[0] if self._click_target_ids else None

        self._is_refreshing_click_target_list = True
        self.click_target_listbox.delete(0, tk.END)
        for click_target in state.click_targets:
            self.click_target_listbox.insert(tk.END, self._format_click_target_label(click_target))
        self.click_target_listbox.selection_clear(0, tk.END)
        if selected_click_target_id is not None:
            click_target_index = self._click_target_ids.index(selected_click_target_id)
            self.click_target_listbox.selection_set(click_target_index)
            self.click_target_listbox.activate(click_target_index)
            self.click_target_listbox.see(click_target_index)
        self._is_refreshing_click_target_list = False

        if selected_click_target_id is not None:
            self._load_click_target_into_form(self._click_targets_by_id[selected_click_target_id])
        else:
            self._load_new_click_target_defaults()

        self._update_click_target_action_states()

    def _load_profile_into_form(self, profile: SavedChromeProfile) -> None:
        self._current_edit_profile_id = profile.id
        self.profile_name_var.set(profile.name)
        self.chrome_path_var.set(profile.chrome_executable)
        self.profile_path_var.set(profile.profile_path)
        self.target_url_var.set(profile.target_url)

    def _load_new_profile_defaults(self) -> None:
        self._current_edit_profile_id = None
        self.profile_name_var.set("")
        if self._state is None:
            chrome_executable = ""
            profile_path = ""
        else:
            chrome_executable = self._state.default_chrome_executable
            profile_root = self._state.default_profile_root
            profile_path = str(Path(profile_root) / "Profile 1") if profile_root else ""
        self.chrome_path_var.set(chrome_executable)
        self.profile_path_var.set(profile_path)
        self.target_url_var.set(DEFAULT_ZALO_URL)
        self.profile_listbox.selection_clear(0, tk.END)

    def _load_account_into_form(self, account: SavedZaloAccount) -> None:
        self._current_edit_account_id = account.id
        self._set_profile_choice_var(self.account_profile_choice_var, account.profile_id)
        self.account_proxy_var.set(account.proxy)

    def _load_new_account_defaults(self) -> None:
        self._current_edit_account_id = None
        self.account_profile_choice_var.set("")
        self.account_proxy_var.set("")
        self.account_listbox.selection_clear(0, tk.END)

    def _load_click_target_into_form(self, click_target: SavedZaloClickTarget) -> None:
        self._current_edit_click_target_id = click_target.id
        self.click_target_name_var.set(click_target.name)
        is_image_target = click_target.selector_kind == "image"
        self.click_target_is_image_var.set(is_image_target)
        self.click_target_selector_kind_var.set("css" if is_image_target else click_target.selector_kind)
        self.click_target_selector_value_var.set(click_target.selector_value)
        self.click_target_upload_file_path_var.set(click_target.upload_file_path)
        self._sync_click_target_upload_path_visibility()

    def _load_new_click_target_defaults(self) -> None:
        self._current_edit_click_target_id = None
        self.click_target_name_var.set("")
        self.click_target_is_image_var.set(False)
        self.click_target_selector_kind_var.set("class")
        self.click_target_selector_value_var.set("")
        self.click_target_upload_file_path_var.set("")
        self.click_target_listbox.selection_clear(0, tk.END)
        self._sync_click_target_upload_path_visibility()

    def _format_account_label(self, account: SavedZaloAccount) -> str:
        if account.profile_id and account.profile_id in self._profiles_by_id:
            base_label = self._profiles_by_id[account.profile_id].name
        elif account.name:
            base_label = account.name
        else:
            base_label = "Missing profile"

        if account.proxy:
            return f"{base_label} | {account.proxy}"
        return base_label

    def _format_click_target_label(self, click_target: SavedZaloClickTarget) -> str:
        label = f"{click_target.name} | {click_target.selector_kind}: {click_target.selector_value}"
        if click_target.upload_file_path:
            label += " | upload"
        return label

    def _start_new_profile(self) -> None:
        self._load_new_profile_defaults()
        self._set_status(
            "Creating a new saved profile. Use Save Profile for an existing Chrome profile folder, or Create Folder + Save to create '<path goc>\\<profile name>' automatically. Launch happens from Zalo Accounts.",
            self.config.text_color,
        )
        self._update_action_states()

    def _start_new_account(self) -> None:
        self._load_new_account_defaults()
        self._set_account_status(
            "Creating a new Zalo account entry. Select one saved profile, enter an optional proxy, then save before launching.",
            self.config.text_color,
        )
        self._update_account_action_states()

    def _start_new_click_target(self) -> None:
        self._load_new_click_target_defaults()
        self._set_click_target_status(
            "Creating a new click target. Upload file path is only used when Selector type is image.",
            self.config.text_color,
        )
        self._update_click_target_action_states()

    def _start_click_target_test(self) -> None:
        if self._click_target_test_in_progress or self._launch_in_progress:
            return

        if self._last_account_remote_debugging_port is None:
            messagebox.showwarning(
                "Test element",
                "Launch a Zalo account first so the app can attach to the active Chrome window.",
            )
            return

        self._click_target_test_in_progress = True
        self._click_target_test_was_image_mode = self.click_target_is_image_var.get()
        self._update_click_target_action_states()
        self._set_click_target_status(
            "Testing selector on the active Zalo page...",
            self.config.accent_color,
        )
        watchdog_delay_ms = int((DEFAULT_CLICK_ELEMENT_TIMEOUT_SECONDS + 5) * 1000)
        self.root.after(watchdog_delay_ms, self._watch_click_target_test_timeout)
        threading.Thread(target=self._click_target_test_worker, daemon=True).start()

    def _click_target_test_worker(self) -> None:
        try:
            result = self.click_element_use_case.execute(
                ClickZaloElementRequest(
                    target_name=self.click_target_name_var.get(),
                    selector_kind=self._resolved_click_target_selector_kind(),
                    selector_value=self.click_target_selector_value_var.get(),
                    upload_file_path=self.click_target_upload_file_path_var.get(),
                    remote_debugging_port=self._last_account_remote_debugging_port or 0,
                    target_url=self._last_account_target_url,
                )
            )
        except (
            BrowserAutomationError,
            LauncherValidationError,
            ZaloClickAutomationError,
            ZaloClickTargetConflictError,
        ) as exc:
            self.root.after(0, lambda: self._handle_click_target_test_error(str(exc)))
            return
        except Exception as exc:  # noqa: BLE001
            self.root.after(
                0,
                lambda: self._handle_click_target_test_error(
                    f"Unexpected Test Element failure: {exc}"
                ),
            )
            return

        self.root.after(0, lambda: self._handle_click_target_test_success(result))

    def _watch_click_target_test_timeout(self) -> None:
        if not self._click_target_test_in_progress:
            return
        if self._click_target_test_was_image_mode:
            self._click_target_test_in_progress = False
            self._update_click_target_action_states()
            self._set_click_target_status(
                "Image upload action appears to have been sent. The browser action completed, but Playwright did not report a clean finish.",
                self.config.success_color,
            )
            return
        self._handle_click_target_test_error(
            "Test Element did not finish cleanly. If the browser action already succeeded, reopen the app and try again."
        )

    def _start_proxy_test(self) -> None:
        if self._proxy_test_in_progress or self._launch_in_progress:
            return

        raw_proxy = self.account_proxy_var.get().strip()
        if not raw_proxy:
            messagebox.showwarning("Test proxy", "Enter a proxy value first.")
            return

        self._proxy_test_in_progress = True
        self._update_account_action_states()
        self._set_account_status(
            "Testing proxy connectivity...",
            self.config.accent_color,
        )
        threading.Thread(target=self._proxy_test_worker, args=(raw_proxy,), daemon=True).start()

    def _proxy_test_worker(self, raw_proxy: str) -> None:
        try:
            result = self.proxy_test_use_case.execute(
                TestProxyConnectionRequest(raw_proxy=raw_proxy)
            )
        except (LauncherValidationError, ProxyConnectionError) as exc:
            self.root.after(0, lambda: self._handle_proxy_test_error(str(exc)))
            return

        self.root.after(0, lambda: self._handle_proxy_test_success(result))

    def _selected_profile_ids(self) -> list[str]:
        return [self._profile_ids[index] for index in self.profile_listbox.curselection() if index < len(self._profile_ids)]

    def _selected_account_id(self) -> str | None:
        selection = self.account_listbox.curselection()
        if not selection:
            return None
        index = selection[0]
        if index >= len(self._account_ids):
            return None
        return self._account_ids[index]

    def _selected_click_target_id(self) -> str | None:
        selection = self.click_target_listbox.curselection()
        if not selection:
            return None
        index = selection[0]
        if index >= len(self._click_target_ids):
            return None
        return self._click_target_ids[index]

    def _on_profile_selected(self, _event) -> None:
        if self._is_refreshing_list:
            return

        selected_profile_ids = self._selected_profile_ids()
        if not selected_profile_ids:
            return
        primary_profile_id = selected_profile_ids[0]

        try:
            state = self.use_case.select_profile(primary_profile_id)
        except (SavedProfileNotFoundError, SettingsPersistenceError) as exc:
            self._handle_data_error(str(exc))
            return

        self._apply_state(state, preferred_profile_ids=selected_profile_ids)
        self._set_status(
            f"Selected profile '{self._profiles_by_id[primary_profile_id].name}'. Use it as a linked profile in the Zalo Accounts tab.",
            self.config.text_color,
        )

    def _on_account_selected(self, _event) -> None:
        if self._is_refreshing_account_list:
            return

        account_id = self._selected_account_id()
        if account_id is None:
            return

        try:
            state = self.workspace_use_case.select_account(account_id)
        except SavedZaloAccountNotFoundError as exc:
            self._handle_account_error(str(exc))
            return

        self._apply_workspace_state(
            state,
            preferred_account_id=account_id,
        )
        self._set_account_status(
            f"Selected '{self._format_account_label(self._accounts_by_id[account_id])}'. Ready to launch from Zalo Accounts.",
            self.config.text_color,
        )

    def _on_click_target_selected(self, _event) -> None:
        if self._is_refreshing_click_target_list:
            return

        click_target_id = self._selected_click_target_id()
        if click_target_id is None:
            return

        try:
            state = self.click_target_use_case.select_click_target(click_target_id)
        except ZaloClickTargetNotFoundError as exc:
            self._handle_click_target_error(str(exc))
            return

        self._apply_click_target_state(
            state,
            preferred_click_target_id=click_target_id,
        )
        self._set_click_target_status(
            f"Selected '{self._format_click_target_label(self._click_targets_by_id[click_target_id])}'.",
            self.config.text_color,
        )

    def _browse_chrome_executable(self) -> None:
        filename = filedialog.askopenfilename(
            title="Select Chrome executable",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")],
        )
        if filename:
            self.chrome_path_var.set(filename)

    def _browse_profile_path(self) -> None:
        directory = filedialog.askdirectory(title="Select Chrome profile folder")
        if directory:
            self.profile_path_var.set(directory)

    def _browse_click_target_upload_file_path(self) -> None:
        filename = filedialog.askopenfilename(
            title="Select upload file",
            filetypes=[
                ("Images", "*.png;*.jpg;*.jpeg;*.webp;*.gif;*.bmp"),
                ("All files", "*.*"),
            ],
        )
        if filename:
            self.click_target_upload_file_path_var.set(filename)

    def _save_profile(self) -> None:
        request = SavedProfileUpsertRequest(
            profile_id=self._current_edit_profile_id,
            name=self.profile_name_var.get(),
            chrome_executable=self.chrome_path_var.get(),
            profile_path=self.profile_path_var.get(),
            target_url=self.target_url_var.get(),
        )

        try:
            state = self.use_case.save_profile(request)
        except (LauncherValidationError, SavedProfileConflictError, SettingsPersistenceError) as exc:
            self._handle_data_error(str(exc))
            return

        saved_profile = next(profile for profile in state.profiles if profile.id == state.selected_profile_id)
        self._apply_state(state, preferred_profile_ids=[saved_profile.id])
        self._set_status(
            f"Saved profile '{saved_profile.name}' with path '{saved_profile.profile_path}'.",
            self.config.success_color,
        )

    def _create_profile(self) -> None:
        request = SavedProfileUpsertRequest(
            profile_id=self._current_edit_profile_id,
            name=self.profile_name_var.get(),
            chrome_executable=self.chrome_path_var.get(),
            profile_path=self.profile_path_var.get(),
            target_url=self.target_url_var.get(),
        )

        try:
            state = self.use_case.create_profile(request)
        except (LauncherValidationError, SavedProfileConflictError, SettingsPersistenceError) as exc:
            self._handle_data_error(str(exc))
            return

        saved_profile = next(profile for profile in state.profiles if profile.id == state.selected_profile_id)
        self._apply_state(state, preferred_profile_ids=[saved_profile.id])
        self._set_status(
            f"Created profile folder from root path and saved '{saved_profile.name}' at '{saved_profile.profile_path}'.",
            self.config.success_color,
        )

    def _save_account(self) -> None:
        profile_label = self.account_profile_choice_var.get().strip()
        request = ZaloAccountUpsertRequest(
            account_id=self._current_edit_account_id,
            name=profile_label,
            profile_id=self._selected_profile_choice_id(self.account_profile_choice_var),
            proxy=self.account_proxy_var.get(),
        )

        try:
            state = self.workspace_use_case.save_account(request)
        except SavedZaloAccountConflictError as exc:
            self._handle_account_error(str(exc))
            return

        saved_account = next(account for account in state.accounts if account.id == state.selected_account_id)
        self._apply_workspace_state(
            state,
            preferred_account_id=saved_account.id,
        )
        self._set_account_status(
            f"Saved proxy mapping for '{self._format_account_label(saved_account)}'.",
            self.config.success_color,
        )

    def _save_click_target(self) -> None:
        request = ZaloClickTargetUpsertRequest(
            click_target_id=self._current_edit_click_target_id,
            name=self.click_target_name_var.get(),
            selector_kind=self._resolved_click_target_selector_kind(),
            selector_value=self.click_target_selector_value_var.get(),
            upload_file_path=self.click_target_upload_file_path_var.get(),
        )

        try:
            state = self.click_target_use_case.save_click_target(request)
        except ZaloClickTargetConflictError as exc:
            self._handle_click_target_error(str(exc))
            return

        saved_click_target = next(
            target for target in state.click_targets if target.id == state.selected_click_target_id
        )
        self._apply_click_target_state(
            state,
            preferred_click_target_id=saved_click_target.id,
        )
        self._set_click_target_status(
            f"Saved click target '{saved_click_target.name}'.",
            self.config.success_color,
        )

    def _resolved_click_target_selector_kind(self) -> str:
        if self.click_target_is_image_var.get():
            return "image"
        selector_kind = self.click_target_selector_kind_var.get().strip()
        selector_value = self.click_target_selector_value_var.get()
        if selector_kind.casefold() != "html" and looks_like_html_snippet(selector_value):
            self.click_target_selector_kind_var.set("html")
            return "html"
        return selector_kind

    def _on_click_target_selector_kind_changed(self, *_args) -> None:
        self._sync_click_target_upload_path_visibility()

    def _sync_click_target_upload_path_visibility(self) -> None:
        is_image_target = self.click_target_is_image_var.get()
        if self.click_target_selector_kind_combobox is not None:
            self.click_target_selector_kind_combobox.configure(state="disabled" if is_image_target else "readonly")
        if self.click_target_is_image_checkbox is not None:
            self.click_target_is_image_checkbox.configure(state="normal")
        for widget in (
            self.click_target_upload_file_label,
            self.click_target_upload_file_entry,
            self.click_target_upload_file_button,
        ):
            if widget is None:
                continue
            if is_image_target:
                widget.grid()
            else:
                widget.grid_remove()

        if self.click_target_hint_label is not None:
            self.click_target_hint_label.configure(
                text=(
                    "Examples: class => menu-item active, id => contact-search-input, data-id => div_TabMsg_ThrdChItem, "
                    "anim-data-id => g1509445607335510374, css => div.chat-list button.open-chat, html => paste the Zalo "
                    "element snippet and the app will resolve a clickable selector. "
                    + (
                        "Image upload target is enabled. Put a CSS selector in Selector value and choose the file to upload."
                        if is_image_target
                        else "Tick Image upload target only when the click should open a file chooser."
                    )
                )
            )

        if not is_image_target:
            self.click_target_upload_file_path_var.set("")

    def _delete_profile(self) -> None:
        profile_id = self._current_edit_profile_id
        if profile_id is None or profile_id not in self._profiles_by_id:
            messagebox.showwarning("Delete profile", "Select a saved profile first.")
            return

        profile_name = self._profiles_by_id[profile_id].name
        if not messagebox.askyesno("Delete profile", f"Delete saved profile '{profile_name}'?"):
            return

        try:
            state = self.use_case.delete_profile(profile_id)
        except (SavedProfileNotFoundError, SettingsPersistenceError) as exc:
            self._handle_data_error(str(exc))
            return

        self._apply_state(state)
        self._set_status(f"Deleted profile '{profile_name}'.", self.config.text_color)

    def _delete_account(self) -> None:
        account_id = self._current_edit_account_id
        if account_id is None or account_id not in self._accounts_by_id:
            messagebox.showwarning("Delete account", "Select a saved account first.")
            return

        account_label = self._format_account_label(self._accounts_by_id[account_id])
        if not messagebox.askyesno("Delete account", f"Delete saved account '{account_label}'?"):
            return

        try:
            state = self.workspace_use_case.delete_account(account_id)
        except SavedZaloAccountNotFoundError as exc:
            self._handle_account_error(str(exc))
            return

        self._apply_workspace_state(
            state,
            preferred_account_id=state.selected_account_id,
        )
        self._set_account_status(f"Deleted account '{account_label}'.", self.config.text_color)

    def _delete_click_target(self) -> None:
        click_target_id = self._current_edit_click_target_id
        if click_target_id is None or click_target_id not in self._click_targets_by_id:
            messagebox.showwarning("Delete click target", "Select a saved click target first.")
            return

        click_target_label = self._format_click_target_label(self._click_targets_by_id[click_target_id])
        if not messagebox.askyesno("Delete click target", f"Delete saved click target '{click_target_label}'?"):
            return

        try:
            state = self.click_target_use_case.delete_click_target(click_target_id)
        except ZaloClickTargetNotFoundError as exc:
            self._handle_click_target_error(str(exc))
            return

        self._apply_click_target_state(
            state,
            preferred_click_target_id=state.selected_click_target_id,
        )
        self._set_click_target_status(f"Deleted click target '{click_target_label}'.", self.config.text_color)

    def _start_account_launch(self) -> None:
        if self._launch_in_progress or self._proxy_test_in_progress:
            return

        account_id = self._selected_account_id()
        if account_id is None and self._current_edit_account_id in self._accounts_by_id:
            account_id = self._current_edit_account_id

        if account_id is None:
            messagebox.showwarning("Launch account", "Save or select a Zalo account before launching.")
            return

        self._launch_in_progress = True
        self._update_account_action_states()
        account_label = self._format_account_label(self._accounts_by_id[account_id])
        self._set_account_status(
            f"Launching '{account_label}' from the Zalo Accounts tab...",
            self.config.accent_color,
        )
        threading.Thread(target=self._launch_account_worker, args=(account_id,), daemon=True).start()

    def _launch_account_worker(self, account_id: str) -> None:
        try:
            result = self.account_launch_use_case.launch_account(account_id)
        except (
            LauncherValidationError,
            ChromeLaunchError,
            SavedProfileNotFoundError,
            SavedZaloAccountConflictError,
            SavedZaloAccountNotFoundError,
        ) as exc:
            self.root.after(0, lambda: self._handle_account_launch_error(str(exc)))
            return

        self.root.after(0, lambda: self._handle_account_launch_success(result))

    def _handle_account_launch_success(self, result: LaunchSavedZaloAccountResult) -> None:
        self._launch_in_progress = False
        self._last_account_remote_debugging_port = result.launch_result.remote_debugging_port
        self._last_account_target_url = result.launch_result.target_url
        self._refresh_workspace_state(preferred_account_id=result.account_id)
        self._update_account_action_states()

        status_message = (
            f"Launched '{result.profile_name}' using profile directory "
            f"'{result.launch_result.profile_directory}'."
        )
        if result.proxy:
            status_message += f" Proxy '{result.proxy}' was applied."
        else:
            status_message += " Direct access mode was used."
        if result.launch_result.window_placement is not None:
            status_message += " Fixed window bounds were applied."
        if not result.workspace_persisted:
            status_message += " The selected account could not be persisted."

        self._set_account_status(status_message, self.config.success_color)

    def _handle_account_launch_error(self, message: str) -> None:
        self._launch_in_progress = False
        self._update_account_action_states()
        self._set_account_status(message, self.config.error_color)
        messagebox.showerror("Launch failed", message)

    def _handle_proxy_test_success(self, result: TestProxyConnectionResult) -> None:
        self._proxy_test_in_progress = False
        self._update_account_action_states()

        status_message = (
            f"Proxy test succeeded. Server '{result.normalized_proxy_server}' "
            f"returned public IP '{result.detected_ip}'."
        )
        if result.uses_authentication:
            status_message += " Authentication was included in the test request."
        self._set_account_status(status_message, self.config.success_color)

    def _handle_proxy_test_error(self, message: str) -> None:
        self._proxy_test_in_progress = False
        self._update_account_action_states()
        self._set_account_status(message, self.config.error_color)
        messagebox.showerror("Proxy test failed", message)

    def _handle_click_target_test_success(self, result: ClickZaloElementResult) -> None:
        self._click_target_test_in_progress = False
        self._click_target_test_was_image_mode = False
        self._update_click_target_action_states()
        status_message = (
            f"Clicked '{result.clicked_target_name}' using selector '{result.resolved_selector}'."
        )
        if result.uploaded_file_path:
            status_message += f" Uploaded file '{result.uploaded_file_path}'."
        self._set_click_target_status(status_message, self.config.success_color)

    def _handle_click_target_test_error(self, message: str) -> None:
        self._click_target_test_in_progress = False
        self._click_target_test_was_image_mode = False
        self._update_click_target_action_states()
        self._set_click_target_status(message, self.config.error_color)
        messagebox.showerror("Test element failed", message)

    def _handle_data_error(self, message: str) -> None:
        self._set_status(message, self.config.error_color)
        messagebox.showerror("Profile error", message)

    def _handle_account_error(self, message: str) -> None:
        self._set_account_status(message, self.config.error_color)
        messagebox.showerror("Account error", message)

    def _handle_click_target_error(self, message: str) -> None:
        self._set_click_target_status(message, self.config.error_color)
        messagebox.showerror("Click target error", message)

    def _refresh_profile_choices(self) -> None:
        self._profile_name_to_id = {profile.name: profile.id for profile in self._profiles_by_id.values()}
        values = tuple(profile.name for profile in self._profiles_by_id.values())
        if self.account_profile_combobox is not None:
            self.account_profile_combobox.configure(values=values)
        if self.account_profile_choice_var.get() not in values:
            self.account_profile_choice_var.set("")

    def _selected_profile_choice_id(self, variable: tk.StringVar) -> str | None:
        return self._profile_name_to_id.get(variable.get().strip())

    def _set_profile_choice_var(self, variable: tk.StringVar, profile_id: str | None) -> None:
        if profile_id is None or profile_id not in self._profiles_by_id:
            variable.set("")
            return
        variable.set(self._profiles_by_id[profile_id].name)

    def _update_action_states(self) -> None:
        has_saved_selection = bool(self._selected_profile_ids()) or (
            self._current_edit_profile_id is not None and self._current_edit_profile_id in self._profiles_by_id
        )

        self.save_button.configure(state="normal")
        self.create_profile_button.configure(state="normal")
        self.new_button.configure(state="normal")
        self.delete_button.configure(
            state="normal"
            if has_saved_selection and self._current_edit_profile_id in self._profiles_by_id
            else "disabled"
        )
        self.profile_listbox.configure(state="normal")

    def _update_account_action_states(self) -> None:
        has_saved_selection = self._current_edit_account_id in self._accounts_by_id
        if self._launch_in_progress:
            self.launch_account_button.configure(state="disabled", text="Launching...")
            self.save_account_button.configure(state="disabled")
            self.new_account_button.configure(state="disabled")
            self.delete_account_button.configure(state="disabled")
            self.test_proxy_button.configure(state="disabled", text="Test Proxy")
            self.account_listbox.configure(state="disabled")
            return

        self.launch_account_button.configure(
            state="normal" if has_saved_selection and not self._proxy_test_in_progress else "disabled",
            text="Launch Account",
        )
        self.save_account_button.configure(state="normal")
        self.new_account_button.configure(state="normal")
        self.delete_account_button.configure(
            state="normal" if has_saved_selection else "disabled"
        )
        self.test_proxy_button.configure(
            state="disabled" if self._proxy_test_in_progress else "normal",
            text="Testing..." if self._proxy_test_in_progress else "Test Proxy",
        )
        self.account_listbox.configure(state="normal")

    def _update_click_target_action_states(self) -> None:
        has_saved_selection = self._current_edit_click_target_id in self._click_targets_by_id
        if self._click_target_test_in_progress:
            self.save_click_target_button.configure(state="disabled")
            self.new_click_target_button.configure(state="disabled")
            self.delete_click_target_button.configure(state="disabled")
            self.test_click_target_button.configure(state="disabled", text="Testing...")
            self.click_target_listbox.configure(state="disabled")
            return

        self.save_click_target_button.configure(state="normal")
        self.new_click_target_button.configure(state="normal")
        self.delete_click_target_button.configure(
            state="normal" if has_saved_selection else "disabled"
        )
        self.test_click_target_button.configure(state="normal", text="Test Element")
        self.click_target_listbox.configure(state="normal")

    def _set_status(self, message: str, color: str) -> None:
        self.status_var.set(message)
        self.status_label.configure(fg=color)

    def _set_account_status(self, message: str, color: str) -> None:
        self.account_status_var.set(message)
        self.account_status_label.configure(fg=color)

    def _set_click_target_status(self, message: str, color: str) -> None:
        self.click_target_status_var.set(message)
        self.click_target_status_label.configure(fg=color)


def main() -> None:
    root = tk.Tk()
    ZaloLauncherGui(root)
    root.mainloop()


if __name__ == "__main__":
    main()
