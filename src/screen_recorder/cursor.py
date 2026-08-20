"""Mouse cursor overlay for captured frames (Windows only).

``mss`` grabs the raw screen buffer and does not include the cursor.
This module reads the current cursor bitmap via the Windows GDI API and
alpha-blends it onto captured frames at the cursor's screen position.
"""

import ctypes
import sys
from ctypes import wintypes

import numpy as np

if sys.platform == "win32":
    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32
else:
    user32 = None
    gdi32 = None

DIB_RGB_COLORS = 0
BI_RGB = 0


class CURSORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("hCursor", wintypes.HANDLE),
        ("ptScreenPos", wintypes.POINT),
    ]


class ICONINFO(ctypes.Structure):
    _fields_ = [
        ("fIcon", wintypes.BOOL),
        ("xHotspot", wintypes.DWORD),
        ("yHotspot", wintypes.DWORD),
        ("hbmMask", wintypes.HANDLE),
        ("hbmColor", wintypes.HANDLE),
    ]


class BITMAP(ctypes.Structure):
    _fields_ = [
        ("bmType", ctypes.c_long),
        ("bmWidth", ctypes.c_long),
        ("bmHeight", ctypes.c_long),
        ("bmWidthBytes", ctypes.c_long),
        ("bmPlanes", wintypes.WORD),
        ("bmBitsPixel", wintypes.WORD),
        ("bmBits", ctypes.c_void_p),
    ]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", ctypes.c_long),
        ("biHeight", ctypes.c_long),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", ctypes.c_long),
        ("biYPelsPerMeter", ctypes.c_long),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER)]


if sys.platform == "win32":
    user32.GetCursorInfo.argtypes = [ctypes.POINTER(CURSORINFO)]
    user32.GetCursorInfo.restype = wintypes.BOOL
    user32.GetIconInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(ICONINFO)]
    user32.GetIconInfo.restype = wintypes.BOOL
    user32.GetDC.argtypes = [wintypes.HWND]
    user32.GetDC.restype = wintypes.HDC
    user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
    user32.ReleaseDC.restype = ctypes.c_int
    gdi32.GetObjectW.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p]
    gdi32.GetObjectW.restype = ctypes.c_int
    gdi32.GetDIBits.argtypes = [
        wintypes.HDC,
        wintypes.HBITMAP,
        wintypes.UINT,
        wintypes.UINT,
        ctypes.c_void_p,
        ctypes.POINTER(BITMAPINFO),
        wintypes.UINT,
    ]
    gdi32.GetDIBits.restype = ctypes.c_int
    gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
    gdi32.DeleteObject.restype = wintypes.BOOL


def _blend_into(
    frame: np.ndarray,
    cursor_rgba: np.ndarray,
    cursor_x: int,
    cursor_y: int,
) -> None:
    """Alpha-blend cursor_rgba (HxWx4, 0-255) into frame at (cursor_x, cursor_y).

    Windows cursor bitmaps from GetIconInfo are stored with premultiplied
    alpha (color channels already multiplied by alpha), so the
    premultiplied compositing formula is used: src + dst * (1 - alpha).
    """
    ch, cw = cursor_rgba.shape[:2]
    fh, fw = frame.shape[:2]

    x0 = max(0, cursor_x)
    y0 = max(0, cursor_y)
    x1 = min(fw, cursor_x + cw)
    y1 = min(fh, cursor_y + ch)
    if x0 >= x1 or y0 >= y1:
        return

    src = cursor_rgba[y0 - cursor_y : y1 - cursor_y, x0 - cursor_x : x1 - cursor_x]
    dst = frame[y0:y1, x0:x1]

    alpha = src[:, :, 3:4].astype(np.float32) / 255.0
    src_rgb = src[:, :, :3].astype(np.float32)
    dst_rgb = dst.astype(np.float32)

    premultiplied = bool(
        (
            (src[:, :, 0] <= src[:, :, 3])
            & (src[:, :, 1] <= src[:, :, 3])
            & (src[:, :, 2] <= src[:, :, 3])
        ).all()
    )
    if premultiplied:
        blended = src_rgb + dst_rgb * (1.0 - alpha)
    else:
        blended = src_rgb * alpha + dst_rgb * (1.0 - alpha)
    dst[:, :, :] = blended.astype(np.uint8)


def draw_cursor(frame_rgb: np.ndarray, origin_left: int = 0, origin_top: int = 0) -> None:
    """
    Draw the mouse cursor into frame_rgb (RGB uint8, modified in place).

    Args:
        frame_rgb: Captured frame in RGB format, shape (H, W, 3).
        origin_left: Screen X of the frame's left edge (for multi-monitor).
        origin_top: Screen Y of the frame's top edge (for multi-monitor).
    """
    if user32 is None or frame_rgb is None:
        return

    ci = CURSORINFO()
    ci.cbSize = ctypes.sizeof(CURSORINFO)
    if not user32.GetCursorInfo(ctypes.byref(ci)):
        return
    # Note: Windows hides the hardware cursor while it is moving fast
    # (CURSOR_SHOWING flag unset), but we still draw it so recordings
    # never lose the cursor during fast mouse movement.

    icon = ICONINFO()
    if not user32.GetIconInfo(ci.hCursor, ctypes.byref(icon)):
        return

    try:
        if not icon.hbmColor:
            return

        bm = BITMAP()
        if not gdi32.GetObjectW(icon.hbmColor, ctypes.sizeof(BITMAP), ctypes.byref(bm)):
            return
        if bm.bmWidth <= 0 or bm.bmHeight <= 0 or bm.bmBitsPixel != 32:
            return

        bi = BITMAPINFO()
        bi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bi.bmiHeader.biWidth = bm.bmWidth
        bi.bmiHeader.biHeight = -bm.bmHeight  # top-down rows
        bi.bmiHeader.biPlanes = 1
        bi.bmiHeader.biBitCount = 32
        bi.bmiHeader.biCompression = BI_RGB

        size = bm.bmWidth * bm.bmHeight * 4
        buf = np.zeros((bm.bmHeight, bm.bmWidth, 4), dtype=np.uint8)

        hdc = user32.GetDC(0)
        try:
            got = gdi32.GetDIBits(
                hdc,
                icon.hbmColor,
                0,
                bm.bmHeight,
                buf.ctypes.data_as(ctypes.c_void_p),
                ctypes.byref(bi),
                DIB_RGB_COLORS,
            )
        finally:
            user32.ReleaseDC(0, hdc)
        if got != bm.bmHeight:
            return

        rgba = np.empty((bm.bmHeight, bm.bmWidth, 4), dtype=np.uint8)
        rgba[:, :, 0] = buf[:, :, 2]
        rgba[:, :, 1] = buf[:, :, 1]
        rgba[:, :, 2] = buf[:, :, 0]
        rgba[:, :, 3] = buf[:, :, 3]

        cx = ci.ptScreenPos.x - origin_left - icon.xHotspot
        cy = ci.ptScreenPos.y - origin_top - icon.yHotspot
        _blend_into(frame_rgb, rgba, cx, cy)
    finally:
        if icon.hbmColor:
            gdi32.DeleteObject(icon.hbmColor)
        if icon.hbmMask:
            gdi32.DeleteObject(icon.hbmMask)