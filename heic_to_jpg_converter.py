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
from PyQt6.QtGui import QIcon
import logging
import datetime

# 导入依赖以获取版本信息
try:
    import PIL
    import PyQt6
    import pillow_heif as pillow_heif_module
except ImportError as e:
    logging.warning(f"无法导入某些依赖: {str(e)}")

# 定义 resource_path 函数
def resource_path(relative_path):
    """获取资源文件的绝对路径，兼容 PyInstaller 的 --onefile 模式"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(__file__), relative_path)

# 设置日志
def setup_logging(log_dir):
    """设置日志，写入文件和控制台，日志文件位于指定目录"""
    try:
        # 确保日志目录存在
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            logging.info(f"创建日志目录: {log_dir}")
        
        log_file = os.path.join(log_dir, "converter_log.txt")
        
        # 配置日志，强制实时写入
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8', mode='w'),
                logging.StreamHandler()
            ],
            force=True  # 强制覆盖现有处理器
        )
        
        # 确保日志实时写入
        for handler in logging.getLogger().handlers:
            if isinstance(handler, logging.FileHandler):
                handler.stream.flush()
        
        logging.info("日志初始化完成，日志文件：%s", log_file)
        
        # 记录程序启动信息
        logging.info("图片格式转换器启动")
        logging.info(f"Python 版本: {sys.version}")
        
        # 获取依赖版本
        try:
            pillow_version = getattr(PIL, '__version__', '未知')
            pyqt6_version = getattr(PyQt6, '__version__', '未知')
            pillow_heif_version = getattr(pillow_heif_module, '__version__', '未知')
            logging.info(f"依赖版本 - Pillow: {pillow_version}, PyQt6: {pyqt6_version}, pillow-heif: {pillow_heif_version}")
        except Exception as e:
            logging.warning(f"无法获取依赖版本: {str(e)}")
            
        return log_file
    except Exception as e:
        # 如果日志文件创建失败，尝试写入临时目录
        import tempfile
        temp_log_dir = tempfile.gettempdir()
        temp_log_file = os.path.join(temp_log_dir, "converter_log.txt")
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(temp_log_file, encoding='utf-8', mode='w'),
                logging.StreamHandler()
            ],
            force=True
        )
        logging.error(f"无法创建日志文件，切换至临时目录: {temp_log_file}, 错误: {str(e)}")
        return temp_log_file

class ConverterThread(QThread):
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    conversion_finished = pyqtSignal()

    def __init__(self, files, output_format, ico_size, output_base_dir):
        super().__init__()
        self.files = files
        self.output_format = output_format
        self.ico_size = ico_size
        self.output_base_dir = output_base_dir

    def process_image(self, file_path, format_mapping):
        logging.info(f"开始处理图片: {file_path}")
        try:
            # 验证文件是否存在
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")

            # 获取图片信息
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            logging.info(f"文件大小: {file_size:.2f} MB")

            # 处理 HEIC 文件
            if file_path.lower().endswith((".heic", ".heic")):
                logging.debug(f"处理 HEIC 文件: {file_path}")
                try:
                    heif_file = pillow_heif.read_heif(file_path)
                    image = Image.frombytes(
                        heif_file.mode,
                        heif_file.size,
                        heif_file.data,
                        "raw",
                    )
                    logging.info(f"HEIC 图片尺寸: {heif_file.size}, 模式: {heif_file.mode}")
                    images_info = [(image, False)]
                except Exception as e:
                    raise ValueError(f"无法读取 HEIC 文件: {str(e)}")
            else:
                # 打开图像并逐帧处理
                try:
                    image = Image.open(file_path)
                    logging.info(f"图片格式: {image.format}, 尺寸: {image.size}, 模式: {image.mode}")
                    images_info = []
                    page_num = 0
                    while True:
                        try:
                            images_info.append((image.copy(), True))
                            image.seek(image.tell() + 1)
                            page_num += 1
                        except EOFError:
                            break
                    logging.info(f"提取到 {len(images_info)} 帧: {file_path}")
                except Exception as e:
                    raise ValueError(f"无法打开图片文件: {str(e)}")

            # 为多帧图像创建子文件夹
            output_filename_base = os.path.splitext(os.path.basename(file_path))[0]
            if len(images_info) > 1:
                output_dir = os.path.join(self.output_base_dir, output_filename_base)
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                    logging.info(f"创建子文件夹: {output_dir}")
            else:
                output_dir = self.output_base_dir

            # 逐帧处理并保存
            for page_num, (img, is_pil_image) in enumerate(images_info):
                logging.info(f"处理第 {page_num + 1} 帧: {file_path}")
                try:
                    # 为 JPG 强制转换为 RGB（去除 Alpha 通道）
                    if self.output_format == "jpg" and img.mode != "RGB":
                        img = img.convert("RGB")
                        logging.debug(f"转换为 RGB 模式")
                    # 为其他格式（如 PNG、WEBP）保留 RGBA，或将非 RGB/RGBA 转换为 RGB
                    elif img.mode not in ("RGB", "RGBA"):
                        img = img.convert("RGB")
                        logging.debug(f"转换为 RGB 模式")

                    # 为 ICO 调整尺寸
                    if self.output_format == "ico" and self.ico_size:
                        if not isinstance(self.ico_size, int) or self.ico_size <= 0:
                            raise ValueError(f"无效的 ICO 尺寸: {self.ico_size}")
                        img = img.resize((self.ico_size, self.ico_size), Image.Resampling.LANCZOS)
                        logging.debug(f"调整 ICO 尺寸: {self.ico_size}x{self.ico_size}")

                    # 保存文件
                    output_filename = output_filename_base
                    if len(images_info) > 1:
                        output_filename += f"_page{page_num + 1}"
                    output_filename += f".{self.output_format}"
                    output_path = os.path.join(output_dir, output_filename)
                    logging.debug(f"准备保存至: {output_path}")

                    pillow_format = format_mapping.get(self.output_format, self.output_format.upper())
                    save_kwargs = {}
                    if self.output_format == "jpg":
                        save_kwargs["quality"] = 95
                    elif self.output_format == "webp":
                        save_kwargs["quality"] = 80
                    elif self.output_format == "ico":
                        save_kwargs["sizes"] = [(self.ico_size, self.ico_size)]

                    img.save(output_path, format=pillow_format, **save_kwargs)
                    logging.info(f"保存成功: {output_path}")

                    if is_pil_image:
                        img.close()
                except Exception as e:
                    logging.error(f"处理第 {page_num + 1} 帧失败: {str(e)}")
                    raise
                finally:
                    if 'img' in locals():
                        img.close()
        except Exception as e:
            logging.error(f"处理图片失败 {file_path}: {str(e)}")
            self.status_updated.emit(f"处理图片失败 {file_path}: {str(e)}")
            raise
        finally:
            # 确保图片对象关闭
            if 'image' in locals():
                image.close()

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
        logging.info(f"开始转换任务，输入文件数量: {total_files}, 输出格式: {self.output_format}")

        processed_files = 0

        # 单线程处理文件
        for file_path in self.files:
            try:
                self.process_image(file_path, format_mapping)
                processed_files += 1
                self.progress_updated.emit(processed_files)
            except Exception as e:
                logging.error(f"线程处理错误 {file_path}: {str(e)}")
                self.status_updated.emit(f"处理图片失败 {file_path}: {str(e)}")
                continue  # 继续处理下一张图片
            finally:
                # 实时刷新日志
                for handler in logging.getLogger().handlers:
                    if isinstance(handler, logging.FileHandler):
                        handler.stream.flush()

        logging.info(f"转换任务完成，成功处理 {processed_files}/{total_files} 张图片")
        self.status_updated.emit("转换完成！")
        self.progress_updated.emit(total_files)
        self.conversion_finished.emit()

class OutputFormatDialog(QDialog):
    def __init__(self, file_count, parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择输出格式")
        self.setFixedSize(400, 165)
        layout = QVBoxLayout()

        self.label = QLabel(f"你选择了 {file_count} 个文件。请选择输出格式：")
        layout.addWidget(self.label)

        self.format_combo = QComboBox()
        self.output_formats = ["JPG", "PNG", "WEBP", "BMP", "GIF", "TIFF", "ICO"]
        self.format_combo.addItems(self.output_formats)
        self.format_combo.currentIndexChanged.connect(self.toggle_ico_size)
        layout.addWidget(self.format_combo)

        self.ico_size_label = QLabel("选择 ICO 尺寸（推荐用于图标）：")
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
        self.setWindowTitle("图片格式转换器")
        self.setFixedSize(400, 100)

        # 默认日志目录（程序所在目录下的 pic 文件夹）
        self.default_log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pic")
        self.log_file = setup_logging(self.default_log_dir)

        # 设置窗口图标
        icon_path = resource_path("Converters.ico")
        self.setWindowIcon(QIcon(icon_path))

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.select_button = QPushButton("选择图片文件")
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
        self.output_base_dir = None

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

    def closeEvent(self, event):
        """捕获窗口关闭事件，记录程序终止"""
        logging.info("用户关闭了程序")
        # 实时刷新日志
        for handler in logging.getLogger().handlers:
            if isinstance(handler, logging.FileHandler):
                handler.stream.flush()
        event.accept()

    def select_files(self):
        input_formats = [
            "Image Files (*.heic *.HEIC *.jpg *.jpeg *.jfif *.JFIF *.png *.bmp *.gif *.tiff *.TIFF *.tif *.TIF *.webp *.ico *.pcx *.tga)"
        ]
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择图片文件", "",
            ";;".join(input_formats)
        )
        if files:
            self.selected_files = files
            # 更新日志目录为输入文件所在目录下的 pic 文件夹
            input_dir = os.path.dirname(files[0])
            self.output_base_dir = os.path.abspath(os.path.join(input_dir, "pic"))
            logging.info(f"用户选择了 {len(files)} 个文件: {files}")
            # 重新设置日志文件到新的 pic 目录
            self.log_file = setup_logging(self.output_base_dir)
            self.show_format_dialog()
        else:
            logging.info("用户未选择任何文件")
            # 实时刷新日志
            for handler in logging.getLogger().handlers:
                if isinstance(handler, logging.FileHandler):
                    handler.stream.flush()

    def show_format_dialog(self):
        file_count = len(self.selected_files)
        if file_count == 0:
            return

        dialog = OutputFormatDialog(file_count, self)
        if dialog.exec():
            self.output_format = dialog.get_selected_format()
            self.ico_size = dialog.get_ico_size()
            logging.info(f"用户选择了输出格式: {self.output_format}, ICO 尺寸: {self.ico_size}")
            self.convert_files()
        else:
            self.selected_files = []
            self.status_label.setText("转换已取消。")
            logging.info("用户取消了转换任务")
            # 实时刷新日志
            for handler in logging.getLogger().handlers:
                if isinstance(handler, logging.FileHandler):
                    handler.stream.flush()

    def convert_files(self):
        total_files = len(self.selected_files)
        if total_files == 0:
            return

        self.progress.setValue(0)
        self.progress.setMaximum(total_files)
        self.select_button.setEnabled(False)
        self.status_label.setText("正在转换...")

        self.converter_thread = ConverterThread(self.selected_files, self.output_format, self.ico_size, self.output_base_dir)
        self.converter_thread.progress_updated.connect(self.update_progress)
        self.converter_thread.status_updated.connect(self.update_status)
        self.converter_thread.conversion_finished.connect(self.on_conversion_finished)
        self.converter_thread.start()

    def update_progress(self, value):
        self.progress.setValue(value)
        logging.debug(f"更新进度: {value}/{self.progress.maximum()}")
        # 实时刷新日志
        for handler in logging.getLogger().handlers:
            if isinstance(handler, logging.FileHandler):
                handler.stream.flush()

    def update_status(self, status):
        self.status_label.setText(status)
        logging.info(f"状态更新: {status}")
        # 实时刷新日志
        for handler in logging.getLogger().handlers:
            if isinstance(handler, logging.FileHandler):
                handler.stream.flush()

    def on_conversion_finished(self):
        self.select_button.setEnabled(True)
        QApplication.instance().beep()
        dialog = QDialog(self)
        dialog.setWindowTitle("完成")
        layout = QVBoxLayout()
        layout.addWidget(QLabel("转换成功完成！文件保存在 'pic' 文件夹中。"))
        button = QPushButton("确定")
        button.clicked.connect(dialog.accept)
        layout.addWidget(button)
        dialog.setLayout(layout)
        dialog.show()
        self.selected_files = []
        logging.info("转换完成对话框显示")
        # 实时刷新日志
        for handler in logging.getLogger().handlers:
            if isinstance(handler, logging.FileHandler):
                handler.stream.flush()

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        window = HeicToJpgConverter()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        logging.error(f"程序运行时发生错误: {str(e)}")
        # 实时刷新日志
        for handler in logging.getLogger().handlers:
            if isinstance(handler, logging.FileHandler):
                handler.stream.flush()
        raise