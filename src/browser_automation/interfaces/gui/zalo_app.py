from __future__ import annotations

import threading
import tkinter as tk
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from browser_automation.application.use_cases.manage_zalo_profiles import (
    DEFAULT_GRID_COLUMNS,
    DEFAULT_GRID_LAUNCH_LIMIT,
    DEFAULT_GRID_ROWS,
    LaunchSavedProfilesGridResult,
    LaunchSavedProfileResult,
    SavedProfileUpsertRequest,
    ZaloProfileManagerState,
    ZaloProfileManagerUseCase,
)
from browser_automation.application.use_cases.manage_zalo_workspace import (
    CookieUpsertRequest,
    ZaloAccountUpsertRequest,
    ZaloWorkspaceManagerUseCase,
    ZaloWorkspaceState,
)
from browser_automation.domain.exceptions import (
    ChromeLaunchError,
    LauncherValidationError,
    SavedCookieConflictError,
    SavedCookieNotFoundError,
    SavedProfileConflictError,
    SavedProfileNotFoundError,
    SavedZaloAccountConflictError,
    SavedZaloAccountNotFoundError,
    SettingsPersistenceError,
)
from browser_automation.domain.zalo_launcher import DEFAULT_ZALO_URL, SavedChromeProfile
from browser_automation.domain.zalo_workspace import SavedCookieEntry, SavedZaloAccount
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
from browser_automation.infrastructure.chrome_launcher.windows_chrome_window_arranger import (
    WindowsChromeWindowArranger,
)


@dataclass(frozen=True, slots=True)
class ZaloGuiConfig:
    title: str = "Zalo Chrome Profile Manager"
    width: int = 1180
    height: int = 760
    bg_color: str = "#f3efe7"
    panel_color: str = "#fffaf2"
    header_color: str = "#1f3a5f"
    accent_color: str = "#0f766e"
    accent_alt_color: str = "#e2e8f0"
    success_color: str = "#166534"
    error_color: str = "#b42318"
    text_color: str = "#172b3a"
    muted_color: str = "#5f6c7b"


class ZaloLauncherGui:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.config = ZaloGuiConfig()
        self.discovery = DefaultChromeInstallationDiscovery()
        self.library_store = JsonSavedProfileLibraryStore()
        self.workspace_store = JsonZaloWorkspaceStore()
        self.use_case = ZaloProfileManagerUseCase(
            library_store=self.library_store,
            chrome_discovery=self.discovery,
            chrome_launcher=SubprocessChromeProcessLauncher(),
            chrome_window_arranger=WindowsChromeWindowArranger(),
        )
        self.workspace_use_case = ZaloWorkspaceManagerUseCase(self.workspace_store)

        self._launch_in_progress = False
        self._is_refreshing_list = False
        self._is_refreshing_cookie_list = False
        self._is_refreshing_account_list = False

        self._current_edit_profile_id: str | None = None
        self._profile_ids: list[str] = []
        self._profiles_by_id: dict[str, SavedChromeProfile] = {}
        self._state: ZaloProfileManagerState | None = None

        self._current_edit_cookie_id: str | None = None
        self._cookie_ids: list[str] = []
        self._cookies_by_id: dict[str, SavedCookieEntry] = {}

        self._current_edit_account_id: str | None = None
        self._account_ids: list[str] = []
        self._accounts_by_id: dict[str, SavedZaloAccount] = {}
        self._workspace_state: ZaloWorkspaceState | None = None

        self._profile_name_to_id: dict[str, str] = {}
        self._cookie_name_to_id: dict[str, str] = {}

        self.profile_name_var = tk.StringVar()
        self.chrome_path_var = tk.StringVar()
        self.profile_path_var = tk.StringVar()
        self.target_url_var = tk.StringVar(value=DEFAULT_ZALO_URL)
        self.status_var = tk.StringVar(
            value=(
                "Profiles tab launches Chrome. Cookies and Zalo Accounts tabs store local operator data."
            )
        )

        self.cookie_name_var = tk.StringVar()
        self.cookie_profile_choice_var = tk.StringVar()
        self.cookie_status_var = tk.StringVar(
            value="Save raw cookie payloads and optionally link them to a Chrome profile."
        )

        self.account_name_var = tk.StringVar()
        self.account_phone_var = tk.StringVar()
        self.account_profile_choice_var = tk.StringVar()
        self.account_cookie_choice_var = tk.StringVar()
        self.account_status_var = tk.StringVar(
            value="Save Zalo account records and optionally link them to a profile or cookie."
        )

        self.cookie_payload_text: tk.Text | None = None
        self.cookie_notes_text: tk.Text | None = None
        self.account_notes_text: tk.Text | None = None
        self.cookie_profile_combobox: ttk.Combobox | None = None
        self.account_profile_combobox: ttk.Combobox | None = None
        self.account_cookie_combobox: ttk.Combobox | None = None

        self._setup_window()
        self._create_widgets()
        self._refresh_state()
        self._refresh_workspace_state()

    def _setup_window(self) -> None:
        self.root.title(self.config.title)
        self.root.geometry(f"{self.config.width}x{self.config.height}")
        self.root.minsize(1040, 680)
        self.root.configure(bg=self.config.bg_color)

    def _create_widgets(self) -> None:
        header_frame = tk.Frame(self.root, bg=self.config.header_color, padx=28, pady=24)
        header_frame.pack(fill=tk.X)

        tk.Label(
            header_frame,
            text=self.config.title,
            font=("Segoe UI Semibold", 18),
            bg=self.config.header_color,
            fg="#f8fafc",
        ).pack(anchor=tk.W)
        tk.Label(
            header_frame,
            text=(
                "Profiles launches Chrome sessions. Cookies stores raw payloads. "
                "Zalo Accounts keeps operator account records linked to profiles or cookies."
            ),
            font=("Segoe UI", 10),
            bg=self.config.header_color,
            fg="#dbe4f0",
            justify=tk.LEFT,
            wraplength=1040,
        ).pack(anchor=tk.W, pady=(6, 0))

        content_frame = tk.Frame(self.root, bg=self.config.bg_color, padx=24, pady=20)
        content_frame.pack(fill=tk.BOTH, expand=True)

        self.notebook = ttk.Notebook(content_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        profile_tab = tk.Frame(self.notebook, bg=self.config.bg_color)
        cookies_tab = tk.Frame(self.notebook, bg=self.config.bg_color)
        accounts_tab = tk.Frame(self.notebook, bg=self.config.bg_color)

        self.notebook.add(profile_tab, text="Profiles")
        self.notebook.add(cookies_tab, text="Cookies")
        self.notebook.add(accounts_tab, text="Zalo Accounts")

        self._create_profile_tab(profile_tab)
        self._create_cookies_tab(cookies_tab)
        self._create_accounts_tab(accounts_tab)

    def _create_profile_tab(self, parent: tk.Frame) -> None:
        parent.grid_columnconfigure(1, weight=1)
        parent.grid_rowconfigure(0, weight=1)

        library_frame = self._create_panel(parent)
        library_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 18))
        library_frame.grid_rowconfigure(3, weight=1)
        library_frame.grid_columnconfigure(0, weight=1)

        tk.Label(
            library_frame,
            text="Saved Profiles",
            font=("Segoe UI Semibold", 13),
            bg=self.config.panel_color,
            fg=self.config.text_color,
        ).grid(row=0, column=0, sticky="w")
        tk.Label(
            library_frame,
            text="One saved item equals one Chrome profile folder.",
            font=("Segoe UI", 9),
            bg=self.config.panel_color,
            fg=self.config.muted_color,
            justify=tk.LEFT,
            wraplength=280,
        ).grid(row=1, column=0, sticky="w", pady=(4, 12))
        tk.Label(
            library_frame,
            text="Ctrl/Shift + click to launch multiple profiles for the 4x2 grid layout.",
            font=("Segoe UI", 9),
            bg=self.config.panel_color,
            fg=self.config.muted_color,
            justify=tk.LEFT,
            wraplength=280,
        ).grid(row=2, column=0, sticky="w", pady=(0, 12))

        list_frame = tk.Frame(library_frame, bg=self.config.panel_color)
        list_frame.grid(row=3, column=0, sticky="nsew")
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        self.profile_listbox = tk.Listbox(
            list_frame,
            activestyle="none",
            exportselection=False,
            font=("Segoe UI", 10),
            bg="#ffffff",
            fg=self.config.text_color,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground="#cbd5e1",
            selectmode=tk.EXTENDED,
            selectbackground="#c7f9ed",
            selectforeground=self.config.text_color,
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

        self.new_button = tk.Button(
            library_actions,
            text="New Profile",
            command=self._start_new_profile,
            bg=self.config.accent_alt_color,
            fg=self.config.text_color,
            activebackground="#cbd5e1",
            activeforeground=self.config.text_color,
            relief=tk.FLAT,
            padx=14,
            pady=8,
            font=("Segoe UI", 9),
        )
        self.new_button.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.delete_button = tk.Button(
            library_actions,
            text="Delete",
            command=self._delete_profile,
            bg="#fee2e2",
            fg="#991b1b",
            activebackground="#fecaca",
            activeforeground="#991b1b",
            relief=tk.FLAT,
            padx=14,
            pady=8,
            font=("Segoe UI", 9),
        )
        self.delete_button.grid(row=0, column=1, sticky="ew")

        detail_frame = self._create_panel(parent)
        detail_frame.grid(row=0, column=1, sticky="nsew")
        detail_frame.grid_columnconfigure(1, weight=1)

        tk.Label(
            detail_frame,
            text="Profile Details",
            font=("Segoe UI Semibold", 13),
            bg=self.config.panel_color,
            fg=self.config.text_color,
        ).grid(row=0, column=0, columnspan=3, sticky="w")
        tk.Label(
            detail_frame,
            text="Example profile path: C:\\Users\\ThangHoang\\AppData\\Local\\Google\\Chrome\\User Data\\Profile 1",
            font=("Segoe UI", 9),
            bg=self.config.panel_color,
            fg=self.config.muted_color,
            justify=tk.LEFT,
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

        tk.Label(
            detail_frame,
            text="Pick the actual profile folder such as 'Default' or 'Profile 1', not the parent 'User Data' folder.",
            font=("Segoe UI", 9),
            bg=self.config.panel_color,
            fg=self.config.muted_color,
            justify=tk.LEFT,
            wraplength=620,
        ).grid(row=6, column=0, columnspan=3, sticky="w", pady=(12, 8))
        tk.Label(
            detail_frame,
            text=f"Grid launch uses the first {DEFAULT_GRID_LAUNCH_LIMIT} selected profiles and arranges them into {DEFAULT_GRID_COLUMNS} columns x {DEFAULT_GRID_ROWS} rows.",
            font=("Segoe UI", 9),
            bg=self.config.panel_color,
            fg=self.config.muted_color,
            justify=tk.LEFT,
            wraplength=620,
        ).grid(row=7, column=0, columnspan=3, sticky="w", pady=(0, 8))

        action_frame = tk.Frame(detail_frame, bg=self.config.panel_color)
        action_frame.grid(row=8, column=0, columnspan=3, sticky="ew", pady=(14, 0))
        action_frame.grid_columnconfigure(1, weight=1)

        self.save_button = tk.Button(
            action_frame,
            text="Save Profile",
            command=self._save_profile,
            bg=self.config.accent_alt_color,
            fg=self.config.text_color,
            activebackground="#cbd5e1",
            activeforeground=self.config.text_color,
            relief=tk.FLAT,
            padx=16,
            pady=8,
            font=("Segoe UI", 9),
        )
        self.save_button.grid(row=0, column=0, sticky="w")

        self.launch_button = tk.Button(
            action_frame,
            text="Launch Selected",
            command=self._start_launch,
            bg=self.config.accent_color,
            fg="#f8fafc",
            activebackground="#115e59",
            activeforeground="#f8fafc",
            relief=tk.FLAT,
            padx=18,
            pady=8,
            font=("Segoe UI Semibold", 10),
        )
        self.launch_button.grid(row=0, column=1, sticky="e")

        self.status_label = tk.Label(
            detail_frame,
            textvariable=self.status_var,
            font=("Segoe UI", 10),
            bg=self.config.panel_color,
            fg=self.config.text_color,
            anchor="w",
            justify=tk.LEFT,
            wraplength=620,
        )
        self.status_label.grid(row=9, column=0, columnspan=3, sticky="ew", pady=(18, 0))

        tk.Label(
            detail_frame,
            text=f"Saved profile library: {self.library_store.path}",
            font=("Consolas", 9),
            bg=self.config.panel_color,
            fg=self.config.muted_color,
            anchor="w",
            justify=tk.LEFT,
        ).grid(row=10, column=0, columnspan=3, sticky="w", pady=(14, 0))

    def _create_cookies_tab(self, parent: tk.Frame) -> None:
        parent.grid_columnconfigure(1, weight=1)
        parent.grid_rowconfigure(0, weight=1)

        library_frame = self._create_panel(parent)
        library_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 18))
        library_frame.grid_rowconfigure(2, weight=1)
        library_frame.grid_columnconfigure(0, weight=1)

        tk.Label(
            library_frame,
            text="Saved Cookies",
            font=("Segoe UI Semibold", 13),
            bg=self.config.panel_color,
            fg=self.config.text_color,
        ).grid(row=0, column=0, sticky="w")
        tk.Label(
            library_frame,
            text="Store a raw cookie payload and optionally link it to one saved Chrome profile.",
            font=("Segoe UI", 9),
            bg=self.config.panel_color,
            fg=self.config.muted_color,
            justify=tk.LEFT,
            wraplength=280,
        ).grid(row=1, column=0, sticky="w", pady=(4, 12))

        cookie_list_frame = tk.Frame(library_frame, bg=self.config.panel_color)
        cookie_list_frame.grid(row=2, column=0, sticky="nsew")
        cookie_list_frame.grid_rowconfigure(0, weight=1)
        cookie_list_frame.grid_columnconfigure(0, weight=1)

        self.cookie_listbox = tk.Listbox(
            cookie_list_frame,
            activestyle="none",
            exportselection=False,
            font=("Segoe UI", 10),
            bg="#ffffff",
            fg=self.config.text_color,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground="#cbd5e1",
            selectbackground="#dbeafe",
            selectforeground=self.config.text_color,
        )
        self.cookie_listbox.grid(row=0, column=0, sticky="nsew")
        self.cookie_listbox.bind("<<ListboxSelect>>", self._on_cookie_selected)

        cookie_scrollbar = tk.Scrollbar(cookie_list_frame, orient=tk.VERTICAL, command=self.cookie_listbox.yview)
        cookie_scrollbar.grid(row=0, column=1, sticky="ns")
        self.cookie_listbox.configure(yscrollcommand=cookie_scrollbar.set)

        cookie_actions = tk.Frame(library_frame, bg=self.config.panel_color)
        cookie_actions.grid(row=3, column=0, sticky="ew", pady=(14, 0))
        cookie_actions.grid_columnconfigure(0, weight=1)
        cookie_actions.grid_columnconfigure(1, weight=1)

        self.new_cookie_button = tk.Button(
            cookie_actions,
            text="New Cookie",
            command=self._start_new_cookie,
            bg=self.config.accent_alt_color,
            fg=self.config.text_color,
            relief=tk.FLAT,
            padx=14,
            pady=8,
            font=("Segoe UI", 9),
        )
        self.new_cookie_button.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.delete_cookie_button = tk.Button(
            cookie_actions,
            text="Delete",
            command=self._delete_cookie,
            bg="#fee2e2",
            fg="#991b1b",
            relief=tk.FLAT,
            padx=14,
            pady=8,
            font=("Segoe UI", 9),
        )
        self.delete_cookie_button.grid(row=0, column=1, sticky="ew")

        detail_frame = self._create_panel(parent)
        detail_frame.grid(row=0, column=1, sticky="nsew")
        detail_frame.grid_columnconfigure(1, weight=1)

        tk.Label(
            detail_frame,
            text="Cookie Details",
            font=("Segoe UI Semibold", 13),
            bg=self.config.panel_color,
            fg=self.config.text_color,
        ).grid(row=0, column=0, columnspan=3, sticky="w")

        self._build_entry_row(detail_frame, 1, "Cookie name", self.cookie_name_var)
        self._build_combobox_row(
            detail_frame,
            2,
            "Linked profile",
            self.cookie_profile_choice_var,
            target_name="cookie_profile",
        )

        self.cookie_payload_text = self._build_text_row(
            detail_frame,
            3,
            "Raw cookie payload",
            height=12,
        )
        self.cookie_notes_text = self._build_text_row(
            detail_frame,
            4,
            "Notes",
            height=6,
        )

        cookie_action_frame = tk.Frame(detail_frame, bg=self.config.panel_color)
        cookie_action_frame.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(14, 0))
        cookie_action_frame.grid_columnconfigure(1, weight=1)

        self.save_cookie_button = tk.Button(
            cookie_action_frame,
            text="Save Cookie",
            command=self._save_cookie,
            bg=self.config.accent_color,
            fg="#f8fafc",
            relief=tk.FLAT,
            padx=18,
            pady=8,
            font=("Segoe UI Semibold", 10),
        )
        self.save_cookie_button.grid(row=0, column=1, sticky="e")

        self.cookie_status_label = tk.Label(
            detail_frame,
            textvariable=self.cookie_status_var,
            font=("Segoe UI", 10),
            bg=self.config.panel_color,
            fg=self.config.text_color,
            anchor="w",
            justify=tk.LEFT,
            wraplength=620,
        )
        self.cookie_status_label.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(18, 0))

        tk.Label(
            detail_frame,
            text=f"Cookie/account library: {self.workspace_store.path}",
            font=("Consolas", 9),
            bg=self.config.panel_color,
            fg=self.config.muted_color,
            anchor="w",
            justify=tk.LEFT,
        ).grid(row=7, column=0, columnspan=3, sticky="w", pady=(14, 0))

    def _create_accounts_tab(self, parent: tk.Frame) -> None:
        parent.grid_columnconfigure(1, weight=1)
        parent.grid_rowconfigure(0, weight=1)

        library_frame = self._create_panel(parent)
        library_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 18))
        library_frame.grid_rowconfigure(2, weight=1)
        library_frame.grid_columnconfigure(0, weight=1)

        tk.Label(
            library_frame,
            text="Saved Zalo Accounts",
            font=("Segoe UI Semibold", 13),
            bg=self.config.panel_color,
            fg=self.config.text_color,
        ).grid(row=0, column=0, sticky="w")
        tk.Label(
            library_frame,
            text="Store operator-facing Zalo account records and optionally link them to profiles or cookies.",
            font=("Segoe UI", 9),
            bg=self.config.panel_color,
            fg=self.config.muted_color,
            justify=tk.LEFT,
            wraplength=280,
        ).grid(row=1, column=0, sticky="w", pady=(4, 12))

        account_list_frame = tk.Frame(library_frame, bg=self.config.panel_color)
        account_list_frame.grid(row=2, column=0, sticky="nsew")
        account_list_frame.grid_rowconfigure(0, weight=1)
        account_list_frame.grid_columnconfigure(0, weight=1)

        self.account_listbox = tk.Listbox(
            account_list_frame,
            activestyle="none",
            exportselection=False,
            font=("Segoe UI", 10),
            bg="#ffffff",
            fg=self.config.text_color,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground="#cbd5e1",
            selectbackground="#fde68a",
            selectforeground=self.config.text_color,
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

        self.new_account_button = tk.Button(
            account_actions,
            text="New Account",
            command=self._start_new_account,
            bg=self.config.accent_alt_color,
            fg=self.config.text_color,
            relief=tk.FLAT,
            padx=14,
            pady=8,
            font=("Segoe UI", 9),
        )
        self.new_account_button.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.delete_account_button = tk.Button(
            account_actions,
            text="Delete",
            command=self._delete_account,
            bg="#fee2e2",
            fg="#991b1b",
            relief=tk.FLAT,
            padx=14,
            pady=8,
            font=("Segoe UI", 9),
        )
        self.delete_account_button.grid(row=0, column=1, sticky="ew")

        detail_frame = self._create_panel(parent)
        detail_frame.grid(row=0, column=1, sticky="nsew")
        detail_frame.grid_columnconfigure(1, weight=1)

        tk.Label(
            detail_frame,
            text="Account Details",
            font=("Segoe UI Semibold", 13),
            bg=self.config.panel_color,
            fg=self.config.text_color,
        ).grid(row=0, column=0, columnspan=3, sticky="w")

        self._build_entry_row(detail_frame, 1, "Account name", self.account_name_var)
        self._build_entry_row(detail_frame, 2, "Phone / login", self.account_phone_var)
        self._build_combobox_row(
            detail_frame,
            3,
            "Linked profile",
            self.account_profile_choice_var,
            target_name="account_profile",
        )
        self._build_combobox_row(
            detail_frame,
            4,
            "Linked cookie",
            self.account_cookie_choice_var,
            target_name="account_cookie",
        )
        self.account_notes_text = self._build_text_row(
            detail_frame,
            5,
            "Notes",
            height=8,
        )

        account_action_frame = tk.Frame(detail_frame, bg=self.config.panel_color)
        account_action_frame.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(14, 0))
        account_action_frame.grid_columnconfigure(1, weight=1)

        self.save_account_button = tk.Button(
            account_action_frame,
            text="Save Account",
            command=self._save_account,
            bg=self.config.accent_color,
            fg="#f8fafc",
            relief=tk.FLAT,
            padx=18,
            pady=8,
            font=("Segoe UI Semibold", 10),
        )
        self.save_account_button.grid(row=0, column=1, sticky="e")

        self.account_status_label = tk.Label(
            detail_frame,
            textvariable=self.account_status_var,
            font=("Segoe UI", 10),
            bg=self.config.panel_color,
            fg=self.config.text_color,
            anchor="w",
            justify=tk.LEFT,
            wraplength=620,
        )
        self.account_status_label.grid(row=7, column=0, columnspan=3, sticky="ew", pady=(18, 0))

        tk.Label(
            detail_frame,
            text=f"Cookie/account library: {self.workspace_store.path}",
            font=("Consolas", 9),
            bg=self.config.panel_color,
            fg=self.config.muted_color,
            anchor="w",
            justify=tk.LEFT,
        ).grid(row=8, column=0, columnspan=3, sticky="w", pady=(14, 0))

    def _create_panel(self, parent: tk.Misc) -> tk.Frame:
        return tk.Frame(
            parent,
            bg=self.config.panel_color,
            padx=18,
            pady=18,
            highlightthickness=1,
            highlightbackground="#d6d3d1",
        )

    def _build_path_row(
        self,
        parent: tk.Frame,
        row: int,
        label: str,
        variable: tk.StringVar,
        button_text: str,
        button_command,
    ) -> None:
        self._build_entry_label(parent, row, label)

        entry = tk.Entry(
            parent,
            textvariable=variable,
            font=("Consolas", 10),
            bg="#ffffff",
            fg=self.config.text_color,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground="#cbd5e1",
            highlightcolor=self.config.accent_color,
        )
        entry.grid(row=row, column=1, sticky="ew", padx=(14, 12), pady=8, ipady=6)

        tk.Button(
            parent,
            text=button_text,
            command=button_command,
            bg=self.config.accent_alt_color,
            fg=self.config.text_color,
            activebackground="#cbd5e1",
            activeforeground=self.config.text_color,
            relief=tk.FLAT,
            padx=14,
            pady=6,
            font=("Segoe UI", 9),
        ).grid(row=row, column=2, sticky="e", pady=8)

    def _build_entry_row(
        self,
        parent: tk.Frame,
        row: int,
        label: str,
        variable: tk.StringVar,
        readonly: bool = False,
    ) -> None:
        self._build_entry_label(parent, row, label)

        entry = tk.Entry(
            parent,
            textvariable=variable,
            state="readonly" if readonly else "normal",
            font=("Consolas", 10),
            bg="#ffffff",
            fg=self.config.text_color,
            readonlybackground="#f8fafc",
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground="#cbd5e1",
            highlightcolor=self.config.accent_color,
        )
        entry.grid(row=row, column=1, sticky="ew", padx=(14, 12), pady=8, ipady=6)

    def _build_combobox_row(
        self,
        parent: tk.Frame,
        row: int,
        label: str,
        variable: tk.StringVar,
        *,
        target_name: str,
    ) -> None:
        self._build_entry_label(parent, row, label)

        combo = ttk.Combobox(
            parent,
            textvariable=variable,
            state="readonly",
            font=("Segoe UI", 10),
        )
        combo.grid(row=row, column=1, sticky="ew", padx=(14, 12), pady=8)
        combo.configure(values=())

        if target_name == "cookie_profile":
            self.cookie_profile_combobox = combo
        elif target_name == "account_profile":
            self.account_profile_combobox = combo
        elif target_name == "account_cookie":
            self.account_cookie_combobox = combo

    def _build_text_row(
        self,
        parent: tk.Frame,
        row: int,
        label: str,
        *,
        height: int,
    ) -> tk.Text:
        self._build_entry_label(parent, row, label)

        text_frame = tk.Frame(parent, bg=self.config.panel_color)
        text_frame.grid(row=row, column=1, columnspan=2, sticky="nsew", padx=(14, 0), pady=8)
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)

        text_widget = tk.Text(
            text_frame,
            height=height,
            wrap="word",
            font=("Consolas", 10),
            bg="#ffffff",
            fg=self.config.text_color,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground="#cbd5e1",
            highlightcolor=self.config.accent_color,
        )
        text_widget.grid(row=0, column=0, sticky="nsew")

        scrollbar = tk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        text_widget.configure(yscrollcommand=scrollbar.set)
        return text_widget

    def _build_entry_label(self, parent: tk.Frame, row: int, label: str) -> None:
        tk.Label(
            parent,
            text=label,
            font=("Segoe UI", 10),
            bg=self.config.panel_color,
            fg=self.config.text_color,
        ).grid(row=row, column=0, sticky="w", pady=8)

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
        self._refresh_cookie_choices()
        self._update_action_states()

    def _refresh_workspace_state(
        self,
        preferred_cookie_id: str | None = None,
        preferred_account_id: str | None = None,
    ) -> None:
        self._apply_workspace_state(
            self.workspace_use_case.load_state(),
            preferred_cookie_id=preferred_cookie_id,
            preferred_account_id=preferred_account_id,
        )

    def _apply_workspace_state(
        self,
        state: ZaloWorkspaceState,
        *,
        preferred_cookie_id: str | None = None,
        preferred_account_id: str | None = None,
    ) -> None:
        self._workspace_state = state
        self._cookies_by_id = {cookie.id: cookie for cookie in state.cookies}
        self._cookie_ids = [cookie.id for cookie in state.cookies]
        self._accounts_by_id = {account.id: account for account in state.accounts}
        self._account_ids = [account.id for account in state.accounts]

        selected_cookie_id = preferred_cookie_id if preferred_cookie_id in self._cookies_by_id else state.selected_cookie_id
        if selected_cookie_id not in self._cookies_by_id:
            selected_cookie_id = self._cookie_ids[0] if self._cookie_ids else None

        selected_account_id = (
            preferred_account_id if preferred_account_id in self._accounts_by_id else state.selected_account_id
        )
        if selected_account_id not in self._accounts_by_id:
            selected_account_id = self._account_ids[0] if self._account_ids else None

        self._is_refreshing_cookie_list = True
        self.cookie_listbox.delete(0, tk.END)
        for cookie in state.cookies:
            self.cookie_listbox.insert(tk.END, cookie.name)
        self.cookie_listbox.selection_clear(0, tk.END)
        if selected_cookie_id is not None:
            cookie_index = self._cookie_ids.index(selected_cookie_id)
            self.cookie_listbox.selection_set(cookie_index)
            self.cookie_listbox.activate(cookie_index)
            self.cookie_listbox.see(cookie_index)
        self._is_refreshing_cookie_list = False

        self._is_refreshing_account_list = True
        self.account_listbox.delete(0, tk.END)
        for account in state.accounts:
            label = account.name if not account.phone_number else f"{account.name} ({account.phone_number})"
            self.account_listbox.insert(tk.END, label)
        self.account_listbox.selection_clear(0, tk.END)
        if selected_account_id is not None:
            account_index = self._account_ids.index(selected_account_id)
            self.account_listbox.selection_set(account_index)
            self.account_listbox.activate(account_index)
            self.account_listbox.see(account_index)
        self._is_refreshing_account_list = False

        self._refresh_cookie_choices()
        self._refresh_profile_choices()

        if selected_cookie_id is not None:
            self._load_cookie_into_form(self._cookies_by_id[selected_cookie_id])
        else:
            self._load_new_cookie_defaults()

        if selected_account_id is not None:
            self._load_account_into_form(self._accounts_by_id[selected_account_id])
        else:
            self._load_new_account_defaults()

        self._update_cookie_action_states()
        self._update_account_action_states()

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

    def _load_cookie_into_form(self, cookie: SavedCookieEntry) -> None:
        self._current_edit_cookie_id = cookie.id
        self.cookie_name_var.set(cookie.name)
        self._set_profile_choice_var(self.cookie_profile_choice_var, cookie.profile_id)
        self._set_text(self.cookie_payload_text, cookie.raw_cookie)
        self._set_text(self.cookie_notes_text, cookie.notes)

    def _load_new_cookie_defaults(self) -> None:
        self._current_edit_cookie_id = None
        self.cookie_name_var.set("")
        self.cookie_profile_choice_var.set("")
        self._set_text(self.cookie_payload_text, "")
        self._set_text(self.cookie_notes_text, "")
        self.cookie_listbox.selection_clear(0, tk.END)

    def _load_account_into_form(self, account: SavedZaloAccount) -> None:
        self._current_edit_account_id = account.id
        self.account_name_var.set(account.name)
        self.account_phone_var.set(account.phone_number)
        self._set_profile_choice_var(self.account_profile_choice_var, account.profile_id)
        self._set_cookie_choice_var(self.account_cookie_choice_var, account.cookie_id)
        self._set_text(self.account_notes_text, account.notes)

    def _load_new_account_defaults(self) -> None:
        self._current_edit_account_id = None
        self.account_name_var.set("")
        self.account_phone_var.set("")
        self.account_profile_choice_var.set("")
        self.account_cookie_choice_var.set("")
        self._set_text(self.account_notes_text, "")
        self.account_listbox.selection_clear(0, tk.END)

    def _start_new_profile(self) -> None:
        self._load_new_profile_defaults()
        self._set_status(
            "Creating a new saved profile. Paste a full Chrome profile path such as '...\\User Data\\Profile 1' and click Save Profile.",
            self.config.text_color,
        )
        self._update_action_states()

    def _start_new_cookie(self) -> None:
        self._load_new_cookie_defaults()
        self._set_cookie_status("Creating a new cookie entry.", self.config.text_color)
        self._update_cookie_action_states()

    def _start_new_account(self) -> None:
        self._load_new_account_defaults()
        self._set_account_status("Creating a new Zalo account entry.", self.config.text_color)
        self._update_account_action_states()

    def _selected_profile_ids(self) -> list[str]:
        return [self._profile_ids[index] for index in self.profile_listbox.curselection() if index < len(self._profile_ids)]

    def _selected_cookie_id(self) -> str | None:
        selection = self.cookie_listbox.curselection()
        if not selection:
            return None
        index = selection[0]
        if index >= len(self._cookie_ids):
            return None
        return self._cookie_ids[index]

    def _selected_account_id(self) -> str | None:
        selection = self.account_listbox.curselection()
        if not selection:
            return None
        index = selection[0]
        if index >= len(self._account_ids):
            return None
        return self._account_ids[index]

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
        if len(selected_profile_ids) == 1:
            self._set_status(f"Selected '{self._profiles_by_id[primary_profile_id].name}'.", self.config.text_color)
            return

        self._set_status(
            f"Selected {len(selected_profile_ids)} profiles for grid launch. Save/Delete is disabled until only one profile is selected.",
            self.config.text_color,
        )

    def _on_cookie_selected(self, _event) -> None:
        if self._is_refreshing_cookie_list:
            return

        cookie_id = self._selected_cookie_id()
        if cookie_id is None:
            return

        try:
            state = self.workspace_use_case.select_cookie(cookie_id)
        except SavedCookieNotFoundError as exc:
            self._handle_cookie_error(str(exc))
            return

        self._apply_workspace_state(
            state,
            preferred_cookie_id=cookie_id,
            preferred_account_id=state.selected_account_id,
        )
        self._set_cookie_status(f"Selected cookie '{self._cookies_by_id[cookie_id].name}'.", self.config.text_color)

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
            preferred_cookie_id=state.selected_cookie_id,
            preferred_account_id=account_id,
        )
        self._set_account_status(
            f"Selected account '{self._accounts_by_id[account_id].name}'.",
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

    def _save_cookie(self) -> None:
        request = CookieUpsertRequest(
            cookie_id=self._current_edit_cookie_id,
            name=self.cookie_name_var.get(),
            raw_cookie=self._get_text(self.cookie_payload_text),
            profile_id=self._selected_profile_choice_id(self.cookie_profile_choice_var),
            notes=self._get_text(self.cookie_notes_text),
        )

        try:
            state = self.workspace_use_case.save_cookie(request)
        except SavedCookieConflictError as exc:
            self._handle_cookie_error(str(exc))
            return

        saved_cookie = next(cookie for cookie in state.cookies if cookie.id == state.selected_cookie_id)
        self._apply_workspace_state(
            state,
            preferred_cookie_id=saved_cookie.id,
            preferred_account_id=state.selected_account_id,
        )
        self._set_cookie_status(
            f"Saved cookie '{saved_cookie.name}'.",
            self.config.success_color,
        )

    def _save_account(self) -> None:
        request = ZaloAccountUpsertRequest(
            account_id=self._current_edit_account_id,
            name=self.account_name_var.get(),
            phone_number=self.account_phone_var.get(),
            profile_id=self._selected_profile_choice_id(self.account_profile_choice_var),
            cookie_id=self._selected_cookie_choice_id(self.account_cookie_choice_var),
            notes=self._get_text(self.account_notes_text),
        )

        try:
            state = self.workspace_use_case.save_account(request)
        except SavedZaloAccountConflictError as exc:
            self._handle_account_error(str(exc))
            return

        saved_account = next(account for account in state.accounts if account.id == state.selected_account_id)
        self._apply_workspace_state(
            state,
            preferred_cookie_id=state.selected_cookie_id,
            preferred_account_id=saved_account.id,
        )
        self._set_account_status(
            f"Saved account '{saved_account.name}'.",
            self.config.success_color,
        )

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

    def _delete_cookie(self) -> None:
        cookie_id = self._current_edit_cookie_id
        if cookie_id is None or cookie_id not in self._cookies_by_id:
            messagebox.showwarning("Delete cookie", "Select a saved cookie first.")
            return

        cookie_name = self._cookies_by_id[cookie_id].name
        if not messagebox.askyesno("Delete cookie", f"Delete saved cookie '{cookie_name}'?"):
            return

        try:
            state = self.workspace_use_case.delete_cookie(cookie_id)
        except SavedCookieNotFoundError as exc:
            self._handle_cookie_error(str(exc))
            return

        self._apply_workspace_state(
            state,
            preferred_cookie_id=state.selected_cookie_id,
            preferred_account_id=state.selected_account_id,
        )
        self._set_cookie_status(f"Deleted cookie '{cookie_name}'.", self.config.text_color)

    def _delete_account(self) -> None:
        account_id = self._current_edit_account_id
        if account_id is None or account_id not in self._accounts_by_id:
            messagebox.showwarning("Delete account", "Select a saved account first.")
            return

        account_name = self._accounts_by_id[account_id].name
        if not messagebox.askyesno("Delete account", f"Delete saved account '{account_name}'?"):
            return

        try:
            state = self.workspace_use_case.delete_account(account_id)
        except SavedZaloAccountNotFoundError as exc:
            self._handle_account_error(str(exc))
            return

        self._apply_workspace_state(
            state,
            preferred_cookie_id=state.selected_cookie_id,
            preferred_account_id=state.selected_account_id,
        )
        self._set_account_status(f"Deleted account '{account_name}'.", self.config.text_color)

    def _start_launch(self) -> None:
        if self._launch_in_progress:
            return

        selected_profile_ids = self._selected_profile_ids()
        if not selected_profile_ids and self._current_edit_profile_id in self._profiles_by_id:
            selected_profile_ids = [self._current_edit_profile_id]

        if not selected_profile_ids:
            messagebox.showwarning("Launch profile", "Save or select a Chrome profile before launching.")
            return

        self._launch_in_progress = True
        self._update_action_states()
        if len(selected_profile_ids) == 1:
            profile_name = self._profiles_by_id[selected_profile_ids[0]].name
            status_message = f"Launching '{profile_name}' from the Profiles tab..."
        else:
            launch_count = min(len(selected_profile_ids), DEFAULT_GRID_LAUNCH_LIMIT)
            status_message = (
                f"Launching {launch_count} selected profiles into a "
                f"{DEFAULT_GRID_COLUMNS}x{DEFAULT_GRID_ROWS} grid..."
            )
        self._set_status(status_message, self.config.accent_color)
        threading.Thread(target=self._launch_worker, args=(tuple(selected_profile_ids),), daemon=True).start()

    def _launch_worker(self, profile_ids: tuple[str, ...]) -> None:
        try:
            if len(profile_ids) == 1:
                result = self.use_case.launch_profile(profile_ids[0])
            else:
                result = self.use_case.launch_profiles_grid(profile_ids)
        except (LauncherValidationError, ChromeLaunchError, SavedProfileNotFoundError) as exc:
            self.root.after(0, lambda: self._handle_launch_error(str(exc)))
            return

        if isinstance(result, LaunchSavedProfileResult):
            self.root.after(0, lambda: self._handle_launch_success(result))
            return
        self.root.after(0, lambda: self._handle_grid_launch_success(result))

    def _handle_launch_success(self, result: LaunchSavedProfileResult) -> None:
        self._launch_in_progress = False
        self._refresh_state(preferred_profile_ids=[result.profile_id])
        self._update_action_states()

        status_message = (
            f"Launched '{result.profile_name}' using profile directory "
            f"'{result.launch_result.profile_directory}'."
        )
        if result.launch_result.window_placement is not None:
            status_message += " Fixed window bounds were applied."
        if not result.library_persisted:
            status_message += " The saved-profile selection could not be persisted."

        self._set_status(status_message, self.config.success_color)

    def _handle_grid_launch_success(self, result: LaunchSavedProfilesGridResult) -> None:
        self._launch_in_progress = False
        selected_profile_ids = [profile.profile_id for profile in result.profiles]
        self._refresh_state(preferred_profile_ids=selected_profile_ids)
        self._update_action_states()

        launched_count = len(result.profiles)
        detected_window_count = sum(1 for profile in result.profiles if profile.window_detected)
        status_message = (
            f"Launched {launched_count} profiles. "
            f"Tiled {result.tiled_window_count} window(s) into a "
            f"{result.grid_columns}x{result.grid_rows} grid."
        )
        if detected_window_count < launched_count:
            status_message += f" {launched_count - detected_window_count} window(s) were not detected in time."
        if result.omitted_profile_count:
            status_message += (
                f" {result.omitted_profile_count} selected profile(s) were omitted because the grid limit is "
                f"{DEFAULT_GRID_LAUNCH_LIMIT}."
            )
        if not result.library_persisted:
            status_message += " The primary selected profile could not be persisted."

        self._set_status(
            status_message,
            self.config.success_color if detected_window_count == launched_count and not result.omitted_profile_count else self.config.text_color,
        )

    def _handle_launch_error(self, message: str) -> None:
        self._launch_in_progress = False
        self._update_action_states()
        self._set_status(message, self.config.error_color)
        messagebox.showerror("Launch failed", message)

    def _handle_data_error(self, message: str) -> None:
        self._set_status(message, self.config.error_color)
        messagebox.showerror("Profile error", message)

    def _handle_cookie_error(self, message: str) -> None:
        self._set_cookie_status(message, self.config.error_color)
        messagebox.showerror("Cookie error", message)

    def _handle_account_error(self, message: str) -> None:
        self._set_account_status(message, self.config.error_color)
        messagebox.showerror("Account error", message)

    def _refresh_profile_choices(self) -> None:
        self._profile_name_to_id = {profile.name: profile.id for profile in self._profiles_by_id.values()}
        values = tuple(profile.name for profile in self._profiles_by_id.values())
        if self.cookie_profile_combobox is not None:
            self.cookie_profile_combobox.configure(values=values)
        if self.account_profile_combobox is not None:
            self.account_profile_combobox.configure(values=values)
        if self.cookie_profile_choice_var.get() not in values:
            self.cookie_profile_choice_var.set("")
        if self.account_profile_choice_var.get() not in values:
            self.account_profile_choice_var.set("")

    def _refresh_cookie_choices(self) -> None:
        self._cookie_name_to_id = {cookie.name: cookie.id for cookie in self._cookies_by_id.values()}
        values = tuple(cookie.name for cookie in self._cookies_by_id.values())
        if self.account_cookie_combobox is not None:
            self.account_cookie_combobox.configure(values=values)
        if self.account_cookie_choice_var.get() not in values:
            self.account_cookie_choice_var.set("")

    def _selected_profile_choice_id(self, variable: tk.StringVar) -> str | None:
        return self._profile_name_to_id.get(variable.get().strip())

    def _selected_cookie_choice_id(self, variable: tk.StringVar) -> str | None:
        return self._cookie_name_to_id.get(variable.get().strip())

    def _set_profile_choice_var(self, variable: tk.StringVar, profile_id: str | None) -> None:
        if profile_id is None or profile_id not in self._profiles_by_id:
            variable.set("")
            return
        variable.set(self._profiles_by_id[profile_id].name)

    def _set_cookie_choice_var(self, variable: tk.StringVar, cookie_id: str | None) -> None:
        if cookie_id is None or cookie_id not in self._cookies_by_id:
            variable.set("")
            return
        variable.set(self._cookies_by_id[cookie_id].name)

    def _get_text(self, widget: tk.Text | None) -> str:
        if widget is None:
            return ""
        return widget.get("1.0", tk.END).strip()

    def _set_text(self, widget: tk.Text | None, value: str) -> None:
        if widget is None:
            return
        widget.delete("1.0", tk.END)
        if value:
            widget.insert("1.0", value)

    def _update_action_states(self) -> None:
        selected_count = len(self._selected_profile_ids())
        has_saved_selection = selected_count > 0 or (
            self._current_edit_profile_id is not None and self._current_edit_profile_id in self._profiles_by_id
        )
        has_multi_selection = selected_count > 1

        if self._launch_in_progress:
            self.launch_button.configure(state="disabled", text="Launching...")
            self.save_button.configure(state="disabled")
            self.new_button.configure(state="disabled")
            self.delete_button.configure(state="disabled")
            self.profile_listbox.configure(state="disabled")
            return

        self.launch_button.configure(
            state="normal" if has_saved_selection else "disabled",
            text="Launch Grid 4x2" if has_multi_selection else "Launch Selected",
        )
        self.save_button.configure(state="disabled" if has_multi_selection else "normal")
        self.new_button.configure(state="normal")
        self.delete_button.configure(
            state="normal"
            if not has_multi_selection and self._current_edit_profile_id in self._profiles_by_id
            else "disabled"
        )
        self.profile_listbox.configure(state="normal")

    def _update_cookie_action_states(self) -> None:
        self.delete_cookie_button.configure(
            state="normal" if self._current_edit_cookie_id in self._cookies_by_id else "disabled"
        )

    def _update_account_action_states(self) -> None:
        self.delete_account_button.configure(
            state="normal" if self._current_edit_account_id in self._accounts_by_id else "disabled"
        )

    def _set_status(self, message: str, color: str) -> None:
        self.status_var.set(message)
        self.status_label.configure(fg=color)

    def _set_cookie_status(self, message: str, color: str) -> None:
        self.cookie_status_var.set(message)
        self.cookie_status_label.configure(fg=color)

    def _set_account_status(self, message: str, color: str) -> None:
        self.account_status_var.set(message)
        self.account_status_label.configure(fg=color)


def main() -> None:
    root = tk.Tk()
    ZaloLauncherGui(root)
    root.mainloop()


if __name__ == "__main__":
    main()
