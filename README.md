# AllCamera

一个用于管理和控制多种品牌工业相机的统一接口和界面，旨在简化相机集成和操作，提高开发效率。

## 主要特性

*   **多相机支持**: 通过工厂模式统一管理和控制不同品牌（如海康威视）的工业相机。
*   **设备管理**: 自动发现、手动选择、刷新相机设备列表。
*   **模拟模式**: 支持在没有物理相机的情况下进行开发和测试。
*   **实时预览**: 提供流畅的相机视频流实时显示，并展示帧率 (FPS)。
*   **参数调整**: 支持实时调整相机的常用参数，如曝光时间、增益、白平衡，并支持自动模式切换。
*   **图像设置**: 配置相机的帧率、触发模式（连续采集、软触发、硬触发）。
*   **触发控制**: 支持手动发送软触发命令进行单帧捕获。
*   **ROI 选择**: 提供图形化界面选择感兴趣区域 (Region of Interest)。
*   **状态监控**: 清晰展示相机连接状态、详细参数信息和操作日志。
*   **用户界面**: 基于 PyQt5 构建，包含可折叠面板和增强的图像查看器。

## 技术栈

*   **编程语言**: Python 3
*   **GUI 框架**: PyQt5
*   **图像处理**: OpenCV (`cv2`), NumPy
*   **核心库**:
    *   `core`: 相机抽象接口、相机工厂 (`CameraFactoryManager`)、具体相机实现 (e.g., `HikvisionCameraFactory`)、工具类 (日志 `logger`, 信号 `signal_manager`, 配置 `config_manager`)
    *   `UI`: PyQt5 界面组件、自定义控件 (`ImageViewerWidget`, `CollapsiblePanel`)、界面逻辑
*   **并发**: `threading` (用于相机数据读取)

## 安装与配置

1.  **先决条件**:
    *   Python 3.x
    *   pip (Python 包管理器)
    *   对应品牌工业相机的 SDK (例如：海康威视 MVS SDK)。请根据您使用的相机型号，从相机制造商官网下载并安装相应的 SDK。确保 SDK 的库文件路径已正确添加到系统环境变量中，或者根据具体 SDK 的要求进行配置。

2.  **克隆仓库**:
    ```bash
    git clone https://github.com/youguoda/AllCamera.git
    cd AllCamera
    ```

3.  **安装 Python 依赖**:
    *   建议在虚拟环境中安装依赖。
    *   目前项目缺少 `requirements.txt` 文件，请根据 `技术栈` 和导入语句手动安装所需库：
      ```bash
      pip install PyQt5 opencv-python numpy
      ```
    *   **注意**: `opencv-python` 包含了 `cv2` 模块。

4.  **配置 (可选)**:
    *   检查 `UI/resources/configs/config.json` 文件，根据需要调整配置项（如果项目使用了该配置文件）。
    *   确保 `logs/` 目录存在且具有写入权限，用于存储日志文件。

## 使用方法

1.  **启动应用程序**:
    在项目根目录下运行以下命令：
    ```bash
    python UI/detectTabs/camera_tab.py
    ```

2.  **基本操作流程**:
    *   **刷新设备**: 启动后，点击 "刷新列表" 按钮来搜索连接到系统的相机。如果启用了 "使用模拟模式"，则会显示模拟设备。
    *   **选择相机**: 从下拉列表中选择要操作的相机，或保持 "自动选择"（通常会选择第一个找到的设备或特定目标型号）。
    *   **连接相机**: 点击 "连接相机" 按钮。连接成功后，按钮变为 "断开相机"，参数面板和控制按钮将被启用。
    *   **开始/停止视频流**: 点击 "开始视频流" 按钮以启动实时预览。再次点击 "停止视频流" 以暂停。
    *   **调整参数**: 在视频流停止时，可以通过右侧面板调整曝光、增益、帧率等参数，然后点击 "应用参数"。部分参数（如触发模式）可能在连接后即可调整。
    *   **软触发**: 在 "软触发" 或 "硬触发" 模式下，点击 "拍照 (软触发)" 按钮可捕获单帧图像。
    *   **选择 ROI**: 点击 "选择 ROI" 按钮，然后在图像预览区域拖动鼠标选择感兴趣区域。选择完成后，ROI 坐标将显示在状态信息中（需要相机支持设置 ROI）。
    *   **查看状态**: 在 "状态信息" 面板查看当前操作日志和相机详细信息。

## 项目结构

```
AllCamera/
├── .gitignore         # Git 忽略文件配置
├── core/              # 核心业务逻辑
│   ├── __init__.py
│   ├── camera/        # 相机相关模块 (接口, 工厂, 具体实现)
│   │   ├── __init__.py
│   │   ├── camera_factory.py
│   │   ├── camera_interface.py
│   │   ├── hikvision_camera_factory.py
│   │   ├── hikvision_camera.py
│   │   └── MvImport/  # 海康威视 SDK Python 封装
│   └── utils/         # 通用工具模块 (日志, 配置, 信号等)
│       ├── __init__.py
│       ├── config_manager.py
│       ├── error_handler.py
│       ├── logger.py
│       └── signal_manager.py
├── logs/              # 日志文件存储目录
├── UI/                # 用户界面相关代码
│   ├── __init__.py
│   ├── controllers/   # 控制器 (连接视图和模型)
│   ├── detectTabs/    # 主要功能标签页 (如相机控制)
│   │   └── camera_tab.py # 相机控制界面的主要实现
│   ├── models/        # 数据模型
│   ├── resources/     # 资源文件 (图标, 配置文件, 主题)
│   │   ├── configs/
│   │   ├── icons/
│   │   └── themes/
│   ├── utils/         # UI 相关工具
│   ├── views/         # 视图 (UI 布局定义)
│   └── widgets/       # 自定义 UI 控件
├── README.md          # 项目说明文件
```

## 贡献指南

我们欢迎各种形式的贡献！如果您想为 AllCamera 做出贡献，请遵循以下步骤：

1.  **报告问题**: 如果您发现任何错误或有功能建议，请通过 [GitHub Issues](<your-issue-tracker-url>) 提交问题。请提供详细的描述、重现步骤和您的环境信息。
2.  **贡献代码**:
    *   Fork 本仓库。
    *   创建一个新的分支 (`git checkout -b feature/your-feature-name`)。
    *   进行修改并提交 (`git commit -am 'Add some feature'`)。
    *   将您的分支推送到 Fork 的仓库 (`git push origin feature/your-feature-name`)。
    *   创建一个 Pull Request 到主仓库的 `main` 或 `develop` 分支。

请确保您的代码遵循项目的编码风格（如果已定义），并添加适当的测试（如果适用）。

## 许可证

本项目采用 [在此处插入许可证名称，例如 MIT] 许可证。详情请参阅 `LICENSE` 文件（如果存在）。

示例：
本项目采用 [MIT](https://opensource.org/licenses/MIT) 许可证。

## 联系方式

*   **维护者**: [你的名字或组织名称] - [你的邮箱地址]
*   **项目链接**: [你的项目仓库 URL]

**致谢**

*   感谢所有为本项目做出贡献的开发者。
*   感谢 [任何你想要感谢的第三方库或资源]。