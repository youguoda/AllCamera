"""
基础控制器类
所有控制器的基类，提供基本功能和接口
"""
from PyQt5.QtCore import QObject


class BaseController(QObject):
    """
    基础控制器类
    负责管理模型和视图之间的交互
    """
    
    def __init__(self):
        """初始化基础控制器"""
        super().__init__()
