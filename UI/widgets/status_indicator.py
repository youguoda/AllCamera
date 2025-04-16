"""
状态指示器控件
------------
用于显示连接状态、运行状态等，具有不同颜色指示不同状态
"""

from PyQt5.QtCore import Qt, QSize, pyqtProperty
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel

from gui001.ui.utils.ui_constants import LIGHT_COLORS


class StatusIndicator(QWidget):
    """
    状态指示器控件
    显示一个带有颜色指示的LED灯和文本标签
    """
    
    # 预定义状态颜色
    STATUS_COLORS = {
        "connected": QColor(LIGHT_COLORS["SUCCESS"]),        # 绿色 - 已连接
        "disconnected": QColor(LIGHT_COLORS["DANGER"]),      # 红色 - 未连接
        "running": QColor(LIGHT_COLORS["SUCCESS"]),          # 绿色 - 运行中
        "stopped": QColor(LIGHT_COLORS["DANGER"]),           # 红色 - 已停止
        "warning": QColor(LIGHT_COLORS["WARNING"]),          # 黄色 - 警告
        "error": QColor(LIGHT_COLORS["DANGER"]),             # 红色 - 错误
        "ready": QColor(LIGHT_COLORS["SUCCESS"]),            # 绿色 - 就绪
        "busy": QColor(LIGHT_COLORS["WARNING"]),             # 黄色 - 忙碌
        "idle": QColor(LIGHT_COLORS["INFO"]),                # 蓝色 - 空闲
    }
    
    def __init__(self, parent=None, size=16, status="disconnected", text=""):
        """
        初始化状态指示器
        
        Args:
            parent: 父控件
            size: 指示灯大小 (像素)
            status: 初始状态 ("connected", "disconnected", "running", "stopped", "warning", "error", "ready", "busy", "idle")
            text: 显示文本
        """
        super().__init__(parent)
        
        self._indicator_size = size
        self._status = status
        self._text = text
        self._color = self.STATUS_COLORS.get(status, QColor(LIGHT_COLORS["DANGER"]))
        self._blinking = False
        self._blink_state = True
        
        # 设置布局
        self._layout = QHBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(5)
        
        # 文本标签
        if text:
            self._label = QLabel(text)
            # 根据状态设置文本颜色
            if status == "connected" or status == "running" or status == "ready":
                self._label.setStyleSheet(f"color: {LIGHT_COLORS['SUCCESS']};")
            elif status == "disconnected" or status == "stopped" or status == "error":
                self._label.setStyleSheet(f"color: {LIGHT_COLORS['DANGER']};")
            elif status == "warning" or status == "busy":
                self._label.setStyleSheet(f"color: {LIGHT_COLORS['WARNING']};")
            else:
                self._label.setStyleSheet(f"color: {LIGHT_COLORS['INFO']};")
                
            self._layout.addWidget(self._label)
        else:
            self._label = None
            
        self.setLayout(self._layout)
        
        # 设置尺寸策略
        self.setMinimumSize(self._indicator_size + 10, self._indicator_size)
        
    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 计算指示灯位置
        x = 0
        y = (self.height() - self._indicator_size) // 2
        
        # 绘制圆形指示灯
        color = self._color if not self._blinking or self._blink_state else QColor(LIGHT_COLORS["BACKGROUND"])
        
        # 绘制边框
        painter.setPen(QPen(QColor(LIGHT_COLORS["BORDER"]), 1))
        painter.setBrush(QBrush(color))
        painter.drawEllipse(x, y, self._indicator_size, self._indicator_size)
        
        # 绘制高光效果
        highlight_size = self._indicator_size * 0.5
        highlight_x = x + self._indicator_size * 0.2
        highlight_y = y + self._indicator_size * 0.2
        
        highlight_color = QColor(255, 255, 255, 80)  # 半透明白色
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(highlight_color))
        painter.drawEllipse(highlight_x, highlight_y, highlight_size, highlight_size)
    
    def sizeHint(self):
        """推荐尺寸"""
        width = self._indicator_size
        if self._label:
            width += self._label.sizeHint().width() + 5
        return QSize(width, self._indicator_size)
    
    def update_status(self, status, text=None):
        """
        更新状态和文本
        
        Args:
            status: 新状态
            text: 新显示文本，如果为None则保持不变
        """
        self._status = status
        self._color = self.STATUS_COLORS.get(status, QColor(LIGHT_COLORS["DANGER"]))
        
        if text is not None:
            self._text = text
            if self._label:
                self._label.setText(text)
                
                # 根据状态设置文本颜色
                if status == "connected" or status == "running" or status == "ready":
                    self._label.setStyleSheet(f"color: {LIGHT_COLORS['SUCCESS']};")
                elif status == "disconnected" or status == "stopped" or status == "error":
                    self._label.setStyleSheet(f"color: {LIGHT_COLORS['DANGER']};")
                elif status == "warning" or status == "busy":
                    self._label.setStyleSheet(f"color: {LIGHT_COLORS['WARNING']};")
                else:
                    self._label.setStyleSheet(f"color: {LIGHT_COLORS['INFO']};")
        
        self.update()
    
    def set_blinking(self, blinking):
        """
        设置是否闪烁
        
        Args:
            blinking: 是否闪烁
        """
        self._blinking = blinking
        self.update()
    
    def toggle_blink(self):
        """切换闪烁状态"""
        if self._blinking:
            self._blink_state = not self._blink_state
            self.update()
            
    # 属性定义 - 用于QSS样式表
    @pyqtProperty(QColor)
    def color(self):
        """获取指示灯颜色"""
        return self._color
        
    @color.setter
    def color(self, color):
        """设置指示灯颜色"""
        self._color = color
        self.update()
        
    @pyqtProperty(int)
    def indicator_size(self):
        """获取指示灯大小"""
        return self._indicator_size
        
    @indicator_size.setter
    def indicator_size(self, size):
        """设置指示灯大小"""
        self._indicator_size = size
        self.update()
        
    @pyqtProperty(str)
    def status(self):
        """获取状态"""
        return self._status
        
    def set_status(self, status):
        """
        设置状态指示器状态
        
        Args:
            status: 状态字符串 ("connected"/"disconnected"/"error")
        """
        color_map = {
            # 修复颜色值类型：字符串 -> QColor
            "connected": QColor(LIGHT_COLORS["SUCCESS"]),
            "disconnected": QColor(LIGHT_COLORS["DISABLED"]),
            "error": QColor(LIGHT_COLORS["DANGER"])
        }
        self._color = color_map.get(status, QColor(LIGHT_COLORS["DISABLED"]))
        self.update()