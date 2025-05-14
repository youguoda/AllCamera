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
import core.camera.hikvision_camera_factory # 确保海康工厂被导入并注册
from core.utils.logger import get_logger


class CameraModel(BaseModel):
    """
    相机模型类
    管理相机设备的连接、参数设置和图像获取
    """

    # --- 信号定义 ---
    # 状态变化信号
    connection_status_changed = pyqtSignal(bool, str)  # is_connected, device_id (empty if disconnected)
    streaming_status_changed = pyqtSignal(bool)    # is_streaming
    camera_list_updated = pyqtSignal(list)         # available_devices_info (List[Dict[str, Any]])
    simulation_mode_status_changed = pyqtSignal(bool) # is_simulation_mode

    # 数据信号
    new_frame_available = pyqtSignal(np.ndarray, str)   # frame, camera_id
    fps_updated = pyqtSignal(float)                # current_fps

    # 参数变化信号
    parameters_updated = pyqtSignal(dict)          # all_current_parameters (Dict[str, Any])
    # single_parameter_updated = pyqtSignal(str, object) # param_name, value (use parameters_updated for consistency)

    # 错误/状态信息信号
    error_occurred = pyqtSignal(str, str)          # error_title, error_message
    status_message_updated = pyqtSignal(str)       # status_message

    def __init__(self):
        """初始化相机模型"""
        super().__init__()
        self.logger = get_logger()

        self._camera: Optional[CameraInterface] = None
        self._camera_mutex = QMutex()   # 保护对_camera实例的访问

        # 相机状态
        self._is_connected = False
        self._is_streaming = False
        self._current_device_id: Optional[str] = None
        self._available_devices_info: List[Dict[str, Any]] = []
        self._is_simulation_mode = False

        # 图像数据
        self._frame_lock = QMutex()
        self._current_frame: Optional[np.ndarray] = None

        # FPS计算
        self._fps_count = 0
        self._last_fps_time = time.time()
        self._current_fps = 0.0
        self._fps_timer = QTimer()
        self._fps_timer.timeout.connect(self._calculate_and_emit_fps)
        self._fps_timer.start(1000)

        self._parameters: Dict[str, Any] = {
            "exposure_time": 10000,
            "gain": 0.0,
            "white_balance_kelvin": 5000,
            "frame_rate": 30,
            "trigger_mode": 0, # 0: Continuous, 1: Software, 2: Hardware (as per camera_tab.py logic)
            "auto_exposure": False,
            "auto_gain": False,
            "auto_wb": False,
            "width": 0,
            "height": 0,
            "pixel_format": "",
            "roi_x": 0,
            "roi_y": 0,
            "roi_width": 0,
            "roi_height": 0,
        }

        self._streaming_thread: Optional[threading.Thread] = None
        self._streaming_active_flag = False
        self._thread_stop_event = threading.Event()

        QTimer.singleShot(100, self._initialize_camera_system)

    def _initialize_camera_system(self):
        self.logger.info("Initializing camera system...")
        # CameraFactoryManager should be usable directly. Registration might happen elsewhere or be static.
        self.enumerate_devices()

    def set_simulation_mode(self, enabled: bool):
        if self._is_simulation_mode == enabled:
            return
        
        with QMutexLocker(self._camera_mutex): # Ensure thread safety when changing critical state
            self._is_simulation_mode = enabled
            self.logger.info(f"Simulation mode set to: {enabled}")
            self.simulation_mode_status_changed.emit(enabled)
            
            if self._is_connected:
                self._internal_disconnect_logic() # Use internal logic that assumes lock is held

        # Enumeration should happen outside the lock if it creates new camera instances
        self.enumerate_devices()
        self.status_message_updated.emit(f"模拟模式已{'启用' if enabled else '禁用'}. 请刷新设备列表或重新连接.")


    def enumerate_devices(self):
        self.logger.info("Enumerating camera devices...")
        self.status_message_updated.emit("正在枚举设备...")
        temp_cam_instance: Optional[CameraInterface] = None
        try:
            available_types = CameraFactoryManager.get_available_types()
            if not available_types:
                self.logger.warning("No camera factory types available for enumeration.")
                self.error_occurred.emit("枚举设备失败", "未找到可用的相机工厂类型。")
                self._available_devices_info = []
                self.camera_list_updated.emit([])
                return

            cam_type_to_use = "hikvision" if "hikvision" in available_types else available_types[0]
            temp_cam_instance = CameraFactoryManager.create_camera(cam_type_to_use, is_simulation=self._is_simulation_mode)

            if not temp_cam_instance:
                self.logger.error(f"Failed to create temp camera for enumeration (type: {cam_type_to_use}).")
                self.error_occurred.emit("枚举设备失败", f"无法创建用于枚举的相机实例 ({cam_type_to_use})。")
                self._available_devices_info = []
                self.camera_list_updated.emit([])
                return
            
            # Ensure the temp instance knows about simulation mode if it's a dynamic property
            if hasattr(temp_cam_instance, 'set_simulation_mode_internal'): # Hypothetical method
                 temp_cam_instance.set_simulation_mode_internal(self._is_simulation_mode)


            devices = temp_cam_instance.enumerate_devices()
            self._available_devices_info = devices if devices else []
            self.logger.info(f"Found {len(self._available_devices_info)} devices.")
            self.camera_list_updated.emit(self._available_devices_info.copy()) # Emit a copy
            
            msg = ""
            if not self._available_devices_info:
                msg = "未找到相机设备。" + ("请检查连接或启用模拟模式。" if not self._is_simulation_mode else "模拟模式已启用。")
            else:
                msg = f"找到 {len(self._available_devices_info)} 个设备。"
            self.status_message_updated.emit(msg)

        except Exception as e:
            self.logger.error(f"Error enumerating devices: {e}", exc_info=True)
            self.error_occurred.emit("枚举设备错误", str(e))
            self._available_devices_info = []
            self.camera_list_updated.emit([])
        finally:
            if temp_cam_instance:
                try:
                    if hasattr(temp_cam_instance, 'is_open') and temp_cam_instance.is_open():
                        temp_cam_instance.close()
                except Exception as e_close:
                    self.logger.warning(f"Error closing temp camera after enumeration: {e_close}")

    def connect_camera(self, device_id: str) -> bool:
        with QMutexLocker(self._camera_mutex):
            if self._is_connected and self._current_device_id == device_id:
                self.logger.info(f"Camera {device_id} is already connected.")
                return True
            if self._is_connected:
                self._internal_disconnect_logic()

            self.logger.info(f"Connecting to camera: {device_id}...")
            self.status_message_updated.emit(f"正在连接到: {device_id}...")

            try:
                cam_type_to_use = "hikvision" # Default or determine from device_id/available_devices
                available_types = CameraFactoryManager.get_available_types()
                if not available_types:
                     self.error_occurred.emit("连接失败", "无可用相机工厂类型")
                     return False
                if cam_type_to_use not in available_types and available_types:
                    cam_type_to_use = available_types[0]
                
                self._camera = CameraFactoryManager.create_camera(cam_type_to_use, is_simulation=self._is_simulation_mode)
                if not self._camera:
                    self.logger.error(f"Failed to create camera instance for {device_id} (type: {cam_type_to_use}).")
                    self.error_occurred.emit("连接失败", f"无法创建相机实例 ({device_id}, 类型: {cam_type_to_use})。")
                    return False

                if self._camera.open(device_id):
                    self._is_connected = True
                    self._current_device_id = device_id
                    self.logger.info(f"Camera {device_id} connected successfully.")
                    self.status_message_updated.emit(f"相机已连接: {device_id}")
                    self._load_initial_parameters_from_camera() # Load params before emitting connected
                    self.connection_status_changed.emit(True, device_id)
                    return True
                else:
                    self.logger.error(f"Failed to open camera {device_id}.")
                    self.error_occurred.emit("连接失败", f"无法打开相机设备: {device_id}。")
                    self._camera = None
                    return False
            except Exception as e:
                self.logger.error(f"Exception connecting to camera {device_id}: {e}", exc_info=True)
                self.error_occurred.emit("连接异常", f"连接相机 {device_id} 时发生错误: {e}")
                self._is_connected = False
                self._current_device_id = None
                self._camera = None
                self.connection_status_changed.emit(False, device_id) # Notify with the device_id that failed
                return False

    def _load_initial_parameters_from_camera(self):
        """Assumes camera lock is held."""
        if not self._camera or not self._is_connected:
            return

        self.logger.info("Loading initial parameters from camera...")
        try:
            cam_params = self._camera.get_parameter() # Expects a dict of all readable params
            if cam_params:
                changed_params = {}
                for key, value in cam_params.items():
                    if key in self._parameters and self._parameters[key] != value:
                        self._parameters[key] = value
                        changed_params[key] = value
                
                if changed_params:
                    self.logger.info(f"Initial parameters updated from camera: {changed_params}")
                    self.parameters_updated.emit(self._parameters.copy())
                else:
                    self.logger.info("Camera parameters match model's initial/current values.")
                self.status_message_updated.emit("相机参数已加载。")
            else:
                self.logger.warning("Could not retrieve initial parameters (get_parameter returned None/empty).")
                self.status_message_updated.emit("无法获取相机初始参数。")
        except Exception as e:
            self.logger.error(f"Error loading initial parameters: {e}", exc_info=True)
            self.error_occurred.emit("参数加载错误", f"从相机加载初始参数失败: {e}")

    def _internal_disconnect_logic(self):
        """Core disconnect logic, assumes camera_mutex is held."""
        if not self._is_connected or not self._camera:
            return

        self.logger.info(f"Internal disconnect for {self._current_device_id}...")
        
        # Stop streaming if active (thread-safe way)
        if self._is_streaming:
            self._streaming_active_flag = False
            if self._streaming_thread and self._streaming_thread.is_alive():
                self._thread_stop_event.set()
                # Short join, actual stop_grabbing is done by _camera.close() or explicitly
                self._streaming_thread.join(timeout=0.1) 
            
            # Camera's close method should ideally handle stopping grabbing
            # but we ensure flags are set.
            self._is_streaming = False 
            # Emit streaming_status_changed outside the lock if possible, or ensure slot is safe
            # For now, emit here. Controller/View should handle UI updates safely.
            # self.streaming_status_changed.emit(False) # Emitted by public disconnect_camera

        try:
            self._camera.close()
            self.logger.info(f"Camera {self._current_device_id} closed internally.")
        except Exception as e:
            self.logger.error(f"Exception during internal camera close for {self._current_device_id}: {e}", exc_info=True)
        finally:
            self._is_connected = False
            old_device_id = self._current_device_id
            self._current_device_id = None
            self._camera = None
            # connection_status_changed emitted by public disconnect_camera

    def disconnect_camera(self):
        public_old_device_id = self._current_device_id # Store before lock
        public_was_streaming = self._is_streaming

        with QMutexLocker(self._camera_mutex):
            self._internal_disconnect_logic()
        
        # Emit signals after releasing the lock
        if public_was_streaming:
             self.streaming_status_changed.emit(False) # Ensure this is emitted if stream was stopped
        self.connection_status_changed.emit(False, public_old_device_id if public_old_device_id else "")
        self.status_message_updated.emit(f"相机 {public_old_device_id if public_old_device_id else ''} 已断开。")


    def start_streaming(self) -> bool:
        with QMutexLocker(self._camera_mutex):
            if not self._is_connected or not self._camera:
                self.error_occurred.emit("操作失败", "相机未连接，无法开始视频流。")
                return False
            if self._is_streaming:
                self.logger.info("Stream is already running.")
                return True

            self.logger.info("Starting camera stream...")
            try:
                # Optionally set trigger mode to continuous if not already
                # if self._parameters.get("trigger_mode") != 0:
                #     if self._camera.set_trigger_mode(0):
                #         self._parameters["trigger_mode"] = 0
                #         self.parameters_updated.emit(self._parameters.copy()) # Notify change
                #     else:
                #         self.logger.warning("Failed to set trigger mode to continuous before streaming.")

                if self._camera.start_grabbing():
                    self._is_streaming = True
                    self._streaming_active_flag = True
                    self._thread_stop_event.clear()
                    self._fps_count = 0
                    self._last_fps_time = time.time()
                    self._streaming_thread = threading.Thread(target=self._frame_grabbing_loop, daemon=True)
                    self._streaming_thread.start()
                    self.logger.info("Camera stream started.")
                    self.status_message_updated.emit("开始图像采集...")
                    self.streaming_status_changed.emit(True)
                    return True
                else:
                    self.logger.error("camera.start_grabbing() returned False.")
                    self.error_occurred.emit("操作失败", "开始图像采集失败 (相机报告失败)。")
                    self._is_streaming = False # Ensure state is consistent
                    return False
            except Exception as e:
                self.logger.error(f"Exception starting stream: {e}", exc_info=True)
                self.error_occurred.emit("操作异常", f"开始图像采集时发生错误: {e}")
                self._is_streaming = False
                self.streaming_status_changed.emit(False) # Notify UI of failure
                return False

    def stop_streaming(self) -> bool:
        if not self._is_streaming: # Quick check
            return True

        self.logger.info("Attempting to stop camera stream...")
        self._streaming_active_flag = False
        if self._streaming_thread and self._streaming_thread.is_alive():
            self._thread_stop_event.set()
            self._streaming_thread.join(timeout=2.0)
            if self._streaming_thread.is_alive():
                self.logger.warning("Streaming thread did not terminate gracefully.")
        self._streaming_thread = None
        
        # Lock for camera hardware access
        with QMutexLocker(self._camera_mutex):
            if not self._is_streaming: # Re-check after thread join, state might have changed
                self.logger.info("Stream was already stopped.")
                return True # Already stopped by another call or thread finishing
            
            if self._camera and self._camera.is_open():
                try:
                    if self._camera.stop_grabbing():
                        self.logger.info("camera.stop_grabbing() successful.")
                    else:
                        self.logger.error("camera.stop_grabbing() returned False.")
                        self.error_occurred.emit("操作失败", "停止图像采集失败 (相机报告失败)。")
                except Exception as e:
                    self.logger.error(f"Exception during camera.stop_grabbing(): {e}", exc_info=True)
                    self.error_occurred.emit("操作异常", f"停止图像采集时发生错误: {e}")
            
            self._is_streaming = False # Set state regardless of stop_grabbing success
        
        self.status_message_updated.emit("停止图像采集。")
        self.streaming_status_changed.emit(False) # Emit signal after lock release
        return True

    def _frame_grabbing_loop(self):
        self.logger.info("Frame grabbing thread started.")
        last_frame_log_time = time.monotonic()

        while self._streaming_active_flag:
            if self._thread_stop_event.is_set():
                self.logger.info("Stop event received, exiting frame grabbing loop.")
                break
            
            frame_data: Optional[np.ndarray] = None
            
            # Try to acquire lock briefly to access camera
            if self._camera_mutex.tryLock(10): # Timeout for lock: 10ms
                try:
                    if self._camera and self._is_streaming: # Check if still valid to grab
                        frame_data = self._camera.get_frame(timeout=50) # Short timeout for frame
                except Exception as e:
                    self.logger.error(f"Error in _camera.get_frame: {e}", exc_info=False) # Less verbose logging in loop
                    time.sleep(0.02) # Sleep on error
                finally:
                    self._camera_mutex.unlock()
            else: # Failed to get lock, camera might be busy
                time.sleep(0.005) # Very short sleep and retry
                continue

            if frame_data is not None:
                with self._frame_lock:
                    self._current_frame = frame_data # Camera should provide a copy or new buffer
                    self._fps_count += 1
                self.new_frame_available.emit(self._current_frame, self._current_device_id or "")
                last_frame_log_time = time.monotonic()
            else:
                # No frame, could be timeout or end of stream
                if self._streaming_active_flag and (time.monotonic() - last_frame_log_time > 1.0):
                    # self.logger.debug("No frame received in last second.") # Avoid log spam
                    last_frame_log_time = time.monotonic()
                time.sleep(0.001) # Minimal sleep if no frame
        
        self.logger.info("Frame grabbing thread finished.")

    def _calculate_and_emit_fps(self):
        # This timer runs on the main thread (where QTimer was created)
        # Accessing _fps_count and _last_fps_time needs to be thread-safe
        # if they are modified by the _frame_grabbing_loop.
        # _fps_count is, _last_fps_time is only modified here.
        
        current_time = time.time()
        elapsed = current_time - self._last_fps_time
        
        with QMutexLocker(self._frame_lock): # Protect _fps_count
            local_fps_count = self._fps_count
            self._fps_count = 0 # Reset for next interval
            
        if elapsed >= 0.95: # Update roughly every second
            self._current_fps = local_fps_count / elapsed
            self._last_fps_time = current_time
            self.fps_updated.emit(self._current_fps)


    def get_current_frame_copy(self) -> Optional[np.ndarray]:
        with self._frame_lock:
            return self._current_frame.copy() if self._current_frame is not None else None

    def set_parameters(self, params_to_set: Dict[str, Any]):
        with QMutexLocker(self._camera_mutex):
            if not self._is_connected or not self._camera:
                self.error_occurred.emit("操作失败", "相机未连接，无法设置参数。")
                return

            self.logger.info(f"Attempting to set parameters: {params_to_set}")
            self.status_message_updated.emit(f"正在应用参数: {list(params_to_set.keys())}")
            
            actually_changed_params = {}

            try:
                # Prefer batch set if camera supports it
                if hasattr(self._camera, 'set_parameters') and callable(self._camera.set_parameters):
                    # This assumes set_parameters takes a dict and applies them.
                    # The CameraInterface should define how this works.
                    # For now, we'll assume it tries its best.
                    self._camera.set_parameters(params_to_set.copy()) # Send a copy
                    # After attempting batch set, we must reload all params to know what actually changed
                else: # Fallback to individual setters
                    for param_name, value in params_to_set.items():
                        if param_name not in self._parameters:
                            self.logger.warning(f"Unknown parameter '{param_name}' in set_parameters. Skipping.")
                            continue
                        
                        success = False
                        # Call specific setters based on param_name
                        if param_name == "exposure_time": success = self._camera.set_exposure_time(value)
                        elif param_name == "gain": success = self._camera.set_gain(value)
                        elif param_name == "frame_rate": success = self._camera.set_frame_rate(value)
                        elif param_name == "trigger_mode": success = self._camera.set_trigger_mode(value)
                        elif param_name == "auto_exposure" and hasattr(self._camera, 'set_auto_exposure'):
                            success = self._camera.set_auto_exposure(value)
                        elif param_name == "auto_gain" and hasattr(self._camera, 'set_auto_gain'):
                            success = self._camera.set_auto_gain(value)
                        elif param_name == "auto_wb" and hasattr(self._camera, 'set_auto_white_balance'):
                            success = self._camera.set_auto_white_balance(value)
                        elif param_name == "white_balance_kelvin" and hasattr(self._camera, 'set_white_balance_kelvin'):
                            success = self._camera.set_white_balance_kelvin(value)
                        elif param_name.startswith("roi_") and hasattr(self._camera, 'set_roi'):
                            # ROI needs all components. Assume they are all in params_to_set if one is.
                            if param_name == "roi_x": # Set ROI only once when the first ROI param is encountered
                                roi_params = {p: params_to_set.get(p, self._parameters[p]) for p in ["roi_x", "roi_y", "roi_width", "roi_height"]}
                                success = self._camera.set_roi(roi_params["roi_x"], roi_params["roi_y"], roi_params["roi_width"], roi_params["roi_height"])
                        else:
                            self.logger.warning(f"No specific setter or attribute for parameter '{param_name}'.")
                            continue # Skip to next parameter

                        if not success:
                             self.logger.warning(f"Failed to set parameter '{param_name}' to '{value}' via camera interface.")
                
                # After attempting to set, always reload from camera to get actual values
                self._load_initial_parameters_from_camera() # This will emit parameters_updated with all current values
                self.status_message_updated.emit("参数已尝试应用，请检查更新后的值。")

            except Exception as e:
                self.logger.error(f"Exception setting parameters: {e}", exc_info=True)
                self.error_occurred.emit("参数设置异常", f"应用参数时发生错误: {e}")
                self._load_initial_parameters_from_camera() # Still try to sync on error

    def get_all_parameters(self) -> Dict[str, Any]:
        # Optionally, refresh from camera before returning, if high accuracy is needed
        # with QMutexLocker(self._camera_mutex):
        #     if self._is_connected and self._camera:
        #         self._load_initial_parameters_from_camera()
        return self._parameters.copy()

    def trigger_software(self):
        with QMutexLocker(self._camera_mutex):
            if not self._is_connected or not self._camera:
                self.error_occurred.emit("操作失败", "相机未连接，无法发送软触发。")
                return
            if not self._is_streaming:
                self.error_occurred.emit("操作提示", "请先开始视频流（即使是触发模式）。")
                return
            
            current_trigger_mode = self._parameters.get("trigger_mode")
            # Assuming 0: Continuous, 1: Software Trigger. Adapt if different.
            if current_trigger_mode == 0:
                self.error_occurred.emit("操作无效", "软触发在连续采集模式下无效。")
                return

            self.logger.info("Sending software trigger...")
            try:
                if self._camera.trigger_once():
                    self.logger.info("Software trigger sent successfully.")
                    self.status_message_updated.emit("已发送软触发命令。")
                else:
                    self.logger.error("camera.trigger_once() returned False.")
                    self.error_occurred.emit("操作失败", "软触发失败 (相机报告失败)。")
            except Exception as e:
                self.logger.error(f"Exception sending software trigger: {e}", exc_info=True)
                self.error_occurred.emit("操作异常", f"软触发时发生错误: {e}")

    def get_status_summary(self) -> Dict[str, Any]:
        return {
            "is_connected": self._is_connected,
            "is_streaming": self._is_streaming,
            "current_device_id": self._current_device_id,
            "is_simulation_mode": self._is_simulation_mode,
            "current_fps": self._current_fps,
            "parameters": self._parameters.copy()
        }

    def cleanup(self):
        self.logger.info("Cleaning up CameraModel...")
        self._fps_timer.stop()
        
        # Ensure streaming is stopped and thread is joined
        if self._is_streaming or (self._streaming_thread and self._streaming_thread.is_alive()):
            self.stop_streaming() 
            # stop_streaming should handle thread joining. If not, join here.
            if self._streaming_thread and self._streaming_thread.is_alive():
                 self._streaming_thread.join(timeout=1.0)


        # Ensure camera is disconnected
        if self._is_connected:
            self.disconnect_camera()

        self.logger.info("CameraModel cleanup complete.")
