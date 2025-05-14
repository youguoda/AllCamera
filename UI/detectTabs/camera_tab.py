"""
@Author: youda
@File: camera_tab.py
@Date: 2025/4/1
@Time: 17:29
@Description: 
"""
# camera.py
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
相机控制应用
"""

import os
import sys
import time
import traceback
import cv2
import numpy as np
import threading

from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QImage, QIcon, QPixmap
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLabel, QPushButton, QComboBox, QSlider, QSpinBox,
                             QCheckBox, QSplitter, QMainWindow, QApplication,
                             QMessageBox)


# 如有必要，添加项目根目录（根据需要调整路径）
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')) # Example: Adjust '..' count
if project_root not in sys.path:
    sys.path.append(project_root)
    print(f"Appended to sys.path: {project_root}")

try:
    # 用户界面实用工具和部件
    from UI.utils.ui_constants import LIGHT_COLORS, SPACING
    from UI.widgets.enhanced_image_viewer import ImageViewerWidget, InteractionMode
    from UI.widgets.collapsible_panel import CollapsiblePanel

    # 核心组件
    from core.camera.camera_factory import CameraFactoryManager
    # 确保在注册需要时导入特定的工厂
    from core.camera.hikvision_camera_factory import HikvisionCameraFactory
    from core.utils.signal_manager import signal_manager
    from core.utils.logger import get_logger

except ImportError as e:
    print(f"Import Error: {e}")
    print("Current sys.path:", sys.path)
    sys.exit(1)



# Get logger instance 获取日志记录器实例
logger = get_logger()

# --- Main Application Class 主应用程序类 ---
class CameraTabWidget(QMainWindow):
    """
    相机控制主窗口

    """

    camera_status_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        """初始化相机控制主窗口"""
        super().__init__(parent)

        # --- 状态变量（来自相机逻辑） ---
        self.camera = None           # 相机对象
        self.is_running = False      # 是否正在运行
        self.current_frame = None    # 当前帧
        self.camera_id = "未知"      # 相机 ID，将在连接时更新
        self.available_devices = []  # 可用的相机设备列表
        self.use_simulation = False  # 默认不使用模拟
        self._camera_connected = False   # 对应相机是否连接

        # 线程与帧率
        self.frame_lock = threading.Lock()       # 用于多线程处理图像帧的锁
        self.new_frame_available = False        # 新帧是否可用标志
        self.fps_count = 0                     # 帧率计数器
        self.last_fps_time = time.time()       # 上次计算帧率的时间
        self.display_fps = 0.0                  # 显示帧率

        # 设置窗口标题和默认大小
        self.setWindowTitle("相机控制")
        self.resize(1200, 800) # Default size

        # --- 构建用户界面 ---
        self._init_ui() # 调用用户界面设置方法

        # --- 连接信号（将用户界面元素与控制逻辑相连） ---
        self._connect_signals_to_logic() # 将用户界面小部件连接到控制方法
        # --- 连接相机核心信号 ---
        self._connect_core_signals()

        # --- 初始化相机逻辑 ---
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_display_and_fps) # 更新图像显示和计算 FPS
        self.timer.start(30)  # 约30帧/秒的显示刷新率

        # 稍微推迟相机的初始化，以便让用户界面能够显示出来(100 毫秒之后，initialize_camera_core 方法会被自动调用)
        QTimer.singleShot(100, self.initialize_camera_core)

        # 更新用户界面状态
        self._update_ui_state()

    def _init_ui(self):
        """
        初始化用户界面 
        设置了 QMainWindow 的中心部件
        """
        # 主容器部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # 中央部件的主布局
        self._main_layout = QVBoxLayout(main_widget)
        self._main_layout.setContentsMargins(SPACING["MEDIUM"], SPACING["MEDIUM"],
                                           SPACING["MEDIUM"], SPACING["MEDIUM"])
        self._main_layout.setSpacing(SPACING["MEDIUM"])

        # --- 用于预览和控制面板的分割器 ---
        self._main_splitter = QSplitter(Qt.Horizontal)
        self._main_splitter.setChildrenCollapsible(False)

        # --- 左侧: 预览区域 ---
        self._preview_widget = QWidget()
        self._preview_layout = QVBoxLayout(self._preview_widget)
        self._preview_layout.setContentsMargins(0, 0, 0, 0)
        self._preview_layout.setSpacing(SPACING["SMALL"]) # 添加工具栏和查看器之间的间距

        # --- 工具栏 ---
        self._toolbar = QWidget()
        self._toolbar_layout = QHBoxLayout(self._toolbar)
        self._toolbar_layout.setContentsMargins(0, 0, 0, 0)
        self._toolbar_layout.setSpacing(SPACING["SMALL"]) # 按钮之间的间距

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
        self._stream_button.setIcon(QIcon("./UI/resources/icons/PlayButton.png")) 
        self._stream_button.setEnabled(False)
        self._stream_button.setStyleSheet(f"""
            QPushButton {{ background-color: {LIGHT_COLORS["SUCCESS"]}; color: white; border: none; border-radius: 4px; padding: {SPACING["SMALL"]}px {SPACING["MEDIUM"]}px; }}
            QPushButton:hover {{ background-color: {LIGHT_COLORS["SUCCESS"]}; }}
            QPushButton:pressed {{ background-color: {LIGHT_COLORS["SUCCESS"]}; }}
            QPushButton:disabled {{ background-color: {LIGHT_COLORS["DISABLED"]}; color: {LIGHT_COLORS["TEXT_DISABLED"]}; }}
        """)
        self._toolbar_layout.addWidget(self._stream_button)

        # 拍照 (软触发) 按钮
        self._capture_button = QPushButton("拍照 (软触发)")
        self._capture_button.setIcon(QIcon("./UI/resources/icons/camera.png")) 
        self._capture_button.setEnabled(False)
        self._capture_button.setStyleSheet(f"""
            QPushButton {{ background-color: {LIGHT_COLORS["INFO"]}; color: white; border: none; border-radius: 4px; padding: {SPACING["SMALL"]}px {SPACING["MEDIUM"]}px; }}
            QPushButton:hover {{ background-color: {LIGHT_COLORS["INFO"]}; }}
            QPushButton:pressed {{ background-color: {LIGHT_COLORS["INFO"]}; }}
            QPushButton:disabled {{ background-color: {LIGHT_COLORS["DISABLED"]}; color: {LIGHT_COLORS["TEXT_DISABLED"]}; }}
        """)
        self._toolbar_layout.addWidget(self._capture_button)

        # ROI 选择按钮
        self._roi_button = QPushButton("选择ROI")
        self._roi_button.setCheckable(True)
        self._roi_button.setEnabled(False)
        self._roi_button.setStyleSheet(f"""
            QPushButton {{ background-color: {LIGHT_COLORS["WARNING"]}; color: white; border: none; border-radius: 4px; padding: {SPACING["SMALL"]}px {SPACING["MEDIUM"]}px; }}
            QPushButton:hover {{ background-color: {LIGHT_COLORS["WARNING"]}; }}
            QPushButton:pressed, QPushButton:checked {{ background-color: {LIGHT_COLORS["WARNING"]}; }}
            QPushButton:disabled {{ background-color: {LIGHT_COLORS["DISABLED"]}; color: {LIGHT_COLORS["TEXT_DISABLED"]}; }}
        """)
        self._toolbar_layout.addWidget(self._roi_button)

        self._toolbar_layout.addStretch()

        # FPS Label  - 为查看器创建一个容器 + 覆盖查看器上面
        self._viewer_container = QWidget()
        self._viewer_container_layout = QVBoxLayout(self._viewer_container)
        self._viewer_container_layout.setContentsMargins(0, 0, 0, 0)
        self._viewer_container_layout.setSpacing(0)

        # Image Viewer
        self._image_viewer = ImageViewerWidget()
        self._image_viewer.setMinimumSize(640, 480) # Ensure minimum size
        self._viewer_container_layout.addWidget(self._image_viewer)

        # FPS标签位于容器内右上角
        self._fps_label = QLabel("FPS: 0.0")
        self._fps_label.setStyleSheet("background-color: rgba(0, 0, 0, 0.5); color: lightgreen; font-size: 14px; padding: 2px 5px; border-radius: 3px;")
        self._fps_label.setAlignment(Qt.AlignRight | Qt.AlignTop)
        self._fps_label.setFixedSize(100, 25) # 调整大小
        self._fps_label.setParent(self._viewer_container) # 将其作为定位的子元素
        # Move it to the top-right corner manually (adjust margins as needed)   
        self._fps_label.move(self._viewer_container.width() - self._fps_label.width() - 5, 5)
        # 确保在调整大小时它能保持在原位置。
        self._viewer_container.resizeEvent = self._on_viewer_resize


        # Add Toolbar and Viewer Container to Preview Layout
        self._preview_layout.addWidget(self._toolbar)
        self._preview_layout.addWidget(self._viewer_container, 1) # Viewer takes available space

        # --- 右侧控制面板 ---
        self._control_widget = QWidget()
        self._control_layout = QVBoxLayout(self._control_widget)
        self._control_layout.setContentsMargins(SPACING["SMALL"], 0, 0, 0) # 添加左边距
        
        self._control_widget.setMinimumWidth(450)  # 设置右侧控制面板最小宽度
        self._control_layout.setSpacing(SPACING["MEDIUM"])

        # --- 1. 相机列表面板 ---
        self._camera_list_panel = CollapsiblePanel("相机连接与选择", self)
        camera_list_content = QWidget()
        self._camera_list_layout = QVBoxLayout(camera_list_content)
        self._camera_list_layout.setSpacing(SPACING["SMALL"])

        # Camera Selection ComboBox
        self._camera_combo = QComboBox()
        self._camera_combo.addItem("自动选择") # Default option
        self._camera_list_layout.addWidget(QLabel("选择设备:"))
        self._camera_list_layout.addWidget(self._camera_combo)

        # Simulation Mode Checkbox
        self._simulation_check = QCheckBox("使用模拟模式")
        self._simulation_check.setChecked(self.use_simulation)
        self._camera_list_layout.addWidget(self._simulation_check)

        # Refresh Button
        self._refresh_button = QPushButton("刷新列表")
        self._refresh_button.setStyleSheet(f"""
            QPushButton {{ background-color: {LIGHT_COLORS["SECONDARY"]}; color: white; border: none; border-radius: 4px; padding: {SPACING["SMALL"]}px {SPACING["MEDIUM"]}px; }}
            QPushButton:hover {{ background-color: {LIGHT_COLORS["SECONDARY_LIGHT"]}; }}
            QPushButton:pressed {{ background-color: {LIGHT_COLORS["SECONDARY_DARK"]}; }}
        """)
        self._camera_list_layout.addWidget(self._refresh_button)

        self._camera_list_panel.add_widget(camera_list_content)

        # --- 2. 相机参数面板 ---
        self._camera_params_panel = CollapsiblePanel("相机参数", self)
        camera_params_content = QWidget()
        self._camera_params_layout = QGridLayout(camera_params_content)
        self._camera_params_layout.setSpacing(SPACING["SMALL"])

        # Exposure Time
        self._camera_params_layout.addWidget(QLabel("曝光时间 (μs):"), 0, 0)
        self._exposure_slider = QSlider(Qt.Horizontal)
        self._exposure_slider.setRange(10, 100000) # Adjusted range
        self._exposure_slider.setValue(10000)
        self._exposure_slider.setEnabled(False)
        self._camera_params_layout.addWidget(self._exposure_slider, 0, 1)
        self._exposure_value_label = QLabel("10000 μs") # Label to show value
        self._camera_params_layout.addWidget(self._exposure_value_label, 0, 2)
        self._auto_exposure_check = QCheckBox("自动")
        self._auto_exposure_check.setEnabled(False) # Check if camera supports this
        self._camera_params_layout.addWidget(self._auto_exposure_check, 0, 3)


        # Gain
        self._camera_params_layout.addWidget(QLabel("增益 (dB):"), 1, 0)
        self._gain_slider = QSlider(Qt.Horizontal)
        self._gain_slider.setRange(0, 20) # Adjusted range (typical for dB)
        self._gain_slider.setValue(0)
        self._gain_slider.setEnabled(False)
        self._camera_params_layout.addWidget(self._gain_slider, 1, 1)
        self._gain_value_label = QLabel("0 dB") # Label to show value
        self._camera_params_layout.addWidget(self._gain_value_label, 1, 2)
        self._auto_gain_check = QCheckBox("自动")
        self._auto_gain_check.setEnabled(False) # Check if camera supports this
        self._camera_params_layout.addWidget(self._auto_gain_check, 1, 3)

        # White Balance (Example - Check if camera supports)
        self._camera_params_layout.addWidget(QLabel("白平衡 (K):"), 2, 0)
        self._wb_slider = QSlider(Qt.Horizontal)
        self._wb_slider.setRange(2000, 8000)
        self._wb_slider.setValue(5000)
        self._wb_slider.setEnabled(False) # Enable if supported
        self._camera_params_layout.addWidget(self._wb_slider, 2, 1)
        self._wb_value_label = QLabel("5000 K")
        self._camera_params_layout.addWidget(self._wb_value_label, 2, 2)
        self._auto_wb_check = QCheckBox("自动")
        self._auto_wb_check.setEnabled(False) # Enable if supported
        self._camera_params_layout.addWidget(self._auto_wb_check, 2, 3)

        # Apply Parameters Button (Moved from separate group)
        self._apply_params_btn = QPushButton("应用参数")
        self._apply_params_btn.setEnabled(False)
        self._camera_params_layout.addWidget(self._apply_params_btn, 3, 0, 1, 4) # Span across columns


        self._camera_params_panel.add_widget(camera_params_content)


        # -- 3. 图像设置面板 --
        self._image_settings_panel = CollapsiblePanel("图像与触发", self)
        image_settings_content = QWidget()
        self._image_settings_layout = QGridLayout(image_settings_content)
        self._image_settings_layout.setSpacing(SPACING["SMALL"])

        # Resolution (Enable if camera supports changing it)
        self._image_settings_layout.addWidget(QLabel("分辨率:"), 0, 0)
        self._resolution_combo = QComboBox()
        self._resolution_combo.addItems(["(当前)", "1920x1080", "1280x720", "640x480"]) # Example
        self._resolution_combo.setEnabled(False) # Enable if supported
        self._image_settings_layout.addWidget(self._resolution_combo, 0, 1)

        # Frame Rate
        self._image_settings_layout.addWidget(QLabel("帧率 (目标):"), 1, 0)
        self._fps_spin = QSpinBox() # Using SpinBox as per UI.py
        self._fps_spin.setRange(1, 200) # Range from camera logic
        self._fps_spin.setValue(30)
        self._fps_spin.setEnabled(False)
        self._image_settings_layout.addWidget(self._fps_spin, 1, 1)
        # Apply button is now in the params panel, applies FPS too

        # Pixel Format (Enable if camera supports changing it)
        self._image_settings_layout.addWidget(QLabel("像素格式:"), 2, 0)
        self._pixel_format_combo = QComboBox()
        self._pixel_format_combo.addItems(["(当前)", "Mono8", "BayerRG8", "RGB8"]) # Example
        self._pixel_format_combo.setEnabled(False) # Enable if supported
        self._image_settings_layout.addWidget(self._pixel_format_combo, 2, 1)

        # Trigger Mode (Moved here from camera logic UI)
        self._image_settings_layout.addWidget(QLabel("触发模式:"), 3, 0)
        self._trigger_combo = QComboBox()
        self._trigger_combo.addItems(["连续采集", "软触发", "硬触发"])
        self._trigger_combo.setEnabled(False)
        self._image_settings_layout.addWidget(self._trigger_combo, 3, 1)

        self._image_settings_panel.add_widget(image_settings_content)

        # -- 4. 状态信息面板 --
        self._status_panel = CollapsiblePanel("状态信息", self)
        status_content = QWidget()
        self._status_layout = QVBoxLayout(status_content)

        # Status Label (from camera logic)
        self._status_label = QLabel("就绪")
        self._status_label.setWordWrap(True)
        self._status_layout.addWidget(self._status_label)

        # Camera Info Label (placeholder for detailed info)
        self._camera_info_label = QLabel("相机信息：未连接")
        self._camera_info_label.setWordWrap(True)
        self._status_layout.addWidget(self._camera_info_label)

        self._status_panel.add_widget(status_content)
        self._status_panel.set_expanded(True) # Keep status expanded by default


        # Add panels to control layout
        self._control_layout.addWidget(self._camera_list_panel)
        self._control_layout.addWidget(self._camera_params_panel)
        self._control_layout.addWidget(self._image_settings_panel)
        self._control_layout.addWidget(self._status_panel)
        self._control_layout.addStretch()

        # Add widgets to splitter
        self._main_splitter.addWidget(self._preview_widget)
        self._main_splitter.addWidget(self._control_widget)

        # Set splitter sizes (adjust ratio as needed)
        self._main_splitter.setSizes([700, 400])

        # Add splitter to main layout
        self._main_layout.addWidget(self._main_splitter)

        # Set initial UI state (controls disabled)
        self._update_ui_state()

    def _on_viewer_resize(self, event):
        """当图像查看器容器大小改变时，重新计算并移动 FPS 标签到右上角"""
        # Default resize event handler
        QWidget.resizeEvent(self._viewer_container, event)
        # Reposition FPS label
        if hasattr(self, '_fps_label'):
            margin = 5
            self._fps_label.move(self._viewer_container.width() - self._fps_label.width() - margin, margin)


    def _connect_signals_to_logic(self):
        """将用户界面元素的信号连接到相机控制逻辑方法上。"""
        # 连接控制
        self._refresh_button.clicked.connect(self.refresh_devices)
        self._connect_button.clicked.connect(self.toggle_connection)
        self._simulation_check.stateChanged.connect(self.toggle_simulation_mode)
        self._camera_combo.currentIndexChanged.connect(self._on_camera_selection_change) # May not be needed if using button

        # 视频流与拍照控制
        self._stream_button.clicked.connect(self.toggle_stream) # Combined start/stop method
        self._capture_button.clicked.connect(self.trigger_once) # Map capture to soft trigger

        # ROI Control
        self._roi_button.clicked.connect(self._on_roi_button_toggled)
        self._image_viewer.get_viewer().roi_selected.connect(self._on_roi_selected_from_viewer)

        # Parameter Controls
        self._exposure_slider.valueChanged.connect(self._on_exposure_slider_changed)
        self._gain_slider.valueChanged.connect(self._on_gain_slider_changed)
        self._wb_slider.valueChanged.connect(self._on_wb_slider_changed) # Assuming WB is used
        # TODO: 连接自动复选框，如果在相机核心实现
        self._auto_exposure_check.stateChanged.connect(self._on_auto_exposure_changed)
        self._auto_gain_check.stateChanged.connect(self._on_auto_gain_changed)
        self._auto_wb_check.stateChanged.connect(self._on_auto_wb_changed)

        self._apply_params_btn.clicked.connect(self.apply_parameters)

        # 图像/触发设置控件
        self._fps_spin.valueChanged.connect(self._on_fps_spin_changed) # Update target FPS
        self._trigger_combo.currentIndexChanged.connect(self.change_trigger_mode)
        # TODO: 连接分辨率和像素格式组合（如果实现的话）

    def _connect_core_signals(self):
        """Connect signals from the camera core (signal_manager)."""
        try:
            signal_manager.frame_ready_signal.connect(self.handle_frame)
        except AttributeError:
            self.show_error("Signal Manager not configured correctly.")
            logger.warning("signal_manager or frame_ready_signal not found.")
        except Exception as e:
             self.show_error(f"Error connecting core signals: {e}")
             logger.error(f"Error connecting core signals: {e}", exc_info=True)


    # --- 用户界面更新与状态管理 ---

    def _update_ui_state(self):
        """根据相机状态更新用户界面元素的启用/禁用状态和文本。"""
        connected = self._camera_connected
        streaming = self.is_running

        # 连接控制
        self._connect_button.setText("断开相机" if connected else "连接相机")
        self._connect_button.setStyleSheet( # 根据状态更新样式
             f"""
            QPushButton {{ background-color: {LIGHT_COLORS["DANGER"] if connected else LIGHT_COLORS["PRIMARY"]}; color: white; border: none; border-radius: 4px; padding: {SPACING["SMALL"]}px {SPACING["MEDIUM"]}px; }}
            QPushButton:hover {{ background-color: {LIGHT_COLORS["DANGER"] if connected else LIGHT_COLORS["PRIMARY"]}; }}
            QPushButton:pressed {{ background-color: {LIGHT_COLORS["DANGER"] if connected else LIGHT_COLORS["PRIMARY"]}; }}
            QPushButton:disabled {{ background-color: {LIGHT_COLORS["DISABLED"]}; color: {LIGHT_COLORS["TEXT_DISABLED"]}; }}
            """
        )
        self._camera_combo.setEnabled(not connected)
        self._refresh_button.setEnabled(not connected)
        self._simulation_check.setEnabled(not connected)


        # 流传输/拍照控制
        self._stream_button.setEnabled(connected)
        self._stream_button.setText("停止视频流" if streaming else "开始视频流")
        self._stream_button.setIcon(QIcon("./UI/resources/icons/Stop-Button.png") if streaming else QIcon("./UI/resources/icons/PlayButton.png"))
        self._stream_button.setStyleSheet( # 基于状态更新样式
            f"""
            QPushButton {{ background-color: {LIGHT_COLORS["DANGER"] if streaming else LIGHT_COLORS["SUCCESS"]}; color: white; border: none; border-radius: 4px; padding: {SPACING["SMALL"]}px {SPACING["MEDIUM"]}px; }}
            QPushButton:hover {{ background-color: {LIGHT_COLORS["DANGER"] if streaming else LIGHT_COLORS["SUCCESS"]}; }}
            QPushButton:pressed {{ background-color: {LIGHT_COLORS["DANGER"] if streaming else LIGHT_COLORS["SUCCESS"]}; }}
            QPushButton:disabled {{ background-color: {LIGHT_COLORS["DISABLED"]}; color: {LIGHT_COLORS["TEXT_DISABLED"]}; }}
            """
        )

        # 仅当已连接、正在流式传输且处于触发模式时，捕获（触发）按钮才启用
        trigger_mode_index = self._trigger_combo.currentIndex()
        can_trigger = connected and streaming and trigger_mode_index > 0 # 仅用于软/硬触发
        self._capture_button.setEnabled(can_trigger)


        # ROI 按钮
        self._roi_button.setEnabled(connected and self._image_viewer.get_viewer().pixmap() is not None) # Enable if image is shown
        if not self._roi_button.isEnabled() and self._roi_button.isChecked():
            self._roi_button.setChecked(False) # Uncheck if disabled
            self._image_viewer.get_viewer().set_interaction_mode(InteractionMode.VIEW)

        # 参数控制
        manual_params_enabled = connected and not streaming # Params usually set when not streaming
        self._exposure_slider.setEnabled(manual_params_enabled and not self._auto_exposure_check.isChecked())
        self._gain_slider.setEnabled(manual_params_enabled and not self._auto_gain_check.isChecked())
        self._wb_slider.setEnabled(manual_params_enabled and not self._auto_wb_check.isChecked()) # Assuming WB supported
        self._fps_spin.setEnabled(manual_params_enabled) # Allow setting target FPS when stopped
        self._apply_params_btn.setEnabled(manual_params_enabled)

        self._auto_exposure_check.setEnabled(manual_params_enabled) # Assuming auto modes supported
        self._auto_gain_check.setEnabled(manual_params_enabled)
        self._auto_wb_check.setEnabled(manual_params_enabled)

        # 图像/触发设置
        # 分辨率/像素格式通常在未连接或未流式传输时设置
        can_change_img_settings = connected and not streaming
        self._resolution_combo.setEnabled(False) # 现在禁用，如果实现则启用
        self._pixel_format_combo.setEnabled(False) # 现在禁用，如果实现则启用
        self._trigger_combo.setEnabled(connected) # 可以在连接时更改触发模式

    def _on_camera_selection_change(self, index):
        """Handle manual camera selection if needed."""
        # Currently, connection logic uses the combo box value when 'Connect' is clicked.
        # This slot could be used for immediate actions if required in the future.
        pass

    def _on_roi_button_toggled(self, checked):
        """Handle ROI button click."""
        if checked:
            self._image_viewer.get_viewer().set_interaction_mode(InteractionMode.SELECT_ROI)
            self.log_status("ROI选择模式：在图像上拖动以选择区域。")
        else:
            self._image_viewer.get_viewer().set_interaction_mode(InteractionMode.VIEW)
            # Status log removed here, selection confirmed in _on_roi_selected_from_viewer

    def _on_roi_selected_from_viewer(self, rect):
        """Handle ROI selection confirmed from the viewer."""
        # 自动取消选中该按钮并切换回查看模式
        self._roi_button.setChecked(False)
        self._image_viewer.get_viewer().set_interaction_mode(InteractionMode.VIEW)

        # Process the selected ROI (e.g., send to camera if supported)
        x, y, w, h = int(rect.x()), int(rect.y()), int(rect.width()), int(rect.height())
        self.log_status(f"选择ROI: x={x}, y={y}, w={w}, h={h} (应用ROI需相机支持)")
        # 添加调用self.camera.set_roi(x, y, w, h)的逻辑
        self.camera.set_roi(x, y, w, h)

    def _on_exposure_slider_changed(self, value):
        self._exposure_value_label.setText(f"{value} μs")
    def _on_gain_slider_changed(self, value):
        # 假设滑块范围0 - 20直接映射到dB
        self._gain_value_label.setText(f"{value} dB")
    def _on_wb_slider_changed(self, value):
        self._wb_value_label.setText(f"{value} K")

    def _on_auto_exposure_changed(self, state):
        is_checked = (state == Qt.Checked)
        self._exposure_slider.setEnabled(not is_checked and self._camera_connected and not self.is_running)
        # TODO:如果支持，调用相机方法来设置自动曝光
        # if self.camera and self.camera.is_open():
        #     self.camera.set_parameter(auto_exposure=is_checked) # Example
        self.log_status(f"自动曝光: {'启用' if is_checked else '禁用'} (需应用参数)")


    def _on_auto_gain_changed(self, state):
        is_checked = (state == Qt.Checked)
        self._gain_slider.setEnabled(not is_checked and self._camera_connected and not self.is_running)
        # TODO: 如果支持，调用相机方法来设置自动增益
        self.log_status(f"自动增益: {'启用' if is_checked else '禁用'} (需应用参数)")

    def _on_auto_wb_changed(self, state):
        is_checked = (state == Qt.Checked)
        self._wb_slider.setEnabled(not is_checked and self._camera_connected and not self.is_running)
         # TODO: 如果支持，调用相机方法来设置自动白平衡
        self.log_status(f"自动白平衡: {'启用' if is_checked else '禁用'} (需应用参数)")


    def _on_fps_spin_changed(self, value):
        """Log target FPS change."""
        # Actual application happens via "Apply Parameters" or potentially when starting stream
        self.log_status(f"目标帧率设置为: {value} FPS (需应用参数或重启流)")


    # --- Camera Core Logic Methods (Adapted from camera.py test script) ---

    def initialize_camera_core(self):
        """初始化相机工厂并为设备列表做准备。"""
        try:
            available_types = CameraFactoryManager.get_available_types()
            print(f"可用相机类型: {available_types}")
            if not available_types:
                 self.show_error("未找到相机工厂类。请确保相机库和工厂已正确安装/注册。")
                 self.log_status("错误：未找到相机驱动或工厂。")
                 return False

            #如果有“hikvision”，则优先选择它，否则选择第一个。
            cam_type = "hikvision" if "hikvision" in available_types else available_types[0]
            logger.info(f"Attempting to create camera of type: {cam_type}")

            self.camera = CameraFactoryManager.create_camera(cam_type)
            if self.camera is None:
                self.show_error(f"创建相机实例失败 (类型: {cam_type})")
                self.log_status(f"错误：创建相机实例失败 ({cam_type})")
                return False

            # 设置初始模拟状态
            self.camera._is_simulation = self.use_simulation

            self.log_status("相机核心初始化成功。请刷新设备列表或连接相机。")
            self.refresh_devices() # 尝试立即列出设备
            return True
        except Exception as e:
            self.show_error(f"初始化相机核心失败: {e}")
            self.log_status(f"错误：初始化相机核心失败: {e}")
            logger.error(f"Camera core initialization failed: {e}", exc_info=True)
            return False

    def refresh_devices(self):
        """Refreshes the list of available camera devices."""
        if self.camera is None:
            if not self.initialize_camera_core(): # Try to init if not already
                 self.show_error("无法刷新：相机核心未初始化。")
                 return

        try:
            # 确保模拟模式是最新的
            self.camera._is_simulation = self.use_simulation

            self.log_status("正在枚举设备...")
            QApplication.processEvents() # Allow UI update

            self.available_devices = self.camera.enumerate_devices()

            self._camera_combo.clear()
            self._camera_combo.addItem("自动选择")
            target_device_index = -1 # Index in the combo box (0 = auto)

            if self.available_devices:
                for i, device in enumerate(self.available_devices):
                    model_name = device.get('model_name', '未知型号')
                    serial_number = device.get('serial_number', '未知SN')
                    device_id = device.get('device_id', f'索引{i}') # Use index as fallback ID
                    device_ip = device.get('device_ip') # Might be None for non-GigE

                    # Build display string
                    display_text = f"[{device_id}] {model_name} (SN:{serial_number})"
                    if device_ip:
                        display_text += f" - {device_ip}"

                    # Check for target model (case-insensitive)
                    is_target = "MV-CI003-GL-N6" in model_name.upper() # Example target

                    if is_target:
                        display_text += " [目标相机]"
                        if target_device_index == -1: # Select the first target found
                            target_device_index = i + 1 # +1 because index 0 is "自动选择"

                    self._camera_combo.addItem(display_text, userData=device_id) # Store device_id as userData

                # Auto-select the target model if found
                if target_device_index != -1:
                    self._camera_combo.setCurrentIndex(target_device_index)
                    self.log_status(f"找到 {len(self.available_devices)} 个设备。已自动选择目标相机。")
                else:
                     self.log_status(f"找到 {len(self.available_devices)} 个设备。")

            else:
                if self.use_simulation:
                    self.log_status("未找到真实相机，将使用模拟模式（如果启用）。")
                    # Add a simulation entry if none found
                    self._camera_combo.addItem("[模拟设备]", userData="simulation_id")
                else:
                    self.log_status("未找到相机设备。请检查连接或启用模拟模式。")

        except Exception as e:
            self.show_error(f"刷新设备列表失败: {e}")
            self.log_status(f"错误：刷新设备列表失败: {e}")
            logger.error(f"Failed to refresh device list: {e}", exc_info=True)

        self._update_ui_state() # Refresh UI state after listing

    def toggle_simulation_mode(self):
        """Toggles the simulation mode on/off."""
        self.use_simulation = self._simulation_check.isChecked()
        if self.camera:
            self.camera._is_simulation = self.use_simulation
            self.log_status(f"模拟模式: {'启用' if self.use_simulation else '禁用'}。请刷新设备列表。")
            # Re-list devices after changing simulation mode
            QTimer.singleShot(50, self.refresh_devices) # Refresh shortly after
        else:
            self.log_status(f"模拟模式: {'启用' if self.use_simulation else '禁用'}。")

        self._update_ui_state()

    def toggle_connection(self):
        """连接到选定的相机或断开当前相机的连接。"""
        if self.camera is None:
            self.show_error("相机核心未初始化。")
            return

        if self._camera_connected: # --- Disconnect ---
            try:
                if self.is_running:
                    self.stop_grabbing() # Stop grabbing before closing

                if self.camera.close():
                    self.log_status("相机已断开")
                    self._camera_connected = False
                    self.camera_id = "未知"
                    self._image_viewer.set_image(None) # Clear image
                    self._camera_info_label.setText("相机信息：未连接")
                else:
                    self.show_error("断开相机失败 (相机报告失败)")
                    # Force state update even on failure?
                    self._camera_connected = False # Assume disconnected if close fails
                    self.camera_id = "未知"

            except Exception as e:
                self.show_error(f"断开相机时发生错误: {e}")
                logger.error(f"Error disconnecting camera: {e}", exc_info=True)
                self._camera_connected = False # Assume disconnected on error
                self.camera_id = "未知"

        else: # --- Connect ---
            device_id_to_connect = None
            selected_index = self._camera_combo.currentIndex()

            if selected_index > 0: # An actual device is selected
                device_id_to_connect = self._camera_combo.itemData(selected_index)
                # Fallback if userData wasn't set correctly
                if not device_id_to_connect:
                    device_info = self._camera_combo.currentText()
                    try:
                        # 提取方括号中的设备ID
                        start_pos = device_info.find('[') + 1
                        end_pos = device_info.find(']')
                        if 0 < start_pos < end_pos:
                           device_id_to_connect = device_info[start_pos:end_pos]
                           logger.warning(f"从设备信息中提取到设备ID: {device_id_to_connect}")
                    except Exception as e:
                        logger.error(f"Could not parse device ID from text: {device_info} - {e}")
                        self.show_error(f"无法解析设备ID: {device_info}")
                        return

            elif selected_index == 0 and not self.available_devices and self.use_simulation:
                 # Special case: Auto-select + No real devices + Simulation enabled
                 device_id_to_connect = "simulation_id" # Use a placeholder ID for simulation
                 self.log_status("自动选择：使用模拟设备。")

            elif selected_index == 0 and self.available_devices:
                 # Auto-select: Prefer target, else first device
                 target_idx = -1
                 for i in range(len(self.available_devices)):
                     model = self.available_devices[i].get('model_name', '').upper()
                     if "MV-CI003-GL-N6" in model: # Example Target
                         target_idx = i
                         break
                 if target_idx != -1:
                     device_id_to_connect = self.available_devices[target_idx].get('device_id')
                     self.log_status(f"自动选择：连接到目标设备 {device_id_to_connect}")
                 else:
                      device_id_to_connect = self.available_devices[0].get('device_id')
                      self.log_status(f"自动选择：连接到第一个设备 {device_id_to_connect}")

            elif selected_index == 0 and not self.available_devices and not self.use_simulation:
                 self.show_error("无可用设备且未启用模拟模式。")
                 return


            if device_id_to_connect is None and selected_index > 0:
                self.show_error("无法确定要连接的设备ID。")
                return
            elif device_id_to_connect is None and selected_index == 0:
                 self.show_error("自动选择失败，无设备可选。")
                 return


            self.log_status(f"正在连接到: {device_id_to_connect}...")
            QApplication.processEvents()

            try:
                if self.camera.open(device_id_to_connect):
                    self._camera_connected = True
                    self.camera_id = device_id_to_connect
                    self.log_status(f"相机已连接: {self.camera_id}")
                    self.camera_status_changed.emit(True)

                    # Update parameters display after connecting
                    self.update_parameter_display()
                    self.change_trigger_mode() # Apply initial trigger mode from combo box

                else:
                    self.show_error(f"连接相机失败: {device_id_to_connect} (相机报告失败)")
                    self._camera_connected = False
                    self.camera_id = "未知"
            except Exception as e:
                self.show_error(f"连接相机时发生错误 ({device_id_to_connect}): {e}")
                logger.error(f"Error connecting camera {device_id_to_connect}: {e}", exc_info=True)
                self._camera_connected = False
                self.camera_id = "未知"

        # Update UI regardless of success/failure
        self._update_ui_state()


    def toggle_stream(self):
        """Starts or stops the camera stream."""
        if not self._camera_connected:
            self.show_error("相机未连接，无法控制视频流。")
            return

        if self.is_running:
            self.stop_grabbing()
        else:
            self.start_grabbing()

    def start_grabbing(self):
        """Starts the image acquisition process."""
        if self.is_running: return # Already running
        if not self._camera_connected: return

        try:
            # Ensure trigger mode is set before starting
            self.change_trigger_mode()

            # Apply current parameter settings before starting stream
            # self.apply_parameters(log_success=False) # Optionally apply silently

            if self.camera.start_grabbing():
                self.log_status("开始图像采集...")
                self.is_running = True
                self.fps_count = 0
                self.last_fps_time = time.time() # Reset FPS counter
            else:
                self.show_error("开始图像采集失败 (相机报告失败)")
                self.is_running = False

        except Exception as e:
            self.show_error(f"开始图像采集时发生错误: {e}")
            logger.error(f"Error starting grabbing: {e}", exc_info=True)
            self.is_running = False

        self._update_ui_state()

    def stop_grabbing(self):
        """Stops the image acquisition process."""
        if not self.is_running: return # Already stopped
        if not self._camera_connected: return

        try:
            if self.camera.stop_grabbing():
                self.log_status("停止图像采集")
                self.is_running = False
                # Optionally clear last frame?
                # self.current_frame = None
                # self._image_viewer.set_image(None) # Or keep last frame?
            else:
                self.show_error("停止图像采集失败 (相机报告失败)")
                # self.is_running = True # State might be uncertain here

        except Exception as e:
            self.show_error(f"停止图像采集时发生错误: {e}")
            logger.error(f"Error stopping grabbing: {e}", exc_info=True)
            # self.is_running = True # State might be uncertain here

        self._update_ui_state()

    def change_trigger_mode(self):
        """将所选的触发模式应用于相机"""
        if self.camera is None or not self._camera_connected:
            return # Cannot set if not connected

        try:
            trigger_mode_index = self._trigger_combo.currentIndex()
            mode_str = self._trigger_combo.currentText()

            if self.camera.set_trigger_mode(trigger_mode_index):
                self.log_status(f"触发模式已设置为: {mode_str}")
                # Update UI immediately after setting mode, especially trigger button state
                self._update_ui_state()
            else:
                self.show_error(f"设置触发模式失败: {mode_str} (相机报告失败)")
                # 可选恢复组合框
                current_cam_mode = self.camera.get_parameter('trigger_mode') # If get_param exists
                self._trigger_combo.setCurrentIndex(current_cam_mode)

        except Exception as e:
            self.show_error(f"更改触发模式时发生错误: {e}")
            logger.error(f"Error changing trigger mode: {e}", exc_info=True)


    def trigger_once(self):
        """Sends a software trigger command to the camera."""
        if not self.is_running:
             self.show_error("请先开始视频流（即使是触发模式）。")
             return
        if self._trigger_combo.currentIndex() == 0: # Continuous mode
             self.show_error("软触发在连续采集模式下无效。")
             return

        try:
            if self.camera.trigger_once():
                self.log_status("已发送软触发命令")
            else:
                self.show_error("软触发失败 (相机报告失败)")
        except Exception as e:
            self.show_error(f"软触发时发生错误: {e}")
            logger.error(f"Error triggering once: {e}", exc_info=True)

    def update_parameter_display(self):
        """从相机读取当前参数并更新UI控件."""
        if self.camera is None or not self._camera_connected:
            self._camera_info_label.setText("相机信息：未连接")
            return

        try:
            params = self.camera.get_parameter() # Assumes method returns a dict
            if not params:
                self.log_status("无法获取相机参数。")
                # Update camera info label with basic info if params fail
                device_info_text = f"相机ID: {self.camera_id}\n"
                found_device = next((d for d in self.available_devices if d.get('device_id') == self.camera_id), None)
                if found_device:
                     device_info_text += f"型号: {found_device.get('model_name', 'N/A')}\n"
                     device_info_text += f"SN: {found_device.get('serial_number', 'N/A')}\n"
                     if found_device.get('device_ip'):
                        device_info_text += f"IP: {found_device.get('device_ip')}\n"
                device_info_text += "参数：无法获取"
                self._camera_info_label.setText(device_info_text)
                return

            # Update Sliders/Spinners/Labels (block signals to prevent loops)
            self._exposure_slider.blockSignals(True)
            self._gain_slider.blockSignals(True)
            self._wb_slider.blockSignals(True)
            self._fps_spin.blockSignals(True)
            # TODO: 如果参数包含自动状态，则添加自动复选框

            exp_val = params.get('exposure_time')
            if exp_val is not None:
                 # Clamp value to slider range if necessary
                 exp_val_clamped = max(self._exposure_slider.minimum(), min(self._exposure_slider.maximum(), int(exp_val)))
                 self._exposure_slider.setValue(exp_val_clamped)
                 self._exposure_value_label.setText(f"{exp_val:.0f} μs") # Show actual value
            else:
                 self._exposure_value_label.setText("N/A")


            gain_val = params.get('gain')
            if gain_val is not None:
                gain_val_clamped = max(self._gain_slider.minimum(), min(self._gain_slider.maximum(), float(gain_val)))
                self._gain_slider.setValue(int(gain_val_clamped)) # Slider might be int
                self._gain_value_label.setText(f"{gain_val:.1f} dB") # Show actual value
            else:
                 self._gain_value_label.setText("N/A")

            # Example for White Balance (assuming param name 'white_balance_kelvin')
            wb_val = params.get('white_balance_kelvin')
            if wb_val is not None:
                wb_val_clamped = max(self._wb_slider.minimum(), min(self._wb_slider.maximum(), int(wb_val)))
                self._wb_slider.setValue(wb_val_clamped)
                self._wb_value_label.setText(f"{wb_val:.0f} K")
            # else: # Don't show N/A if feature might not exist
            #     self._wb_value_label.setText("N/A")


            fps_val = params.get('frame_rate')
            if fps_val is not None:
                self._fps_spin.setValue(int(fps_val))
            # else: leave current value


            # TODO: etc基于params. get（'auto_exposure_mode'）等更新自动复选框。
            # self._auto_exposure_check.setChecked(params.get('auto_exposure', False))


            # Update Camera Info Label
            info_text = f"相机ID: {self.camera_id}\n"
            found_device = next((d for d in self.available_devices if d.get('device_id') == self.camera_id), None)
            if found_device:
                info_text += f"型号: {found_device.get('model_name', 'N/A')}\n"
                info_text += f"SN: {found_device.get('serial_number', 'N/A')}\n"
                if found_device.get('device_ip'):
                    info_text += f"IP: {found_device.get('device_ip')}\n"

            info_text += f"分辨率: {params.get('width', 'N/A')}x{params.get('height', 'N/A')}\n"
            info_text += f"像素格式: {params.get('pixel_format', 'N/A')}\n" # Assuming get_parameter returns this
            info_text += f"帧率: {params.get('frame_rate', 'N/A'):.1f} FPS\n"
            info_text += f"曝光: {params.get('exposure_time', 'N/A'):.0f} μs\n"
            info_text += f"增益: {params.get('gain', 'N/A'):.1f} dB"
            # Add WB if available params.get('white_balance_kelvin', 'N/A')

            self._camera_info_label.setText(info_text)


        except Exception as e:
            self.log_status(f"更新参数显示失败: {e}")
            logger.error(f"Failed to update parameter display: {e}", exc_info=True)
            self._camera_info_label.setText(f"相机ID: {self.camera_id}\n参数：更新失败")


        finally:
             # Unblock signals
            self._exposure_slider.blockSignals(False)
            self._gain_slider.blockSignals(False)
            self._wb_slider.blockSignals(False)
            self._fps_spin.blockSignals(False)
            # TODO: Unblock auto checkboxes

    def apply_parameters(self, log_success=True):
        """Applies the parameter values from the UI controls to the camera."""
        if self.camera is None or not self._camera_connected:
            self.show_error("相机未连接，无法应用参数。")
            return
        if self.is_running:
             self.show_error("请先停止视频流再应用参数。") # Usually safer
             return


        params_to_set = {}
        success_flags = {}

        try:
            # --- Collect values from UI ---
            target_fps = self._fps_spin.value()
            params_to_set['frame_rate'] = target_fps # Assuming camera uses 'frame_rate' key

            if not self._auto_exposure_check.isChecked():
                params_to_set['exposure_time'] = self._exposure_slider.value()
            else:
                 params_to_set['auto_exposure'] = True # Or specific enum value if needed

            if not self._auto_gain_check.isChecked():
                 params_to_set['gain'] = self._gain_slider.value()
            else:
                 params_to_set['auto_gain'] = True # Or specific enum value

            # Assuming white balance is supported and uses 'white_balance_kelvin' key
            if not self._auto_wb_check.isChecked():
                 params_to_set['white_balance_kelvin'] = self._wb_slider.value()
            else:
                 params_to_set['auto_wb'] = True # Or specific enum value


            # TODO: 如果实现的话，添加分辨率和像素格式
            # if self._resolution_combo.currentIndex() > 0:
            #     res_str = self._resolution_combo.currentText()
            #     w, h = map(int, res_str.split('x'))
            #     params_to_set['width'] = w
            #     params_to_set['height'] = h

            # if self._pixel_format_combo.currentIndex() > 0:
            #     params_to_set['pixel_format'] = self._pixel_format_combo.currentText()

            # --- Apply parameters using set_parameter ---
            self.log_status(f"正在应用参数: {params_to_set}")
            QApplication.processEvents()

            # Use the unified set_parameter method if available
            if hasattr(self.camera, 'set_parameter') and callable(self.camera.set_parameter):
                 results = self.camera.set_parameter(**params_to_set) # Pass dict as kwargs

                 if isinstance(results, dict): # Assume it returns success flags per param
                      success_flags = results
                      num_success = sum(1 for v in results.values() if v)
                      num_total = len(results)
                      if log_success:
                          self.log_status(f"参数应用完成 ({num_success}/{num_total} 成功).")
                      if num_success < num_total:
                           failed_params = [k for k, v in results.items() if not v]
                           self.show_error(f"部分参数应用失败: {', '.join(failed_params)}")

                 elif isinstance(results, bool): # Assume it returns overall success
                      if results:
                          if log_success: self.log_status("所有参数已成功应用。")
                          for key in params_to_set: success_flags[key] = True # Mark all as success
                      else:
                          self.show_error("应用参数失败 (相机报告整体失败)。")
                          for key in params_to_set: success_flags[key] = False

                 else:
                      # Fallback: Assume success if no error? Risky.
                      if log_success: self.log_status("参数已发送 (未确认成功状态)。")
                      for key in params_to_set: success_flags[key] = True # Assume success


            else:
                # Fallback: Try individual setters if set_parameter doesn't exist
                # This is less ideal and depends on specific camera class methods
                num_success = 0
                num_total = 0
                logger.warning("Camera class lacks unified 'set_parameter'. Trying individual setters.")
                if 'exposure_time' in params_to_set and hasattr(self.camera, 'set_exposure'):
                     num_total += 1
                     if self.camera.set_exposure(params_to_set['exposure_time']): num_success += 1; success_flags['exposure_time'] = True
                     else: success_flags['exposure_time'] = False
                if 'gain' in params_to_set and hasattr(self.camera, 'set_gain'):
                     num_total += 1
                     if self.camera.set_gain(params_to_set['gain']): num_success += 1; success_flags['gain'] = True
                     else: success_flags['gain'] = False
                # Add others (fps, wb, auto modes) if individual setters exist
                if log_success:
                    self.log_status(f"参数应用完成 ({num_success}/{num_total} 成功 via individual setters).")


            # Refresh display with actual values read back from camera
            QTimer.singleShot(100, self.update_parameter_display)


        except Exception as e:
            self.show_error(f"应用参数时发生错误: {e}")
            logger.error(f"Error applying parameters: {e}", exc_info=True)

        # Update UI state in case something changed (e.g., auto mode disabled manual slider)
        self._update_ui_state()


    def handle_frame(self, frame, camera_id):
        """通过信号从相机核心接收一帧图像."""
        if frame is not None:
            with self.frame_lock:
                # 进行复制，以便与相机回调线程解耦
                self.current_frame = frame.copy()
                self.camera_id = camera_id 
                self.new_frame_available = True
                # 在此处增加帧率计数器
                self.fps_count += 1


    def _update_display_and_fps(self):
        """定时器触发的函数，用于在 UI 线程中安全地更新图像显示并计算 FPS。"""
        frame_to_display = None
        with self.frame_lock:
            if self.new_frame_available and self.current_frame is not None:
                # 获取最新帧并标记为已处理
                frame_to_display = self.current_frame
                self.new_frame_available = False

        # --- 处理帧（锁外部） ---
        if frame_to_display is not None:
            try:
                height, width = frame_to_display.shape[:2]   #获取帧的高度、宽度
                bytes_per_line = frame_to_display.strides[0]  #每行的字节数

                if len(frame_to_display.shape) == 3: # Color 颜色 
                    # 检查是BGR还是RGB
                    if frame_to_display.shape[2] == 3:
                        q_image = QImage(frame_to_display.data, width, height, bytes_per_line, QImage.Format_BGR888)
                    elif frame_to_display.shape[2] == 4: # BGRA?
                         q_image = QImage(frame_to_display.data, width, height, bytes_per_line, QImage.Format_ARGB32) 
                    else:
                        logger.warning(f"不支持的彩色图像形状: {frame_to_display.shape}")
                        return # 如果格式未知则跳过显示
                elif len(frame_to_display.shape) == 2: # Grayscale  灰度
                    q_image = QImage(frame_to_display.data, width, height, bytes_per_line, QImage.Format_Grayscale8)
                else:
                     logger.warning(f"不支持的图像形状: {frame_to_display.shape}")
                     return # 如果格式未知则跳过显示

                # 转换为QPixmap以在ImageViewerWidget中显示（它处理像素图）
                #q_image.copy()防止底层数据在 QPixmap 仍在使用时被释放或修改
                pixmap = QPixmap.fromImage(q_image.copy())
                self._image_viewer.set_image(pixmap) # 设置并显示新的 pixmap

            except Exception as e:
                logger.error(f"图像转换/显示错误: {e}", exc_info=True)

        # --- 计算并更新帧率 ---
        now = time.time()
        elapsed = now - self.last_fps_time    #self.last_fps_time：记录上次计算 FPS 的时间
        if elapsed >= 1.0: #每秒更新帧率显示
            with self.frame_lock: # 安全获取计数
                current_fps_count = self.fps_count
                self.fps_count = 0 # 重置下一个时间间隔的计数器
            self.display_fps = current_fps_count / elapsed
            self.last_fps_time = now
            self._fps_label.setText(f"FPS: {self.display_fps:.1f}")


    def log_status(self, message):
        """Logs a message to the logger and updates the status label."""
        logger.info(message)
        self._status_label.setText(message)

    def show_error(self, message):
        """Logs an error and displays it in the status label and a message box."""
        logger.error(message)
        self._status_label.setText(f"错误: {message}")
        # Optionally show a popup message box for critical errors
        # QMessageBox.critical(self, "错误", message)

    def closeEvent(self, event):
        """Handles the window closing event."""
        self.log_status("正在关闭应用程序...")
        self.timer.stop() # Stop display updates

        if self.camera:
            try:
                if self.is_running:
                    logger.info("Stopping grabbing before exit...")
                    self.camera.stop_grabbing()
                if self._camera_connected:
                    logger.info("Closing camera before exit...")
                    self.camera.close()
            except Exception as e:
                logger.error(f"Error during camera cleanup: {e}", exc_info=True)

        logger.info("清理完成，退出。")
        super().closeEvent(event)


# --- Main Execution Main执行 ---
def main():
    """Main function to run the application."""
    app = QApplication(sys.argv)

    # app.setStyle("Fusion")

    window = CameraTabWidget()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    # 确保存在必要的目录（例如，用于日志）
    log_dir = os.path.join(project_root, 'logs') # Example log dir 示例日志目录
    os.makedirs(log_dir, exist_ok=True)

    main()
