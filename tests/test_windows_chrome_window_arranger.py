import types

from browser_automation.infrastructure.chrome_launcher.windows_chrome_window_arranger import (
    WindowRect,
    WindowsChromeWindowArranger,
    calculate_grid_rectangles,
)


def test_calculate_grid_rectangles_returns_4x2_cells_in_order() -> None:
    work_area = WindowRect(left=0, top=0, right=1920, bottom=1080)

    rectangles = calculate_grid_rectangles(
        work_area,
        columns=4,
        rows=2,
        count=8,
    )

    assert rectangles[0] == WindowRect(left=0, top=0, right=480, bottom=540)
    assert rectangles[1] == WindowRect(left=480, top=0, right=960, bottom=540)
    assert rectangles[3] == WindowRect(left=1440, top=0, right=1920, bottom=540)
    assert rectangles[4] == WindowRect(left=0, top=540, right=480, bottom=1080)
    assert rectangles[7] == WindowRect(left=1440, top=540, right=1920, bottom=1080)


def test_calculate_grid_rectangles_consumes_full_work_area_with_integer_boundaries() -> None:
    work_area = WindowRect(left=5, top=10, right=1005, bottom=611)

    rectangles = calculate_grid_rectangles(
        work_area,
        columns=4,
        rows=2,
        count=8,
    )

    assert rectangles[0] == WindowRect(left=5, top=10, right=255, bottom=310)
    assert rectangles[1].left == rectangles[0].right
    assert rectangles[3].right == 1005
    assert rectangles[4].top == rectangles[0].bottom
    assert rectangles[7] == WindowRect(left=755, top=310, right=1005, bottom=611)


def test_windows_arranger_calculate_grid_placements_maps_rectangles_to_window_bounds() -> None:
    arranger = WindowsChromeWindowArranger()
    arranger._supported = True
    arranger._get_primary_work_area = types.MethodType(
        lambda self: WindowRect(left=0, top=0, right=1200, bottom=800),
        arranger,
    )

    placements = arranger.calculate_grid_placements(count=3, columns=4, rows=2)

    assert [(placement.left, placement.top, placement.width, placement.height) for placement in placements] == [
        (0, 0, 300, 400),
        (300, 0, 300, 400),
        (600, 0, 300, 400),
    ]
