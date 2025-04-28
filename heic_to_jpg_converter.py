"""
Image Format Converter

Dependencies:
- Python 3.6+
- PyQt6: GUI framework
- pillow-heif: For HEIC format support
- opencv-python: For image processing
- numpy: Dependency of opencv-python
- PIL (Pillow): For image handling

Install dependencies:
pip install PyQt6 pillow-heif opencv-python numpy Pillow -i https://pypi.tuna.tsinghua.edu.cn/simple
"""

import sys
import os
from PIL import Image
import pillow_heif
import cv2
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QFileDialog, QProgressBar, QLabel, QDialog, QComboBox, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

class ConverterThread(QThread):
    progress_updated = pyqtSignal(int)  # 进度更新信号
    status_updated = pyqtSignal(str)   # 状态更新信号
    conversion_finished = pyqtSignal() # 转换完成信号

    def __init__(self, files, output_format, ico_size):
        super().__init__()
        self.files = files
        self.output_format = output_format
        self.ico_size = ico_size
        self.lock = threading.Lock()  # 用于线程安全的进度更新

    def process_image(self, file_path, output_base_dir, format_mapping):
        """处理单个文件，支持逐帧处理以优化内存使用"""
        try:
            self.status_updated.emit(f"Processing file: {file_path}")
            # 处理 HEIC 文件
            if file_path.lower().endswith((".heic", ".heic")):
                heif_file = pillow_heif.read_heif(file_path)
                image = Image.frombytes(
                    heif_file.mode,
                    heif_file.size,
                    heif_file.data,
                    "raw",
                )
                images_info = [(image, False)]  # (image, is_pil_image)
            else:
                # 打开图像并逐帧处理
                image = Image.open(file_path)
                images_info = []
                page_num = 0
                while True:
                    try:
                        images_info.append((image.copy(), True))
                        image.seek(image.tell() + 1)
                        page_num += 1
                    except EOFError:
                        break

            # 为多帧图像创建子文件夹
            output_filename_base = os.path.splitext(os.path.basename(file_path))[0]
            if len(images_info) > 1:
                output_dir = os.path.join(output_base_dir, output_filename_base)
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
            else:
                output_dir = output_base_dir

            # 逐帧处理并保存
            for page_num, (img, is_pil_image) in enumerate(images_info):
                self.status_updated.emit(f"Processing page {page_num + 1} of {file_path}")
                # 使用 OpenCV 处理图像
                if is_pil_image:
                    # 将 PIL 图像转换为 OpenCV 格式
                    img_array = np.array(img)
                    if len(img_array.shape) == 2:  # 灰度图
                        img_cv = cv2.cvtColor(img_array, cv2.COLOR_GRAY2BGR)
                    elif img_array.shape[2] == 4:  # RGBA
                        img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGR)
                    elif img_array.shape[2] == 3:  # RGB
                        img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                    else:
                        raise ValueError(f"Unsupported image mode: {img.mode}")
                else:
                    img_cv = np.array(img)

                # 提前检查是否需要模式转换（OpenCV 已经是 BGR，无需额外转换）
                # 为 ICO 调整尺寸
                if self.output_format == "ico" and self.ico_size:
                    if not isinstance(self.ico_size, int) or self.ico_size <= 0:
                        raise ValueError(f"Invalid ICO size: {self.ico_size}")
                    img_cv = cv2.resize(img_cv, (self.ico_size, self.ico_size), interpolation=cv2.INTER_LANCZOS4)

                # 保存文件，添加页面编号（如果多页）
                output_filename = output_filename_base
                if len(images_info) > 1:
                    output_filename += f"_page{page_num + 1}"
                output_filename += f".{self.output_format}"
                output_path = os.path.join(output_dir, output_filename)

                pillow_format = format_mapping.get(self.output_format, self.output_format.upper())

                if self.output_format == "ico":
                    # 转换回 PIL 格式以保存 ICO
                    img_pil = Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))
                    img_pil.save(output_path, format="ICO", sizes=[(self.ico_size, self.ico_size)])
                else:
                    # 使用 OpenCV 保存其他格式
                    if self.output_format == "jpg":
                        cv2.imwrite(output_path, img_cv, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
                    else:
                        cv2.imwrite(output_path, img_cv)

                if is_pil_image:
                    img.close()

        except Exception as e:
            self.status_updated.emit(f"Error processing {file_path}: {str(e)}")
            raise

    def run(self):
        format_mapping = {
            "jpg": "JPEG",
            "png": "PNG",
            "webp": "WEBP",
            "bmp": "BMP",
            "gif": "GIF",
            "tiff": "TIFF",
            "ico": "ICO"
        }

        total_files = len(self.files)
        processed_files = 0

        # 确保输出基础目录存在
        if self.files:
            input_dir = os.path.dirname(self.files[0])
            output_base_dir = os.path.join(input_dir, "pic")
            if not os.path.exists(output_base_dir):
                os.makedirs(output_base_dir)

        # 使用线程池并行处理文件
        max_workers = min(os.cpu_count() or 1, 4)  # 限制最大线程数，避免过多线程
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {executor.submit(self.process_image, file_path, output_base_dir, format_mapping): file_path for file_path in self.files}
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    future.result()  # 抛出异常（如果有）
                    with self.lock:
                        processed_files += 1
                        self.progress_updated.emit(processed_files)
                except Exception as e:
                    self.status_updated.emit(f"Error processing {file_path}: {str(e)}")
                    return

        self.status_updated.emit("Conversion completed!")
        self.progress_updated.emit(total_files)
        self.conversion_finished.emit()

class OutputFormatDialog(QDialog):
    def __init__(self, file_count, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Output Format")
        self.setFixedSize(400, 165)
        layout = QVBoxLayout()

        # 提示标签
        self.label = QLabel(f"You have selected {file_count} file(s). Select output format:")
        layout.addWidget(self.label)

        # 输出格式下拉框
        self.format_combo = QComboBox()
        self.output_formats = ["JPG", "PNG", "WEBP", "BMP", "GIF", "TIFF", "ICO"]
        self.format_combo.addItems(self.output_formats)
        self.format_combo.currentIndexChanged.connect(self.toggle_ico_size)
        layout.addWidget(self.format_combo)

        # ICO 尺寸选择（默认隐藏）
        self.ico_size_label = QLabel("Select ICO size (recommended for icons):")
        self.ico_size_label.setVisible(False)
        layout.addWidget(self.ico_size_label)
        self.ico_size_combo = QComboBox()
        self.ico_sizes = ["16x16", "32x32", "64x64", "128x128", "256x256"]
        self.ico_size_combo.addItems(self.ico_sizes)
        self.ico_size_combo.setVisible(False)
        layout.addWidget(self.ico_size_combo)

        # 按钮
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

        self.setLayout(layout)

    def toggle_ico_size(self):
        is_ico = self.format_combo.currentText().lower() == "ico"
        self.ico_size_label.setVisible(is_ico)
        self.ico_size_combo.setVisible(is_ico)

    def get_selected_format(self):
        return self.format_combo.currentText().lower()

    def get_ico_size(self):
        if self.format_combo.currentText().lower() == "ico":
            size_str = self.ico_size_combo.currentText()
            return int(size_str.split("x")[0])
        return None

class HeicToJpgConverter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Format Converter")
        self.setFixedSize(400, 100)

        # 设置窗口图标
        from PyQt6.QtGui import QIcon
        import os
        icon_path = os.path.join(os.path.dirname(__file__), "Converters.ico")
        self.setWindowIcon(QIcon(icon_path))

        # 主窗口布局
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # 选择文件按钮
        self.select_button = QPushButton("Select Image Files")
        self.select_button.clicked.connect(self.select_files)
        self.layout.addWidget(self.select_button)

        # 进度条
        self.progress = QProgressBar()
        self.progress.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.progress)

        # 状态标签
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.status_label)

        # 存储选择的文件
        self.selected_files = []
        self.output_format = "jpg"
        self.ico_size = None
        self.converter_thread = None

        # 美化样式
        self.setStyleSheet("""
            QPushButton {
                padding: 8px;
                font-size: 14px;
                background-color: #007BFF;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QProgressBar {
                height: 20px;
                text-align: center;
            }
            QLabel {
                font-size: 12px;
            }
            QComboBox {
                padding: 5px;
                font-size: 12px;
            }
        """)

    def select_files(self):
        # 支持的输入格式，明确添加 .tif 和 .TIFF
        input_formats = [
            "Image Files (*.heic *.HEIC *.jpg *.jpeg *.png *.bmp *.gif *.tiff *.TIFF *.tif *.TIF *.webp *.ico *.pcx *.tga)"
        ]
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Image Files", "",
            ";;".join(input_formats)
        )
        if files:
            self.selected_files = files
            self.show_format_dialog()

    def show_format_dialog(self):
        file_count = len(self.selected_files)
        if file_count == 0:
            return

        # 显示输出格式选择对话框
        dialog = OutputFormatDialog(file_count, self)
        if dialog.exec():
            self.output_format = dialog.get_selected_format()
            self.ico_size = dialog.get_ico_size()
            self.convert_files()
        else:
            self.selected_files = []
            self.status_label.setText("Conversion canceled.")

    def convert_files(self):
        total_files = len(self.selected_files)
        if total_files == 0:
            return

        # 重置进度条
        self.progress.setValue(0)
        self.progress.setMaximum(total_files)
        self.select_button.setEnabled(False)
        self.status_label.setText("Converting...")

        # 启动转换线程
        self.converter_thread = ConverterThread(self.selected_files, self.output_format, self.ico_size)
        self.converter_thread.progress_updated.connect(self.update_progress)
        self.converter_thread.status_updated.connect(self.update_status)
        self.converter_thread.conversion_finished.connect(self.on_conversion_finished)
        self.converter_thread.start()

    def update_progress(self, value):
        self.progress.setValue(value)

    def update_status(self, status):
        self.status_label.setText(status)

    def on_conversion_finished(self):
        self.select_button.setEnabled(True)
        QApplication.instance().beep()  # 提示音
        dialog = QDialog(self)
        dialog.setWindowTitle("Done")
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Conversion completed successfully! Files saved in 'pic' folder."))
        button = QPushButton("OK")
        button.clicked.connect(dialog.accept)
        layout.addWidget(button)
        dialog.setLayout(layout)
        dialog.show()  # 使用 show() 而不是 exec()，避免嵌套事件循环
        self.selected_files = []

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # 现代 Fusion 风格
    window = HeicToJpgConverter()
    window.show()
    sys.exit(app.exec())