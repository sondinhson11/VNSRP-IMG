import os
import sys
import threading
import queue
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import sys as _sys_download
_APP_ROOT = Path(getattr(_sys_download, "frozen", False) and _sys_download.executable or __file__).resolve().parent

ROOT_DIR = str(_APP_ROOT)
DEFAULT_SAVE_DIR = os.path.join(ROOT_DIR, "output", "cfx_weapon_images")

PAGE_URL = "https://docs.fivem.net/docs/game-references/weapon-models/"
BASE_URL = "https://docs.fivem.net"
ITEM_LABEL = "ảnh vũ khí"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

PAGE_TITLE = "Tải ảnh Weapon models từ Cfx.re Docs"


class DownloadFrame(tk.Frame):
    def __init__(self, master, default_dir: str, page_url: str, base_url: str,
                 item_label: str, page_title: str, log_queue=None, root=None):
        super().__init__(master)
        self._root = root
        self.page_url = page_url
        self.base_url = base_url
        self.item_label = item_label
        self.save_dir = default_dir

        self.log_queue: "queue.Queue[str]" = log_queue if log_queue is not None else queue.Queue()
        self.stop_flag = threading.Event()
        self.worker = None
        self.lock = threading.Lock()

        self._build_styles(master if root is None else root)
        self._build_ui()
        self._update_dir_label()
        if log_queue is None:
            self._poll_log()

    def _build_styles(self, master):
        style = ttk.Style(master)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background="#1e1e2e")
        style.configure("Card.TFrame", background="#2a2a3c")
        style.configure("TLabel", background="#1e1e2e", foreground="#e0e0e0",
                        font=("Segoe UI", 10))
        style.configure("Card.TLabel", background="#2a2a3c", foreground="#e0e0e0",
                        font=("Segoe UI", 10))
        style.configure("Title.TLabel", background="#1e1e2e", foreground="#89b4fa",
                        font=("Segoe UI", 16, "bold"))
        style.configure("Sub.TLabel", background="#1e1e2e", foreground="#a6adc8",
                        font=("Segoe UI", 9))
        style.configure("Path.TLabel", background="#2a2a3c", foreground="#a6e3a1",
                        font=("Consolas", 9))
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=(14, 8))
        style.configure("Primary.TButton", background="#89b4fa", foreground="#1e1e2e")
        style.configure("Success.TButton", background="#a6e3a1", foreground="#1e1e2e")
        style.configure("Danger.TButton", background="#f38ba8", foreground="#1e1e2e")

    def _build_ui(self):
        header = ttk.Frame(self)
        header.pack(fill="x", padx=16, pady=(16, 8))
        ttk.Label(header, text=PAGE_TITLE, style="Title.TLabel").pack(anchor="w")
        ttk.Label(header, text=f"Tự động quét trang web và tải tất cả {self.item_label}.",
                  style="Sub.TLabel").pack(anchor="w")

        # Thư mục lưu
        dir_frame = ttk.LabelFrame(self, text="  Thư mục lưu  ")
        dir_frame.pack(fill="x", padx=16, pady=(0, 8))
        self.lbl_dir = ttk.Label(dir_frame, text="", style="Path.TLabel", anchor="w")
        self.lbl_dir.pack(fill="x", padx=10, pady=(8, 4))
        btn_row = ttk.Frame(dir_frame)
        btn_row.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(btn_row, text="📂 Chọn thư mục...", style="Primary.TButton",
                   command=self.choose_dir).pack(side="left")
        ttk.Button(btn_row, text="↩️ Mặc định", style="Primary.TButton",
                   command=self.reset_dir).pack(side="left", padx=8)
        ttk.Button(btn_row, text="📁 Mở thư mục", style="Primary.TButton",
                   command=self.open_dir).pack(side="left")

        # Trang nguồn
        url_frame = ttk.LabelFrame(self, text="  Nguồn  ")
        url_frame.pack(fill="x", padx=16, pady=(0, 8))
        self.url_var = tk.StringVar(value=self.page_url)
        entry = ttk.Entry(url_frame, textvariable=self.url_var)
        entry.pack(fill="x", padx=10, pady=10)

        # Nút hành động
        action = ttk.Frame(self)
        action.pack(fill="x", padx=16, pady=(0, 8))
        self.btn_start = ttk.Button(action, text="▶  BẮT ĐẦU TẢI", style="Success.TButton",
                                    command=self.start_download)
        self.btn_start.pack(side="left")
        self.btn_stop = ttk.Button(action, text="⏹ DỪNG", style="Danger.TButton",
                                   command=self.stop_download, state="disabled")
        self.btn_stop.pack(side="left", padx=8)

        # Log
        log_frame = ttk.LabelFrame(self, text="  Nhật ký  ")
        log_frame.pack(fill="both", expand=True, padx=16, pady=(0, 12))
        self.log_text = tk.Text(log_frame, height=10, bg="#11111b", fg="#cdd6f4",
                                insertbackground="#cdd6f4", font=("Consolas", 9),
                                relief="flat", borderwidth=0)
        self.log_text.pack(fill="both", expand=True, padx=8, pady=8)
        self.log_text.configure(state="disabled")

    # ---------- log ----------
    def _log(self, msg: str):
        self.log_queue.put(msg)

    def _append_log(self, msg: str):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _poll_log(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()
                self._append_log(msg)
        except queue.Empty:
            pass
        self.after(80, self._poll_log)

    # ---------- thư mục ----------
    def _update_dir_label(self):
        self.lbl_dir.configure(text=self.save_dir)

    def choose_dir(self):
        folder = filedialog.askdirectory(title="Chọn thư mục lưu", initialdir=self.save_dir)
        if not folder:
            return
        self.save_dir = folder
        self._update_dir_label()
        self._log(f"📂 Đã đổi thư mục lưu -> {folder}")

    def reset_dir(self):
        self.save_dir = DEFAULT_SAVE_DIR
        self._update_dir_label()
        self._log(f"↩️ Đã khôi phục thư mục mặc định: {DEFAULT_SAVE_DIR}")

    def open_dir(self):
        Path(self.save_dir).mkdir(parents=True, exist_ok=True)
        try:
            if sys.platform.startswith("win"):
                os.startfile(self.save_dir)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                os.system(f'open "{self.save_dir}"')
            else:
                os.system(f'xdg-open "{self.save_dir}"')
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không mở được thư mục: {e}")

    # ---------- tải ----------
    def start_download(self):
        if not self.lock.acquire(blocking=False):
            self._log("⚠️ Đang tải, vui lòng chờ hoặc bấm DỪNG.")
            return
        self.stop_flag.clear()
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Lỗi", "Chưa nhập URL nguồn.")
            self.lock.release()
            return
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self._log("\n" + "=" * 56)

        def runner():
            try:
                self._download(url)
            except Exception as e:
                self._log(f"❌ Lỗi không mong muốn: {e}")
            finally:
                self.btn_start.configure(state="normal")
                self.btn_stop.configure(state="disabled")
                self.lock.release()

        self.worker = threading.Thread(target=runner, daemon=True)
        self.worker.start()

    def stop_download(self):
        if self.worker and self.worker.is_alive():
            self._log("⏹ Đang dừng...")
            self.stop_flag.set()

    def _download(self, url: str):
        save_dir = self.save_dir
        Path(save_dir).mkdir(parents=True, exist_ok=True)

        self._log(f"🌐 Đang truy cập: {url}")
        try:
            response = requests.get(url, headers=HEADERS, timeout=30)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            self._log(f"❌ Không thể truy cập trang web: {e}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        content = soup.find('article') or soup
        images = content.find_all('img')
        self._log(f"🔎 Tìm thấy {len(images)} thẻ img. Bắt đầu tải {self.item_label}...\n")

        count = 0
        for img in images:
            if self.stop_flag.is_set():
                self._log("⏹ Đã dừng theo yêu cầu.")
                break
            img_url = img.get('src')
            if not img_url:
                continue
            img_url = urljoin(self.base_url, img_url)
            filename = os.path.basename(img_url.split('?')[0])
            if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif')):
                continue
            try:
                data = requests.get(img_url, headers=HEADERS, timeout=30).content
                with open(os.path.join(save_dir, filename), 'wb') as f:
                    f.write(data)
                self._log(f"  [+] {filename}")
                count += 1
            except Exception as e:
                self._log(f"  [-] Lỗi {img_url}: {e}")

        if not self.stop_flag.is_set():
            self._log(f"\n✅ Hoàn tất! Đã tải {count} {self.item_label} vào '{save_dir}'.")
        else:
            self._log(f"\n⏹ Đã dừng. Đã tải được {count} {self.item_label}.")


if __name__ == "__main__":
    root = tk.Tk()
    root.title(PAGE_TITLE)
    root.geometry("760x600")
    root.minsize(680, 540)
    root.configure(bg="#1e1e2e")
    DownloadFrame(
        root,
        default_dir=DEFAULT_SAVE_DIR,
        page_url=PAGE_URL,
        base_url=BASE_URL,
        item_label=ITEM_LABEL,
        page_title=PAGE_TITLE,
        root=root,
    ).pack(fill="both", expand=True)
    root.mainloop()