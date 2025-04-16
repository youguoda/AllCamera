"""
相机视图类
提供相机控制和图像显示的用户界面
"""
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import time

from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QImage, QPixmap, QIcon
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QComboBox, QSlider, QSpinBox, QCheckBox, QSplitter, QMessageBox,
    QGroupBox, QFormLayout, QLineEdit, QDoubleSpinBox
)

from UI.views.base_view import BaseView
from UI.widgets.enhanced_image_viewer import ImageViewerWidget, InteractionMode
from UI.widgets.collapsible_panel import CollapsiblePanel
from UI.utils.ui_constants import LIGHT_COLORS, SPACING
from core.utils.logger import get_logger


class CameraView(BaseView):
    """
    相机视图类
    提供相机控制和图像显示的用户界面
    """
    
    # 自定义信号
    connect_camera_signal = pyqtSignal(str)   # 连接相机信号
    disconnect_camera_signal = pyqtSignal()   # 断开相机信号
    start_streaming_signal = pyqtSignal()    # 开始流式传输信号
    stop_streaming_signal = pyqtSignal()     # 停止流式传输信号
    trigger_once_signal = pyqtSignal()        # 触发一次信号
    set_parameter_signal = pyqtSignal(str, object)   # 设置参数信号
    set_roi_signal = pyqtSignal(int, int, int, int)   # 设置ROI信号
    reset_roi_signal = pyqtSignal()           # 重置ROI信号
    
    def __init__(self, parent=None):
        """
        初始化相机视图
        
        Args:
            parent: 父级窗口部件
        """
        super().__init__(parent)
        self.logger = get_logger()
        
        # 状态变量
        self._is_connected = False    # 是否已连接相机
        self._is_streaming = False    # 是否正在流式传输
        self._current_device_id = ""  # 当前连接的相机设备ID
        self._available_devices = []  # 可用的相机设备列表
        self._current_fps = 0.0       # 当前帧率
        
        # 图像相关
        self._current_frame = None      # 当前帧数据
        self._last_update_time = time.time()    # 上次更新时间
        
        # UI更新定时器
        self._ui_timer = QTimer(self)
        self._ui_timer.timeout.connect(self._update_ui_timer)
        self._ui_timer.start(30)  # 30毫秒更新一次
        
        # 设置UI
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI组件"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(SPACING["MEDIUM"], SPACING["MEDIUM"],
                                      SPACING["MEDIUM"], SPACING["MEDIUM"])
        main_layout.setSpacing(SPACING["MEDIUM"])
        
        # 创建分割器
        self._main_splitter = QSplitter(Qt.Horizontal)
        self._main_splitter.setChildrenCollapsible(False)
        
        # --- 左侧: 预览区域 ---
        self._preview_widget = QWidget()
        self._preview_layout = QVBoxLayout(self._preview_widget)
        self._preview_layout.setContentsMargins(0, 0, 0, 0)
        self._preview_layout.setSpacing(SPACING["SMALL"])
        
        # 工具栏
        self._toolbar = QWidget()
        self._toolbar_layout = QHBoxLayout(self._toolbar)
        self._toolbar_layout.setContentsMargins(0, 0, 0, 0)
        self._toolbar_layout.setSpacing(SPACING["SMALL"])
        
        # 连接按钮
        self._connect_button = QPushButton("连接相机")
        self._connect_button.setIcon(QIcon("./UI/resources/icons/connect.png"))
        self._connect_button.setStyleSheet(f"""
            QPushButton {{ background-color: {LIGHT_COLORS["PRIMARY"]}; color: white; border: none; border-radius: 4px; padding: {SPACING["SMALL"]}px {SPACING["MEDIUM"]}px; }}
            QPushButton:hover {{ background-color: {LIGHT_COLORS["PRIMARY_LIGHT"]}; }}
            QPushButton:pressed {{ background-color: {LIGHT_COLORS["PRIMARY_DARK"]}; }}
            QPushButton:disabled {{ background-color: {LIGHT_COLORS["DISABLED"]}; color: {LIGHT_COLORS["TEXT_DISABLED"]}; }}
        """)
        self._toolbar_layout.addWidget(self._connect_button)
        
        # 开始/停止视频流按钮
        self._stream_button = QPushButton("开始视频流")
        self._stream_button.setEnabled(False)
        self._stream_button.setStyleSheet(f"""
            QPushButton {{ background-color: {LIGHT_COLORS["SUCCESS"]}; color: white; border: none; border-radius: 4px; padding: {SPACING["SMALL"]}px {SPACING["MEDIUM"]}px; }}
            QPushButton:hover {{ background-color: {LIGHT_COLORS["SUCCESS_LIGHT"]}; }}
            QPushButton:pressed {{ background-color: {LIGHT_COLORS["SUCCESS_DARK"]}; }}
            QPushButton:disabled {{ background-color: {LIGHT_COLORS["DISABLED"]}; color: {LIGHT_COLORS["TEXT_DISABLED"]}; }}
        """)
        self._toolbar_layout.addWidget(self._stream_button)
        
        # 拍照按钮
        self._capture_button = QPushButton("拍照 (软触发)")
        self._capture_button.setEnabled(False)
        self._capture_button.setStyleSheet(f"""
            QPushButton {{ background-color: {LIGHT_COLORS["INFO"]}; color: white; border: none; border-radius: 4px; padding: {SPACING["SMALL"]}px {SPACING["MEDIUM"]}px; }}
            QPushButton:hover {{ background-color: {LIGHT_COLORS["INFO_LIGHT"]}; }}
            QPushButton:pressed {{ background-color: {LIGHT_COLORS["INFO_DARK"]}; }}
            QPushButton:disabled {{ background-color: {LIGHT_COLORS["DISABLED"]}; color: {LIGHT_COLORS["TEXT_DISABLED"]}; }}
        """)
        self._toolbar_layout.addWidget(self._capture_button)
        
        # ROI按钮
        self._roi_button = QPushButton("选择ROI")
        self._roi_button.setCheckable(True)
        self._roi_button.setEnabled(False)
        self._roi_button.setStyleSheet(f"""
            QPushButton {{ background-color: {LIGHT_COLORS["WARNING"]}; color: white; border: none; border-radius: 4px; padding: {SPACING["SMALL"]}px {SPACING["MEDIUM"]}px; }}
            QPushButton:hover {{ background-color: {LIGHT_COLORS["WARNING_LIGHT"]}; }}
            QPushButton:pressed, QPushButton:checked {{ background-color: {LIGHT_COLORS["WARNING_DARK"]}; }}
            QPushButton:disabled {{ background-color: {LIGHT_COLORS["DISABLED"]}; color: {LIGHT_COLORS["TEXT_DISABLED"]}; }}
        """)
        self._toolbar_layout.addWidget(self._roi_button)
        
        self._toolbar_layout.addStretch()
        
        # FPS标签
        self._fps_label = QLabel("FPS: 0.0")
        self._fps_label.setStyleSheet("background-color: rgba(0, 0, 0, 0.5); color: lightgreen; font-size: 14px; padding: 2px 5px; border-radius: 3px;")
        self._toolbar_layout.addWidget(self._fps_label)
        
        self._preview_layout.addWidget(self._toolbar)
        
        # 图像查看器容器
        self._viewer_container = QWidget()
        self._viewer_container_layout = QVBoxLayout(self._viewer_container)
        self._viewer_container_layout.setContentsMargins(0, 0, 0, 0)
        self._viewer_container_layout.setSpacing(0)
        
        # 图像查看器
        self._image_viewer = ImageViewerWidget()
        self._image_viewer.setMinimumSize(640, 480)
        self._image_viewer.set_interaction_mode(InteractionMode.VIEW)
        self._viewer_container_layout.addWidget(self._image_viewer)
        
        self._preview_layout.addWidget(self._viewer_container, 1)
        
        # --- 右侧: 控制面板 ---
        self._control_panel = QWidget()
        self._control_panel.setMinimumWidth(300)
        self._control_panel.setMaximumWidth(400)
        self._control_panel_layout = QVBoxLayout(self._control_panel)
        self._control_panel_layout.setContentsMargins(0, 0, 0, 0)
        self._control_panel_layout.setSpacing(SPACING["MEDIUM"])
        
        # 相机选择面板
        self._camera_selection_panel = CollapsiblePanel("相机选择", collapsed=False)
        self._camera_selection_layout = QVBoxLayout()
        self._camera_selection_layout.setContentsMargins(SPACING["SMALL"], SPACING["SMALL"],
                                                        SPACING["SMALL"], SPACING["SMALL"])
        self._camera_selection_layout.setSpacing(SPACING["SMALL"])
        
        # 相机选择组合框
        self._camera_combo = QComboBox()
        self._camera_combo.setStyleSheet(f"""
            QComboBox {{ border: 1px solid {LIGHT_COLORS["BORDER"]}; border-radius: 4px; padding: {SPACING["SMALL"]}px; }}
            QComboBox:hover {{ border-color: {LIGHT_COLORS["PRIMARY"]}; }}
            QComboBox:disabled {{ background-color: {LIGHT_COLORS["DISABLED"]}; color: {LIGHT_COLORS["TEXT_DISABLED"]}; }}
        """)
        self._camera_selection_layout.addWidget(self._camera_combo)
        
        # 刷新相机列表按钮
        self._refresh_button = QPushButton("刷新相机列表")
        self._refresh_button.setStyleSheet(f"""
            QPushButton {{ background-color: {LIGHT_COLORS["SECONDARY"]}; color: white; border: none; border-radius: 4px; padding: {SPACING["SMALL"]}px; }}
            QPushButton:hover {{ background-color: {LIGHT_COLORS["SECONDARY_LIGHT"]}; }}
            QPushButton:pressed {{ background-color: {LIGHT_COLORS["SECONDARY_DARK"]}; }}
            QPushButton:disabled {{ background-color: {LIGHT_COLORS["DISABLED"]}; color: {LIGHT_COLORS["TEXT_DISABLED"]}; }}
        """)
        self._camera_selection_layout.addWidget(self._refresh_button)
        
        self._camera_selection_panel.add_layout(self._camera_selection_layout)
        self._control_panel_layout.addWidget(self._camera_selection_panel)
        
        # 相机参数面板
        self._camera_params_panel = CollapsiblePanel("相机参数", collapsed=False)
        self._camera_params_layout = QFormLayout()
        self._camera_params_layout.setContentsMargins(SPACING["SMALL"], SPACING["SMALL"],
                                                     SPACING["SMALL"], SPACING["SMALL"])
        self._camera_params_layout.setSpacing(SPACING["SMALL"])
        
        # 曝光设置
        self._exposure_label = QLabel("曝光时间 (μs):")
        self._exposure_spinbox = QDoubleSpinBox()
        self._exposure_spinbox.setRange(1, 1000000)
        self._exposure_spinbox.setDecimals(1)
        self._exposure_spinbox.setSingleStep(100)
        self._exposure_spinbox.setEnabled(False)
        self._exposure_spinbox.setStyleSheet(f"""
            QDoubleSpinBox {{ border: 1px solid {LIGHT_COLORS["BORDER"]}; border-radius: 4px; padding: {SPACING["SMALL"]}px; }}
            QDoubleSpinBox:hover {{ border-color: {LIGHT_COLORS["PRIMARY"]}; }}
            QDoubleSpinBox:disabled {{ background-color: {LIGHT_COLORS["DISABLED"]}; color: {LIGHT_COLORS["TEXT_DISABLED"]}; }}
        """)
        self._camera_params_layout.addRow(self._exposure_label, self._exposure_spinbox)
        
        # 增益设置
        self._gain_label = QLabel("增益:")
        self._gain_spinbox = QDoubleSpinBox()
        self._gain_spinbox.setRange(0, 100)
        self._gain_spinbox.setDecimals(1)
        self._gain_spinbox.setSingleStep(0.5)
        self._gain_spinbox.setEnabled(False)
        self._gain_spinbox.setStyleSheet(f"""
            QDoubleSpinBox {{ border: 1px solid {LIGHT_COLORS["BORDER"]}; border-radius: 4px; padding: {SPACING["SMALL"]}px; }}
            QDoubleSpinBox:hover {{ border-color: {LIGHT_COLORS["PRIMARY"]}; }}
            QDoubleSpinBox:disabled {{ background-color: {LIGHT_COLORS["DISABLED"]}; color: {LIGHT_COLORS["TEXT_DISABLED"]}; }}
        """)
        self._camera_params_layout.addRow(self._gain_label, self._gain_spinbox)
        
        # 触发模式设置
        self._trigger_label = QLabel("触发模式:")
        self._trigger_mode_checkbox = QCheckBox("启用")
        self._trigger_mode_checkbox.setEnabled(False)
        self._camera_params_layout.addRow(self._trigger_label, self._trigger_mode_checkbox)
        
        self._camera_params_panel.add_layout(self._camera_params_layout)
        self._control_panel_layout.addWidget(self._camera_params_panel)
        
        # ROI信息面板
        self._roi_info_panel = CollapsiblePanel("ROI信息", collapsed=True)
        self._roi_info_layout = QFormLayout()
        self._roi_info_layout.setContentsMargins(SPACING["SMALL"], SPACING["SMALL"],
                                                SPACING["SMALL"], SPACING["SMALL"])
        self._roi_info_layout.setSpacing(SPACING["SMALL"])
        
        # ROI位置和大小
        self._roi_x_label = QLabel("X坐标:")
        self._roi_x_spinbox = QSpinBox()
        self._roi_x_spinbox.setRange(0, 10000)
        self._roi_x_spinbox.setEnabled(False)
        self._roi_info_layout.addRow(self._roi_x_label, self._roi_x_spinbox)
        
        self._roi_y_label = QLabel("Y坐标:")
        self._roi_y_spinbox = QSpinBox()
        self._roi_y_spinbox.setRange(0, 10000)
        self._roi_y_spinbox.setEnabled(False)
        self._roi_info_layout.addRow(self._roi_y_label, self._roi_y_spinbox)
        
        self._roi_width_label = QLabel("宽度:")
        self._roi_width_spinbox = QSpinBox()
        self._roi_width_spinbox.setRange(0, 10000)
        self._roi_width_spinbox.setEnabled(False)
        self._roi_info_layout.addRow(self._roi_width_label, self._roi_width_spinbox)
        
        self._roi_height_label = QLabel("高度:")
        self._roi_height_spinbox = QSpinBox()
        self._roi_height_spinbox.setRange(0, 10000)
        self._roi_height_spinbox.setEnabled(False)
        self._roi_info_layout.addRow(self._roi_height_label, self._roi_height_spinbox)
        
        # 设置ROI按钮
        self._set_roi_button = QPushButton("设置ROI")
        self._set_roi_button.setEnabled(False)
        self._roi_info_layout.addRow("", self._set_roi_button)
        
        # 重置ROI按钮
        self._reset_roi_button = QPushButton("重置ROI")
        self._reset_roi_button.setEnabled(False)
        self._roi_info_layout.addRow("", self._reset_roi_button)
        
        self._roi_info_panel.add_layout(self._roi_info_layout)
        self._control_panel_layout.addWidget(self._roi_info_panel)
        
        # 设备信息面板
        self._device_info_panel = CollapsiblePanel("设备信息", collapsed=False)
        self._device_info_layout = QVBoxLayout()
        self._device_info_layout.setContentsMargins(SPACING["SMALL"], SPACING["SMALL"],
                                                   SPACING["SMALL"], SPACING["SMALL"])
        self._device_info_layout.setSpacing(SPACING["SMALL"])
        
        # 设备信息标签
        self._device_info_label = QLabel("未连接相机")
        self._device_info_label.setWordWrap(True)
        self._device_info_layout.addWidget(self._device_info_label)
        
        self._device_info_panel.add_layout(self._device_info_layout)
        self._control_panel_layout.addWidget(self._device_info_panel)
        
        # 添加弹簧
        self._control_panel_layout.addStretch()
        
        # 添加分割器部件
        self._main_splitter.addWidget(self._preview_widget)
        self._main_splitter.addWidget(self._control_panel)
        
        # 设置分割器初始大小比例 (左侧占70%)
        self._main_splitter.setSizes([700, 300])
        
        # 将分割器添加到主布局
        main_layout.addWidget(self._main_splitter)
        
        # 连接信号
        self._connect_signals()
    
    def _connect_signals(self):
        """连接UI信号到槽函数"""
        # 按钮信号
        self._connect_button.clicked.connect(self._on_connect_button_clicked)  # 连接按钮点击事件
        self._stream_button.clicked.connect(self._on_stream_button_clicked)    # 开始/停止视频流按钮点击事件
        self._capture_button.clicked.connect(self._on_capture_button_clicked)  # 拍照按钮点击事件
        self._roi_button.clicked.connect(self._on_roi_button_clicked)          # ROI按钮点击事件
        self._refresh_button.clicked.connect(self._on_refresh_button_clicked)  # 刷新相机列表按钮点击事件
        self._set_roi_button.clicked.connect(self._on_set_roi_button_clicked)  # 设置ROI按钮点击事件
        self._reset_roi_button.clicked.connect(self._on_reset_roi_button_clicked)   # 重置ROI按钮点击事件
        
        # 参数信号
        self._exposure_spinbox.valueChanged.connect(self._on_exposure_changed)   # 曝光时间改变事件
        self._gain_spinbox.valueChanged.connect(self._on_gain_changed)           # 增益改变事件
        self._trigger_mode_checkbox.stateChanged.connect(self._on_trigger_mode_changed)   # 触发模式改变事件
        
        # 图像查看器信号
        self._image_viewer.roi_selected.connect(self._on_viewer_roi_selected)   # ROI选择事件
    
    def update_device_info(self, info: Dict[str, Any]):
        """
        更新设备信息显示
        
        Args:
            info: 设备信息
        """
        if not info:
            self._device_info_label.setText("未连接相机")
            return
        
        # 构建信息文本
        info_text = ""
        for key, value in info.items():
            info_text += f"<b>{key}:</b> {value}<br>"
        
        self._device_info_label.setText(info_text)
    
    def show_error(self, error_msg: str):
        """
        显示错误信息
        
        Args:
            error_msg: 错误信息
        """
        self.logger.error(f"相机错误: {error_msg}")
        QMessageBox.critical(self, "相机错误", error_msg)
    
    def update_status(self, status: Dict[str, Any]):
        """
        更新相机状态
        
        Args:
            status: 相机状态信息
        """
        # 更新连接状态
        connected = status.get('connected', False)
        self.update_connection_status(connected)
        
        # 更新流式传输状态
        streaming = status.get('streaming', False)
        self.update_streaming_status(streaming)
        
        # 更新设备ID
        self._current_device_id = status.get('device_id', "")
        
        # 更新参数
        parameters = status.get('parameters', {})
        for param_name, value in parameters.items():
            self.update_parameter(param_name, value)
        
        # 更新FPS
        fps = status.get('fps', 0.0)
        self.update_fps(fps)
        
        # 更新ROI
        roi = status.get('roi', (0, 0, 0, 0))
        self.update_parameter('roi', roi)
        
        # 更新设备信息
        device_info = status.get('device_info', {})
        self.update_device_info(device_info)
        
    # --- 事件处理方法 ---
    def _on_connect_button_clicked(self):
        """连接/断开相机按钮点击事件"""
        if not self._is_connected:
            # 获取当前选择的相机ID
            if self._camera_combo.count() == 0:
                QMessageBox.warning(self, "警告", "没有可用的相机设备")
                return
            
            device_id = self._camera_combo.currentData()
            if not device_id:
                QMessageBox.warning(self, "警告", "请选择相机设备")
                return
            
            # 发送连接信号
            self.connect_camera_signal.emit(device_id)
        else:
            # 发送断开连接信号
            self.disconnect_camera_signal.emit()
    
    def _on_stream_button_clicked(self):
        """开始/停止视频流按钮点击事件"""
        if not self._is_streaming:
            # 发送开始流式传输信号
            self.start_streaming_signal.emit()
        else:
            # 发送停止流式传输信号
            self.stop_streaming_signal.emit()
    
    def _on_capture_button_clicked(self):
        """拍照按钮点击事件"""
        self.trigger_once_signal.emit()
    
    def _on_roi_button_clicked(self):
        """ROI选择按钮点击事件"""
        if self._roi_button.isChecked():
            # 启用ROI选择模式
            self._image_viewer.set_interaction_mode(InteractionMode.SELECT_ROI)
            self.logger.info("开始ROI选择模式")
        else:
            # 禁用ROI选择模式
            self._image_viewer.set_interaction_mode(InteractionMode.VIEW)
            self.logger.info("取消ROI选择模式")
    
    def _on_refresh_button_clicked(self):
        """刷新相机列表按钮点击事件"""
        self.event_signal.emit("refresh_camera_list", {})
    
    def _on_set_roi_button_clicked(self):
        """设置ROI按钮点击事件"""
        x = self._roi_x_spinbox.value()
        y = self._roi_y_spinbox.value()
        width = self._roi_width_spinbox.value()
        height = self._roi_height_spinbox.value()
        
        # 发送设置ROI信号
        self.set_roi_signal.emit(x, y, width, height)
    
    def _on_reset_roi_button_clicked(self):
        """重置ROI按钮点击事件"""
        self.reset_roi_signal.emit()
    
    def _on_exposure_changed(self, value):
        """曝光值变更事件"""
        if self._is_connected:
            self.set_parameter_signal.emit("exposure", value)
    
    def _on_gain_changed(self, value):
        """增益值变更事件"""
        if self._is_connected:
            self.set_parameter_signal.emit("gain", value)
    
    def _on_trigger_mode_changed(self, state):
        """触发模式变更事件"""
        if self._is_connected:
            self.set_parameter_signal.emit("trigger_mode", state == Qt.Checked)
    
    def _on_viewer_roi_selected(self, rect):
        """图像查看器ROI选择事件"""
        # 从QRectF中提取坐标和尺寸
        x = rect.x()
        y = rect.y()
        width = rect.width()
        height = rect.height()
        
        self.logger.info(f"ROI选择: x={x}, y={y}, width={width}, height={height}")
        
        # 更新ROI信息面板
        self._roi_x_spinbox.setValue(int(x))
        self._roi_y_spinbox.setValue(int(y))
        self._roi_width_spinbox.setValue(int(width))
        self._roi_height_spinbox.setValue(int(height))
        
        # 取消ROI选择模式
        self._roi_button.setChecked(False)
        self._image_viewer.set_interaction_mode(InteractionMode.VIEW)
    
    def _update_ui_timer(self):
        """UI更新定时器事件"""
        # 如果有新帧可用，刷新图像
        if self._current_frame is not None:
            current_time = time.time()
            elapsed = current_time - self._last_update_time
            
            # 限制刷新率，最多每30ms刷新一次 (约33fps)
            if elapsed >= 0.03:
                self._update_image_display()
                self._last_update_time = current_time
    
    def _update_image_display(self):
        """更新图像显示"""
        if self._current_frame is not None:
            self._image_viewer.setImage(self._current_frame)
    
    # --- 公共方法 ---
    def update_connection_status(self, connected: bool):
        """
        更新连接状态
        
        Args:
            connected: 是否已连接
        """
        self._is_connected = connected
        
        # 更新UI状态
        self._camera_combo.setEnabled(not connected)
        self._refresh_button.setEnabled(not connected)
        self._connect_button.setText("断开相机" if connected else "连接相机")
        self._stream_button.setEnabled(connected)
        self._capture_button.setEnabled(connected)
        self._exposure_spinbox.setEnabled(connected)
        self._gain_spinbox.setEnabled(connected)
        self._trigger_mode_checkbox.setEnabled(connected)
        self._roi_button.setEnabled(connected)
        self._exposure_spinbox.setEnabled(connected)
        self._gain_spinbox.setEnabled(connected)
        
        if not connected:
            # 断开连接时重置UI状态
            self.update_streaming_status(False)
            self._image_viewer.clear_all()
            self._device_info_label.setText("未连接相机")
    
    def update_streaming_status(self, streaming: bool):
        """
        更新流式传输状态
        
        Args:
            streaming: 是否正在流式传输
        """
        self._is_streaming = streaming
        
        # 更新UI状态
        if streaming:
            self._stream_button.setText("停止视频流")
            self._stream_button.setStyleSheet(f"""
                QPushButton {{ background-color: {LIGHT_COLORS["DANGER"]}; color: white; border: none; border-radius: 4px; padding: {SPACING["SMALL"]}px {SPACING["MEDIUM"]}px; }}
                QPushButton:hover {{ background-color: {LIGHT_COLORS["DANGER_LIGHT"]}; }}
                QPushButton:pressed {{ background-color: {LIGHT_COLORS["DANGER_DARK"]}; }}
            """)
            self._capture_button.setEnabled(False)
            self._trigger_mode_checkbox.setEnabled(False)
        else:
            self._stream_button.setText("开始视频流")
            self._stream_button.setStyleSheet(f"""
                QPushButton {{ background-color: {LIGHT_COLORS["SUCCESS"]}; color: white; border: none; border-radius: 4px; padding: {SPACING["SMALL"]}px {SPACING["MEDIUM"]}px; }}
                QPushButton:hover {{ background-color: {LIGHT_COLORS["SUCCESS_LIGHT"]}; }}
                QPushButton:pressed {{ background-color: {LIGHT_COLORS["SUCCESS_DARK"]}; }}
            """)
            self._capture_button.setEnabled(True)
            self._trigger_mode_checkbox.setEnabled(True)
    
    def update_frame(self, frame: np.ndarray):
        """
        更新图像帧
        
        Args:
            frame: 图像帧数据
        """
        if frame is not None:
            self._current_frame = frame.copy()
    
    def update_parameter(self, param_name: str, value: Any):
        """
        更新参数显示
        
        Args:
            param_name: 参数名称
            value: 参数值
        """
        if param_name == "exposure":
            self._exposure_spinbox.blockSignals(True)
            self._exposure_spinbox.setValue(float(value))
            self._exposure_spinbox.blockSignals(False)
        elif param_name == "gain":
            self._gain_spinbox.blockSignals(True)
            self._gain_spinbox.setValue(float(value))
            self._gain_spinbox.blockSignals(False)
        elif param_name == "trigger_mode":
            self._trigger_mode_checkbox.blockSignals(True)
            self._trigger_mode_checkbox.setChecked(bool(value))
            self._trigger_mode_checkbox.blockSignals(False)
        elif param_name == "roi":
            x, y, width, height = value
            self._roi_x_spinbox.blockSignals(True)
            self._roi_y_spinbox.blockSignals(True)
            self._roi_width_spinbox.blockSignals(True)
            self._roi_height_spinbox.blockSignals(True)
            
            self._roi_x_spinbox.setValue(int(x))
            self._roi_y_spinbox.setValue(int(y))
            self._roi_width_spinbox.setValue(int(width))
            self._roi_height_spinbox.setValue(int(height))
            
            self._roi_x_spinbox.blockSignals(False)
            self._roi_y_spinbox.blockSignals(False)
            self._roi_width_spinbox.blockSignals(False)
            self._roi_height_spinbox.blockSignals(False)
    
    def update_camera_list(self, devices: List[Dict[str, Any]]):
        """
        更新相机设备列表
        
        Args:
            devices: 相机设备列表
        """
        self._available_devices = devices
        
        # 清空列表
        self._camera_combo.clear()
        
        # 添加设备
        for device in devices:
            device_id = device.get("id", "")
            device_name = device.get("name", "未知设备")
            display_text = f"{device_name} ({device_id})"
            self._camera_combo.addItem(display_text, device_id)
    
    def update_fps(self, fps: float):
        """
        更新FPS显示
        
        Args:
            fps: 当前FPS值
        """
        self._current_fps = fps
        self._fps_label.setText(f"FPS: {fps:.1f}")
