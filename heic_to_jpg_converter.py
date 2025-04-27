import sys
import os
from PIL import Image
import pillow_heif
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QFileDialog, QProgressBar, QLabel, QDialog, QComboBox, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

class ConverterThread(QThread):
    progress_updated = pyqtSignal(int)  # 进度更新信号
    status_updated = pyqtSignal(str)   # 状态更新信号
    conversion_finished = pyqtSignal() # 转换完成信号

    def __init__(self, files, output_format, ico_size):
        super().__init__()
        self.files = files
        self.output_format = output_format
        self.ico_size = ico_size

    def run(self):
        total_files = len(self.files)
        for i, file_path in enumerate(self.files):
            try:
                # 处理 HEIC 文件
                if file_path.lower().endswith((".heic", ".heic")):
                    heif_file = pillow_heif.read_heif(file_path)
                    image = Image.frombytes(
                        heif_file.mode,
                        heif_file.size,
                        heif_file.data,
                        "raw",
                    )
                else:
                    # 其他格式直接用 Pillow 打开
                    image = Image.open(file_path)

                # 转换为 RGB（某些格式如 ICO 需要）
                if image.mode not in ("RGB", "RGBA"):
                    image = image.convert("RGB")

                # 为 ICO 调整尺寸
                if self.output_format == "ico" and self.ico_size:
                    image = image.resize((self.ico_size, self.ico_size), Image.Resampling.LANCZOS)

                # 获取原文件所在目录
                input_dir = os.path.dirname(file_path)
                # 创建同级的 pic 文件夹
                output_dir = os.path.join(input_dir, "pic")
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                # 构建输出路径
                output_filename = os.path.splitext(os.path.basename(file_path))[0] + f".{self.output_format}"
                output_path = os.path.join(output_dir, output_filename)
                # 保存文件
                image.save(output_path, self.output_format.upper(), quality=95 if self.output_format == "jpg" else 100)
                # 关闭图像对象，释放资源
                image.close()
                # 更新进度
                self.progress_updated.emit(i + 1)
            except Exception as e:
                self.status_updated.emit(f"Error: {str(e)}")
                return

        # 转换完成
        self.status_updated.emit("Conversion completed!")
        self.progress_updated.emit(total_files)
        self.conversion_finished.emit()

class OutputFormatDialog(QDialog):
    def __init__(self, file_count, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Output Format")
        self.setFixedSize(400, 100)
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
        # 支持的输入格式
        input_formats = [
            "Image Files (*.heic *.HEIC *.jpg *.jpeg *.png *.bmp *.gif *.tiff *.webp *.ico *.pcx *.tga)"
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