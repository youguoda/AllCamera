"""
基础模型类
所有模型的基类，提供基本功能和接口
"""
from PyQt5.QtCore import QObject, pyqtSignal


class BaseModel(QObject):
    """
    基础模型类
    提供基本的数据管理和信号功能
    """
    
    # 状态变化信号
    status_changed = pyqtSignal(dict)
    
    # 错误信号
    error_signal = pyqtSignal(str)
    
    def __init__(self):
        """初始化基础模型"""
        super().__init__()
    
    def get_status(self):
        """
        获取模型状态
        
        Returns:
            dict: 模型状态
        """
        return {}
