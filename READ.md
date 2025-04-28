图像格式转换工具
软件介绍
这是一个基于 Python 和 PyQt6 的图形界面（GUI）工具，用于将图像在多种格式之间转换，支持包括 HEIC、JPG、JFIF、PNG、WEBP、BMP、GIF、TIFF、ICO 和 TGA 在内的多种输入格式。工具支持批量处理、多帧图像（如 GIF、TIFF）分离为单帧，以及 ICO 格式的尺寸调整。程序轻量高效，移除 OpenCV 依赖，适合日常图像格式转换需求。
功能特性

多格式支持：输入格式包括 HEIC、JPG、JFIF、PNG、WEBP、BMP、GIF、TIFF、ICO、TGA；输出格式包括 JPG、PNG、WEBP、BMP、GIF、TIFF、ICO。
HEIC 支持：转换 iPhone 常用的 HEIC 格式。
多帧处理：将 GIF 或 TIFF 的多帧图像分离为单帧，保存到以原文件名命名的子文件夹。
ICO 尺寸调整：支持 16x16 到 256x256 的 ICO 图标尺寸。
友好界面：提供文件选择、进度条和状态提示，操作简单。
高效轻量：使用 Pillow 处理图像，无需 OpenCV，打包体积小（约 30-100 MB）。

运行所需的依赖
环境要求

Python：3.6 或更高版本
操作系统：Windows、macOS 或 Linux

依赖库

PyQt6：图形界面框架
pillow-heif：支持 HEIC 格式
Pillow：图像处理核心库

安装依赖
推荐使用国内镜像源（清华大学镜像源）加速下载：
pip install PyQt6 pillow-heif Pillow -i https://pypi.tuna.tsinghua.edu.cn/simple

其他国内镜像源（可选）
如果清华大学镜像源不可用，可尝试以下镜像源：

阿里云：pip install PyQt6 pillow-heif Pillow -i https://mirrors.aliyun.com/pypi/simple/


豆瓣：pip install PyQt6 pillow-heif Pillow -i http://pypi.douban.com/simple/ --trusted-host pypi.douban.com


中国科技大学：pip install PyQt6 pillow-heif Pillow -i https://pypi.mirrors.ustc.edu.cn/simple/



打包所需的依赖与指令
打包工具

PyInstaller：将 Python 脚本打包为独立可执行文件。
UPX（可选）：压缩可执行文件，减小体积。

安装打包依赖

安装 PyInstaller：pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple


安装 UPX（可选）：
下载 UPX 5.0.0 或最新版：UPX 官网 或 GitHub 发布页。
解压到指定目录（例如 D:\upx），确保包含 upx.exe（Windows）或 upx（Linux/macOS）。
无需将 UPX 添加到系统环境变量，PyInstaller 通过 --upx-dir 指定路径。



打包命令
确保 heic_to_jpg_converter.py 和 Converters.ico 在同一目录下。


pyinstaller --noconfirm --onefile --windowed --icon=Converters.ico --add-data "Converters.ico;." --hidden-import=PyQt6 --hidden-import=PyQt6.QtCore --hidden-import=PyQt6.QtGui --hidden-import=PyQt6.QtWidgets --hidden-import=pillow_heif --hidden-import=PIL heic_to_jpg_converter.py


命令选项说明

--onedir：生成包含可执行文件和依赖的文件夹（推荐，兼容性高）。
--windowed：以图形界面模式运行（无命令行窗口）。
--icon：设置程序图标。
--add-data：嵌入 Converters.ico（Windows 使用 ; 分隔，macOS/Linux 使用 :）。
--hidden-import：包含必要模块。
--upx-dir：指定 UPX 目录（仅带 UPX 时使用）。
如果 UPX 路径不同，替换 D:\upx 为实际路径。

打包结果

位置：dist/heic_to_jpg_converter/。
大小：带 UPX 约 30-70 MB，不带 UPX 约 50-100 MB。
分发：将整个 dist/heic_to_jpg_converter/ 文件夹复制给用户，双击 heic_to_jpg_converter.exe 运行。

使用方法
运行程序

准备文件：
确保 heic_to_jpg_converter.py 和 Converters.ico 在同一目录。
安装依赖（见上文）。


运行脚本：python heic_to_jpg_converter.py


操作步骤：
打开程序，点击“Select Image Files”选择图像（支持 HEIC、JPG、JFIF、PNG、GIF、TGA 等）。
在弹出的对话框中选择输出格式（JPG、PNG、WEBP 等）和 ICO 尺寸（如果适用）。
点击“OK”开始转换。
转换后的文件保存在输入文件目录下的 pic 子文件夹：
单帧图像：如 pic/image.jpg。
多帧图像：如 pic/image/image_page1.jpg。





示例

输入：photo.jfif（单帧）、animation.gif（5 帧）。
输出：
pic/photo.jpg（JFIF 转换为 JPG）。
pic/animation/animation_page1.jpg 到 animation_page5.jpg（GIF 帧分离）。



常见问题

转换失败：
检查界面状态信息（status_label）或日志（控制台）。
确认输入文件未损坏（用 file image.jfif 检查）。


打包程序无法运行：
检查是否缺少 DLL（如 libheif）：
找到 venv\Lib\site-packages\pillow_heif 中的 DLL。
添加到打包命令：--add-binary "venv\Lib\site-packages\pillow_heif\*.dll;pillow_heif".


在无 Python 环境的电脑上测试。


打包体积过大：
使用 UPX 压缩（--upx-dir）。
确认未包含 OpenCV（本程序已移除）。


JFIF 文件无法选择：
确认文件扩展名为 .jfif（用 dir 检查）。
检查日志中的 Selected files 信息。



许可证
本项目采用 MIT 许可证，可自由使用、修改和分发。
