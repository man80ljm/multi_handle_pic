import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image
import pillow_heif
import os
import threading

class HeicToJpgConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("HEIC to JPG Converter")
        self.root.geometry("400x200")
        self.root.resizable(False, False)

        # 主框架
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 选择文件按钮
        self.select_button = ttk.Button(self.main_frame, text="Select HEIC Files", command=self.select_files)
        self.select_button.grid(row=0, column=0, pady=20)

        # 进度条
        self.progress = ttk.Progressbar(self.main_frame, orient="horizontal", length=300, mode="determinate")
        self.progress.grid(row=1, column=0, pady=20)

        # 状态标签
        self.status_label = ttk.Label(self.main_frame, text="")
        self.status_label.grid(row=2, column=0, pady=10)

        # 存储选择的文件
        self.selected_files = []

    def select_files(self):
        # 打开文件选择对话框，仅允许 .heic 文件
        files = filedialog.askopenfilenames(
            title="Select HEIC Files",
            filetypes=[("HEIC Files", "*.heic *.HEIC")]
        )
        if files:
            self.selected_files = list(files)
            # 显示确认对话框
            self.show_confirmation()

    def show_confirmation(self):
        file_count = len(self.selected_files)
        if file_count == 0:
            return

        # 显示确认对话框
        response = messagebox.askyesno(
            title="Confirm Conversion",
            message=f"You have selected {file_count} file(s). Convert to JPG?"
        )
        if response:
            # 开始转换（在新线程中以防止界面冻结）
            threading.Thread(target=self.convert_files, daemon=True).start()
        else:
            # 用户选择“否”，清空选择
            self.selected_files = []
            self.status_label.config(text="Conversion canceled.")

    def convert_files(self):
        total_files = len(self.selected_files)
        if total_files == 0:
            return

        # 重置进度条
        self.progress["value"] = 0
        self.progress["maximum"] = total_files
        self.select_button.config(state="disabled")
        self.status_label.config(text="Converting...")

        for i, file_path in enumerate(self.selected_files):
            try:
                # 读取 HEIC 文件
                heif_file = pillow_heif.read_heif(file_path)
                image = Image.frombytes(
                    heif_file.mode,
                    heif_file.size,
                    heif_file.data,
                    "raw",
                )
                # 获取原文件所在目录
                input_dir = os.path.dirname(file_path)
                # 创建同级的 pic 文件夹
                output_dir = os.path.join(input_dir, "pic")
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                # 构建输出路径
                output_filename = os.path.splitext(os.path.basename(file_path))[0] + ".jpg"
                output_path = os.path.join(output_dir, output_filename)
                # 保存为 JPG
                image.save(output_path, "JPEG", quality=95)
                # 更新进度条
                self.progress["value"] = i + 1
                self.root.update_idletasks()
            except Exception as e:
                self.status_label.config(text=f"Error: {str(e)}")
                self.select_button.config(state="normal")
                return

        # 转换完成
        self.status_label.config(text="Conversion completed!")
        self.select_button.config(state="normal")
        messagebox.showinfo("Done", "Conversion completed successfully! Files saved in 'pic' folder.")
        self.selected_files = []

if __name__ == "__main__":
    root = tk.Tk()
    app = HeicToJpgConverter(root)
    root.mainloop()