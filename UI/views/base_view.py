"""
基础视图类
所有视图的基类，提供基本功能和接口
"""
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal


class BaseView(QWidget):
    """
    基础视图类
    提供UI组件和用户交互的基础
    """
    
    # 通用事件信号
    event_signal = pyqtSignal(str, dict)
    
    def __init__(self, parent=None):
        """
        初始化基础视图
        
        Args:
            parent: 父级窗口部件
        """
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI组件"""
        pass
    
    def update_ui(self, data):
        """
        更新UI显示
        
        Args:
            data: 更新数据
        """
        pass
