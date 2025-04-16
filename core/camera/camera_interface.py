"""
相机接口模块

定义了相机的通用接口，所有具体相机实现都应该实现这个接口。
使用适配器模式，提供统一的相机操作接口。
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

class CameraInterface(ABC):
    """
    相机接口抽象类
    
    定义了相机操作的标准接口，所有具体相机实现都应实现这个接口。
    """
    
    @abstractmethod
    def enumerate_devices(self) -> List[Dict[str, Any]]:
        """
        枚举可用的相机设备
        
        Returns:
            可用相机设备列表，每个设备为一个字典，包含设备信息
        """
        pass
    
    @abstractmethod
    def open(self, device_id: str = "") -> bool:
        """
        打开相机
        
        Args:
            device_id: 相机ID，为空时打开第一个可用相机
            
        Returns:
            是否成功打开相机
        """
        pass
    
    @abstractmethod
    def close(self) -> bool:
        """
        关闭相机
        
        Returns:
            是否成功关闭相机
        """
        pass
    
    @abstractmethod
    def is_open(self) -> bool:
        """
        检查相机是否已打开
        
        Returns:
            相机是否已打开
        """
        pass
    
    @abstractmethod
    def start_grabbing(self) -> bool:
        """
        开始采集图像
        
        Returns:
            是否成功开始采集
        """
        pass
    
    @abstractmethod
    def stop_grabbing(self) -> bool:
        """
        停止采集图像
        
        Returns:
            是否成功停止采集
        """
        pass
    
    @abstractmethod
    def get_frame(self, timeout: int = 1000) -> Optional[np.ndarray]:
        """
        获取一帧图像
        
        Args:
            timeout: 超时时间(毫秒)
            
        Returns:
            图像数据，获取失败时返回None
        """
        pass
    
    @abstractmethod
    def trigger_once(self) -> bool:
        """
        触发一次采集
        
        Returns:
            是否成功触发
        """
        pass
    
    @abstractmethod
    def set_trigger_mode(self, enabled: bool) -> bool:
        """
        设置触发模式
        
        Args:
            enabled: 是否启用触发模式
            
        Returns:
            是否成功设置
        """
        pass
    
    @abstractmethod
    def set_exposure(self, exposure_time: float) -> bool:
        """
        设置曝光时间
        
        Args:
            exposure_time: 曝光时间(微秒)
            
        Returns:
            是否成功设置
        """
        pass
    
    @abstractmethod
    def get_exposure(self) -> float:
        """
        获取曝光时间
        
        Returns:
            曝光时间(微秒)
        """
        pass
    
    @abstractmethod
    def set_gain(self, gain: float) -> bool:
        """
        设置增益
        
        Args:
            gain: 增益值
            
        Returns:
            是否成功设置
        """
        pass
    
    @abstractmethod
    def get_gain(self) -> float:
        """
        获取增益
        
        Returns:
            增益值
        """
        pass
    
    @abstractmethod
    def set_roi(self, x: int, y: int, width: int, height: int) -> bool:
        """
        设置感兴趣区域(ROI)
        
        Args:
            x: 左上角x坐标
            y: 左上角y坐标
            width: 宽度
            height: 高度
            
        Returns:
            是否成功设置
        """
        pass
    
    @abstractmethod
    def get_roi(self) -> Tuple[int, int, int, int]:
        """
        获取感兴趣区域(ROI)
        
        Returns:
            (x, y, width, height)
        """
        pass
    
    @abstractmethod
    def reset_roi(self) -> bool:
        """
        重置感兴趣区域(ROI)到最大尺寸
        
        Returns:
            是否成功重置
        """
        pass
    
    @abstractmethod
    def get_device_info(self) -> Dict[str, Any]:
        """
        获取设备信息
        
        Returns:
            设备信息字典
        """
        pass
