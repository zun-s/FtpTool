# FtpTool - Python Desktop Application

## 项目简介 (Project Overview)
本项目是一个基于 Python 开发的桌面应用程序，主要用于**多节点 FTP 文件同步与分发**。通过可视化的用户界面，能够一键将同一个压缩包或文件同时上传到多个不同的 FTP 服务器中，极大简化多节点部署、测试包分发以及文件同步的繁杂工作。

## 技术栈 (Tech Stack)
- **编程语言**: Python 3.14+ 
- **GUI 框架**: PyQt6 / PySide6 / CustomTkinter (可根据您的实际偏好进行选择和修改)
- **打包工具**: PyInstaller / Nuitka
- **其他依赖**: 详见 `requirements.txt`

## 目录结构 (Project Structure)
以下是推荐的 Python 桌面应用初始目录结构：

```text
FtpTool/
├── src/                # 源代码主目录
│   ├── main.py         # 程序主入口文件
│   ├── ui/             # GUI 界面代码 (视图层)
│   ├── core/           # 核心业务逻辑 (控制层/模型层)
│   └── utils/          # 工具类和通用辅助函数
├── assets/             # 静态资源文件 (如图标、图片、样式表等)
├── tests/              # 单元测试与集成测试代码
├── requirements.txt    # 项目 Python 依赖包列表
├── .gitignore          # Git 忽略配置
└── README.md           # 项目说明文档
```

## 快速开始 (Quick Start)

### 1. 环境准备
确保您的计算机上已安装 Python 3.14 或更高版本。建议使用虚拟环境来管理本项目依赖。

### 2. 获取代码
```bash
git clone https://github.com/zun-s/FtpTool.git
cd FtpTool
```

### 3. 创建并激活虚拟环境
```bash
python -m venv venv

# Windows 系统激活:
venv\Scripts\activate

# macOS/Linux 系统激活:
source venv/bin/activate
```

### 4. 安装依赖
```bash
pip install -r requirements.txt
```

### 5. 运行程序
```bash
python src/main.py
```

### 6. 打包为 Windows 可执行文件 (.exe)
如果你希望在没有 Python 环境的电脑上运行本项目，可以使用 `PyInstaller` 将其打包为单个独立的 EXE 文件。

1. **安装打包工具**:
   (确保你已经激活了虚拟环境)
   ```bash
   pip install pyinstaller
   ```
2. **执行打包命令**:
   在项目根目录（`FtpTool`）下执行以下命令：
   ```bash
   pyinstaller --noconfirm --onedir --windowed --add-data "src;src/" --add-data "assets;assets/" --name "FtpTool" "src/main.py"
   ```
   *参数说明：*
   - `--windowed` 或 `-w`: 运行程序时不显示黑色控制台终端窗口 (如果是开发调试排错可以去掉这个参数)
   - `--onedir` 或 `-D`: 生成一个包含各种依赖文件的文件夹结构 (相较于单文件打包启动更快，也可换为 `--onefile` 打包为单文件)
   - `--add-data`: 打包时把额外的非代码资源拷贝进去
   - `--name`: 指定输出的可执行文件和文件夹名称为 FtpTool
3. **获取打包结果**:
   打包完成后，在根目录下会生成一个 `dist/FtpTool/` 文件夹。你可以直接进入这个文件夹，双击运行里面的 `FtpTool.exe` 即可启动程序。

## 初始化构建步骤指南
为了帮助您快速启动项目，建议按照以下步骤进行：
1. **建立基础框架**：根据上述目录结构创建相应的文件夹和空白文件。
2. **编写入口文件**：在 `src/main.py` 中编写最基础的 GUI 窗口启动代码，确保能够弹出一个空白窗口。
3. **设计核心 UI**：在 `src/ui/` 下逐步实现主窗口布局。
4. **核心逻辑开发**：在 `src/core/` 编写您的 FTP 交互或核心功能代码。
5. **持续迭代与测试**：编写测试用例并使用 `pytest` 等工具保证代码质量。

## 许可证 (License)
本项目基于 [MIT License](LICENSE) 开源。

## 主要功能 (Core Features)
1. **一键多发**：支持将多个文件、压缩包或**整个文件夹**（支持子目录穿透）同时上传到多个目标 FTP 服务器，达成一键分发和部署的目的。
2. **多服务器管理**：支持添加、编辑、删除和保存多个 FTP 服务器连接配置。
3. **独立配置与跳过**：支持为单个服务器指定**独立的远端上传路径**，也支持通过界面的勾选框在当前上传任务中临时**跳过 (不启用)** 某台服务器。
4. **上传状态可视化**：提供清晰的进度条和各个服务器的上传状态反馈，实时掌握成功或失败情况。
5. **并发上传**：采用多线程或异步方式实现对多个服务器并发上传，大幅提升分发效率。
6. **本地配置持久化**：将预设的 FTP 服务器列表及详细配置保存在本地 JSON，方便下次随时调用。
7. **远端文件直览与管理**：支持在服务器列表中右键选中“浏览远端目录”，通过优雅的**左右分栏**直接查看 FTP 上的文件和文件夹结构。
8. **远端下载与删除**：在浏览目录时，支持选中文件或**整个文件夹**进行一键下载到本地（递归下载），或是直接在远端执行双重确认的永久删除操作。
