图像格式转换工具
这是一个简单的图形界面（GUI）工具，用于将图像在多种格式之间进行转换，支持 HEIC、JPG、PNG、GIF、TIFF 等格式。使用 PyQt6 构建，支持批量转换，并能处理多帧图像（例如 GIF、TIFF），将多帧图像的每一帧保存到单独的子文件夹中。
功能特性

支持多种格式之间的图像转换：JPG、PNG、WEBP、BMP、GIF、TIFF、ICO。
支持 HEIC 格式（iPhone 常用格式）。
处理多帧图像（例如 GIF、TIFF），将每帧保存为单独文件，并存放在以原文件名命名的子文件夹中。
支持 ICO 格式的尺寸调整。
提供友好的图形界面，包含进度条和状态更新。
优化了性能，支持并行处理和内存高效的帧处理。

依赖环境
本工具需要安装以下 Python 库：

Python：3.6 或更高版本
PyQt6：用于图形界面框架
pillow-heif：支持 HEIC 格式
opencv-python：用于高效图像处理
numpy：opencv-python 的依赖
Pillow：用于图像处理

安装依赖
使用以下命令安装所有依赖库，推荐使用国内镜像源以加速下载（以清华大学镜像源为例）：
pip install PyQt6 pillow-heif opencv-python numpy Pillow -i https://pypi.tuna.tsinghua.edu.cn/simple

其他国内镜像源（可选）
如果清华大学镜像源不可用，可以尝试以下镜像源：

阿里云镜像源：pip install PyQt6 pillow-heif opencv-python numpy Pillow -i https://mirrors.aliyun.com/pypi/simple/


豆瓣镜像源：pip install PyQt6 pillow-heif opencv-python numpy Pillow -i http://pypi.douban.com/simple/ --trusted-host pypi.douban.com


中国科技大学镜像源：pip install PyQt6 pillow-heif opencv-python numpy Pillow -i https://pypi.mirrors.ustc.edu.cn/simple/



使用方法
运行工具

下载或克隆本项目：
确保 heic_to_jpg_converter.py 文件和 Converters.ico 图标文件在同一目录下。


安装依赖：使用上述命令安装所有依赖库。
运行脚本：python heic_to_jpg_converter.py


使用图形界面：
工具会打开一个窗口，显示“选择图像文件”按钮。
点击按钮，选择一个或多个图像文件（支持 HEIC、JPG、PNG、GIF、TIFF 等格式）。
弹出的对话框中选择输出格式（例如 JPG、PNG、ICO）以及 ICO 尺寸（如果适用）。
点击“确定”开始转换。
转换后的文件会保存在输入文件所在目录下的 pic 子文件夹中：
单帧图像直接保存在 pic 文件夹中（例如 pic/image.jpg）。
多帧图像（例如 GIF、TIFF）会保存在以原文件名命名的子文件夹中（例如 pic/image/image_page1.jpg）。





示例

输入文件：photo.heic、animation.gif（一个包含 5 帧的 GIF）
输出文件：
pic/photo.jpg（单帧 HEIC 转换为 JPG）
pic/animation/animation_page1.jpg 到 pic/animation/animation_page5.jpg（GIF 的每一帧转换为 JPG）



构建可执行文件
你可以使用 PyInstaller 将工具打包为独立的可执行文件，用户无需安装 Python 或任何依赖即可运行。
打包前的准备

安装 PyInstaller：pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple


安装 UPX（可选，用于减小可执行文件体积）：
从 UPX 官网 下载 UPX。
将 UPX 可执行文件放置在一个目录中（例如 D:\upx）。



打包命令
运行以下命令将工具打包为一个文件夹（使用 --onedir 模式），包含可执行文件和所有依赖：
pyinstaller --noconfirm --onedir --windowed --icon=Converters.ico --add-data "Converters.ico;." --hidden-import=opencv-python --hidden-import=numpy --hidden-import=pillow_heif --hidden-import=PyQt6 --hidden-import=PyQt6.QtCore --hidden-import=PyQt6.QtGui --hidden-import=PyQt6.QtWidgets --upx-dir D:\upx heic_to_jpg_converter.py


选项说明：
--onedir：将程序打包为一个文件夹（推荐使用，便于兼容性和调试）。
--windowed：以图形界面模式运行（不弹出命令行窗口）。
--icon=Converters.ico：设置程序图标（确保 Converters.ico 文件在项目目录中）。
--add-data "Converters.ico;."：将图标文件嵌入打包（Windows 使用 ; 分隔，macOS/Linux 使用 :）。
--hidden-import：确保包含所有依赖库。
--upx-dir D:\upx：使用 UPX 压缩可执行文件以减小体积（需调整为你的 UPX 目录）。
heic_to_jpg_converter.py：主脚本文件名。



打包结果

运行命令后，PyInstaller 会在 dist 目录中生成一个 heic_to_jpg_converter 文件夹。
该文件夹包含可执行文件和所有依赖。
将整个 heic_to_jpg_converter 文件夹分发给用户，用户双击 heic_to_jpg_converter.exe 即可运行程序。

打包注意事项

如果可执行文件运行时提示缺少 DLL（例如 opencv_videoio_ffmpeg*.dll），需要手动添加：
在 Python 环境中找到 DLL 文件（通常在 venv\Lib\site-packages\cv2 目录）。
将命令中添加 --add-binary 选项：--add-binary "cv2\opencv_videoio_ffmpeg*.dll;cv2"




在没有 Python 或依赖的电脑上测试打包后的程序，确保正常运行。

常见问题

转换失败：检查界面中的状态信息，查看错误详情。确保输入文件未损坏。
可执行文件无法运行：确认所有依赖已正确打包。如果缺少 DLL，请使用 --add-binary 添加。
可执行文件体积过大：--onedir 模式提高了兼容性，UPX 压缩可以减小体积，但可能被某些杀毒软件误报。

许可证
本项目采用 MIT 许可证。您可以自由使用、修改和分发。
