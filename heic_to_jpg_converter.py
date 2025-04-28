"""
Image Format Converter (No OpenCV)

Dependencies:
- Python 3.6+
- PyQt6: GUI framework
- pillow-heif: For HEIC format support
- PIL (Pillow): For image handling

Install dependencies:
pip install PyQt6 pillow-heif Pillow -i https://pypi.tuna.tsinghua.edu.cn/simple
"""

import sys
import os
from PIL import Image
import pillow_heif
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QFileDialog, QProgressBar, QLabel, QDialog, QComboBox, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon  # 确保已导入 QIcon
import logging

# 定义 resource_path 函数，放在文件开头（类定义之前）
def resource_path(relative_path):
    """获取资源文件的绝对路径，兼容 PyInstaller 的 --onefile 模式"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(__file__), relative_path)

# 设置日志
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

class ConverterThread(QThread):
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    conversion_finished = pyqtSignal()

    def __init__(self, files, output_format, ico_size):
        super().__init__()
        self.files = files
        self.output_format = output_format
        self.ico_size = ico_size

    def process_image(self, file_path, output_base_dir, format_mapping):
        logging.info(f"Starting to process: {file_path}")
        try:
            # 处理 HEIC 文件
            if file_path.lower().endswith((".heic", ".heic")):
                logging.debug(f"Processing HEIC file: {file_path}")
                heif_file = pillow_heif.read_heif(file_path)
                image = Image.frombytes(
                    heif_file.mode,
                    heif_file.size,
                    heif_file.data,
                    "raw",
                )
                images_info = [(image, False)]
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
                logging.debug(f"Extracted {len(images_info)} frames from {file_path}")

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
                logging.info(f"Processing page {page_num + 1} of {file_path}")
                # 为 JPG 强制转换为 RGB（去除 Alpha 通道）
                if self.output_format == "jpg" and img.mode != "RGB":
                    img = img.convert("RGB")
                # 为其他格式（如 PNG、WEBP）保留 RGBA，或将非 RGB/RGBA 转换为 RGB
                elif img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGB")

                # 为 ICO 调整尺寸
                if self.output_format == "ico" and self.ico_size:
                    if not isinstance(self.ico_size, int) or self.ico_size <= 0:
                        raise ValueError(f"Invalid ICO size: {self.ico_size}")
                    img = img.resize((self.ico_size, self.ico_size), Image.Resampling.LANCZOS)

                # 保存文件
                output_filename = output_filename_base
                if len(images_info) > 1:
                    output_filename += f"_page{page_num + 1}"
                output_filename += f".{self.output_format}"
                output_path = os.path.join(output_dir, output_filename)
                logging.debug(f"Saving to: {output_path}")

                pillow_format = format_mapping.get(self.output_format, self.output_format.upper())
                save_kwargs = {}
                if self.output_format == "jpg":
                    save_kwargs["quality"] = 95
                elif self.output_format == "webp":
                    save_kwargs["quality"] = 80  # 默认有损压缩，质量 80
                    # 可选：支持无损压缩
                    # save_kwargs["lossless"] = True
                elif self.output_format == "ico":
                    save_kwargs["sizes"] = [(self.ico_size, self.ico_size)]

                img.save(output_path, format=pillow_format, **save_kwargs)
                logging.info(f"Saved: {output_path}")

                if is_pil_image:
                    img.close()

        except Exception as e:
            logging.error(f"Error processing {file_path}: {str(e)}")
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
            output_base_dir = os.path.abspath(os.path.join(input_dir, "pic"))
            logging.debug(f"Output base dir: {output_base_dir}")
            if not os.path.exists(output_base_dir):
                os.makedirs(output_base_dir)

        # 单线程处理文件
        for file_path in self.files:
            try:
                self.process_image(file_path, output_base_dir, format_mapping)
                processed_files += 1
                self.progress_updated.emit(processed_files)
            except Exception as e:
                logging.error(f"Error in thread for {file_path}: {str(e)}")
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

        self.label = QLabel(f"You have selected {file_count} file(s). Select output format:")
        layout.addWidget(self.label)

        self.format_combo = QComboBox()
        self.output_formats = ["JPG", "PNG", "WEBP", "BMP", "GIF", "TIFF", "ICO"]
        self.format_combo.addItems(self.output_formats)
        self.format_combo.currentIndexChanged.connect(self.toggle_ico_size)
        layout.addWidget(self.format_combo)

        self.ico_size_label = QLabel("Select ICO size (recommended for icons):")
        self.ico_size_label.setVisible(False)
        layout.addWidget(self.ico_size_label)
        self.ico_size_combo = QComboBox()
        self.ico_sizes = ["16x16", "32x32", "64x64", "128x128", "256x256"]
        self.ico_size_combo.addItems(self.ico_sizes)
        self.ico_size_combo.setVisible(False)
        layout.addWidget(self.ico_size_combo)

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
        icon_path = resource_path("Converters.ico")
        self.setWindowIcon(QIcon(icon_path))

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.select_button = QPushButton("Select Image Files")
        self.select_button.clicked.connect(self.select_files)
        self.layout.addWidget(self.select_button)

        self.progress = QProgressBar()
        self.progress.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.progress)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.status_label)

        self.selected_files = []
        self.output_format = "jpg"
        self.ico_size = None
        self.converter_thread = None

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
        input_formats = [
            "Image Files (*.heic *.HEIC *.jpg *.jpeg *.jfif *.JFIF *.png *.bmp *.gif *.tiff *.TIFF *.tif *.TIF *.webp *.ico *.pcx *.tga)"
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

        self.progress.setValue(0)
        self.progress.setMaximum(total_files)
        self.select_button.setEnabled(False)
        self.status_label.setText("Converting...")

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
        QApplication.instance().beep()
        dialog = QDialog(self)
        dialog.setWindowTitle("Done")
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Conversion completed successfully! Files saved in 'pic' folder."))
        button = QPushButton("OK")
        button.clicked.connect(dialog.accept)
        layout.addWidget(button)
        dialog.setLayout(layout)
        dialog.show()
        self.selected_files = []

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = HeicToJpgConverter()
    window.show()
    sys.exit(app.exec())