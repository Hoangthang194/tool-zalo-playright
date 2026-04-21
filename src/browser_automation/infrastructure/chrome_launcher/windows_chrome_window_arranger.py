from __future__ import annotations

import ctypes
import os
import time
from collections.abc import Callable, Collection, Sequence
from dataclasses import dataclass

from browser_automation.domain.exceptions import ChromeLaunchError
from browser_automation.domain.zalo_launcher import WindowPlacement

if os.name == "nt":
    from ctypes import wintypes
    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
else:
    wintypes = None
    WNDENUMPROC = None

SPI_GETWORKAREA = 0x0030
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
GW_OWNER = 4
SW_RESTORE = 9
_CHROME_WINDOW_CLASS_NAME = "Chrome_WidgetWin_1"


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


@dataclass(frozen=True, slots=True)
class WindowRect:
    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top


def calculate_grid_rectangles(
    work_area: WindowRect,
    *,
    columns: int,
    rows: int,
    count: int,
) -> tuple[WindowRect, ...]:
    if columns <= 0 or rows <= 0:
        raise ValueError("Grid columns and rows must be positive integers.")
    if count <= 0:
        return ()

    max_cells = columns * rows
    target_count = min(count, max_cells)
    work_width = work_area.width
    work_height = work_area.height
    rectangles: list[WindowRect] = []

    for cell_index in range(target_count):
        row_index, column_index = divmod(cell_index, columns)
        left = work_area.left + (work_width * column_index) // columns
        right = work_area.left + (work_width * (column_index + 1)) // columns
        top = work_area.top + (work_height * row_index) // rows
        bottom = work_area.top + (work_height * (row_index + 1)) // rows
        rectangles.append(
            WindowRect(
                left=left,
                top=top,
                right=right,
                bottom=bottom,
            )
        )

    return tuple(rectangles)


class WindowsChromeWindowArranger:
    def __init__(
        self,
        *,
        poll_interval_seconds: float = 0.15,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self._poll_interval_seconds = poll_interval_seconds
        self._sleep = sleeper
        self._supported = os.name == "nt"

        if self._supported:
            self._user32 = ctypes.WinDLL("user32", use_last_error=True)
            self._kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            self._configure_win32_bindings()
        else:
            self._user32 = None
            self._kernel32 = None

    def snapshot_window_handles(self) -> frozenset[int]:
        if not self._supported:
            return frozenset()
        return frozenset(self._enumerate_chrome_window_handles())

    def calculate_grid_placements(
        self,
        *,
        count: int,
        columns: int,
        rows: int,
    ) -> tuple[WindowPlacement, ...]:
        if count <= 0:
            return ()
        if not self._supported:
            raise ChromeLaunchError("Chrome window placement is only supported on Windows.")

        rectangles = calculate_grid_rectangles(
            self._get_primary_work_area(),
            columns=columns,
            rows=rows,
            count=count,
        )
        return tuple(
            WindowPlacement(
                left=rectangle.left,
                top=rectangle.top,
                width=rectangle.width,
                height=rectangle.height,
            )
            for rectangle in rectangles
        )

    def wait_for_new_window(
        self,
        existing_window_handles: Collection[int],
        timeout_seconds: float,
    ) -> int | None:
        if not self._supported:
            return None

        known_window_handles = set(existing_window_handles)
        deadline = time.monotonic() + timeout_seconds

        while True:
            current_window_handles = self.snapshot_window_handles()
            for window_handle in current_window_handles:
                if window_handle not in known_window_handles:
                    return window_handle

            if time.monotonic() >= deadline:
                return None

            self._sleep(self._poll_interval_seconds)

    def apply_window_placement(
        self,
        window_handle: int,
        placement: WindowPlacement,
    ) -> None:
        if not self._supported:
            raise ChromeLaunchError("Chrome window placement is only supported on Windows.")
        self._move_window_to_placement(window_handle, placement)

    def tile_windows(
        self,
        window_handles: Sequence[int],
        *,
        columns: int,
        rows: int,
    ) -> int:
        if not window_handles:
            return 0
        if not self._supported:
            raise ChromeLaunchError("Chrome window tiling is only supported on Windows.")

        placements = self.calculate_grid_placements(
            count=len(window_handles),
            columns=columns,
            rows=rows,
        )

        for window_handle, placement in zip(window_handles, placements, strict=False):
            self._move_window_to_placement(window_handle, placement)

        return len(placements)

    def _get_primary_work_area(self) -> WindowRect:
        rect = RECT()
        if not self._user32.SystemParametersInfoW(
            SPI_GETWORKAREA,
            0,
            ctypes.byref(rect),
            0,
        ):
            raise ChromeLaunchError("Could not determine the primary monitor work area.")

        return WindowRect(
            left=rect.left,
            top=rect.top,
            right=rect.right,
            bottom=rect.bottom,
        )

    def _enumerate_chrome_window_handles(self) -> tuple[int, ...]:
        handles: list[int] = []

        @WNDENUMPROC
        def enum_windows_proc(hwnd, _lparam):
            if self._is_chrome_top_level_window(hwnd):
                handles.append(int(hwnd))
            return True

        if not self._user32.EnumWindows(enum_windows_proc, 0):
            raise ChromeLaunchError("Could not enumerate top-level windows.")

        return tuple(handles)

    def _is_chrome_top_level_window(self, hwnd: int) -> bool:
        if not self._user32.IsWindowVisible(hwnd):
            return False
        if self._user32.GetWindow(hwnd, GW_OWNER):
            return False
        if self._get_window_class_name(hwnd) != _CHROME_WINDOW_CLASS_NAME:
            return False

        process_id = self._get_window_process_id(hwnd)
        if process_id == 0:
            return False

        executable_name = self._get_process_executable_name(process_id)
        if executable_name is None:
            return False
        return executable_name.casefold() == "chrome.exe"

    def _get_window_class_name(self, hwnd: int) -> str:
        buffer = ctypes.create_unicode_buffer(256)
        length = self._user32.GetClassNameW(hwnd, buffer, len(buffer))
        if length <= 0:
            return ""
        return buffer.value

    def _get_window_process_id(self, hwnd: int) -> int:
        process_id = wintypes.DWORD(0)
        self._user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
        return int(process_id.value)

    def _get_process_executable_name(self, process_id: int) -> str | None:
        process_handle = self._kernel32.OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION,
            False,
            process_id,
        )
        if not process_handle:
            return None

        try:
            buffer_length = wintypes.DWORD(2048)
            image_path_buffer = ctypes.create_unicode_buffer(buffer_length.value)
            if not self._kernel32.QueryFullProcessImageNameW(
                process_handle,
                0,
                image_path_buffer,
                ctypes.byref(buffer_length),
            ):
                return None
            return os.path.basename(image_path_buffer.value)
        finally:
            self._kernel32.CloseHandle(process_handle)

    def _move_window_to_placement(
        self,
        window_handle: int,
        placement: WindowPlacement,
    ) -> None:
        self._user32.ShowWindow(window_handle, SW_RESTORE)
        if not self._user32.MoveWindow(
            window_handle,
            placement.left,
            placement.top,
            placement.width,
            placement.height,
            True,
        ):
            raise ChromeLaunchError(f"Could not move Chrome window handle {window_handle}.")

    def _configure_win32_bindings(self) -> None:
        self._user32.EnumWindows.argtypes = [WNDENUMPROC, wintypes.LPARAM]
        self._user32.EnumWindows.restype = wintypes.BOOL

        self._user32.IsWindowVisible.argtypes = [wintypes.HWND]
        self._user32.IsWindowVisible.restype = wintypes.BOOL

        self._user32.GetWindow.argtypes = [wintypes.HWND, ctypes.c_uint]
        self._user32.GetWindow.restype = wintypes.HWND

        self._user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
        self._user32.GetClassNameW.restype = ctypes.c_int

        self._user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        self._user32.GetWindowThreadProcessId.restype = wintypes.DWORD

        self._user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
        self._user32.ShowWindow.restype = wintypes.BOOL

        self._user32.MoveWindow.argtypes = [
            wintypes.HWND,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            wintypes.BOOL,
        ]
        self._user32.MoveWindow.restype = wintypes.BOOL

        self._user32.SystemParametersInfoW.argtypes = [
            ctypes.c_uint,
            ctypes.c_uint,
            ctypes.c_void_p,
            ctypes.c_uint,
        ]
        self._user32.SystemParametersInfoW.restype = wintypes.BOOL

        self._kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self._kernel32.OpenProcess.restype = wintypes.HANDLE

        self._kernel32.QueryFullProcessImageNameW.argtypes = [
            wintypes.HANDLE,
            wintypes.DWORD,
            wintypes.LPWSTR,
            ctypes.POINTER(wintypes.DWORD),
        ]
        self._kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL

        self._kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        self._kernel32.CloseHandle.restype = wintypes.BOOL
