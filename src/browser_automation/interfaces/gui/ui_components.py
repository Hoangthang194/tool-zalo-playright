from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from tkinter import scrolledtext, ttk


@dataclass(frozen=True, slots=True)
class SharedGuiTheme:
    bg_color: str = "#f3efe7"
    panel_color: str = "#fffaf2"
    header_color: str = "#1f3a5f"
    accent_color: str = "#0f766e"
    accent_alt_color: str = "#e2e8f0"
    success_color: str = "#166534"
    error_color: str = "#b42318"
    text_color: str = "#172b3a"
    muted_color: str = "#5f6c7b"
    danger_bg: str = "#fee2e2"
    danger_fg: str = "#991b1b"
    border_color: str = "#cbd5e1"
    panel_border_color: str = "#d6d3d1"
    input_bg: str = "#ffffff"
    input_readonly_bg: str = "#f8fafc"
    primary_active_bg: str = "#115e59"
    secondary_active_bg: str = "#cbd5e1"
    danger_active_bg: str = "#fecaca"
    console_bg: str = "#1c2735"
    console_fg: str = "#c9d3df"
    content_padx: int = 24
    content_pady: int = 20
    header_padx: int = 28
    header_pady: int = 24
    panel_padx: int = 18
    panel_pady: int = 18
    field_ipady: int = 7
    label_pady: int = 8
    button_padx: int = 14
    button_pady: int = 8


class SharedGuiFactory:
    combobox_style_name = "Shared.TCombobox"

    def __init__(self, root: tk.Misc, theme: SharedGuiTheme) -> None:
        self.theme = theme
        self.style = ttk.Style(root)
        self._configure_styles()

    def _configure_styles(self) -> None:
        # Keeps ttk.Combobox height aligned with tk.Entry on Windows themes.
        self.style.configure(self.combobox_style_name, padding=(8, 2, 8, 2))

    def configure_window(
        self,
        root: tk.Tk,
        *,
        title: str,
        width: int,
        height: int,
        min_width: int | None = None,
        min_height: int | None = None,
    ) -> None:
        root.title(title)
        root.geometry(f"{width}x{height}")
        if min_width is not None and min_height is not None:
            root.minsize(min_width, min_height)
        root.configure(bg=self.theme.bg_color)

    def create_header(
        self,
        parent: tk.Misc,
        *,
        title: str,
        subtitle: str,
        wraplength: int,
    ) -> tk.Frame:
        frame = tk.Frame(
            parent,
            bg=self.theme.header_color,
            padx=self.theme.header_padx,
            pady=self.theme.header_pady,
        )
        frame.pack(fill=tk.X)

        tk.Label(
            frame,
            text=title,
            font=("Segoe UI Semibold", 18),
            bg=self.theme.header_color,
            fg="#f8fafc",
        ).pack(anchor=tk.W)
        tk.Label(
            frame,
            text=subtitle,
            font=("Segoe UI", 10),
            bg=self.theme.header_color,
            fg="#dbe4f0",
            justify=tk.LEFT,
            wraplength=wraplength,
        ).pack(anchor=tk.W, pady=(6, 0))
        return frame

    def create_content_frame(self, parent: tk.Misc) -> tk.Frame:
        frame = tk.Frame(
            parent,
            bg=self.theme.bg_color,
            padx=self.theme.content_padx,
            pady=self.theme.content_pady,
        )
        frame.pack(fill=tk.BOTH, expand=True)
        return frame

    def create_panel(self, parent: tk.Misc) -> tk.Frame:
        return tk.Frame(
            parent,
            bg=self.theme.panel_color,
            padx=self.theme.panel_padx,
            pady=self.theme.panel_pady,
            highlightthickness=1,
            highlightbackground=self.theme.panel_border_color,
        )

    def create_section_label(self, parent: tk.Misc, text: str) -> tk.Label:
        return tk.Label(
            parent,
            text=text,
            font=("Segoe UI Semibold", 13),
            bg=self.theme.panel_color,
            fg=self.theme.text_color,
        )

    def create_body_label(
        self,
        parent: tk.Misc,
        text: str,
        *,
        wraplength: int | None = None,
        fg: str | None = None,
        bg: str | None = None,
        font: tuple[str, int] | tuple[str, int, str] = ("Segoe UI", 10),
        justify: str = tk.LEFT,
        anchor: str = "w",
    ) -> tk.Label:
        label = tk.Label(
            parent,
            text=text,
            font=font,
            bg=self.theme.panel_color if bg is None else bg,
            fg=self.theme.text_color if fg is None else fg,
            justify=justify,
            anchor=anchor,
        )
        if wraplength is not None:
            label.configure(wraplength=wraplength)
        return label

    def create_muted_label(self, parent: tk.Misc, text: str, *, wraplength: int) -> tk.Label:
        return self.create_body_label(
            parent,
            text,
            wraplength=wraplength,
            fg=self.theme.muted_color,
            font=("Segoe UI", 9),
        )

    def create_code_label(self, parent: tk.Misc, text: str) -> tk.Label:
        return self.create_body_label(
            parent,
            text,
            fg=self.theme.muted_color,
            font=("Consolas", 9),
            justify=tk.LEFT,
            anchor="w",
        )

    def create_entry(
        self,
        parent: tk.Misc,
        *,
        textvariable: tk.StringVar,
        readonly: bool = False,
        width: int | None = None,
    ) -> tk.Entry:
        kwargs: dict[str, object] = {}
        if width is not None:
            kwargs["width"] = width
        return tk.Entry(
            parent,
            textvariable=textvariable,
            state="readonly" if readonly else "normal",
            font=("Consolas", 10),
            bg=self.theme.input_bg,
            fg=self.theme.text_color,
            readonlybackground=self.theme.input_readonly_bg,
            insertbackground=self.theme.text_color,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=self.theme.border_color,
            highlightcolor=self.theme.accent_color,
            **kwargs,
        )

    def create_combobox(
        self,
        parent: tk.Misc,
        *,
        textvariable: tk.StringVar,
        values: tuple[str, ...] = (),
        state: str = "readonly",
    ) -> ttk.Combobox:
        combo = ttk.Combobox(
            parent,
            textvariable=textvariable,
            values=values,
            state=state,
            font=("Consolas", 10),
            style=self.combobox_style_name,
        )
        return combo

    def create_button(
        self,
        parent: tk.Misc,
        *,
        text: str,
        command,
        variant: str = "secondary",
        font: tuple[str, int] | tuple[str, int, str] | None = None,
        padx: int | None = None,
        pady: int | None = None,
    ) -> tk.Button:
        if variant == "primary":
            bg = self.theme.accent_color
            fg = "#f8fafc"
            active_bg = self.theme.primary_active_bg
            active_fg = "#f8fafc"
            default_font = ("Segoe UI Semibold", 10)
        elif variant == "danger":
            bg = self.theme.danger_bg
            fg = self.theme.danger_fg
            active_bg = self.theme.danger_active_bg
            active_fg = self.theme.danger_fg
            default_font = ("Segoe UI", 9)
        else:
            bg = self.theme.accent_alt_color
            fg = self.theme.text_color
            active_bg = self.theme.secondary_active_bg
            active_fg = self.theme.text_color
            default_font = ("Segoe UI", 9)

        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            activebackground=active_bg,
            activeforeground=active_fg,
            relief=tk.FLAT,
            padx=self.theme.button_padx if padx is None else padx,
            pady=self.theme.button_pady if pady is None else pady,
            font=default_font if font is None else font,
        )

    def create_listbox(
        self,
        parent: tk.Misc,
        *,
        multiselect: bool = False,
        select_background: str | None = None,
    ) -> tk.Listbox:
        return tk.Listbox(
            parent,
            activestyle="none",
            exportselection=False,
            font=("Segoe UI", 10),
            bg=self.theme.input_bg,
            fg=self.theme.text_color,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=self.theme.border_color,
            selectmode=tk.EXTENDED if multiselect else tk.BROWSE,
            selectbackground=self.theme.accent_alt_color if select_background is None else select_background,
            selectforeground=self.theme.text_color,
        )

    def create_status_label(
        self,
        parent: tk.Misc,
        *,
        textvariable: tk.StringVar,
        wraplength: int,
    ) -> tk.Label:
        return tk.Label(
            parent,
            textvariable=textvariable,
            font=("Segoe UI", 10),
            bg=self.theme.panel_color,
            fg=self.theme.text_color,
            anchor="w",
            justify=tk.LEFT,
            wraplength=wraplength,
        )

    def create_scrolled_log(self, parent: tk.Misc, *, height: int = 15) -> scrolledtext.ScrolledText:
        return scrolledtext.ScrolledText(
            parent,
            height=height,
            bg=self.theme.console_bg,
            fg=self.theme.console_fg,
            font=("Consolas", 10),
            state="disabled",
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=self.theme.border_color,
            insertbackground=self.theme.console_fg,
            border=0,
        )

    def grid_form_label(self, parent: tk.Misc, row: int, text: str) -> tk.Label:
        label = self.create_body_label(
            parent,
            text,
            font=("Segoe UI", 10),
            fg=self.theme.text_color,
            bg=self.theme.panel_color,
        )
        label.grid(row=row, column=0, sticky="w", pady=self.theme.label_pady)
        return label

    def grid_entry_row(
        self,
        parent: tk.Misc,
        *,
        row: int,
        label: str,
        variable: tk.StringVar,
        readonly: bool = False,
    ) -> tk.Entry:
        self.grid_form_label(parent, row, label)
        entry = self.create_entry(parent, textvariable=variable, readonly=readonly)
        entry.grid(
            row=row,
            column=1,
            sticky="ew",
            padx=(14, 12),
            pady=self.theme.label_pady,
            ipady=self.theme.field_ipady,
        )
        return entry

    def grid_combobox_row(
        self,
        parent: tk.Misc,
        *,
        row: int,
        label: str,
        variable: tk.StringVar,
    ) -> ttk.Combobox:
        self.grid_form_label(parent, row, label)
        combo = self.create_combobox(parent, textvariable=variable)
        combo.grid(
            row=row,
            column=1,
            sticky="ew",
            padx=(14, 12),
            pady=self.theme.label_pady,
            ipady=self.theme.field_ipady,
        )
        return combo

    def grid_path_row(
        self,
        parent: tk.Misc,
        *,
        row: int,
        label: str,
        variable: tk.StringVar,
        button_text: str,
        button_command,
    ) -> tuple[tk.Entry, tk.Button]:
        self.grid_form_label(parent, row, label)
        entry = self.create_entry(parent, textvariable=variable)
        entry.grid(
            row=row,
            column=1,
            sticky="ew",
            padx=(14, 12),
            pady=self.theme.label_pady,
            ipady=self.theme.field_ipady,
        )
        button = self.create_button(
            parent,
            text=button_text,
            command=button_command,
            variant="secondary",
            font=("Segoe UI", 9),
            pady=6,
        )
        button.grid(row=row, column=2, sticky="e", pady=self.theme.label_pady)
        return entry, button
