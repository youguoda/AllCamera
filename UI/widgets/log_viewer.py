"""
系统日志查看器
------------
用于显示系统日志和调试信息的控件
"""

import time
from enum import Enum, auto
from collections import deque

from PyQt5.QtGui import QColor, QTextCharFormat, QBrush, QTextCursor
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QSizePolicy,
                             QPushButton, QComboBox, QLabel, QCheckBox,
                             QToolButton)

from UI.utils.ui_constants import LIGHT_COLORS, SPACING, FONTS


class LogLevel(Enum):
    """日志级别枚举"""
    DEBUG = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


class LogEntry:
    """日志条目类"""
    def __init__(self, level, message, timestamp=None, module=None):
        """
        初始化日志条目
        
        Args:
            level: 日志级别
            message: 日志消息
            timestamp: 时间戳（默认为当前时间）
            module: 模块名称
        """
        self.level = level
        self.message = message
        self.timestamp = timestamp if timestamp is not None else time.time()
        self.module = module
        
    def formatted_time(self):
        """获取格式化的时间"""
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.timestamp))


class LogViewer(QTextEdit):
    """
    日志查看器控件
    用于显示格式化的日志信息
    """
    
    def __init__(self, parent=None, max_entries=1000):
        """
        初始化日志查看器
        
        Args:
            parent: 父控件
            max_entries: 最大日志条目数
        """
        super().__init__(parent)
        
        # 配置日志显示属性
        self.setReadOnly(True)
        self.setLineWrapMode(QTextEdit.NoWrap)
        self.setUndoRedoEnabled(False)
        self.document().setMaximumBlockCount(max_entries)
        
        # 日志条目存储
        self._log_entries = deque(maxlen=max_entries)
        self._filtered_entries = []
        
        # 过滤设置
        self._min_level = LogLevel.DEBUG
        self._module_filter = None
        self._text_filter = None
        
        # 颜色定义
        self._level_colors = {
            LogLevel.DEBUG: QColor("#787878"),  # 灰色
            LogLevel.INFO: QColor("#0078D7"),   # 蓝色
            LogLevel.WARNING: QColor("#FFA500"),  # 橙色
            LogLevel.ERROR: QColor("#FF0000"),    # 红色
            LogLevel.CRITICAL: QColor("#8B0000")  # 深红色
        }
        
        # 样式设置
        self._setup_style()
    
    def _setup_style(self):
        """设置日志查看器样式"""
        self.setStyleSheet(f"""
            QTextEdit {{
                background-color: {LIGHT_COLORS["SURFACE"]};
                color: {LIGHT_COLORS["TEXT_PRIMARY"]};
                font-family: "Consolas", "Courier New", monospace;
                font-size: {FONTS["SIZE_TITLE"]}px;
                border: 1px solid {LIGHT_COLORS["BORDER"]};
                selection-background-color: {LIGHT_COLORS["PRIMARY"] + "40"};
                padding: {SPACING["SMALL"]}px;
            }}
        """)
    
    def add_log(self, level, message, module=None):
        """
        添加日志条目
        
        Args:
            level: 日志级别
            message: 日志消息
            module: 模块名称
        """
        # 创建日志条目
        entry = LogEntry(level, message, module=module)
        self._log_entries.append(entry)
        
        # 如果符合过滤条件，则显示
        if self._should_display(entry):
            self._append_entry_to_view(entry)
    
    def _should_display(self, entry):
        """
        检查日志条目是否符合过滤条件
        
        Args:
            entry: 日志条目
        
        Returns:
            bool: 是否符合过滤条件
        """
        # 检查日志级别
        if entry.level.value < self._min_level.value:
            return False
        
        # 检查模块过滤
        if self._module_filter and entry.module != self._module_filter:
            return False
        
        # 检查文本过滤
        if self._text_filter and self._text_filter.lower() not in entry.message.lower():
            return False
        
        return True
    
    def _append_entry_to_view(self, entry):
        """
        将日志条目添加到视图
        
        Args:
            entry: 日志条目
        """
        # 创建文本格式
        format = QTextCharFormat()
        format.setForeground(QBrush(self._level_colors.get(entry.level, QColor("black"))))
        
        # 级别格式（加粗）
        level_format = QTextCharFormat(format)
        if entry.level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            font = level_format.font()
            font.setBold(True)
            level_format.setFont(font)
        
        # 构建日志文本
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        # 时间戳
        self.setTextCursor(cursor)
        cursor.insertText(f"[{entry.formatted_time()}] ", format)
        
        # 日志级别
        level_text = f"[{entry.level.name}]"
        cursor.insertText(level_text, level_format)
        
        # 模块名称（如果有）
        if entry.module:
            cursor.insertText(f" [{entry.module}]", format)
        
        # 日志消息
        cursor.insertText(f": {entry.message}\n", format)
        
        # 滚动到底部
        self.ensureCursorVisible()
    
    def set_min_level(self, level):
        """
        设置最小日志级别
        
        Args:
            level: 最小日志级别
        """
        self._min_level = level
        self.refresh_view()
    
    def set_module_filter(self, module):
        """
        设置模块过滤器
        
        Args:
            module: 模块名称，None表示不过滤
        """
        self._module_filter = module
        self.refresh_view()
    
    def set_text_filter(self, text):
        """
        设置文本过滤器
        
        Args:
            text: 过滤文本，None表示不过滤
        """
        self._text_filter = text
        self.refresh_view()
    
    def refresh_view(self):
        """刷新日志视图"""
        # 清空当前视图
        self.clear()
        
        # 重新添加符合条件的日志
        for entry in self._log_entries:
            if self._should_display(entry):
                self._append_entry_to_view(entry)
    
    def clear_logs(self):
        """清空所有日志"""
        self._log_entries.clear()
        self.clear()


class LogViewerWidget(QWidget):
    """
    日志查看器小部件
    包括日志显示和控制面板
    """
    
    def __init__(self, parent=None, max_entries=1000):
        """
        初始化日志查看器小部件
        
        Args:
            parent: 父控件
            max_entries: 最大日志条目数
        """
        super().__init__(parent)
        
        # 创建布局
        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(2)  # 减小间距
        
        # 控制面板 - 使用更紧凑的布局
        self._control_panel = QWidget()
        self._control_layout = QHBoxLayout(self._control_panel)
        self._control_layout.setContentsMargins(2, 1, 2, 1)  # 减小边距
        
        # 日志级别选择 - 使用更小的控件
        self._level_label = QLabel("级别:")
        self._level_label.setMaximumWidth(30)
        self._level_combo = QComboBox()
        self._level_combo.addItems(["调试", "信息", "警告", "错误", "严重"])
        self._level_combo.setCurrentIndex(0)
        self._level_combo.setMaximumWidth(60)
        
        # 过滤输入 - 设置为紧凑型
        self._filter_label = QLabel("过滤:")
        self._filter_label.setMaximumWidth(30)
        self._filter_input = QComboBox()
        self._filter_input.setEditable(True)
        self._filter_input.setInsertPolicy(QComboBox.InsertAtTop)
        self._filter_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._filter_input.setMaximumHeight(22)  # 减小高度
        
        # 删除自动滚动选项框，改用按钮
        self._search_button = QToolButton()
        self._search_button.setText("搜索")
        self._search_button.setMaximumWidth(40)
        
        # 添加到控制面板
        self._control_layout.addWidget(self._level_label)
        self._control_layout.addWidget(self._level_combo)
        self._control_layout.addWidget(self._filter_label)
        self._control_layout.addWidget(self._filter_input)
        self._control_layout.addWidget(self._search_button)
        
        # 日志查看器
        self._log_viewer = LogViewer(max_entries=max_entries)
        self._log_viewer.setMaximumHeight(120)  # 限制高度
        
        # 添加到主布局
        self._layout.addWidget(self._control_panel)
        self._layout.addWidget(self._log_viewer)
        
        self.setLayout(self._layout)
        
        # 连接信号槽
        self._level_combo.currentIndexChanged.connect(self._on_level_changed)
        self._filter_input.editTextChanged.connect(self._on_filter_changed)
        self._search_button.clicked.connect(self._on_search_clicked)
    
    def _on_level_changed(self, index):
        """
        日志级别变化处理
        
        Args:
            index: 级别索引
        """
        level_map = [
            LogLevel.DEBUG,
            LogLevel.INFO,
            LogLevel.WARNING,
            LogLevel.ERROR,
            LogLevel.CRITICAL
        ]
        
        if 0 <= index < len(level_map):
            self._log_viewer.set_min_level(level_map[index])
    
    def _on_filter_changed(self, text):
        """
        过滤文本变化处理
        
        Args:
            text: 过滤文本
        """
        self._log_viewer.set_text_filter(text if text else None)
    
    def _on_search_clicked(self):
        """搜索按钮点击处理"""
        text = self._filter_input.currentText()
        if text and text not in [self._filter_input.itemText(i) for i in range(self._filter_input.count())]:
            self._filter_input.addItem(text)
        self._log_viewer.set_text_filter(text if text else None)
    
    def add_log(self, level, message, module=None):
        """
        添加日志条目
        
        Args:
            level: 日志级别
            message: 日志消息
            module: 模块名称
        """
        self._log_viewer.add_log(level, message, module)
    
    def log_debug(self, message, module=None):
        """记录调试日志"""
        self.add_log(LogLevel.DEBUG, message, module)
    
    def log_info(self, message, module=None):
        """记录信息日志"""
        self.add_log(LogLevel.INFO, message, module)
    
    def log_warning(self, message, module=None):
        """记录警告日志"""
        self.add_log(LogLevel.WARNING, message, module)
    
    def log_error(self, message, module=None):
        """记录错误日志"""
        self.add_log(LogLevel.ERROR, message, module)
    
    def log_critical(self, message, module=None):
        """记录严重错误日志"""
        self.add_log(LogLevel.CRITICAL, message, module)
    
    def clear_logs(self):
        """清空所有日志"""
        self._log_viewer.clear_logs()
