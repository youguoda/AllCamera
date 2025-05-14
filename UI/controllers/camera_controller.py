"""
相机控制器类
管理相机模型和视图之间的通信和交互
"""
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

from PyQt5.QtCore import pyqtSlot, QObject

# from UI.controllers.base_controller import BaseController
from UI.models.camera_model import CameraModel
from UI.views.camera_view import CameraView
from core.utils.logger import get_logger


class CameraController(QObject): # QObject for signals/slots if not inheriting BaseController
    """
    相机控制器类
    处理与相机相关的业务逻辑和UI交互
    """

    def __init__(self, model: CameraModel, view: CameraView, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.logger = get_logger()

        self._model = model
        self._view = view

        self._connect_signals()
        self.initialize_controller_state()

    def _connect_signals(self):
        """连接模型、视图和控制器之间的信号与槽。"""
        self.logger.info("Connecting MVC signals for Camera...")

        # --- 视图信号 -> 控制器槽 ---
        self._view.refresh_devices_requested.connect(self._handle_refresh_devices)
        self._view.connect_button_clicked.connect(self._handle_connect_disconnect)
        self._view.simulation_mode_toggled.connect(self._handle_simulation_mode_toggled)
        self._view.device_selection_changed.connect(self._handle_device_selection_changed) # May not be needed if connect uses current combo value

        self._view.stream_button_clicked.connect(self._handle_stream_toggle)
        self._view.trigger_button_clicked.connect(self._handle_trigger_button)
        self._view.roi_button_toggled.connect(self._handle_roi_mode_toggled) # View toggles ROI mode in viewer

        self._view.parameter_changed_by_user.connect(self._handle_single_parameter_change_from_ui)
        self._view.apply_all_parameters_requested.connect(self._handle_apply_all_parameters)


        # --- 模型信号 -> 控制器槽 (控制器再更新视图) ---
        self._model.connection_status_changed.connect(self._on_model_connection_status_changed)
        self._model.streaming_status_changed.connect(self._on_model_streaming_status_changed)
        self._model.camera_list_updated.connect(self._on_model_camera_list_updated)
        self._model.simulation_mode_status_changed.connect(self._on_model_simulation_mode_changed)

        self._model.new_frame_available.connect(self._on_model_new_frame)
        self._model.fps_updated.connect(self._view.update_fps_display) #可以直接连接

        self._model.parameters_updated.connect(self._on_model_parameters_updated)
        # self._model.single_parameter_updated.connect(self._on_model_single_parameter_updated) # Covered by parameters_updated

        self._model.error_occurred.connect(self._view.show_error_message) # 直接连接
        self._model.status_message_updated.connect(self._view.show_status_message) # 直接连接

    def initialize_controller_state(self):
        """初始化控制器状态，例如获取初始设备列表和参数。"""
        self.logger.info("Initializing CameraController state...")
        self._model.enumerate_devices() # 请求模型枚举设备
        # 视图将通过 camera_list_updated 信号更新
        
        initial_params = self._model.get_all_parameters()
        self._view.update_parameters_display(initial_params)
        
        initial_status = self._model.get_status_summary()
        self._view.update_ui_enable_states(
            is_connected=initial_status.get("is_connected", False),
            is_streaming=initial_status.get("is_streaming", False)
        )
        self._view.update_simulation_mode_checkbox(initial_status.get("is_simulation_mode", False))


    # --- 视图信号处理槽 ---
    @pyqtSlot()
    def _handle_refresh_devices(self):
        self.logger.info("Controller: Refresh devices requested.")
        self._model.enumerate_devices()

    @pyqtSlot()
    def _handle_connect_disconnect(self):
        self.logger.info("Controller: Connect/Disconnect button clicked.")
        if self._model.get_status_summary().get("is_connected"):
            self._model.disconnect_camera()
        else:
            selected_device_id = self._view.get_current_selected_device_id()
            # selected_device_id can be None if "自动选择" is selected and it has None as userData
            if selected_device_id is None or selected_device_id == "": 
                self.logger.info("Controller: Attempting to connect to auto-selected device.")
                self._model.connect_camera("") # Model handles empty string for auto-selection
            else:
                self.logger.info(f"Controller: Attempting to connect to device: {selected_device_id}")
                self._model.connect_camera(selected_device_id)

    @pyqtSlot(bool)
    def _handle_simulation_mode_toggled(self, enabled: bool):
        self.logger.info(f"Controller: Simulation mode toggled to {enabled}.")
        self._model.set_simulation_mode(enabled)

    @pyqtSlot(str)
    def _handle_device_selection_changed(self, device_id: str):
        self.logger.info(f"Controller: Device selection changed in view to: {device_id if device_id else 'Auto'}.")
        # No direct action usually, connect button will use the current selection.
        # If immediate connection on selection is desired, logic would go here.

    @pyqtSlot()
    def _handle_stream_toggle(self):
        self.logger.info("Controller: Stream toggle button clicked.")
        if self._model.get_status_summary().get("is_streaming"):
            self._model.stop_streaming()
        else:
            self._model.start_streaming()

    @pyqtSlot()
    def _handle_trigger_button(self):
        self.logger.info("Controller: Trigger button clicked.")
        self._model.trigger_software()

    @pyqtSlot(bool)
    def _handle_roi_mode_toggled(self, is_roi_mode: bool):
        self.logger.info(f"Controller: ROI selection mode toggled to {is_roi_mode}.")
        # View handles ImageViewer mode. Controller could do more if needed.

    @pyqtSlot(str, object)
    def _handle_single_parameter_change_from_ui(self, param_name: str, value: Any):
        self.logger.info(f"Controller: UI changed parameter '{param_name}' to '{value}'.")
        if param_name == "roi_from_viewer" and isinstance(value, tuple) and len(value) == 4:
            x, y, w, h = value
            params_to_set = {"roi_x": x, "roi_y": y, "roi_width": w, "roi_height": h}
            self._model.set_parameters(params_to_set)
        else:
            self._model.set_parameters({param_name: value})

    @pyqtSlot(dict)
    def _handle_apply_all_parameters(self, params: Dict[str, Any]):
        self.logger.info(f"Controller: Apply all parameters requested: {params}")
        self._model.set_parameters(params)

    # --- 模型信号处理槽 ---
    @pyqtSlot(bool, str)
    def _on_model_connection_status_changed(self, is_connected: bool, device_id: str):
        self.logger.info(f"Controller: Model connection status changed: {is_connected}, Device: '{device_id}'")
        self._view.update_connection_status(is_connected, device_id)
        current_streaming = self._model.get_status_summary().get("is_streaming", False)
        self._view.update_ui_enable_states(is_connected, current_streaming and is_connected) # Stream can only be true if connected

    @pyqtSlot(bool)
    def _on_model_streaming_status_changed(self, is_streaming: bool):
        self.logger.info(f"Controller: Model streaming status changed: {is_streaming}")
        self._view.update_streaming_status(is_streaming)
        current_connected = self._model.get_status_summary().get("is_connected", False)
        self._view.update_ui_enable_states(current_connected, is_streaming)

    @pyqtSlot(list)
    def _on_model_camera_list_updated(self, devices: List[Dict[str, Any]]):
        self.logger.info(f"Controller: Model camera list updated. Found {len(devices)} devices.")
        current_model_device_id = self._model.get_status_summary().get("current_device_id")
        self._view.update_available_devices(devices, current_model_device_id)

    @pyqtSlot(bool)
    def _on_model_simulation_mode_changed(self, is_simulation: bool):
        self.logger.info(f"Controller: Model simulation mode status changed: {is_simulation}")
        self._view.update_simulation_mode_checkbox(is_simulation)
        status_summary = self._model.get_status_summary()
        self._view.update_ui_enable_states(
            status_summary.get("is_connected", False),
            status_summary.get("is_streaming", False)
        )

    @pyqtSlot(np.ndarray, str)
    def _on_model_new_frame(self, frame: np.ndarray, camera_id: str):
        # self.logger.debug(f"Controller: New frame from cam {camera_id}") # Potentially spammy
        self._view.display_frame(frame)

    @pyqtSlot(dict)
    def _on_model_parameters_updated(self, params: Dict[str, Any]):
        self.logger.info(f"Controller: Model parameters updated: {list(params.keys())}")
        self._view.update_parameters_display(params)
        status_summary = self._model.get_status_summary()
        self._view.update_ui_enable_states(
            status_summary.get("is_connected", False),
            status_summary.get("is_streaming", False)
        )

    def cleanup(self):
        """Perform cleanup actions for the controller."""
        self.logger.info("Cleaning up CameraController...")
        # Model and View should handle their own cleanup if they are QObjects and managed by Qt's parent-child system
        # Or if they have explicit cleanup methods that need to be called.
        # self._model.cleanup() # If model has a cleanup method
