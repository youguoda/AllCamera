"""
现代化标签页控件
------------
提供美观的标签式界面，支持图标和自定义样式
"""

from PyQt5.QtCore import Qt, QSize, pyqtSignal, QPoint, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QIcon, QPainter, QColor
from PyQt5.QtWidgets import (QTabWidget, QTabBar, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel)

from UI.utils.ui_constants import SPACING, FONTS
from UI.resources.themes.colors import LIGHT_COLORS


class ModernTabBar(QTabBar):
    """
    现代化标签栏
    提供美观的标签样式和动画效果
    """
    
    def __init__(self, parent=None):
        """初始化标签栏"""
        super().__init__(parent)
        
        # 配置属性
        self.setDrawBase(False)
        self.setExpanding(False)
        self.setMovable(True)
        self.setIconSize(QSize(20, 20))
        self.setElideMode(Qt.ElideRight)
        self.setUsesScrollButtons(True)
        
        # 样式属性
        self._indicator_color = QColor(LIGHT_COLORS["PRIMARY"])
        self._indicator_height = 3
        self._tab_padding = 10
        self._animation_duration = 150
        
        # 动画
        self._indicator_pos = 0
        self._indicator_width = 0
        self._animation = QPropertyAnimation(self, b"indicator_pos")
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
        self._animation.setDuration(self._animation_duration)
        
        self._width_animation = QPropertyAnimation(self, b"indicator_width")
        self._width_animation.setEasingCurve(QEasingCurve.OutCubic)
        self._width_animation.setDuration(self._animation_duration)
        
        # 设置样式
        self._set_style()
    
    def _set_style(self):
        """设置标签栏样式"""
        self.setStyleSheet(f"""
            QTabBar {{
                background-color: {LIGHT_COLORS["BACKGROUND"]};
                border: none;
            }}
            
            QTabBar::tab {{
                background-color: transparent;
                color: {LIGHT_COLORS["TEXT_SECONDARY"]};
                font-size: {FONTS["SIZE_NORMAL"]}px;
                padding: {SPACING["MEDIUM"]}px {SPACING["LARGE"]}px;
                margin-right: 2px;
                border: none;
            }}
            
            QTabBar::tab:selected {{
                color: {LIGHT_COLORS["PRIMARY"]};
                background-color: {LIGHT_COLORS["PRIMARY"] + "10"};
                font-weight: bold;
            }}
            
            QTabBar::tab:hover:!selected {{
                color: {LIGHT_COLORS["TEXT_PRIMARY"]};
                background-color: {LIGHT_COLORS["HOVER"]};
            }}
            
            QTabBar::tab:disabled {{
                color: {LIGHT_COLORS["DISABLED"]};
                background-color: transparent;
            }}
            
            QTabBar::scroller {{
                width: 20px;
            }}
            
            QTabBar QToolButton {{
                background-color: {LIGHT_COLORS["BACKGROUND"]};
                border: none;
            }}
            
            QTabBar QToolButton::right-arrow {{
                image: url(:/icons/arrow-right.png);
            }}
            
            QTabBar QToolButton::left-arrow {{
                image: url(:/icons/arrow-left.png);
            }}
        """)
    
    def tabSizeHint(self, index):
        """
        获取标签大小建议
        
        Args:
            index: 标签索引
        
        Returns:
            QSize: 标签大小
        """
        size = super().tabSizeHint(index)
        size.setWidth(size.width() + self._tab_padding * 2)
        size.setHeight(max(size.height(), 40))
        return size
    
    def paintEvent(self, event):
        """
        绘制标签栏
        
        Args:
            event: 绘制事件
        """
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制下划线指示器
        if self.count() > 0:
            painter.setPen(Qt.NoPen)
            painter.setBrush(self._indicator_color)
            
            # 绘制指示器
            rect = QPoint(self._indicator_pos, self.height() - self._indicator_height)
            painter.drawRect(int(rect.x()), int(rect.y()), 
                            int(self._indicator_width), int(self._indicator_height))
    
    def set_indicator_position(self, index):
        """
        设置指示器位置
        
        Args:
            index: 标签索引
        """
        if index < 0 or index >= self.count():
            return
            
        # 获取标签矩形
        rect = self.tabRect(index)
        
        # 设置动画
        self._animation.setStartValue(self._indicator_pos)
        self._animation.setEndValue(rect.x())
        
        self._width_animation.setStartValue(self._indicator_width)
        self._width_animation.setEndValue(rect.width())
        
        # 启动动画
        self._animation.start()
        self._width_animation.start()
    
    def get_indicator_pos(self):
        """获取指示器位置"""
        return self._indicator_pos
    
    def set_indicator_pos(self, pos):
        """设置指示器位置"""
        self._indicator_pos = pos
        self.update()
    
    def get_indicator_width(self):
        """获取指示器宽度"""
        return self._indicator_width
    
    def set_indicator_width(self, width):
        """设置指示器宽度"""
        self._indicator_width = width
        self.update()
    
    # 定义属性
    indicator_pos = property(get_indicator_pos, set_indicator_pos)
    indicator_width = property(get_indicator_width, set_indicator_width)


class ModernTabWidget(QTabWidget):
    """
    现代化标签页控件
    提供美观的标签式界面，支持图标和自定义样式
    """
    
    # 自定义信号
    tab_closed = pyqtSignal(int)  # 标签关闭信号
    
    def __init__(self, parent=None):
        """初始化标签页控件"""
        super().__init__(parent)
        
        # 创建并设置现代标签栏
        self._tab_bar = ModernTabBar()
        self.setTabBar(self._tab_bar)
        
        # 配置属性
        self.setTabsClosable(False)  # 默认不显示关闭按钮
        self.setMovable(True)
        self.setDocumentMode(True)
        
        # 设置样式
        self._set_style()
        
        # 连接信号槽
        self.currentChanged.connect(self._on_tab_changed)
        self.tabCloseRequested.connect(self._on_tab_close_requested)
    
    def _set_style(self):
        """设置标签页控件样式"""
        self.setStyleSheet(f"""
            QTabWidget {{
                background-color: {LIGHT_COLORS["BACKGROUND"]};
                border: none;
            }}
            
            QTabWidget::pane {{
                background-color: {LIGHT_COLORS["SECONDARY"]};
                border: 1px solid {LIGHT_COLORS["BORDER"]};
                border-top: none;
            }}
        """)
    
    def _on_tab_changed(self, index):
        """
        标签切换事件处理
        
        Args:
            index: 新的活动标签索引
        """
        # 更新指示器位置
        self._tab_bar.set_indicator_position(index)
    
    def _on_tab_close_requested(self, index):
        """
        标签关闭请求事件处理
        
        Args:
            index: 要关闭的标签索引
        """
        # 发出关闭信号
        self.tab_closed.emit(index)
    
    def add_tab_with_icon(self, widget, icon, text):
        """
        添加带图标的标签页
        
        Args:
            widget: 标签页内容控件
            icon: 图标（QIcon对象或图标路径）
            text: 标签文本
        
        Returns:
            int: 新标签页索引
        """
        # 转换图标
        if isinstance(icon, str):
            icon = QIcon(icon)
        
        # 添加标签页
        index = self.addTab(widget, icon, text)
        
        # 如果是第一个标签，更新指示器位置
        if self.count() == 1:
            self._tab_bar.set_indicator_position(0)
        
        return index


class TabWithCloseButton(QWidget):
    """
    带关闭按钮的标签内容
    用于在标签栏上显示关闭按钮
    """
    
    # 自定义信号
    close_clicked = pyqtSignal()
    
    def __init__(self, text, icon=None, closable=True, parent=None):
        """
        初始化带关闭按钮的标签
        
        Args:
            text: 标签文本
            icon: 图标（QIcon对象或图标路径）
            closable: 是否显示关闭按钮
            parent: 父控件
        """
        super().__init__(parent)
        
        # 创建布局
        self._layout = QHBoxLayout()
        self._layout.setContentsMargins(4, 2, 4, 2)
        self._layout.setSpacing(4)
        
        # 图标
        if icon is not None:
            if isinstance(icon, str):
                icon = QIcon(icon)
            
            self._icon_label = QLabel()
            self._icon_label.setPixmap(icon.pixmap(16, 16))
            self._layout.addWidget(self._icon_label)
        
        # 文本标签
        self._text_label = QLabel(text)
        self._text_label.setAlignment(Qt.AlignCenter)
        self._layout.addWidget(self._text_label)
        
        # 关闭按钮
        if closable:
            self._close_button = QPushButton("×")
            self._close_button.setFixedSize(16, 16)
            self._close_button.setStyleSheet("""
                QPushButton {
                    border: none;
                    color: #888;
                    font-weight: bold;
                    font-size: 14px;
                    background-color: transparent;
                }
                
                QPushButton:hover {
                    color: #f00;
                }
            """)
            self._layout.addWidget(self._close_button)
            
            # 连接信号槽
            self._close_button.clicked.connect(self.close_clicked)
        
        self.setLayout(self._layout)


class ModernDockableTabWidget(QWidget):
    """
    现代化可停靠标签页控件
    提供可分离和停靠的标签页功能
    """
    
    def __init__(self, parent=None):
        """初始化可停靠标签页控件"""
        super().__init__(parent)
        
        # 创建布局
        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        
        # 标签页控件
        self._tab_widget = ModernTabWidget()
        
        # 添加到布局
        self._layout.addWidget(self._tab_widget)
        
        self.setLayout(self._layout)
        
        # 连接信号槽
        self._tab_widget.tabCloseRequested.connect(self._on_tab_close_requested)
    
    def _on_tab_close_requested(self, index):
        """
        标签关闭请求事件处理
        
        Args:
            index: 要关闭的标签索引
        """
        # 移除标签页
        widget = self._tab_widget.widget(index)
        self._tab_widget.removeTab(index)
        
        # 释放控件资源
        if widget is not None:
            widget.deleteLater()
    
    def add_tab(self, widget, title, icon=None, closable=False):
        """
        添加标签页
        
        Args:
            widget: 标签页内容控件
            title: 标签文本
            icon: 图标（QIcon对象或图标路径）
            closable: 是否可关闭
        
        Returns:
            int: 新标签页索引
        """
        # 设置是否显示关闭按钮
        self._tab_widget.setTabsClosable(closable)
        
        # 添加标签页
        if icon is not None:
            return self._tab_widget.add_tab_with_icon(widget, icon, title)
        else:
            return self._tab_widget.addTab(widget, title)
    
    def get_tab_widget(self):
        """
        获取内部标签页控件
        
        Returns:
            ModernTabWidget: 标签页控件
        """
        return self._tab_widget
