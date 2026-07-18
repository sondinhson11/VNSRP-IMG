"""Launcher UI gom 3 tool vào một cửa sổ duy nhất.

Bật start.bat lên sẽ chạy file này, hiện 1 cửa sổ UI chính với 3 tab:
  - Xử lý ảnh (ImageToolFrame từ image_tool.py)
  - Tải ảnh xe (DownloadFrame từ download_cfx_vehicles.py)
  - Tải ảnh vũ khí (DownloadFrame từ download_cfx_weapons.py)

Mỗi tab có log riêng để tiện theo dõi.
"""

import os
import sys
import queue
from pathlib import Path
import tkinter as tk
from tkinter import ttk

# Import các tool đã refactor (class là Frame, không phải Tk)
try:
    import image_tool
    ImageToolFrame = image_tool.ImageToolFrame
    image_tool_main = image_tool.main  # dùng để setup_folders
except Exception as e:
    print(f"Lỗi import image_tool: {e}")
    raise

try:
    import download_cfx_vehicles as cfx_veh
    DownloadFrameVeh = cfx_veh.DownloadFrame
    cfx_veh_main = cfx_veh.main if hasattr(cfx_veh, "main") else None
except Exception as e:
    print(f"Lỗi import download_cfx_vehicles: {e}")
    raise

try:
    import download_cfx_weapons as cfx_wpn
    DownloadFrameWpn = cfx_wpn.DownloadFrame
    cfx_wpn_main = cfx_wpn.main if hasattr(cfx_wpn, "main") else None
except Exception as e:
    print(f"Lỗi import download_cfx_weapons: {e}")
    raise

APP_DIR = Path(__file__).resolve().parent


class Launcher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Tool VNSRP - Xử lý ảnh & Tải CFX")
        self.geometry("880x680")
        self.minsize(800, 620)
        self.configure(bg="#1e1e2e")

        # Đảm bảo thư mục input/output tồn tại (gọi từ image_tool)
        try:
            image_tool.setup_folders()
        except Exception:
            pass

        self._build_styles()
        self._build_header()
        self._build_tabs()
        self._build_footer()

    def _build_styles(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Launcher.TFrame", background="#1e1e2e")
        style.configure("Header.TFrame", background="#1e1e2e")
        style.configure("Launcher.TLabel", background="#1e1e2e", foreground="#cdd6f4",
                        font=("Segoe UI", 10))
        style.configure("Title.TLabel", background="#1e1e2e", foreground="#89b4fa",
                        font=("Segoe UI", 18, "bold"))
        style.configure("Sub.TLabel", background="#1e1e2e", foreground="#a6adc8",
                        font=("Segoe UI", 9))
        style.configure("Footer.TLabel", background="#1e1e2e", foreground="#6c7086",
                        font=("Segoe UI", 9))
        style.configure("TNotebook", background="#1e1e2e", borderwidth=0)
        style.configure("TNotebook.Tab", padding=(18, 10), font=("Segoe UI", 11, "bold"))
        style.map("TNotebook.Tab",
                  background=[("selected", "#2a2a3c")],
                  foreground=[("selected", "#89b4fa")])

    def _build_header(self):
        header = ttk.Frame(self, style="Header.TFrame")
        header.pack(fill="x", padx=20, pady=(18, 6))
        ttk.Label(header, text="VNSRP TOOLBOX", style="Title.TLabel").pack(anchor="w")
        ttk.Label(header, text="Xử lý ảnh & tải ảnh CFX — chọn tab bên dưới để dùng.",
                  style="Sub.TLabel").pack(anchor="w")

    def _build_tabs(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=20, pady=(6, 6))

        # ----- Tab 1: Xử lý ảnh -----
        tab_img = ttk.Frame(notebook, style="Launcher.TFrame")
        notebook.add(tab_img, text="  🖼  Xử lý ảnh  ")
        ImageToolFrame(tab_img, root=self).pack(fill="both", expand=True, padx=4, pady=4)

        # ----- Tab 2: Tải xe -----
        tab_veh = ttk.Frame(notebook, style="Launcher.TFrame")
        notebook.add(tab_veh, text="  🚗  Tải ảnh XE  ")
        DownloadFrameVeh(
            tab_veh,
            default_dir=cfx_veh.DEFAULT_SAVE_DIR,
            page_url=cfx_veh.PAGE_URL,
            base_url=cfx_veh.BASE_URL,
            item_label=cfx_veh.ITEM_LABEL,
            page_title=cfx_veh.PAGE_TITLE,
            root=self,
        ).pack(fill="both", expand=True, padx=4, pady=4)

        # ----- Tab 3: Tải vũ khí -----
        tab_wpn = ttk.Frame(notebook, style="Launcher.TFrame")
        notebook.add(tab_wpn, text="  🔫  Tải ảnh VŨ KHÍ  ")
        DownloadFrameWpn(
            tab_wpn,
            default_dir=cfx_wpn.DEFAULT_SAVE_DIR,
            page_url=cfx_wpn.PAGE_URL,
            base_url=cfx_wpn.BASE_URL,
            item_label=cfx_wpn.ITEM_LABEL,
            page_title=cfx_wpn.PAGE_TITLE,
            root=self,
        ).pack(fill="both", expand=True, padx=4, pady=4)

    def _build_footer(self):
        footer = ttk.Frame(self, style="Header.TFrame")
        footer.pack(fill="x", padx=20, pady=(0, 14))
        ttk.Label(footer, text=f"Thư mục làm việc: {APP_DIR}",
                  style="Footer.TLabel").pack(side="left")


def main():
    app = Launcher()
    app.mainloop()


if __name__ == "__main__":
    main()
