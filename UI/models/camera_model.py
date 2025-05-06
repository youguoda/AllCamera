"""
相机模型类
管理相机设备的连接和数据交互
"""
from typing import Dict, List, Any, Optional, Tuple
import threading
import time
import numpy as np

from PyQt5.QtCore import pyqtSignal, QMutex, QMutexLocker, QTimer, QObject

from UI.models.base_model import BaseModel
from core.camera.camera_factory import CameraFactoryManager
from core.camera.camera_interface import CameraInterface
from core.camera.hikvision_camera_factory import HikvisionCameraFactory
from core.utils.logger import get_logger


class CameraModel(BaseModel):
    """
    相机模型类
    管理相机设备的连接、参数设置和图像获取
    """
    
    # 自定义信号
    connection_status_changed = pyqtSignal(bool)   # 连接状态
    streaming_status_changed = pyqtSignal(bool)    # 流式传输状态
    new_frame_available = pyqtSignal(np.ndarray)   # 新帧
    parameter_changed = pyqtSignal(str, object)    # 参数
    camera_list_changed = pyqtSignal(list)         # 相机列表
    fps_updated = pyqtSignal(float)                # FPS更新
    
    def __init__(self):
        """初始化相机模型"""
        super().__init__()
        self.logger = get_logger()
        
        # 相机实例
        self._camera = None
        self._camera_mutex = QMutex()   # 相机访问锁
        
        # 相机状态
        self._is_connected = False   # 连接状态
        self._is_streaming = False   # 流式传输状态
        self._current_device_id = ""  # 当前设备ID
        self._available_devices = []  # 可用设备列表
        
        # 图像数据
        self._frame_lock = QMutex()   # 图像访问锁  
        self._current_frame = None    # 当前帧
        self._roi = (0, 0, 0, 0)  # x, y, width, height
        
        # FPS计算
        self._fps_count = 0    # FPS计数
        self._last_fps_time = time.time()  # 上次FPS计算时间
        self._current_fps = 0.0  # 当前FPS
        self._fps_timer = QTimer()      # FPS更新定时器
        self._fps_timer.timeout.connect(self._update_fps)           # FPS更新定时器连接
        self._fps_timer.start(1000)  # 每秒更新一次FPS
        
        # 相机参数
        self._parameters = {
            "exposure": 0.0,
            "gain": 0.0,
            "trigger_mode": False,
            "white_balance": 50,  # 添加白平衡默认值 (假设范围0-100)
            "auto_exposure": False, # 添加自动曝光默认值
            "auto_gain": False,     # 添加自动增益默认值
            "auto_wb": False        # 添加自动白平衡默认值
        }
        
        # 帧获取线程
        self._streaming_thread = None
        self._streaming_active = False
        self._thread_lock = QMutex()
        
        # 相机初始化
        self._is_simulation = False  # 是否使用模拟模式
        QTimer.singleShot(100, self.initialize_camera)  # 延迟初始化相机
    
    def initialize_camera(self):
        """初始化相机"""
        try:
            # 获取可用相机类型
            available_types = CameraFactoryManager.get_available_types()
            if "hikvision" not in available_types:
                self.error_signal.emit("未找到海康威视相机工厂类，请确保已注册")
                return False
                
            # 创建相机实例
            self._camera = CameraFactoryManager.create_camera("hikvision")
            if self._camera is None:
                self.error_signal.emit("创建相机实例失败")
                return False
                
            # 设置模拟模式
            self._camera._is_simulation = self._is_simulation
                
            self.logger.info("相机实例创建成功")
            self.enumerate_devices()
            return True
        except Exception as e:
            self.logger.error(f"初始化相机失败: {str(e)}")
            self.error_signal.emit(f"初始化相机失败: {str(e)}")
            return False
    
    def enumerate_devices(self) -> List[Dict[str, Any]]:
        """
        枚举可用的相机设备
        
        Returns:
            List[Dict[str, Any]]: 可用相机设备列表
        """
        self.logger.info("枚举相机设备")
        factory_manager = CameraFactoryManager()
        # 使用默认相机类型，通常是 "MvCamera" 或项目中定义的其他类型
        camera_type = "hikvision"  # 可以根据项目实际情况修改
        camera = factory_manager.create_camera(camera_type)
        
        if camera:
            try:
                devices = camera.enumerate_devices()
                self._available_devices = devices
                self.camera_list_changed.emit(devices)
                return devices
            except Exception as e:
                self.logger.error(f"枚举相机设备失败: {str(e)}")
                self.error_signal.emit(f"枚举相机设备失败: {str(e)}")
                return []
        else:
            self.logger.error(f"创建相机实例失败: 相机类型 '{camera_type}' 不存在")
            self.error_signal.emit(f"创建相机实例失败: 相机类型 '{camera_type}' 不存在")
            return []
    
    def set_simulation_mode(self, enabled: bool):
        """设置模拟模式"""
        self._is_simulation = enabled
        self.logger.info(f"模拟模式设置为: {enabled}")
        # 如果相机已连接，可能需要重新初始化或应用设置
        if self._camera:
            self._camera._is_simulation = enabled
            # 如果需要，可以在这里添加重新连接或更新设备列表的逻辑
            # self.disconnect_camera()
            # self.initialize_camera()
            # self.enumerate_devices()
    
    def connect_camera(self, device_id: str = "") -> bool:
        """
        连接相机
        
        Args:
            device_id: 相机设备ID
            
        Returns:
            bool: 是否成功连接
        """
        with QMutexLocker(self._camera_mutex):
            # 如果已连接，先断开
            if self._is_connected:
                self.disconnect_camera()
            
            # 创建相机实例
            factory_manager = CameraFactoryManager()
            # 使用默认相机类型，与 enumerate_devices 保持一致
            camera_type = "hikvision"  # 可以根据项目实际情况修改
            self._camera = factory_manager.create_camera(camera_type)
            
            if not self._camera:
                self.logger.error(f"创建相机实例失败: 相机类型 '{camera_type}' 不存在")
                self.error_signal.emit(f"创建相机实例失败: 相机类型 '{camera_type}' 不存在")
                return False
            
            # 连接相机
            try:
                result = self._camera.open(device_id)
                if result:
                    self._is_connected = True
                    self._current_device_id = device_id
                    
                    # 读取相机当前参数
                    self._parameters["exposure"] = self._camera.get_exposure()
                    self._parameters["gain"] = self._camera.get_gain()
                    # 读取其他新增参数的初始值 (如果相机支持)
                    # try:
                    #     self._parameters["white_balance"] = self._camera.get_white_balance() # 假设有get_white_balance方法
                    #     self._parameters["auto_exposure"] = self._camera.get_auto_exposure() # 假设有get_auto_exposure方法
                    #     self._parameters["auto_gain"] = self._camera.get_auto_gain()       # 假设有get_auto_gain方法
                    #     self._parameters["auto_wb"] = self._camera.get_auto_wb()           # 假设有get_auto_wb方法
                    # except AttributeError:
                    #     self.logger.warning("相机不支持读取部分新增参数的初始值")
                    
                    # 发送信号
                    self.connection_status_changed.emit(True)
                    self.status_changed.emit(self.get_status())
                    
                    self.logger.info(f"相机连接成功: {device_id}")
                    return True
                else:
                    self.logger.error(f"相机连接失败: {device_id}")
                    self.error_signal.emit(f"相机连接失败: {device_id}")
                    return False
            except Exception as e:
                self.logger.error(f"相机连接异常: {str(e)}")
                self.error_signal.emit(f"相机连接异常: {str(e)}")
                return False
    
    def disconnect_camera(self) -> bool:
        """
        断开相机连接
        
        Returns:
            bool: 是否成功断开
        """
        with QMutexLocker(self._camera_mutex):
            if not self._is_connected or not self._camera:
                return True
            
            # 如果正在流式传输，先停止
            if self._is_streaming:
                self.stop_streaming()
            
            # 断开相机
            try:
                result = self._camera.close()
                if result:
                    self._is_connected = False
                    self._camera = None
                    
                    # 发送信号
                    self.connection_status_changed.emit(False)
                    self.status_changed.emit(self.get_status())
                    
                    self.logger.info("相机断开连接")
                    return True
                else:
                    self.logger.error("相机断开连接失败")
                    self.error_signal.emit("相机断开连接失败")
                    return False
            except Exception as e:
                self.logger.error(f"相机断开连接异常: {str(e)}")
                self.error_signal.emit(f"相机断开连接异常: {str(e)}")
                return False
    
    def start_streaming(self) -> bool:
        """
        开始图像流
        
        Returns:
            bool: 是否成功开始流式传输
        """
        with QMutexLocker(self._thread_lock):
            if not self._is_connected or not self._camera:
                self.logger.error("相机未连接，无法开始图像流")
                self.error_signal.emit("相机未连接，无法开始图像流")
                return False
            
            if self._is_streaming:
                return True
            
            try:
                # 关闭触发模式，以便连续采集
                if self._parameters["trigger_mode"]:
                    self._camera.set_trigger_mode(False)
                    self._parameters["trigger_mode"] = False
                    self.parameter_changed.emit("trigger_mode", False)
                
                # 开始采集
                result = self._camera.start_grabbing()
                if result:
                    self._is_streaming = True
                    self._streaming_active = True
                    
                    # 创建并启动帧获取线程
                    self._streaming_thread = threading.Thread(
                        target=self._frame_grabbing_thread,
                        daemon=True
                    )
                    self._streaming_thread.start()
                    
                    # 发送信号
                    self.streaming_status_changed.emit(True)
                    self.status_changed.emit(self.get_status())
                    
                    self.logger.info("相机开始图像流")
                    return True
                else:
                    self.logger.error("相机开始图像流失败")
                    self.error_signal.emit("相机开始图像流失败")
                    return False
            except Exception as e:
                self.logger.error(f"相机开始图像流异常: {str(e)}")
                self.error_signal.emit(f"相机开始图像流异常: {str(e)}")
                return False
    
    def stop_streaming(self) -> bool:
        """
        停止图像流
        
        Returns:
            bool: 是否成功停止流式传输
        """
        with QMutexLocker(self._thread_lock):
            if not self._is_streaming:
                return True
            
            # 停止帧获取线程
            self._streaming_active = False
            
            # 等待线程结束
            if self._streaming_thread and self._streaming_thread.is_alive():
                self._streaming_thread.join(timeout=1.0)
                self._streaming_thread = None
            
            try:
                # 停止相机采集
                if self._camera:
                    result = self._camera.stop_grabbing()
                    if result:
                        self._is_streaming = False
                        
                        # 发送信号
                        self.streaming_status_changed.emit(False)
                        self.status_changed.emit(self.get_status())
                        
                        self.logger.info("相机停止图像流")
                        return True
                    else:
                        self.logger.error("相机停止图像流失败")
                        self.error_signal.emit("相机停止图像流失败")
                        return False
                return True
            except Exception as e:
                self.logger.error(f"相机停止图像流异常: {str(e)}")
                self.error_signal.emit(f"相机停止图像流异常: {str(e)}")
                return False
    
    def _frame_grabbing_thread(self):
        """帧获取线程"""
        self.logger.info("帧获取线程启动")
        
        while self._streaming_active:
            try:
                if not self._camera:
                    break
                
                # 获取帧
                frame = self._camera.get_frame(timeout=1000)
                if frame is not None:
                    # 更新当前帧
                    with QMutexLocker(self._frame_lock):
                        self._current_frame = frame.copy()
                    
                    # 更新FPS计数
                    self._fps_count += 1
                    
                    # 发送信号
                    self.new_frame_available.emit(frame)
            except Exception as e:
                self.logger.error(f"帧获取异常: {str(e)}")
                time.sleep(0.1)  # 避免线程过快循环
        
        self.logger.info("帧获取线程结束")
    
    def _update_fps(self):
        """更新FPS"""
        current_time = time.time()
        elapsed = current_time - self._last_fps_time
        
        if elapsed > 0:
            self._current_fps = self._fps_count / elapsed
            self.fps_updated.emit(self._current_fps)
        
        self._fps_count = 0
        self._last_fps_time = current_time
    
    def get_current_frame(self) -> Optional[np.ndarray]:
        """
        获取当前帧
        
        Returns:
            Optional[np.ndarray]: 当前帧图像
        """
        with QMutexLocker(self._frame_lock):
            if self._current_frame is not None:
                return self._current_frame.copy()
            return None
    
    def trigger_once(self) -> bool:
        """
        触发一次采集
        
        Returns:
            bool: 是否成功触发
        """
        with QMutexLocker(self._camera_mutex):
            if not self._is_connected or not self._camera:
                self.logger.error("相机未连接，无法触发采集")
                self.error_signal.emit("相机未连接，无法触发采集")
                return False
            
            try:
                # 确保相机在触发模式下
                if not self._parameters["trigger_mode"]:
                    self._camera.set_trigger_mode(True)
                    self._parameters["trigger_mode"] = True
                    self.parameter_changed.emit("trigger_mode", True)
                
                # 执行触发
                result = self._camera.trigger_once()
                if result:
                    self.logger.info("相机触发采集成功")
                    return True
                else:
                    self.logger.error("相机触发采集失败")
                    self.error_signal.emit("相机触发采集失败")
                    return False
            except Exception as e:
                self.logger.error(f"相机触发采集异常: {str(e)}")
                self.error_signal.emit(f"相机触发采集异常: {str(e)}")
                return False
    
    def set_parameter(self, param_name: str, value: Any) -> bool:
        """
        设置相机参数
        
        Args:
            param_name: 参数名称
            value: 参数值
            
        Returns:
            bool: 是否成功设置
        """
        with QMutexLocker(self._camera_mutex):
            if not self._is_connected or not self._camera:
                self.logger.error(f"相机未连接，无法设置参数: {param_name}")
                self.error_signal.emit(f"相机未连接，无法设置参数: {param_name}")
                return False
            
            try:
                result = False
                
                if param_name == "exposure":
                    result = self._camera.set_exposure(float(value))
                elif param_name == "gain":
                    result = self._camera.set_gain(float(value))
                elif param_name == "trigger_mode":
                    result = self._camera.set_trigger_mode(bool(value))
                else:
                    self.logger.warning(f"未知的相机参数: {param_name}")
                    return False
                
                if result:
                    # 更新参数缓存
                    self._parameters[param_name] = value
                    
                    # 发送信号
                    self.parameter_changed.emit(param_name, value)
                    self.logger.info(f"相机参数设置成功: {param_name}={value}")
                    return True
                else:
                    self.logger.error(f"相机参数设置失败: {param_name}={value}")
                    self.error_signal.emit(f"相机参数设置失败: {param_name}={value}")
                    return False
            except Exception as e:
                self.logger.error(f"相机参数设置异常: {param_name}={value}, 错误: {str(e)}")
                self.error_signal.emit(f"相机参数设置异常: {param_name}={value}, 错误: {str(e)}")
                return False
    
    def get_parameter(self, param_name: str) -> Any:
        """
        获取相机参数
        
        Args:
            param_name: 参数名称
            
        Returns:
            Any: 参数值
        """
        with QMutexLocker(self._camera_mutex):
            if not self._is_connected or not self._camera:
                return None
            
            try:
                if param_name == "exposure":
                    value = self._camera.get_exposure()
                    self._parameters[param_name] = value
                    return value
                elif param_name == "gain":
                    value = self._camera.get_gain()
                    self._parameters[param_name] = value
                    return value
                elif param_name == "trigger_mode":
                    return self._parameters[param_name]
                else:
                    self.logger.warning(f"未知的相机参数: {param_name}")
                    return None
            except Exception as e:
                self.logger.error(f"获取相机参数异常: {param_name}, 错误: {str(e)}")
                return None
    
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
        with QMutexLocker(self._camera_mutex):
            if not self._is_connected or not self._camera:
                self.logger.error("相机未连接，无法设置ROI")
                self.error_signal.emit("相机未连接，无法设置ROI")
                return False
            
            try:
                result = self._camera.set_roi(x, y, width, height)
                if result:
                    self._roi = (x, y, width, height)
                    self.parameter_changed.emit("roi", self._roi)
                    self.logger.info(f"相机ROI设置成功: x={x}, y={y}, width={width}, height={height}")
                    return True
                else:
                    self.logger.error(f"相机ROI设置失败: x={x}, y={y}, width={width}, height={height}")
                    self.error_signal.emit(f"相机ROI设置失败: x={x}, y={y}, width={width}, height={height}")
                    return False
            except Exception as e:
                self.logger.error(f"相机ROI设置异常: {str(e)}")
                self.error_signal.emit(f"相机ROI设置异常: {str(e)}")
                return False
    
    def reset_roi(self) -> bool:
        """
        重置ROI区域
        
        Returns:
            bool: 是否成功重置
        """
        with QMutexLocker(self._camera_mutex):
            if not self._is_connected or not self._camera:
                self.logger.error("相机未连接，无法重置ROI")
                self.error_signal.emit("相机未连接，无法重置ROI")
                return False
            
            try:
                result = self._camera.reset_roi()
                if result:
                    self._roi = self._camera.get_roi()
                    self.parameter_changed.emit("roi", self._roi)
                    self.logger.info("相机ROI重置成功")
                    return True
                else:
                    self.logger.error("相机ROI重置失败")
                    self.error_signal.emit("相机ROI重置失败")
                    return False
            except Exception as e:
                self.logger.error(f"相机ROI重置异常: {str(e)}")
                self.error_signal.emit(f"相机ROI重置异常: {str(e)}")
                return False
    
    def get_roi(self) -> Tuple[int, int, int, int]:
        """
        获取ROI区域
        
        Returns:
            Tuple[int, int, int, int]: (x, y, width, height)
        """
        with QMutexLocker(self._camera_mutex):
            if not self._is_connected or not self._camera:
                return (0, 0, 0, 0)
            
            try:
                self._roi = self._camera.get_roi()
                return self._roi
            except Exception as e:
                self.logger.error(f"获取相机ROI异常: {str(e)}")
                return (0, 0, 0, 0)
    
    def is_connected(self) -> bool:
        """
        检查相机是否已连接
        
        Returns:
            bool: 是否已连接
        """
        return self._is_connected
    
    def is_streaming(self) -> bool:
        """
        检查相机是否正在流式传输
        
        Returns:
            bool: 是否正在流式传输
        """
        return self._is_streaming
    
    def get_current_device_id(self) -> str:
        """
        获取当前相机设备ID
        
        Returns:
            str: 当前相机设备ID
        """
        return self._current_device_id
    
    def get_available_devices(self) -> List[Dict[str, Any]]:
        """
        获取可用的相机设备列表
        
        Returns:
            List[Dict[str, Any]]: 可用相机设备列表
        """
        return self._available_devices
    
    def get_device_info(self) -> Dict[str, Any]:
        """
        获取相机设备信息
        
        Returns:
            Dict[str, Any]: 相机设备信息
        """
        with QMutexLocker(self._camera_mutex):
            if not self._is_connected or not self._camera:
                return {}
            
            try:
                return self._camera.get_device_info()
            except Exception as e:
                self.logger.error(f"获取相机设备信息异常: {str(e)}")
                return {}
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取相机状态
        
        Returns:
            Dict[str, Any]: 相机状态信息
        """
        status = {
            "connected": self._is_connected,
            "streaming": self._is_streaming,
            "device_id": self._current_device_id,
            "parameters": self._parameters.copy(),
            "fps": self._current_fps,
            "roi": self._roi
        }
        
        # 如果相机已连接，获取设备信息
        if self._is_connected and self._camera:
            try:
                status["device_info"] = self._camera.get_device_info()
            except Exception:
                status["device_info"] = {}
        
        return status
