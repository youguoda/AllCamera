logger.py文件是一个日志管理模块，提供了统一的日志记录功能(从而不需要在各个模块中重复定义)。
## 主要组件和功能：

1. **LoggerSignals类**

* 继承自QObject，用于在Qt UI中显示日志
* 定义了log\_message信号，用于发送日志级别和内容

2. **Logger类（核心类）**

* 使用单例模式实现，确保全局只有一个日志实例
* 主要功能：

  * 支持控制台输出
  * 支持文件输出（可配置文件大小和备份数量）默认日志文件名为 app_YYYYMMDD.log。
  * 支持UI显示（通过Qt信号）
* 支持的日志级别：

  * debug：调试信息
  * info：一般信息
  * warning：警告信息
  * error：错误信息
  * exception：异常信息（包含堆栈）
  * critical：严重错误

3. **工具函数**

* `setup_logger()`：设置并返回logger实例
* `get_logger()`：获取全局logger实例

4. **主要特性**

* 日志格式：`时间 [级别] [文件名:行号] - 消息内容`
* 支持日志文件自动轮转（默认最大10MB，保留10个备份）
* 支持同时输出到控制台、文件和UI
* 线程安全（使用Python自带的logging模块）

日志模块使用：

1. **获取 Logger 实例**: 在需要记录日志的 Python 文件中，首先导入 `get_logger` 函数，然后调用它来获取全局唯一的 Logger 实例。

    ```python
    from core.utils.logger import get_logger

    # 获取 logger 实例
    logger = get_logger()
    ```
2. **记录日志**: 获取到 `logger` 实例后，就可以调用它提供的不同级别的方法来记录日志了。

    ```python
    # 记录不同级别的日志
    logger.debug("这是一条调试信息，通常用于开发阶段。")
    logger.info("这是一条普通信息，例如程序启动、配置加载成功等。")
    logger.warning("这是一条警告信息，表示可能出现问题，但不影响程序运行。")
    logger.error("记录一个错误，程序可能无法完成某个操作。")
    logger.critical("记录一个严重错误，可能导致程序崩溃。")

    # 记录异常信息（会自动包含错误发生时的堆栈信息）
    try:
        result = 10 / 0
    except ZeroDivisionError:
        logger.exception("计算出错！") # 会记录 "计算出错！" 以及详细的除零错误堆栈
    ```
3.  **(可选) 初始化配置**: 通常，你会在应用程序的入口处（例如 `main.py` 或 `app.py`）调用 `setup_logger` 一次，来配置日志级别和文件输出等。如果在调用 `get_logger` 时还没有初始化，它会自动使用默认设置进行初始化。

    ```python
    from core.utils.logger import setup_logger
    import logging

    # 在程序启动时进行配置
    # 设置最低记录级别为 INFO，日志文件存放在 'logs' 目录下
    setup_logger(level=logging.INFO, log_dir='app_logs')

    # 后续在其他模块中直接调用 get_logger() 即可
    # logger = get_logger()
    # logger.info(...)
    ```
4. **(可选) 在 Qt UI 中显示日志**: 如果你的应用有 PyQt 界面，并且想在界面上显示日志：

    * 在你的 UI 类中，导入 `logger_signals`。
    * 将 `logger_signals.log_message` 信号连接到一个槽函数（例如，更新一个 `QTextEdit` 控件）。

    ```python
    from PyQt5.QtWidgets import QTextEdit
    from core.utils.logger import logger_signals

    class MyMainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.log_display = QTextEdit(self) # 假设有一个 QTextEdit 用于显示日志
            # ... 其他UI设置 ...

            # 连接信号到槽函数
            logger_signals.log_message.connect(self.update_log_display)

        def update_log_display(self, level, message):
            # 在 UI 控件中追加日志
            self.log_display.append(f"[{level}] {message}")

    # 当其他地方调用 logger.info("...") 时，update_log_display 会被触发
    ```