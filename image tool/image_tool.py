import os
import sys
import threading
import shutil
import queue
from pathlib import Path
from PIL import Image, ImageFilter
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    from rembg import remove
except ImportError:
    print("Lỗi: Chưa cài đặt thư viện 'rembg' hoặc 'onnxruntime'.")
    print("Vui lòng chạy lệnh: pip install rembg onnxruntime Pillow")
    sys.exit(1)

# Khi chạy .exe (PyInstaller), __file__ trỏ vào thư mục giải nén tạm (_MEIPASS),
# nên cần lấy đường dẫn thư mục chứa file thực thi (sys.executable) làm gốc.
# Khi chạy .py bình thường thì sys.executable == python.exe, lấy dirname là thư mục script cũng OK.
import sys as _sys
_APP_ROOT = Path(getattr(_sys, "frozen", False) and _sys.executable or __file__).resolve().parent

# Cố định thư mục input và output (theo thư mục chứa tool)
INPUT_DIR = _APP_ROOT / "input"
OUTPUT_DIR = _APP_ROOT / "output"

def setup_folders():
    """Tự động tạo thư mục input và output nếu chưa có"""
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def process_remove_background():
    print(f"\n📁 Đang quét ảnh trong thư mục: {INPUT_DIR.absolute()}")
    count = 0
    
    for filepath in INPUT_DIR.rglob('*'):
        if filepath.is_file() and filepath.suffix.lower() in ['.png', '.jpg', '.jpeg', '.webp']:
            count += 1
            try:
                # Tái tạo lại cấu trúc thư mục con từ input sang output
                rel_path = filepath.relative_to(INPUT_DIR)
                out_path = OUTPUT_DIR / rel_path
                out_path.parent.mkdir(parents=True, exist_ok=True)

                # Ép đuôi thành PNG để giữ được nền trong suốt
                out_file = out_path.with_suffix('.png') 
                print(f"✂️ Đang xóa nền: {filepath.name} -> {out_file.name}")

                with open(filepath, 'rb') as i:
                    input_data = i.read()
                    output_data = remove(input_data)

                with open(out_file, 'wb') as o:
                    o.write(output_data)

            except Exception as e:
                print(f"❌ Lỗi khi xử lý {filepath.name}: {e}")
                
    if count == 0:
        print("\n⚠️ Không tìm thấy ảnh nào trong thư mục 'input'!")
        print("👉 Hãy copy ảnh vào thư mục 'input' rồi chạy lại tool nhé.")
    else:
        print(f"\n✅ HOÀN THÀNH XÓA NỀN CHO {count} ẢNH! (Kiểm tra thư mục 'output')")

def process_convert_format(target_format):
    print(f"\n📁 Đang quét ảnh trong thư mục: {INPUT_DIR.absolute()}")
    target_ext = f".{target_format.lower()}"
    count = 0

    for filepath in INPUT_DIR.rglob('*'):
        if filepath.is_file() and filepath.suffix.lower() in ['.png', '.jpg', '.jpeg', '.webp']:
            count += 1
            try:
                rel_path = filepath.relative_to(INPUT_DIR)
                out_path = OUTPUT_DIR / rel_path
                out_path.parent.mkdir(parents=True, exist_ok=True)

                out_file = out_path.with_suffix(target_ext)
                print(f"🔄 Đang chuyển đổi: {filepath.name} -> {out_file.name}")

                with Image.open(filepath) as img:
                    if target_format.lower() in ['jpg', 'jpeg']:
                        # Xử lý nền trong suốt khi convert sang JPG (đổ nền trắng)
                        if img.mode in ('RGBA', 'LA', 'P'):
                            bg = Image.new("RGB", img.size, (255, 255, 255))
                            if img.mode == 'P':
                                img = img.convert('RGBA')
                            bg.paste(img, mask=img.split()[3])
                            img = bg
                        else:
                            img = img.convert("RGB")
                            
                    img.save(out_file, format=target_format.upper() if target_format.lower() != 'jpg' else 'JPEG')

            except Exception as e:
                print(f"❌ Lỗi khi xử lý {filepath.name}: {e}")

    if count == 0:
        print("\n⚠️ Không tìm thấy ảnh nào trong thư mục 'input'!")
        print("👉 Hãy copy ảnh vào thư mục 'input' rồi chạy lại tool nhé.")
    else:
        print(f"\n✅ HOÀN THÀNH CHUYỂN ĐỔI CHO {count} ẢNH!")
        for filepath in INPUT_DIR.rglob('*'):
            if filepath.is_file() and filepath.suffix.lower() in ['.png', '.jpg', '.jpeg', '.webp']:
                filepath.unlink()
        print("🗑️ Đã xóa ảnh trong thư mục 'input'.")

def process_resize():
    print("\n📐 CHỌN KÍCH THƯỚC RESIZE")
    print("1. 512 x 512 (Preset)")
    print("2. 1024 x 1024 (Preset)")
    print("3. 1920 x 1080 (Preset)")
    print("4. Tự nhập kích thước")
    preset_choice = input("👉 Chọn (1, 2, 3 hoặc 4): ").strip()

    if preset_choice == '1':
        target_w, target_h = 512, 512
    elif preset_choice == '2':
        target_w, target_h = 1024, 1024
    elif preset_choice == '3':
        target_w, target_h = 1920, 1080
    elif preset_choice == '4':
        try:
            w = input("  Nhập chiều rộng (px): ").strip()
            h = input("  Nhập chiều cao (px): ").strip()
            target_w, target_h = int(w), int(h)
            if target_w <= 0 or target_h <= 0:
                print("❌ Kích thước phải lớn hơn 0!")
                return
        except ValueError:
            print("❌ Vui lòng nhập số nguyên hợp lệ!")
            return
    else:
        print("❌ Lựa chọn không hợp lệ!")
        return

    print(f"\n📁 Đang quét ảnh trong thư mục: {INPUT_DIR.absolute()}")
    count = 0

    for filepath in INPUT_DIR.rglob('*'):
        if filepath.is_file() and filepath.suffix.lower() in ['.png', '.jpg', '.jpeg', '.webp']:
            count += 1
            try:
                rel_path = filepath.relative_to(INPUT_DIR)
                out_path = OUTPUT_DIR / rel_path
                out_path.parent.mkdir(parents=True, exist_ok=True)

                print(f"📐 Đang resize: {filepath.name} -> {target_w}x{target_h}")

                with Image.open(filepath) as img:
                    resized = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
                    sharpened = resized.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
                    sharpened.save(out_path, format=img.format or 'PNG')

            except Exception as e:
                print(f"❌ Lỗi khi xử lý {filepath.name}: {e}")

    if count == 0:
        print("\n⚠️ Không tìm thấy ảnh nào trong thư mục 'input'!")
        print("👉 Hãy copy ảnh vào thư mục 'input' rồi chạy lại tool nhé.")
    else:
        print(f"\n✅ HOÀN THÀNH RESIZE {count} ẢNH VỀ {target_w}x{target_h}!")
        for filepath in INPUT_DIR.rglob('*'):
            if filepath.is_file() and filepath.suffix.lower() in ['.png', '.jpg', '.jpeg', '.webp']:
                filepath.unlink()
        print("🗑️ Đã xóa ảnh trong thư mục 'input'.")

def process_rename_files():
    print("\n🔤 CHỌN KIỂU ĐỔI TÊN FILE")
    print("1. IN HOA TOÀN BỘ (VD: my image.JPG -> MY IMAGE.JPG)")
    print("2. Viết thường toàn bộ (VD: My Image.JPG -> my image.jpg)")
    print("3. Viết Hoa Đầu Mỗi Từ (VD: my image.JPG -> My Image.JPG)")
    style_choice = input("👉 Chọn (1, 2 hoặc 3): ").strip()

    if style_choice not in ('1', '2', '3'):
        print("❌ Lựa chọn không hợp lệ!")
        return

    print(f"\n📁 Đang quét file trong: {INPUT_DIR.absolute()} -> {OUTPUT_DIR.absolute()}")
    count = 0
    skipped = 0

    for filepath in INPUT_DIR.rglob('*'):
        if not filepath.is_file():
            continue
        old_name = filepath.name
        stem, dot, ext = old_name.rpartition('.')
        if not dot:
            continue

        if style_choice == '1':
            new_stem = stem.upper()
        elif style_choice == '2':
            new_stem = stem.lower()
        else:  # Viết Hoa Đầu Mỗi Từ
            new_stem = stem.title()

        new_name = f"{new_stem}{dot}{ext}"

        # Tái tạo cấu trúc thư mục con từ input sang output
        rel_path = filepath.relative_to(INPUT_DIR)
        out_path = OUTPUT_DIR / rel_path.parent / new_name
        out_path.parent.mkdir(parents=True, exist_ok=True)

        if out_path.exists():
            print(f"⚠️ Bỏ qua (đã tồn tại): {old_name} -> {new_name}")
            skipped += 1
            continue

        try:
            import shutil
            shutil.copy2(filepath, out_path)
            print(f"✏️ {old_name} -> {new_name}")
            count += 1
        except Exception as e:
            print(f"❌ Lỗi đổi tên {old_name}: {e}")
            skipped += 1

    print(f"\n✅ HOÀN THÀNH ĐỔI TÊN {count} FILE! (Kết quả trong thư mục 'output')"
          + (f" (Bỏ qua {skipped} file)" if skipped else ""))


def main():
    setup_folders()
    root = tk.Tk()
    root.title("Tool 4 trong 1: Xử lý ảnh")
    root.geometry("760x660")
    root.minsize(700, 600)
    root.configure(bg="#1e1e2e")
    ImageToolFrame(root, root=root).pack(fill="both", expand=True)
    root.mainloop()


if __name__ == "__main__":
    main()


class ImageToolFrame(tk.Frame):
    IMAGE_EXTS = ('.png', '.jpg', '.jpeg', '.webp')

    def __init__(self, master=None, log_queue=None, root: "tk.Misc | None" = None):
        super().__init__(master)
        self._root = root  # root cửa sổ cha (dùng cho after, open folder)
        self.log_queue: "queue.Queue[str]" = log_queue if log_queue is not None else queue.Queue()
        self.worker = None
        self.worker_lock = threading.Lock()

        # Thư mục input / output mặc định (có thể đổi qua UI)
        self.input_dir: Path = INPUT_DIR
        self.output_dir: Path = OUTPUT_DIR

        self._build_inner()
        self._refresh_counts()
        if log_queue is None:
            # chạy độc lập -> cần poll log riêng
            self._poll_log()

    # ---------- giao diện ----------
    def _build_styles(self, master):
        style = ttk.Style(master)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background="#1e1e2e")
        style.configure("Card.TFrame", background="#2a2a3c")
        style.configure("TLabel", background="#1e1e2e", foreground="#e0e0e0", font=("Segoe UI", 10))
        style.configure("Card.TLabel", background="#2a2a3c", foreground="#e0e0e0", font=("Segoe UI", 10))
        style.configure("Title.TLabel", background="#1e1e2e", foreground="#89b4fa",
                        font=("Segoe UI", 16, "bold"))
        style.configure("Sub.TLabel", background="#1e1e2e", foreground="#a6adc8",
                        font=("Segoe UI", 9))
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=(14, 8))
        style.map("TButton",
                  foreground=[("disabled", "#6c7086")],
                  background=[("active", "#585b70")])
        style.configure("Primary.TButton", background="#89b4fa", foreground="#1e1e2e")
        style.configure("Success.TButton", background="#a6e3a1", foreground="#1e1e2e")
        style.configure("Warn.TButton", background="#f9e2af", foreground="#1e1e2e")
        style.configure("Danger.TButton", background="#f38ba8", foreground="#1e1e2e")
        style.configure("TNotebook", background="#1e1e2e", borderwidth=0)
        style.configure("TNotebook.Tab", padding=(16, 8), font=("Segoe UI", 10, "bold"))
        style.map("TNotebook.Tab",
                  background=[("selected", "#2a2a3c")],
                  foreground=[("selected", "#89b4fa")])
        style.configure("TLabelframe", background="#2a2a3c", foreground="#cdd6f4",
                        borderwidth=0, relief="flat")
        style.configure("TLabelframe.Label", background="#2a2a3c", foreground="#89b4fa",
                        font=("Segoe UI", 10, "bold"))
        style.configure("TEntry", fieldbackground="#313244", foreground="#e0e0e0",
                        insertcolor="#e0e0e0", padding=6)
        style.configure("TCombobox", fieldbackground="#313244", background="#313244",
                        foreground="#e0e0e0", padding=6)
        style.configure("Horizontal.TScale", background="#2a2a3c", troughcolor="#313244")

    def _build_inner(self):
        # styles cần master là root hoặc widget bất kỳ trong cùng tree
        master_for_style = self._root if self._root is not None else self
        self._build_styles(master_for_style)

        header = ttk.Frame(self)
        header.pack(fill="x", padx=16, pady=(16, 8))
        ttk.Label(header, text="TOOL XỬ LÝ ẢNH", style="Title.TLabel").pack(anchor="w")
        ttk.Label(header, text="Bỏ ảnh vào thư mục 'input' và bấm nút để xử lý, kết quả ở 'output'.",
                  style="Sub.TLabel").pack(anchor="w")

        info = ttk.Frame(self)
        info.pack(fill="x", padx=16, pady=(0, 8))
        self.lbl_input = ttk.Label(info, style="Card.TLabel")
        self.lbl_input.pack(side="left", padx=(0, 8))
        self.lbl_output = ttk.Label(info, style="Card.TLabel")
        self.lbl_output.pack(side="left")

        folder_row = ttk.Frame(self)
        folder_row.pack(fill="x", padx=16, pady=(0, 8))
        ttk.Button(folder_row, text="📂 Chọn thư mục INPUT", style="Primary.TButton",
                   command=self.choose_input).pack(side="left")
        ttk.Button(folder_row, text="📂 Chọn thư mục OUTPUT", style="Primary.TButton",
                   command=self.choose_output).pack(side="left", padx=8)
        ttk.Button(folder_row, text="↩️ Khôi phục mặc định", style="Primary.TButton",
                   command=self.reset_dirs).pack(side="left")

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        self._tab_remove_bg(notebook)
        self._tab_convert(notebook)
        self._tab_resize(notebook)
        self._tab_rename(notebook)

        log_frame = ttk.LabelFrame(self, text="  Nhật ký  ")
        log_frame.pack(fill="both", expand=False, padx=16, pady=(0, 12))
        self.log_text = tk.Text(log_frame, height=9, bg="#11111b", fg="#cdd6f4",
                                insertbackground="#cdd6f4", font=("Consolas", 9),
                                relief="flat", borderwidth=0)
        self.log_text.pack(fill="both", expand=True, padx=8, pady=8)
        self.log_text.configure(state="disabled")

        bottom = ttk.Frame(self)
        bottom.pack(fill="x", padx=16, pady=(0, 12))
        ttk.Button(bottom, text="Mở thư mục input", style="Primary.TButton",
                   command=lambda: self._open_folder(INPUT_DIR)).pack(side="left")
        ttk.Button(bottom, text="Mở thư mục output", style="Primary.TButton",
                   command=lambda: self._open_folder(OUTPUT_DIR)).pack(side="left", padx=8)

    def _card(self, parent):
        return ttk.Frame(parent, style="Card.TFrame", padding=14)

    def _tab_remove_bg(self, notebook):
        tab = self._card(notebook)
        notebook.add(tab, text="  Xóa nền  ")
        ttk.Label(tab, text="Tự động xóa nền mọi ảnh trong 'input'.", style="Card.TLabel").pack(anchor="w")
        ttk.Label(tab, text="Kết quả lưu vào 'output' (định dạng PNG, giữ nền trong suốt).",
                  style="Card.TLabel").pack(anchor="w", pady=(2, 12))
        ttk.Button(tab, text="▶  BẮT ĐẦU XÓA NỀN", style="Success.TButton",
                   command=self.run_remove_background).pack(anchor="w")

    def _tab_convert(self, notebook):
        tab = self._card(notebook)
        notebook.add(tab, text="  Đổi định dạng  ")
        ttk.Label(tab, text="Chuyển đổi mọi ảnh trong 'input' sang định dạng khác.",
                  style="Card.TLabel").pack(anchor="w")
        ttk.Label(tab, text="Ảnh gốc sẽ bị xoá sau khi chuyển đổi xong.",
                  style="Card.TLabel").pack(anchor="w", pady=(2, 12))

        row = ttk.Frame(tab, style="Card.TFrame")
        row.pack(fill="x")
        ttk.Label(row, text="Định dạng đích:", style="Card.TLabel").pack(side="left")
        self.convert_var = tk.StringVar(value="PNG")
        ttk.Combobox(row, textvariable=self.convert_var, state="readonly",
                     values=("PNG", "WEBP", "JPG"), width=12).pack(side="left", padx=8)
        ttk.Button(tab, text="▶  BẮT ĐẦU CHUYỂN ĐỔI", style="Warn.TButton",
                   command=self.run_convert_format).pack(anchor="w", pady=(12, 0))

    def _tab_resize(self, notebook):
        tab = self._card(notebook)
        notebook.add(tab, text="  Resize  ")
        ttk.Label(tab, text="Thay đổi kích thước mọi ảnh trong 'input' (giữ định dạng gốc).",
                  style="Card.TLabel").pack(anchor="w")
        ttk.Label(tab, text="Ảnh gốc sẽ bị xoá sau khi resize xong.",
                  style="Card.TLabel").pack(anchor="w", pady=(2, 12))

        row = ttk.Frame(tab, style="Card.TFrame")
        row.pack(fill="x", pady=(0, 8))
        ttk.Label(row, text="Preset:", style="Card.TLabel").pack(side="left")
        self.resize_preset_var = tk.StringVar(value="512 x 512")
        ttk.Combobox(row, textvariable=self.resize_preset_var, state="readonly",
                     values=("512 x 512", "1024 x 1024", "1920 x 1080", "Tự nhập"),
                     width=15).pack(side="left", padx=8)

        size_row = ttk.Frame(tab, style="Card.TFrame")
        size_row.pack(fill="x")
        ttk.Label(size_row, text="Rộng:", style="Card.TLabel").pack(side="left")
        self.resize_w_var = tk.StringVar(value="512")
        ttk.Entry(size_row, textvariable=self.resize_w_var, width=8).pack(side="left", padx=(4, 12))
        ttk.Label(size_row, text="Cao:", style="Card.TLabel").pack(side="left")
        self.resize_h_var = tk.StringVar(value="512")
        ttk.Entry(size_row, textvariable=self.resize_h_var, width=8).pack(side="left", padx=4)

        ttk.Button(tab, text="▶  BẮT ĐẦU RESIZE", style="Warn.TButton",
                   command=self.run_resize).pack(anchor="w", pady=(12, 0))

    def _tab_rename(self, notebook):
        tab = self._card(notebook)
        notebook.add(tab, text="  Đổi tên  ")
        ttk.Label(tab, text="Đọc ảnh từ 'input', ghi ra 'output' với tên đã đổi (giữ định dạng gốc).",
                  style="Card.TLabel").pack(anchor="w")

        row = ttk.Frame(tab, style="Card.TFrame")
        row.pack(fill="x", pady=(12, 0))
        ttk.Label(row, text="Kiểu đổi tên:", style="Card.TLabel").pack(side="left")
        self.rename_style_var = tk.StringVar(value="Viết Hoa Đầu Mỗi Từ")
        ttk.Combobox(row, textvariable=self.rename_style_var, state="readonly",
                     values=("IN HOA TOÀN BỘ", "Viết thường toàn bộ", "Viết Hoa Đầu Mỗi Từ"),
                     width=22).pack(side="left", padx=8)

        ttk.Button(tab, text="▶  BẮT ĐẦU ĐỔI TÊN", style="Danger.TButton",
                   command=self.run_rename).pack(anchor="w", pady=(12, 0))

    # ---------- tiện ích ----------
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

    def _refresh_counts(self):
        try:
            in_count = sum(1 for p in self.input_dir.rglob('*')
                           if p.is_file() and p.suffix.lower() in self.IMAGE_EXTS)
        except Exception:
            in_count = 0
        try:
            out_count = sum(1 for p in self.output_dir.rglob('*')
                            if p.is_file() and p.suffix.lower() in self.IMAGE_EXTS)
        except Exception:
            out_count = 0
        self.lbl_input.configure(text=f"📥 input: {in_count} ảnh  →  {self.input_dir}")
        self.lbl_output.configure(text=f"📤 output: {out_count} ảnh  →  {self.output_dir}")

    def choose_input(self):
        folder = filedialog.askdirectory(title="Chọn thư mục INPUT", initialdir=str(self.input_dir))
        if not folder:
            return
        p = Path(folder)
        p.mkdir(parents=True, exist_ok=True)
        self.input_dir = p
        self._log(f"📂 Đã đổi thư mục INPUT -> {p}")
        self._refresh_counts()

    def choose_output(self):
        folder = filedialog.askdirectory(title="Chọn thư mục OUTPUT", initialdir=str(self.output_dir))
        if not folder:
            return
        p = Path(folder)
        p.mkdir(parents=True, exist_ok=True)
        self.output_dir = p
        self._log(f"📂 Đã đổi thư mục OUTPUT -> {p}")
        self._refresh_counts()

    def reset_dirs(self):
        self.input_dir = INPUT_DIR
        self.output_dir = OUTPUT_DIR
        self._log("↩️ Đã khôi phục thư mục input/output mặc định.")
        self._refresh_counts()

    def _open_folder(self, folder: Path):
        folder.mkdir(parents=True, exist_ok=True)
        try:
            if sys.platform.startswith("win"):
                os.startfile(str(folder))  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                os.system(f'open "{folder}"')
            else:
                os.system(f'xdg-open "{folder}"')
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không mở được thư mục: {e}")

    def _run_in_thread(self, target, *args, refresh_after=True):
        if not self.worker_lock.acquire(blocking=False):
            self._log("⚠️ Tool đang chạy, vui lòng chờ xong.")
            return
        self._refresh_counts()
        self._log("\n" + "=" * 56)

        def runner():
            try:
                target(*args)
            except Exception as e:
                self._log(f"❌ Lỗi không mong muốn: {e}")
            finally:
                self.worker_lock.release()
                self.after(0, self._refresh_counts)

        self.worker = threading.Thread(target=runner, daemon=True)
        self.worker.start()

    # ---------- chạy chức năng ----------
    def run_remove_background(self):
        self._run_in_thread(self._do_remove_background)

    def _do_remove_background(self):
        self._log("✂️ Bắt đầu xóa nền...")
        count = 0
        for filepath in self.input_dir.rglob('*'):
            if not filepath.is_file() or filepath.suffix.lower() not in self.IMAGE_EXTS:
                continue
            count += 1
            try:
                rel = filepath.relative_to(self.input_dir)
                out = self.output_dir / rel
                out = out.with_suffix('.png')
                out.parent.mkdir(parents=True, exist_ok=True)
                self._log(f"  ✂️ {filepath.name} -> {out.name}")
                with open(filepath, 'rb') as f:
                    data = remove(f.read())
                with open(out, 'wb') as f:
                    f.write(data)
            except Exception as e:
                self._log(f"  ❌ {filepath.name}: {e}")
        if count == 0:
            self._log("⚠️ Không có ảnh nào trong input.")
        else:
            self._log(f"✅ Xong! Đã xóa nền {count} ảnh. Xem trong output.")

    def run_convert_format(self):
        fmt_map = {"PNG": "png", "WEBP": "webp", "JPG": "jpg"}
        target = fmt_map.get(self.convert_var.get())
        if not target:
            messagebox.showerror("Lỗi", "Chọn định dạng hợp lệ.")
            return
        self._run_in_thread(self._do_convert_format, target)

    def _do_convert_format(self, target_format: str):
        self._log(f"🔄 Bắt đầu chuyển đổi sang {target_format.upper()}...")
        count = 0
        for filepath in self.input_dir.rglob('*'):
            if not filepath.is_file() or filepath.suffix.lower() not in self.IMAGE_EXTS:
                continue
            count += 1
            try:
                rel = filepath.relative_to(self.input_dir)
                out = self.output_dir / rel
                out = out.with_suffix(f".{target_format}")
                out.parent.mkdir(parents=True, exist_ok=True)
                self._log(f"  🔄 {filepath.name} -> {out.name}")
                with Image.open(filepath) as img:
                    if target_format == 'jpg':
                        if img.mode in ('RGBA', 'LA', 'P'):
                            bg = Image.new("RGB", img.size, (255, 255, 255))
                            if img.mode == 'P':
                                img = img.convert('RGBA')
                            bg.paste(img, mask=img.split()[3])
                            img = bg
                        else:
                            img = img.convert("RGB")
                    img.save(out, format='JPEG' if target_format == 'jpg' else target_format.upper())
            except Exception as e:
                self._log(f"  ❌ {filepath.name}: {e}")

        if count == 0:
            self._log("⚠️ Không có ảnh nào trong input.")
        else:
            self._log(f"✅ Xong! Đã chuyển đổi {count} ảnh.")
            # xoá ảnh gốc trong input
            for fp in self.input_dir.rglob('*'):
                if fp.is_file() and fp.suffix.lower() in self.IMAGE_EXTS:
                    try:
                        fp.unlink()
                    except Exception:
                        pass
            self._log("🗑️ Đã xoá ảnh trong input.")

    def run_resize(self):
        preset = self.resize_preset_var.get()
        try:
            if preset == "Tự nhập":
                w = int(self.resize_w_var.get())
                h = int(self.resize_h_var.get())
            elif preset == "512 x 512":
                w, h = 512, 512
            elif preset == "1024 x 1024":
                w, h = 1024, 1024
            elif preset == "1920 x 1080":
                w, h = 1920, 1080
            else:
                raise ValueError("preset không hợp lệ")
            if w <= 0 or h <= 0:
                raise ValueError("kích thước phải > 0")
        except ValueError as e:
            messagebox.showerror("Lỗi", f"Kích thước không hợp lệ: {e}")
            return
        self._run_in_thread(self._do_resize, w, h)

    def _do_resize(self, w: int, h: int):
        self._log(f"📐 Bắt đầu resize về {w}x{h}...")
        count = 0
        for filepath in self.input_dir.rglob('*'):
            if not filepath.is_file() or filepath.suffix.lower() not in self.IMAGE_EXTS:
                continue
            count += 1
            try:
                rel = filepath.relative_to(self.input_dir)
                out = self.output_dir / rel
                out.parent.mkdir(parents=True, exist_ok=True)
                self._log(f"  📐 {filepath.name} -> {w}x{h}")
                with Image.open(filepath) as img:
                    img = img.resize((w, h), Image.Resampling.LANCZOS)
                    img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
                    img.save(out, format=(Path(filepath).suffix[1:].upper() or 'PNG'))
            except Exception as e:
                self._log(f"  ❌ {filepath.name}: {e}")

        if count == 0:
            self._log("⚠️ Không có ảnh nào trong input.")
        else:
            self._log(f"✅ Xong! Đã resize {count} ảnh.")
            for fp in self.input_dir.rglob('*'):
                if fp.is_file() and fp.suffix.lower() in self.IMAGE_EXTS:
                    try:
                        fp.unlink()
                    except Exception:
                        pass
            self._log("🗑️ Đã xoá ảnh trong input.")

    def run_rename(self):
        style_map = {
            "IN HOA TOÀN BỘ": '1',
            "Viết thường toàn bộ": '2',
            "Viết Hoa Đầu Mỗi Từ": '3',
        }
        style_key = style_map.get(self.rename_style_var.get())
        if not style_key:
            messagebox.showerror("Lỗi", "Chọn kiểu đổi tên hợp lệ.")
            return
        self._run_in_thread(self._do_rename, style_key)

    def _do_rename(self, style_key: str):
        labels = {'1': 'IN HOA', '2': 'in thường', '3': 'Viết Hoa Đầu'}
        self._log(f"🔤 Bắt đầu đổi tên ({labels.get(style_key, '')})...")
        count = 0
        skipped = 0
        for filepath in self.input_dir.rglob('*'):
            if not filepath.is_file():
                continue
            old_name = filepath.name
            stem, dot, ext = old_name.rpartition('.')
            if not dot:
                continue
            if style_key == '1':
                new_stem = stem.upper()
            elif style_key == '2':
                new_stem = stem.lower()
            else:
                new_stem = stem.title()
            new_name = f"{new_stem}{dot}{ext}"

            rel = filepath.relative_to(self.input_dir)
            out = self.output_dir / rel.parent / new_name
            if out.exists():
                self._log(f"  ⚠️ Bỏ qua (đã tồn tại): {old_name} -> {new_name}")
                skipped += 1
                continue
            out.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(filepath, out)
                self._log(f"  ✏️ {old_name} -> {new_name}")
                count += 1
            except Exception as e:
                self._log(f"  ❌ {old_name}: {e}")
                skipped += 1
        self._log(f"✅ Xong! Đã đổi tên {count} ảnh (bỏ qua {skipped}).")