"""
相机控制器类
管理相机模型和视图之间的通信和交互
"""
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

from PyQt5.QtCore import pyqtSlot, QObject

from UI.controllers.base_controller import BaseController
from UI.models.camera_model import CameraModel
from UI.views.camera_view import CameraView # Import CameraView
from core.utils.logger import get_logger


class CameraController(BaseController):
    """
    相机控制器类
    处理与相机相关的业务逻辑和UI交互
    """
    
    def __init__(self, model: CameraModel):
        """
        初始化相机控制器
        
        Args:
            model: 相机模型实例
        """
        super().__init__()
        self.logger = get_logger()
        
        # 保存模型引用
        self._model = model
    
    def enumerate_devices(self) -> List[Dict[str, Any]]:
        """
        枚举可用的相机设备
        
        Returns:
            List[Dict[str, Any]]: 可用相机设备列表
        """
        self.logger.info("枚举相机设备")
        return self._model.enumerate_devices()
    
    @pyqtSlot(str, result=bool)
    def connect_camera(self, device_id: str = "") -> bool:
        """
        连接相机
        
        Args:
            device_id: 相机设备ID
            
        Returns:
            bool: 是否成功连接
        """
        self.logger.info(f"连接相机: {device_id}")
        return self._model.connect_camera(device_id)
    
    @pyqtSlot(result=bool)
    def disconnect_camera(self) -> bool:
        """
        断开相机连接
        
        Returns:
            bool: 是否成功断开
        """
        self.logger.info("断开相机连接")
        return self._model.disconnect_camera()
    
    @pyqtSlot(result=bool)
    def start_streaming(self) -> bool:
        """
        开始图像流
        
        Returns:
            bool: 是否成功开始流式传输
        """
        self.logger.info("开始相机图像流")
        return self._model.start_streaming()
    
    @pyqtSlot(result=bool)
    def stop_streaming(self) -> bool:
        """
        停止图像流
        
        Returns:
            bool: 是否成功停止流式传输
        """
        self.logger.info("停止相机图像流")
        return self._model.stop_streaming()
    
    @pyqtSlot(result=bool)
    def trigger_once(self) -> bool:
        """
        触发一次采集
        
        Returns:
            bool: 是否成功触发
        """
        self.logger.info("触发相机采集一次")
        return self._model.trigger_once()
    
    @pyqtSlot(str, object, result=bool)
    def set_parameter(self, param_name: str, value: Any) -> bool:
        """
        设置相机参数
        
        Args:
            param_name: 参数名称
            value: 参数值
            
        Returns:
            bool: 是否成功设置
        """
        self.logger.info(f"设置相机参数: {param_name}={value}")
        return self._model.set_parameter(param_name, value)
    
    @pyqtSlot(str, result=object)
    def get_parameter(self, param_name: str) -> Any:
        """
        获取相机参数
        
        Args:
            param_name: 参数名称
            
        Returns:
            Any: 参数值
        """
        return self._model.get_parameter(param_name)
    
    @pyqtSlot(int, int, int, int, result=bool)
    def set_roi(self, x: int, y: int, width: int, height: int) -> bool:
        """
        设置ROI区域
        
        Args:
            x: 左上角x坐标
            y: 左上角y坐标
            width: 宽度
            height: 高度
            
        Returns:
            bool: 是否成功设置
        """
        self.logger.info(f"设置相机ROI: x={x}, y={y}, width={width}, height={height}")
        return self._model.set_roi(x, y, width, height)
    
    @pyqtSlot(result=bool)
    def reset_roi(self) -> bool:
        """
        重置ROI区域
        
        Returns:
            bool: 是否成功重置
        """
        self.logger.info("重置相机ROI")
        return self._model.reset_roi()
    
    @pyqtSlot(result=tuple)
    def get_roi(self) -> Tuple[int, int, int, int]:
        """
        获取ROI区域
        
        Returns:
            Tuple[int, int, int, int]: (x, y, width, height)
        """
        return self._model.get_roi()
    
    @pyqtSlot(result=bool)
    def is_connected(self) -> bool:
        """
        检查相机是否已连接
        
        Returns:
            bool: 是否已连接
        """
        return self._model.is_connected()
    
    @pyqtSlot(result=bool)
    def is_streaming(self) -> bool:
        """
        检查相机是否正在流式传输
        
        Returns:
            bool: 是否正在流式传输
        """
        return self._model.is_streaming()
    
    @pyqtSlot(result=dict)
    def get_current_frame(self) -> Optional[np.ndarray]:
        """
        获取当前帧
        
        Returns:
            Optional[np.ndarray]: 当前帧图像
        """
        return self._model.get_current_frame()
    
    @pyqtSlot(result=str)
    def get_current_device_id(self) -> str:
        """
        获取当前连接的设备ID
        
        Returns:
            str: 当前相机设备ID
        """
        return self._model.get_current_device_id()
    
    @pyqtSlot(result=list)
    def get_available_devices(self) -> List[Dict[str, Any]]:
        """
        获取可用的相机设备列表
        
        Returns:
            List[Dict[str, Any]]: 可用相机设备列表
        """
        return self._model.get_available_devices()
    
    @pyqtSlot(result=dict)
    def get_device_info(self) -> Dict[str, Any]:
        """
        获取相机设备信息
        
        Returns:
            Dict[str, Any]: 相机设备信息
        """
        return self._model.get_device_info()
    
    @pyqtSlot(result=dict)
    def get_status(self) -> Dict[str, Any]:
        """
        获取相机状态
        
        Returns:
            Dict[str, Any]: 相机状态信息
        """
        return self._model.get_status()
    
    @pyqtSlot(bool)
    def set_simulation_mode(self, enabled: bool):
        """设置模拟模式"""
        self.logger.info(f"设置模拟模式: {enabled}")
        self._model.set_simulation_mode(enabled)
        # 切换模式后，重新枚举设备以反映变化（模拟或真实）
        self.enumerate_devices()
        # 可能需要断开并重新连接，或者根据具体逻辑处理
        # self.disconnect_camera()

    def setup_view_connections(self, view: CameraView):
        """
        设置视图和控制器之间的信号连接
        
        Args:
            view: 相机视图实例
        """
        self.logger.info("设置视图连接")
        
        # 连接视图信号到控制器槽
        view.connect_camera_signal.connect(self.connect_camera)
        view.disconnect_camera_signal.connect(self.disconnect_camera)
        view.start_streaming_signal.connect(self.start_streaming)
        view.stop_streaming_signal.connect(self.stop_streaming)
        view.trigger_once_signal.connect(self.trigger_once)
        view.set_parameter_signal.connect(self.set_parameter)
        view.set_roi_signal.connect(self.set_roi)
        view.reset_roi_signal.connect(self.reset_roi)
        view.simulation_mode_changed.connect(self.set_simulation_mode) # 连接模拟模式信号
        
        # 连接模型信号到视图槽
        self._model.connection_status_changed.connect(view.update_connection_status)
        self._model.streaming_status_changed.connect(view.update_streaming_status)
        self._model.new_frame_available.connect(view.update_frame)
        self._model.parameter_changed.connect(view.update_parameter)
        self._model.camera_list_changed.connect(view.update_camera_list)
        self._model.fps_updated.connect(view.update_fps)
        # self._model.error_signal.connect(view.show_error_message)
        self._model.status_changed.connect(view.update_status)

    def initialize(self):
        """初始化控制器"""
        self.logger.info("初始化相机控制器")
        # 可以在这里执行一些初始化逻辑，例如初始枚举设备
        # self.enumerate_devices()
        
        # 初始化视图状态
        view.update_status(self._model.get_status())
