"""
相机视图类
提供相机控制和图像显示的用户界面
"""
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QRectF, QSize
from PyQt5.QtGui import QImage, QPixmap, QIcon
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QComboBox, QSlider, QSpinBox, QCheckBox, QSplitter, QMessageBox,
    QDoubleSpinBox # 确保 QDoubleSpinBox 已导入
)

from UI.views.base_view import BaseView # 假设存在
from UI.widgets.enhanced_image_viewer import ImageViewerWidget, InteractionMode
from UI.widgets.collapsible_panel import CollapsiblePanel
from UI.utils.ui_constants import LIGHT_COLORS, SPACING # 假设存在
from core.utils.logger import get_logger


class CameraView(BaseView):
    """
    相机视图类
    提供相机控制和图像显示的用户界面
    """

    # --- 用户操作信号 ---
    refresh_devices_requested = pyqtSignal()
    connect_button_clicked = pyqtSignal() # 连接/断开按钮被点击
    simulation_mode_toggled = pyqtSignal(bool)
    device_selection_changed = pyqtSignal(str) # 参数为选中的 device_id

    stream_button_clicked = pyqtSignal() # 开始/停止流按钮被点击
    trigger_button_clicked = pyqtSignal() # 软触发按钮
    roi_button_toggled = pyqtSignal(bool) # ROI选择模式切换

    # 参数相关信号
    parameter_changed_by_user = pyqtSignal(str, object) # (param_name, value) 当用户通过控件修改时
    apply_all_parameters_requested = pyqtSignal(dict) # 请求应用当前UI上的所有参数

    # ROI SpinBox 值改变信号 (如果需要直接通过spinbox设置ROI)
    # roi_spinbox_changed = pyqtSignal(str, int) # (roi_param_name, value)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.logger = get_logger()
        self.setWindowTitle("相机控制视图") # 可以由外部设置
        self._setup_ui()
        self._connect_ui_signals()
        self.update_ui_enable_states(is_connected=False, is_streaming=False) # 初始禁用多数控件

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(SPACING["MEDIUM"], SPACING["MEDIUM"], SPACING["MEDIUM"], SPACING["MEDIUM"])
        main_layout.setSpacing(SPACING["MEDIUM"])

        self._main_splitter = QSplitter(Qt.Horizontal)
        self._main_splitter.setChildrenCollapsible(False)

        # --- 左侧: 预览区域 ---
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(SPACING["SMALL"])

        # 工具栏
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(SPACING["SMALL"])

        self._connect_button = QPushButton("连接相机")
        self._connect_button.setIcon(QIcon("./UI/resources/icons/connect.png")) # 路径可能需要调整
        self._connect_button.setStyleSheet(f"""
            QPushButton {{ background-color: {LIGHT_COLORS["PRIMARY"]}; color: white; border: none; border-radius: 4px; padding: {SPACING["SMALL"]}px {SPACING["MEDIUM"]}px; }}
            QPushButton:hover {{ background-color: {LIGHT_COLORS["PRIMARY_LIGHT"]}; }}
            QPushButton:pressed {{ background-color: {LIGHT_COLORS["PRIMARY_DARK"]}; }}
            QPushButton:disabled {{ background-color: {LIGHT_COLORS["DISABLED"]}; color: {LIGHT_COLORS["TEXT_DISABLED"]}; }}
        """)
        toolbar_layout.addWidget(self._connect_button)

        self._stream_button = QPushButton("开始视频流")
        self._stream_button.setIcon(QIcon("./UI/resources/icons/PlayButton.png"))
        self._stream_button.setStyleSheet(f"""
            QPushButton {{ background-color: {LIGHT_COLORS["SUCCESS"]}; color: white; border: none; border-radius: 4px; padding: {SPACING["SMALL"]}px {SPACING["MEDIUM"]}px; }}
            QPushButton:hover {{ background-color: {LIGHT_COLORS["SUCCESS_LIGHT"] if "SUCCESS_LIGHT" in LIGHT_COLORS else LIGHT_COLORS["SUCCESS"]}; }}
            QPushButton:pressed {{ background-color: {LIGHT_COLORS["SUCCESS_DARK"] if "SUCCESS_DARK" in LIGHT_COLORS else LIGHT_COLORS["SUCCESS"]}; }}
            QPushButton:disabled {{ background-color: {LIGHT_COLORS["DISABLED"]}; color: {LIGHT_COLORS["TEXT_DISABLED"]}; }}
        """)
        toolbar_layout.addWidget(self._stream_button)

        self._trigger_button = QPushButton("拍照 (软触发)") # 对应原 _capture_button
        self._trigger_button.setIcon(QIcon("./UI/resources/icons/camera.png"))
        self._trigger_button.setStyleSheet(f"""
            QPushButton {{ background-color: {LIGHT_COLORS["INFO"]}; color: white; border: none; border-radius: 4px; padding: {SPACING["SMALL"]}px {SPACING["MEDIUM"]}px; }}
            QPushButton:hover {{ background-color: {LIGHT_COLORS["INFO_LIGHT"] if "INFO_LIGHT" in LIGHT_COLORS else LIGHT_COLORS["INFO"]}; }}
            QPushButton:pressed {{ background-color: {LIGHT_COLORS["INFO_DARK"] if "INFO_DARK" in LIGHT_COLORS else LIGHT_COLORS["INFO"]}; }}
            QPushButton:disabled {{ background-color: {LIGHT_COLORS["DISABLED"]}; color: {LIGHT_COLORS["TEXT_DISABLED"]}; }}
        """)
        toolbar_layout.addWidget(self._trigger_button)

        self._roi_button = QPushButton("选择ROI")
        self._roi_button.setCheckable(True)
        self._roi_button.setStyleSheet(f"""
            QPushButton {{ background-color: {LIGHT_COLORS["WARNING"]}; color: white; border: none; border-radius: 4px; padding: {SPACING["SMALL"]}px {SPACING["MEDIUM"]}px; }}
            QPushButton:hover {{ background-color: {LIGHT_COLORS["WARNING_LIGHT"] if "WARNING_LIGHT" in LIGHT_COLORS else LIGHT_COLORS["WARNING"]}; }}
            QPushButton:pressed, QPushButton:checked {{ background-color: {LIGHT_COLORS["WARNING_DARK"] if "WARNING_DARK" in LIGHT_COLORS else LIGHT_COLORS["WARNING"]}; }}
            QPushButton:disabled {{ background-color: {LIGHT_COLORS["DISABLED"]}; color: {LIGHT_COLORS["TEXT_DISABLED"]}; }}
        """)
        toolbar_layout.addWidget(self._roi_button)

        toolbar_layout.addStretch()
        preview_layout.addWidget(toolbar)

        # 图像查看器容器 (为了FPS标签覆盖)
        self._viewer_container = QWidget() # Made a member for resizeEvent
        viewer_container_layout = QVBoxLayout(self._viewer_container)
        viewer_container_layout.setContentsMargins(0,0,0,0)
        viewer_container_layout.setSpacing(0)

        self._image_viewer = ImageViewerWidget()
        self._image_viewer.setMinimumSize(640, 480)
        viewer_container_layout.addWidget(self._image_viewer)
        
        self._fps_label = QLabel("FPS: 0.0", self._viewer_container)
        self._fps_label.setStyleSheet("background-color: rgba(0, 0, 0, 0.5); color: lightgreen; font-size: 14px; padding: 2px 5px; border-radius: 3px;")
        self._fps_label.setAlignment(Qt.AlignRight | Qt.AlignTop)
        self._fps_label.setFixedSize(100, 25)
        
        preview_layout.addWidget(self._viewer_container, 1)
        self._viewer_container.resizeEvent = self._on_viewer_container_resize

        # --- 右侧: 控制面板 ---
        control_widget = QWidget()
        self._control_layout = QVBoxLayout(control_widget)
        self._control_layout.setContentsMargins(SPACING["SMALL"], 0, 0, 0)
        self._control_layout.setSpacing(SPACING["MEDIUM"])

        # 1. 相机连接与选择面板
        camera_list_panel = CollapsiblePanel("相机连接与选择", self)
        camera_list_content = QWidget()
        camera_list_layout = QVBoxLayout(camera_list_content)
        camera_list_layout.addWidget(QLabel("选择设备:"))
        self._camera_combo = QComboBox()
        camera_list_layout.addWidget(self._camera_combo)
        self._simulation_check = QCheckBox("使用模拟模式")
        camera_list_layout.addWidget(self._simulation_check)
        self._refresh_button = QPushButton("刷新列表")
        self._refresh_button.setStyleSheet(f"""
             QPushButton {{ background-color: {LIGHT_COLORS["SECONDARY"]}; color: white; border: none; border-radius: 4px; padding: {SPACING["SMALL"]}px {SPACING["MEDIUM"]}px; }}
             QPushButton:hover {{ background-color: {LIGHT_COLORS["SECONDARY_LIGHT"] if "SECONDARY_LIGHT" in LIGHT_COLORS else LIGHT_COLORS["SECONDARY"]}; }}
             QPushButton:pressed {{ background-color: {LIGHT_COLORS["SECONDARY_DARK"] if "SECONDARY_DARK" in LIGHT_COLORS else LIGHT_COLORS["SECONDARY"]}; }}
        """)
        camera_list_layout.addWidget(self._refresh_button)
        camera_list_panel.add_widget(camera_list_content)
        self._control_layout.addWidget(camera_list_panel)

        # 2. 相机参数面板
        camera_params_panel = CollapsiblePanel("相机参数", self)
        camera_params_content = QWidget()
        camera_params_q_grid_layout = QGridLayout(camera_params_content)

        camera_params_q_grid_layout.addWidget(QLabel("曝光时间 (μs):"), 0, 0)
        self._exposure_slider = QSlider(Qt.Horizontal)
        self._exposure_slider.setRange(10, 100000)
        camera_params_q_grid_layout.addWidget(self._exposure_slider, 0, 1)
        self._exposure_value_label = QLabel("10000 μs")
        camera_params_q_grid_layout.addWidget(self._exposure_value_label, 0, 2)
        self._auto_exposure_check = QCheckBox("自动")
        camera_params_q_grid_layout.addWidget(self._auto_exposure_check, 0, 3)

        camera_params_q_grid_layout.addWidget(QLabel("增益 (dB):"), 1, 0)
        self._gain_slider = QSlider(Qt.Horizontal)
        self._gain_slider.setRange(0, 20)
        camera_params_q_grid_layout.addWidget(self._gain_slider, 1, 1)
        self._gain_value_label = QLabel("0 dB")
        camera_params_q_grid_layout.addWidget(self._gain_value_label, 1, 2)
        self._auto_gain_check = QCheckBox("自动")
        camera_params_q_grid_layout.addWidget(self._auto_gain_check, 1, 3)

        camera_params_q_grid_layout.addWidget(QLabel("白平衡 (K):"), 2, 0)
        self._wb_slider = QSlider(Qt.Horizontal)
        self._wb_slider.setRange(2000, 8000)
        camera_params_q_grid_layout.addWidget(self._wb_slider, 2, 1)
        self._wb_value_label = QLabel("5000 K")
        camera_params_q_grid_layout.addWidget(self._wb_value_label, 2, 2)
        self._auto_wb_check = QCheckBox("自动")
        camera_params_q_grid_layout.addWidget(self._auto_wb_check, 2, 3)
        
        self._apply_params_button = QPushButton("应用参数")
        camera_params_q_grid_layout.addWidget(self._apply_params_button, 3, 0, 1, 4)

        camera_params_panel.add_widget(camera_params_content)
        self._control_layout.addWidget(camera_params_panel)

        # 3. 图像与触发面板
        image_settings_panel = CollapsiblePanel("图像与触发", self)
        image_settings_content = QWidget()
        image_settings_q_grid_layout = QGridLayout(image_settings_content)

        image_settings_q_grid_layout.addWidget(QLabel("分辨率:"), 0, 0)
        self._resolution_combo = QComboBox()
        self._resolution_combo.addItems(["(当前)", "1920x1080", "1280x720", "640x480"])
        image_settings_q_grid_layout.addWidget(self._resolution_combo, 0, 1)

        image_settings_q_grid_layout.addWidget(QLabel("帧率 (目标):"), 1, 0)
        self._fps_spin = QSpinBox()
        self._fps_spin.setRange(1, 200)
        image_settings_q_grid_layout.addWidget(self._fps_spin, 1, 1)

        image_settings_q_grid_layout.addWidget(QLabel("像素格式:"), 2, 0)
        self._pixel_format_combo = QComboBox()
        self._pixel_format_combo.addItems(["(当前)", "Mono8", "BayerRG8", "RGB8"])
        image_settings_q_grid_layout.addWidget(self._pixel_format_combo, 2, 1)

        image_settings_q_grid_layout.addWidget(QLabel("触发模式:"), 3, 0)
        self._trigger_mode_combo = QComboBox()
        self._trigger_mode_combo.addItems(["连续采集", "软触发", "硬触发"])
        image_settings_q_grid_layout.addWidget(self._trigger_mode_combo, 3, 1)

        image_settings_panel.add_widget(image_settings_content)
        self._control_layout.addWidget(image_settings_panel)

        # 4. 状态信息面板
        status_panel = CollapsiblePanel("状态信息", self)
        status_panel.set_expanded(True)
        status_content = QWidget()
        status_layout = QVBoxLayout(status_content)
        self._status_label = QLabel("就绪")
        self._status_label.setWordWrap(True)
        status_layout.addWidget(self._status_label)
        self._camera_info_label = QLabel("相机信息：未连接")
        self._camera_info_label.setWordWrap(True)
        status_layout.addWidget(self._camera_info_label)
        status_panel.add_widget(status_content)
        self._control_layout.addWidget(status_panel)

        self._control_layout.addStretch()

        self._main_splitter.addWidget(preview_widget)
        self._main_splitter.addWidget(control_widget)
        self._main_splitter.setSizes([700, 450])

        main_layout.addWidget(self._main_splitter)

    def _on_viewer_container_resize(self, event: QSize): # Corrected type hint
        if hasattr(self, '_fps_label') and self._fps_label:
            margin = 5
            parent_width = self._viewer_container.width() # Access parent through member
            self._fps_label.move(parent_width - self._fps_label.width() - margin, margin)
        QWidget.resizeEvent(self._viewer_container, event)


    def _connect_ui_signals(self):
        self._refresh_button.clicked.connect(self.refresh_devices_requested)
        self._connect_button.clicked.connect(self.connect_button_clicked)
        self._simulation_check.toggled.connect(self.simulation_mode_toggled)
        self._camera_combo.currentIndexChanged.connect(self._on_camera_selection_changed)

        self._stream_button.clicked.connect(self.stream_button_clicked)
        self._trigger_button.clicked.connect(self.trigger_button_clicked)
        self._roi_button.toggled.connect(self._on_roi_button_toggled_by_user)

        self._exposure_slider.valueChanged.connect(lambda value: self._on_parameter_slider_changed("exposure_time", value, self._exposure_value_label, " μs"))
        self._gain_slider.valueChanged.connect(lambda value: self._on_parameter_slider_changed("gain", value, self._gain_value_label, " dB"))
        self._wb_slider.valueChanged.connect(lambda value: self._on_parameter_slider_changed("white_balance_kelvin", value, self._wb_value_label, " K"))
        
        self._auto_exposure_check.toggled.connect(lambda checked: self._on_auto_param_toggled("auto_exposure", checked, self._exposure_slider))
        self._auto_gain_check.toggled.connect(lambda checked: self._on_auto_param_toggled("auto_gain", checked, self._gain_slider))
        self._auto_wb_check.toggled.connect(lambda checked: self._on_auto_param_toggled("auto_wb", checked, self._wb_slider))

        self._fps_spin.valueChanged.connect(lambda value: self.parameter_changed_by_user.emit("frame_rate", value))
        self._trigger_mode_combo.currentIndexChanged.connect(lambda index: self.parameter_changed_by_user.emit("trigger_mode", index))
        
        self._resolution_combo.currentIndexChanged.connect(self._on_resolution_changed)
        self._pixel_format_combo.currentIndexChanged.connect(self._on_pixel_format_changed)

        self._apply_params_button.clicked.connect(self._on_apply_all_parameters)
        self._image_viewer.get_viewer().roi_selected.connect(self._on_roi_selected_from_viewer_widget)

    def _on_camera_selection_changed(self, index: int):
        if index >= 0: # Ensure a valid index
            device_id = self._camera_combo.itemData(index) # itemData can be None for "自动选择"
            if device_id is not None: # Only emit if a specific device is selected
                self.device_selection_changed.emit(device_id)
            elif self._camera_combo.currentText() == "自动选择": # Handle "自动选择" explicitly if needed
                self.device_selection_changed.emit("") # Or a special value like "auto"

    def _on_roi_button_toggled_by_user(self, checked: bool):
        if checked:
            self._image_viewer.get_viewer().set_interaction_mode(InteractionMode.SELECT_ROI)
            self.show_status_message("ROI选择模式：在图像上拖动以选择区域。")
        else:
            self._image_viewer.get_viewer().set_interaction_mode(InteractionMode.VIEW)
        self.roi_button_toggled.emit(checked)

    def _on_roi_selected_from_viewer_widget(self, rect: QRectF):
        self.logger.info(f"ROI selected from viewer: {rect.x()},{rect.y()},{rect.width()},{rect.height()}")
        if self._roi_button.isChecked():
            self._roi_button.setChecked(False) 
        self.show_status_message(f"选择ROI: x={int(rect.x())}, y={int(rect.y())}, w={int(rect.width())}, h={int(rect.height())} (应用ROI需相机支持)")
        # Notify controller about the new ROI from viewer
        self.parameter_changed_by_user.emit("roi_from_viewer", 
                                            (int(rect.x()), int(rect.y()), 
                                             int(rect.width()), int(rect.height())))


    def _on_parameter_slider_changed(self, param_name: str, value: int, label_widget: QLabel, unit: str):
        label_widget.setText(f"{value}{unit}")
        self.parameter_changed_by_user.emit(param_name, value)

    def _on_auto_param_toggled(self, param_name: str, checked: bool, slider_widget: QSlider):
        # slider_widget.setEnabled(not checked) # This will be handled by update_ui_enable_states
        self.parameter_changed_by_user.emit(param_name, checked)
        # self.show_status_message(f"{param_name}: {'启用' if checked else '禁用'} (需应用参数)") # Status comes from model/controller

    def _on_resolution_changed(self, index: int):
        if index > 0:
            resolution_str = self._resolution_combo.currentText()
            self.parameter_changed_by_user.emit("resolution", resolution_str)

    def _on_pixel_format_changed(self, index: int):
        if index > 0:
            pixel_format_str = self._pixel_format_combo.currentText()
            self.parameter_changed_by_user.emit("pixel_format", pixel_format_str)

    def _on_apply_all_parameters(self):
        params = self.get_all_ui_parameters()
        self.apply_all_parameters_requested.emit(params)

    def update_connection_status(self, is_connected: bool, device_id: str):
        self.logger.info(f"View: Updating connection status to {is_connected} for device '{device_id}'")
        self._connect_button.setText("断开相机" if is_connected else "连接相机")
        
        current_streaming_status = self._stream_button.text() == "停止视频流" # Infer current stream state from button
        self.update_ui_enable_states(is_connected=is_connected, is_streaming=current_streaming_status and is_connected)

        if is_connected:
            self._connect_button.setStyleSheet(f"""
                QPushButton {{ background-color: {LIGHT_COLORS["DANGER"]}; color: white; border: none; border-radius: 4px; padding: {SPACING["SMALL"]}px {SPACING["MEDIUM"]}px; }}
                QPushButton:hover {{ background-color: {LIGHT_COLORS["DANGER_LIGHT"] if "DANGER_LIGHT" in LIGHT_COLORS else LIGHT_COLORS["DANGER"]}; }}
                QPushButton:pressed {{ background-color: {LIGHT_COLORS["DANGER_DARK"] if "DANGER_DARK" in LIGHT_COLORS else LIGHT_COLORS["DANGER"]}; }}
            """)
        else:
            self._connect_button.setStyleSheet(f"""
                QPushButton {{ background-color: {LIGHT_COLORS["PRIMARY"]}; color: white; border: none; border-radius: 4px; padding: {SPACING["SMALL"]}px {SPACING["MEDIUM"]}px; }}
                QPushButton:hover {{ background-color: {LIGHT_COLORS["PRIMARY_LIGHT"]}; }}
                QPushButton:pressed {{ background-color: {LIGHT_COLORS["PRIMARY_DARK"]}; }}
            """)
            self._camera_info_label.setText("相机信息：未连接")
            self.display_frame(None)

    def update_streaming_status(self, is_streaming: bool):
        self.logger.info(f"View: Updating streaming status to {is_streaming}")
        self._stream_button.setText("停止视频流" if is_streaming else "开始视频流")
        self._stream_button.setIcon(QIcon("./UI/resources/icons/Stop-Button.png" if is_streaming else "./UI/resources/icons/PlayButton.png"))
        
        if is_streaming:
             self._stream_button.setStyleSheet(f"""
                QPushButton {{ background-color: {LIGHT_COLORS["DANGER"]}; color: white; border: none; border-radius: 4px; padding: {SPACING["SMALL"]}px {SPACING["MEDIUM"]}px; }}
                QPushButton:hover {{ background-color: {LIGHT_COLORS["DANGER_LIGHT"] if "DANGER_LIGHT" in LIGHT_COLORS else LIGHT_COLORS["DANGER"]}; }}
                QPushButton:pressed {{ background-color: {LIGHT_COLORS["DANGER_DARK"] if "DANGER_DARK" in LIGHT_COLORS else LIGHT_COLORS["DANGER"]}; }}
             """)
        else:
             self._stream_button.setStyleSheet(f"""
                QPushButton {{ background-color: {LIGHT_COLORS["SUCCESS"]}; color: white; border: none; border-radius: 4px; padding: {SPACING["SMALL"]}px {SPACING["MEDIUM"]}px; }}
                QPushButton:hover {{ background-color: {LIGHT_COLORS["SUCCESS_LIGHT"] if "SUCCESS_LIGHT" in LIGHT_COLORS else LIGHT_COLORS["SUCCESS"]}; }}
                QPushButton:pressed {{ background-color: {LIGHT_COLORS["SUCCESS_DARK"] if "SUCCESS_DARK" in LIGHT_COLORS else LIGHT_COLORS["SUCCESS"]}; }}
             """)
        
        current_connected_status = self._connect_button.text() == "断开相机"
        self.update_ui_enable_states(is_connected=current_connected_status, is_streaming=is_streaming)

    def update_available_devices(self, devices: List[Dict[str, Any]], current_selection_id: Optional[str] = None):
        self.logger.info(f"View: Updating available devices. Found: {len(devices)}. Current selection hint: {current_selection_id}")
        self._camera_combo.blockSignals(True)
        self._camera_combo.clear()
        self._camera_combo.addItem("自动选择", None) 
        
        selected_idx_to_set = 0 
        for i, device_info in enumerate(devices):
            dev_id = device_info.get('device_id', f'unknown_id_{i}')
            model_name = device_info.get('model_name', '未知型号')
            sn = device_info.get('serial_number', 'N/A')
            ip = device_info.get('device_ip', '')
            display_text = f"[{dev_id}] {model_name} (SN:{sn})"
            if ip: display_text += f" - {ip}"
            
            self._camera_combo.addItem(display_text, userData=dev_id)
            if dev_id == current_selection_id:
                selected_idx_to_set = i + 1
        
        if current_selection_id is None and self._camera_combo.count() > 0: # No specific selection, default to "自动选择"
            selected_idx_to_set = 0
        
        self._camera_combo.setCurrentIndex(selected_idx_to_set)
        self._camera_combo.blockSignals(False)

    def update_simulation_mode_checkbox(self, is_simulation: bool):
        self._simulation_check.blockSignals(True)
        self._simulation_check.setChecked(is_simulation)
        self._simulation_check.blockSignals(False)

    def display_frame(self, frame: Optional[np.ndarray]):
        if frame is None:
            self._image_viewer.set_image(None)
            return
        try:
            h, w = frame.shape[:2]
            stride = frame.strides[0]
            fmt = QImage.Format_Grayscale8
            if frame.ndim == 3:
                if frame.shape[2] == 3: fmt = QImage.Format_BGR888
                elif frame.shape[2] == 4: fmt = QImage.Format_ARGB32
                else: self.logger.warning(f"Unsupported color frame: {frame.shape}"); return
            elif frame.ndim != 2:
                 self.logger.warning(f"Unsupported frame: {frame.shape}"); return
            
            qimg = QImage(frame.data, w, h, stride, fmt)
            self._image_viewer.set_image(qimg.copy())
        except Exception as e:
            self.logger.error(f"Error displaying frame: {e}", exc_info=True)

    def update_fps_display(self, fps: float):
        self._fps_label.setText(f"FPS: {fps:.1f}")

    def update_parameters_display(self, params: Dict[str, Any]):
        self.logger.debug(f"View: Updating parameters display with: {params}")

        def set_val(widget, val, block=True):
            if block: widget.blockSignals(True)
            if isinstance(widget, QSlider): widget.setValue(int(val))
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)): widget.setValue(val) # Handles int/float
            elif isinstance(widget, QCheckBox): widget.setChecked(bool(val))
            elif isinstance(widget, QComboBox):
                idx = widget.findData(val) if val is not None else -1 # findData for value
                if idx == -1 and val is not None: idx = widget.findText(str(val)) # fallback to text
                if idx != -1: widget.setCurrentIndex(idx)
                elif widget.count() > 0 and val is None : widget.setCurrentIndex(0) # Default to first if val is None (e.g. "Current")
            if block: widget.blockSignals(False)

        # Parameters from model
        exp_time = params.get("exposure_time", self._exposure_slider.minimum())
        set_val(self._exposure_slider, exp_time)
        self._exposure_value_label.setText(f"{exp_time:.0f} μs")
        set_val(self._auto_exposure_check, params.get("auto_exposure", False))

        gain_val = params.get("gain", self._gain_slider.minimum())
        set_val(self._gain_slider, gain_val)
        self._gain_value_label.setText(f"{gain_val:.1f} dB")
        set_val(self._auto_gain_check, params.get("auto_gain", False))

        wb_k = params.get("white_balance_kelvin", self._wb_slider.minimum())
        set_val(self._wb_slider, wb_k)
        self._wb_value_label.setText(f"{wb_k:.0f} K")
        set_val(self._auto_wb_check, params.get("auto_wb", False))

        set_val(self._fps_spin, params.get("frame_rate", 30))
        set_val(self._trigger_mode_combo, params.get("trigger_mode", 0)) # Index for combo
        
        # Update resolution and pixel format combos if values are present
        res_val = params.get("resolution")
        if res_val: set_val(self._resolution_combo, res_val)
        else: self._resolution_combo.setCurrentIndex(0) # Default to "(当前)"

        px_fmt_val = params.get("pixel_format")
        if px_fmt_val: set_val(self._pixel_format_combo, px_fmt_val)
        else: self._pixel_format_combo.setCurrentIndex(0) # Default to "(当前)"

        # Update camera info label
        info_parts = [f"相机ID: {params.get('device_id', 'N/A')}"]
        if 'model_name' in params: info_parts.append(f"型号: {params['model_name']}")
        if 'serial_number' in params: info_parts.append(f"SN: {params['serial_number']}")
        if 'device_ip' in params: info_parts.append(f"IP: {params['device_ip']}")
        info_parts.append(f"分辨率: {params.get('width', 'N/A')}x{params.get('height', 'N/A')}")
        info_parts.append(f"像素格式: {params.get('pixel_format', 'N/A')}")
        info_parts.append(f"帧率 (目标): {params.get('frame_rate', 'N/A')} FPS")
        info_parts.append(f"曝光: {params.get('exposure_time', 'N/A'):.0f} μs ({'自动' if params.get('auto_exposure') else '手动'})")
        info_parts.append(f"增益: {params.get('gain', 'N/A'):.1f} dB ({'自动' if params.get('auto_gain') else '手动'})")
        info_parts.append(f"白平衡: {params.get('white_balance_kelvin', 'N/A'):.0f} K ({'自动' if params.get('auto_wb') else '手动'})")
        self._camera_info_label.setText("\n".join(info_parts))
        
        # Update enable states based on new params (especially auto modes)
        is_connected = self._connect_button.text() == "断开相机" # Infer from button
        is_streaming = self._stream_button.text() == "停止视频流"
        self.update_ui_enable_states(is_connected, is_streaming)


    def show_status_message(self, message: str):
        self.logger.info(f"View Status: {message}")
        self._status_label.setText(message)

    def show_error_message(self, title: str, message: str):
        self.logger.error(f"View Error: {title} - {message}")
        self._status_label.setText(f"错误: {message}")
        QMessageBox.critical(self, title, message)

    def get_current_selected_device_id(self) -> Optional[str]:
        if self._camera_combo.currentIndex() >= 0:
            return self._camera_combo.currentData()
        return None

    def get_all_ui_parameters(self) -> Dict[str, Any]:
        params = {
            "exposure_time": self._exposure_slider.value(),
            "gain": self._gain_slider.value(),
            "white_balance_kelvin": self._wb_slider.value(),
            "auto_exposure": self._auto_exposure_check.isChecked(),
            "auto_gain": self._auto_gain_check.isChecked(),
            "auto_wb": self._auto_wb_check.isChecked(),
            "frame_rate": self._fps_spin.value(),
            "trigger_mode": self._trigger_mode_combo.currentIndex(),
        }
        if self._resolution_combo.currentIndex() > 0:
            params["resolution"] = self._resolution_combo.currentText()
        if self._pixel_format_combo.currentIndex() > 0:
            params["pixel_format"] = self._pixel_format_combo.currentText()
        return params

    def update_ui_enable_states(self, is_connected: bool, is_streaming: bool):
        self._camera_combo.setEnabled(not is_connected)
        self._refresh_button.setEnabled(not is_connected)
        self._simulation_check.setEnabled(not is_connected)

        self._stream_button.setEnabled(is_connected)
        
        # Get current UI state for auto params to decide slider enable state
        auto_exp = self._auto_exposure_check.isChecked()
        auto_gain = self._auto_gain_check.isChecked()
        auto_wb = self._auto_wb_check.isChecked()

        params_adjustable = is_connected and not is_streaming
        
        self._trigger_button.setEnabled(is_connected and (not is_streaming or self._trigger_mode_combo.currentIndex() != 0))
        self._trigger_mode_combo.setEnabled(is_connected) # Can change trigger mode if connected, even if streaming (model handles logic)


        self._roi_button.setEnabled(is_connected and self._image_viewer.get_viewer().pixmap() is not None)
        if not self._roi_button.isEnabled() and self._roi_button.isChecked():
            self._roi_button.setChecked(False) # This will trigger its toggled signal
            # self._image_viewer.get_viewer().set_interaction_mode(InteractionMode.VIEW) # Handled by _on_roi_button_toggled

        self._apply_params_button.setEnabled(params_adjustable)
        self._fps_spin.setEnabled(params_adjustable)
        self._resolution_combo.setEnabled(params_adjustable)
        self._pixel_format_combo.setEnabled(params_adjustable)

        self._auto_exposure_check.setEnabled(params_adjustable)
        self._auto_gain_check.setEnabled(params_adjustable)
        self._auto_wb_check.setEnabled(params_adjustable)

        self._exposure_slider.setEnabled(params_adjustable and not auto_exp)
        self._gain_slider.setEnabled(params_adjustable and not auto_gain)
        self._wb_slider.setEnabled(params_adjustable and not auto_wb)

    def closeEvent(self, event):
        self.logger.info("CameraView closing.")
        # Any view-specific cleanup if needed
        super().closeEvent(event)
