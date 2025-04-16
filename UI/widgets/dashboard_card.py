"""
仪表盘卡片控件
-----------
用于在仪表盘上显示数据统计、状态信息等
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPainter, QIcon, QPixmap
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QFrame

from UI.utils.ui_constants import LIGHT_COLORS, SPACING, FONTS


class DashboardCard(QFrame):
    """
    仪表盘卡片
    用于显示统计数据、状态信息等
    """
    
    def __init__(self, title, value="", icon=None, subtitle="", 
                 color=LIGHT_COLORS["PRIMARY"], parent=None):
        """
        初始化仪表盘卡片
        
        Args:
            title: 卡片标题
            value: 显示的数值或状态
            icon: 图标路径或QIcon对象
            subtitle: 子标题或描述文本
            color: 卡片主色调（边框和标题颜色）
            parent: 父控件
        """
        super().__init__(parent)
        
        self._title = title
        self._value = value
        self._icon = icon
        self._subtitle = subtitle
        self._color = color
        
        # 设置卡片样式
        self.setObjectName("dashboard_card")
        self.setStyleSheet(f"""
            #dashboard_card {{
                background-color: {LIGHT_COLORS["SURFACE"]};
                border: 1px solid {self._color};
                border-radius: 6px;
            }}
        """)
        
        # 创建布局
        self._main_layout = QVBoxLayout()
        self._main_layout.setContentsMargins(SPACING["MEDIUM"], SPACING["MEDIUM"], 
                                           SPACING["MEDIUM"], SPACING["MEDIUM"])
        self._main_layout.setSpacing(SPACING["SMALL"])
        
        # 标题区域
        self._header_layout = QHBoxLayout()
        self._header_layout.setContentsMargins(0, 0, 0, 0)
        self._header_layout.setSpacing(SPACING["SMALL"])
        
        # 标题标签
        self._title_label = QLabel(title)
        self._title_label.setObjectName("card_title")
        self._title_label.setStyleSheet(f"""
            #card_title {{
                color: {self._color};
                font-size: {FONTS["SIZE_NORMAL"]}px;
                font-weight: bold;
            }}
        """)
        
        # 添加图标（如果提供）
        if icon:
            self._icon_label = QLabel()
            self._icon_label.setFixedSize(24, 24)
            self._icon_label.setObjectName("card_icon")
            
            # 处理颜色值或图标
            if isinstance(icon, str) and icon.startswith("#"):
                # 创建颜色圆形图标
                pixmap = QPixmap(24, 24)
                pixmap.fill(Qt.transparent)
                painter = QPainter(pixmap)
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setBrush(QColor(icon))
                painter.drawEllipse(2, 2, 20, 20)
                painter.end()
                self._icon_label.setPixmap(pixmap)
            elif isinstance(icon, QIcon):
                self._icon_label.setPixmap(icon.pixmap(24, 24))
            else:
                self._icon_label.setPixmap(QIcon(icon).pixmap(24, 24))
            self._header_layout.addWidget(self._icon_label)
            
        self._header_layout.addWidget(self._title_label)
        self._header_layout.addStretch()
    
        # 数值区域
        self._value_label = QLabel(str(value))
        self._value_label.setObjectName("card_value")
        self._value_label.setAlignment(Qt.AlignCenter)
        self._value_label.setStyleSheet(f"""
            #card_value {{
                font-size: {FONTS["SIZE_TITLE"]}px;
                font-weight: bold;
                color: {LIGHT_COLORS["TEXT_PRIMARY"]};
            }}
        """)
        
        # 子标题/描述
        if subtitle:
            self._subtitle_label = QLabel(subtitle)
            self._subtitle_label.setObjectName("card_subtitle")
            self._subtitle_label.setAlignment(Qt.AlignCenter)
            self._subtitle_label.setStyleSheet(f"""
                #card_subtitle {{
                    color: {LIGHT_COLORS["TEXT_SECONDARY"]};
                    font-size: {FONTS["SIZE_SMALL"]}px;
                }}
            """)
        else:
            self._subtitle_label = None
        
        # 组装布局
        self._main_layout.addLayout(self._header_layout)
        self._main_layout.addWidget(self._value_label)
        if self._subtitle_label:
            self._main_layout.addWidget(self._subtitle_label)
            
            self.setLayout(self._main_layout)
            
            # 设置尺寸策略
            self.setMinimumSize(120, 100)
            
    def set_value(self, value, color=None):
        """
        更新卡片数值
        
        Args:
            value: 新数值
            color: 数值颜色（可选）
        """
        self._value = value
        self._value_label.setText(str(value))
        
        if color:
            self._value_label.setStyleSheet(f"""
                #card_value {{
                    font-size: {FONTS["SIZE_TITLE"]}px;
                    font-weight: bold;
                    color: {color};
                }}
            """)
    
    def update_subtitle(self, subtitle):
        """
        更新子标题文本
        
        Args:
            subtitle: 新子标题
        """
        self._subtitle = subtitle
        
        if self._subtitle_label:
            self._subtitle_label.setText(subtitle)
        else:
            # 如果之前没有子标题，则创建
            self._subtitle_label = QLabel(subtitle)
            self._subtitle_label.setObjectName("card_subtitle")
            self._subtitle_label.setAlignment(Qt.AlignCenter)
            self._subtitle_label.setStyleSheet(f"""
                #card_subtitle {{
                    color: {LIGHT_COLORS["TEXT_SECONDARY"]};
                    font-size: {FONTS["SIZE_SMALL"]}px;
                }}
            """)
            self._main_layout.addWidget(self._subtitle_label)
        
    def set_color(self, color):
        """
        设置卡片主色调
        
        Args:
            color: 新颜色
        """
        self._color = color
        
        # 更新卡片样式
        self.setStyleSheet(f"""
            #dashboard_card {{
                background-color: {LIGHT_COLORS["SURFACE"]};
                border: 1px solid {self._color};
                border-radius: 6px;
            }}
        """)
        
        # 更新标题颜色
        self._title_label.setStyleSheet(f"""
            #card_title {{
                color: {self._color};
                font-size: {FONTS["SIZE_NORMAL"]}px;
                font-weight: bold;
            }}
            """)


class CounterCard(DashboardCard):
    """
    计数器卡片
    用于显示计数器数据（如良品数、不良品数等）
    """
    
    def __init__(self, title, count=0, icon=None, subtitle="", 
                color=LIGHT_COLORS["PRIMARY"], parent=None):
        """
        初始化计数器卡片
        
        Args:
            title: 卡片标题
            count: 计数值
            icon: 图标路径或QIcon对象
            subtitle: 子标题或描述文本
            color: 卡片主色调
            parent: 父控件
        """
        super().__init__(title, str(count), icon, subtitle, color, parent)
        self._count = count
    
    def increment(self, color=None):
        """增加计数"""
        self._count += 1
        self.set_value(str(self._count), color)
        
    def decrement(self, color=None):
        """减少计数"""
        self._count = max(0, self._count - 1)  # 确保不小于0
        self.set_value(str(self._count), color)
        
    def reset(self):
        """重置计数器"""
        self._count = 0
        self.set_value(str(self._count))
        
    def set_count(self, count, color=None):
        """
        设置计数值
        
        Args:
            count: 新计数值
            color: 数值颜色（可选）
        """
        self._count = max(0, count)  # 确保不小于0
        self.set_value(str(self._count), color)


class StatusCard(DashboardCard):
    """
    状态卡片
    用于显示设备或组件状态
    """
    
    STATUS_COLORS = {
        "connected": LIGHT_COLORS["SUCCESS"],
        "disconnected": LIGHT_COLORS["DANGER"],
        "running": LIGHT_COLORS["SUCCESS"],
        "stopped": LIGHT_COLORS["DANGER"],
        "warning": LIGHT_COLORS["WARNING"],
        "error": LIGHT_COLORS["DANGER"],
        "ready": LIGHT_COLORS["SUCCESS"],
        "busy": LIGHT_COLORS["WARNING"],
        "idle": LIGHT_COLORS["INFO"],
    }
    
    def __init__(self, title, status="disconnected", icon=None, subtitle="", parent=None):
        """
        初始化状态卡片
        
        Args:
            title: 卡片标题
            status: 状态值
            icon: 图标路径或QIcon对象
            subtitle: 子标题或描述文本
            parent: 父控件
        """
        # 获取状态对应的颜色
        color = self.STATUS_COLORS.get(status, LIGHT_COLORS["DANGER"])
        
        # 状态文本映射
        status_text_map = {
            "connected": "已连接",
            "disconnected": "未连接",
            "running": "运行中",
            "stopped": "已停止",
            "warning": "警告",
            "error": "错误",
            "ready": "就绪",
            "busy": "忙碌",
            "idle": "空闲",
        }
        
        status_text = status_text_map.get(status, status)
        
        super().__init__(title, status_text, icon, subtitle, color, parent)
        self._status = status
    
    def set_status(self, status, subtitle=None):
        """
        设置状态
        
        Args:
            status: 新状态
            subtitle: 新子标题（可选）
        """
        self._status = status
        
        # 获取状态对应的颜色
        color = self.STATUS_COLORS.get(status, LIGHT_COLORS["DANGER"])
        
        # 状态文本映射
        status_text_map = {
            "connected": "已连接",
            "disconnected": "未连接",
            "running": "运行中",
            "stopped": "已停止",
            "warning": "警告",
            "error": "错误",
            "ready": "就绪",
            "busy": "忙碌",
            "idle": "空闲",
        }
        
        status_text = status_text_map.get(status, status)
        
        # 更新卡片
        self.set_value(status_text, color)
        self.set_color(color)
        
        if subtitle:
            self.update_subtitle(subtitle)
    # In DashboardCard class
    def set_value(self, value, color=None):
        """
        更新卡片数值

        Args:
            value: 新数值
            color: 数值颜色（可选）
        """
        self._value = value
        self._value_label.setText(str(value))

        if color:
            self._value_label.setStyleSheet(f"""
                #card_value {{
                    font-size: {FONTS["SIZE_TITLE"]}px;
                    font-weight: bold;
                    color: {color};
                }}
            """)