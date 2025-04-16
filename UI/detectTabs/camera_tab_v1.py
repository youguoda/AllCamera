#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海康威视相机集成测试脚本（完整改进版 v3）

此脚本整合了所有补丁和优化，专门针对MV-CI003-GL-N6型号相机进行优化，提供以下特性：
1. 自动识别并选择MV-CI003-GL-N6型号相机
2. 设备列表显示增强，包含型号名称和序列号
3. 修复参数结构体传递问题
4. 改进相机连接和参数显示
5. 健壮的错误处理和详细的诊断信息
"""

import os
import sys
import time
import traceback
import ctypes
import cv2
import numpy as np
import threading
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QLabel, QComboBox, 
                           QSlider, QGroupBox, QGridLayout, QCheckBox,
                           QLineEdit, QSpinBox, QDoubleSpinBox, QMessageBox)
from PyQt5.QtGui import QImage, QPixmap

# Add project root if necessary (adjust path as needed)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')) # Example: Adjust '..' count
if project_root not in sys.path:
    sys.path.append(project_root)
    print(f"Appended to sys.path: {project_root}")

try:
    # UI Utilities and Widgets (from the first code block's context)
    from UI.utils.ui_constants import LIGHT_COLORS, SPACING
    from UI.widgets.enhanced_image_viewer import ImageViewerWidget, InteractionMode
    from UI.widgets.collapsible_panel import CollapsiblePanel

    # Core Components (from the second code block's context)
    from core.camera.camera_factory import CameraFactoryManager
    # Ensure the specific factory is imported if needed for registration, though CameraFactoryManager handles it
    from core.camera.hikvision_camera_factory import HikvisionCameraFactory
    from core.utils.signal_manager import signal_manager
    from core.utils.logger import get_logger

except ImportError as e:
    print(f"Import Error: {e}")
    print("Current sys.path:", sys.path)
    sys.exit(1)


# 导入相机相关模块
from core.camera.camera_factory import CameraFactoryManager
from core.camera.hikvision_camera_factory import HikvisionCameraFactory  # 确保工厂类被导入
from core.utils.signal_manager import signal_manager    
from core.utils.logger import get_logger

# 获取日志记录器
logger = get_logger()


class CameraTabWidget(QMainWindow):
    """相机控制主窗口"""
    
    def __init__(self):
        """初始化相机控制主窗口"""
        super().__init__()
        
        # 相机实例
        self.camera = None
        self.is_running = False
        self.current_frame = None
        self.camera_id = "未知"
        self.available_devices = []
        self.use_simulation = False
        
        # 设置窗口标题和大小
        self.setWindowTitle("相机控制")
        self.resize(1200, 800)
        
        # 创建UI
        self.setup_ui()
        
        # 连接信号
        self.connect_signals()
        
        # 启动定时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_display)
        self.timer.start(30)  # 约30FPS
        
        # 自动初始化相机
        QTimer.singleShot(100, self.initialize_camera)
        
        # 线程锁和新帧标志
        self.frame_lock = threading.Lock()
        self.new_frame_available = False
        
        # 添加FPS计数
        self.fps_count = 0
        self.last_fps_time = time.time()
    
    def setup_ui(self):
        """设置用户界面"""
        # 主窗口部件和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # 左侧图像显示区域
        self.image_box = QGroupBox("相机图像")
        image_layout = QVBoxLayout(self.image_box)
        
        # 图像显示标签
        self.image_label = QLabel()
        self.image_label.setMinimumSize(640, 480)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: black;")
        
        # 添加FPS显示标签
        self.fps_label = QLabel("FPS: 0.0")
        self.fps_label.setStyleSheet("background-color: black; color: green; font-size: 14px; padding: 2px;")
        self.fps_label.setAlignment(Qt.AlignRight | Qt.AlignTop)
        
        # 使用叠加布局放置图像和FPS标签
        image_container = QWidget()
        image_layout_container = QVBoxLayout(image_container)
        image_layout_container.setContentsMargins(0, 0, 0, 0)
        image_layout_container.addWidget(self.image_label)
        
        # 将FPS标签放在右上角
        fps_container = QWidget(image_container)
        fps_container.setStyleSheet("background: transparent;")
        fps_layout = QHBoxLayout(fps_container)
        fps_layout.setContentsMargins(0, 5, 5, 0)
        fps_layout.addStretch()
        fps_layout.addWidget(self.fps_label)
        fps_container.setFixedHeight(30)
        
        # 将图像容器添加到主布局
        image_layout_container.addWidget(fps_container)
        image_layout.addWidget(image_container)
        
        # 图像信息标签
        self.info_label = QLabel("未连接相机")
        self.info_label.setAlignment(Qt.AlignCenter)
        image_layout.addWidget(self.info_label)
        
        # 右侧控制面板
        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)
        
        # 相机连接控件
        connection_box = QGroupBox("相机连接")
        connection_layout = QGridLayout(connection_box)
        
        # 设备选择
        connection_layout.addWidget(QLabel("设备:"), 0, 0)
        self.device_combo = QComboBox()
        self.device_combo.addItem("自动选择")
        connection_layout.addWidget(self.device_combo, 0, 1)
        
        # 模拟模式选项
        self.simulation_check = QCheckBox("使用模拟模式")
        self.simulation_check.setChecked(False)  # 默认不使用模拟模式
        connection_layout.addWidget(self.simulation_check, 1, 0, 1, 2)
        
        # 刷新设备按钮
        self.refresh_btn = QPushButton("刷新设备列表")
        self.refresh_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {LIGHT_COLORS["SECONDARY"]};
                        color: white;
                        border: none;
                        border-radius: 4px;
                        padding: {SPACING["SMALL"]}px {SPACING["MEDIUM"]}px;
                    }}

                    QPushButton:hover {{
                        background-color: {LIGHT_COLORS["SECONDARY_LIGHT"]};
                    }}

                    QPushButton:pressed {{
                        background-color: {LIGHT_COLORS["SECONDARY_DARK"]};
                    }}
                """)
        connection_layout.addWidget(self.refresh_btn, 2, 0)
        
        # 连接/断开按钮
        self.connect_btn = QPushButton("连接相机")
        connection_layout.addWidget(self.connect_btn, 2, 1)
        
        # 采集控制
        grabbing_box = QGroupBox("采集控制")
        grabbing_layout = QGridLayout(grabbing_box)
        
        # 开始/停止采集按钮
        self.start_grab_btn = QPushButton("开始采集")
        self.start_grab_btn.setEnabled(False)
        grabbing_layout.addWidget(self.start_grab_btn, 0, 0)
        
        self.stop_grab_btn = QPushButton("停止采集")
        self.stop_grab_btn.setEnabled(False)
        grabbing_layout.addWidget(self.stop_grab_btn, 0, 1)
        
        # 触发模式
        trigger_box = QGroupBox("触发模式")
        trigger_layout = QGridLayout(trigger_box)
        
        # 模式选择
        trigger_layout.addWidget(QLabel("触发模式:"), 0, 0)
        self.trigger_combo = QComboBox()
        self.trigger_combo.addItems(["连续采集", "软触发", "硬触发"])
        self.trigger_combo.setEnabled(False)
        trigger_layout.addWidget(self.trigger_combo, 0, 1)
        
        # 软触发按钮
        self.trigger_btn = QPushButton("软触发一次")
        self.trigger_btn.setEnabled(False)
        trigger_layout.addWidget(self.trigger_btn, 1, 0, 1, 2)
        
        # 相机参数
        params_box = QGroupBox("相机参数")
        params_layout = QGridLayout(params_box)
        
        # 帧率
        params_layout.addWidget(QLabel("帧率:"), 0, 0)
        self.frame_rate_spin = QDoubleSpinBox()
        self.frame_rate_spin.setRange(1, 200)
        self.frame_rate_spin.setValue(30)
        self.frame_rate_spin.setEnabled(False)
        params_layout.addWidget(self.frame_rate_spin, 0, 1)
        
        # 曝光时间
        params_layout.addWidget(QLabel("曝光时间 (μs):"), 1, 0)
        self.exposure_spin = QDoubleSpinBox()
        self.exposure_spin.setRange(10, 1000000)
        self.exposure_spin.setValue(10000)
        self.exposure_spin.setEnabled(False)
        params_layout.addWidget(self.exposure_spin, 1, 1)
        
        # 增益
        params_layout.addWidget(QLabel("增益:"), 2, 0)
        self.gain_spin = QDoubleSpinBox()
        self.gain_spin.setRange(0, 100)
        self.gain_spin.setValue(0)
        self.gain_spin.setEnabled(False)
        params_layout.addWidget(self.gain_spin, 2, 1)
        
        # 应用参数按钮
        self.apply_params_btn = QPushButton("应用参数")
        self.apply_params_btn.setEnabled(False)
        params_layout.addWidget(self.apply_params_btn, 3, 0, 1, 2)
        
        # 当前状态和日志
        status_box = QGroupBox("状态信息")
        status_layout = QVBoxLayout(status_box)
        self.status_label = QLabel("就绪")
        status_layout.addWidget(self.status_label)
        
        # 添加所有控件到控制面板
        control_layout.addWidget(connection_box)
        control_layout.addWidget(grabbing_box)
        control_layout.addWidget(trigger_box)
        control_layout.addWidget(params_box)
        control_layout.addWidget(status_box)
        control_layout.addStretch()
        
        # 添加到主布局
        main_layout.addWidget(self.image_box, 2)
        main_layout.addWidget(control_panel, 1)
    
    def connect_signals(self):
        """连接信号和槽"""
        # 相机信号
        signal_manager.frame_ready_signal.connect(self.handle_frame)
        
        # 按钮信号
        self.refresh_btn.clicked.connect(self.refresh_devices)
        self.connect_btn.clicked.connect(self.toggle_connection)
        self.start_grab_btn.clicked.connect(self.start_grabbing)
        self.stop_grab_btn.clicked.connect(self.stop_grabbing)
        self.trigger_btn.clicked.connect(self.trigger_once)
        self.apply_params_btn.clicked.connect(self.apply_parameters)
        
        # 触发模式变更
        self.trigger_combo.currentIndexChanged.connect(self.change_trigger_mode)
        
        # 模拟模式变更
        self.simulation_check.stateChanged.connect(self.toggle_simulation_mode)
    
    def initialize_camera(self):
        """初始化相机"""
        try:
            # 获取可用相机类型
            available_types = CameraFactoryManager.get_available_types()
            if "hikvision" not in available_types:
                self.show_error("未找到海康威视相机工厂类，请确保已注册")
                return False
                
            # 创建相机实例
            self.camera = CameraFactoryManager.create_camera("hikvision")
            if self.camera is None:
                self.show_error("创建相机实例失败")
                return False
                
            # 设置模拟模式
            self.camera._is_simulation = self.use_simulation
                
            self.log_status("相机实例创建成功")
            self.refresh_devices()
            return True
        except Exception as e:
            self.show_error(f"初始化相机失败: {str(e)}")
            traceback.print_exc()
            return False
    
    def refresh_devices(self):
        """
        刷新相机设备列表
        """
        try:
            if self.camera is None:
                self.show_error("相机实例未创建")
                return
                
            # 更新模拟模式
            self.camera._is_simulation = self.use_simulation
                
            # 枚举设备
            self.available_devices = self.camera.enumerate_devices()
            
            # 更新下拉框
            self.device_combo.clear()
            self.device_combo.addItem("自动选择")
            
            target_device_index = -1
            
            if self.available_devices:
                for i, device in enumerate(self.available_devices):
                    device_info = ""
                    # 提取详细信息
                    model_name = device.get('model_name', 'Unknown')
                    serial_number = device.get('serial_number', 'Unknown')
                    device_type = device.get('device_type', 'Unknown')
                    device_id = device.get('device_id', str(i))
                    
                    # 检查是否是目标型号
                    is_target = device.get('is_target_model', False) or "MV-CI003-GL-N6" in model_name
                    
                    if device_type == "GigE":
                        device_ip = device.get('device_ip', 'Unknown')
                        device_info = f"[{device_id}] {model_name} (SN:{serial_number}) - {device_ip}"
                    else:
                        device_info = f"[{device_id}] {model_name} (SN:{serial_number})"
                    
                    # 如果是目标型号，添加标记并记录索引
                    if is_target:
                        device_info += " [目标相机]"
                        if target_device_index == -1:  # 记录第一个目标相机
                            target_device_index = i + 1  # +1 因为索引0是"自动选择"
                    
                    self.device_combo.addItem(device_info)
                
                # 自动选择目标型号相机
                if target_device_index != -1:
                    self.device_combo.setCurrentIndex(target_device_index)
                    self.log_status(f"已自动选择MV-CI003-GL-N6型号相机 (index: {target_device_index})")
                
                self.log_status(f"找到 {len(self.available_devices)} 个相机设备")
            else:
                if self.use_simulation:
                    self.log_status("未找到真实相机设备，将使用模拟模式")
                else:
                    self.log_status("未找到相机设备，请检查连接或启用模拟模式")
        except Exception as e:
            self.show_error(f"刷新设备列表失败: {str(e)}")
            traceback.print_exc()
    
    def toggle_simulation_mode(self):
        """切换模拟模式"""
        self.use_simulation = self.simulation_check.isChecked()
        if self.camera:
            self.camera._is_simulation = self.use_simulation
            self.log_status(f"模拟模式: {'启用' if self.use_simulation else '禁用'}")
            self.refresh_devices()
    
    def toggle_connection(self):
        """
        连接或断开相机
        
        改进版：支持从设备信息字符串中提取设备ID
        """
        if self.camera is None:
            self.show_error("相机实例未创建")
            return
            
        if not self.camera.is_open():
            # 连接相机
            device_id = ""
            if self.device_combo.currentIndex() > 0:
                # 从设备信息字符串中提取设备ID，格式为 "[ID] 型号 (SN:序列号) - IP"
                device_info = self.device_combo.currentText()
                try:
                    # 提取方括号中的设备ID
                    start_pos = device_info.find('[') + 1
                    end_pos = device_info.find(']')
                    if start_pos > 0 and end_pos > start_pos:
                        device_id = device_info[start_pos:end_pos]
                        logger.info(f"从设备信息中提取到设备ID: {device_id}")
                except:
                    device_id = ""
                
            try:
                if self.camera.open(device_id):
                    model_info = ""
                    for device in self.available_devices:
                        if device.get('device_id') == device_id:
                            model_info = f" ({device.get('model_name', 'Unknown')})"
                            break
                    
                    self.log_status(f"相机已连接: {device_id if device_id else '默认设备'}{model_info}")
                    self.connect_btn.setText("断开相机")
                    
                    # 获取相机信息
                    self.camera_id = device_id if device_id else "默认设备"
                    
                    # 启用控件
                    self.start_grab_btn.setEnabled(True)
                    self.trigger_combo.setEnabled(True)
                    self.frame_rate_spin.setEnabled(True)
                    self.exposure_spin.setEnabled(True)
                    self.gain_spin.setEnabled(True)
                    self.apply_params_btn.setEnabled(True)
                    
                    # 获取当前参数
                    self.update_parameter_display()
                else:
                    self.show_error("连接相机失败")
            except Exception as e:
                self.show_error(f"连接相机时发生错误: {str(e)}")
                traceback.print_exc()
        else:
            # 断开相机
            try:
                if self.camera.is_grabbing():
                    self.stop_grabbing()
                    
                if self.camera.close():
                    self.log_status("相机已断开")
                    self.connect_btn.setText("连接相机")
                    
                    # 禁用控件
                    self.start_grab_btn.setEnabled(False)
                    self.stop_grab_btn.setEnabled(False)
                    self.trigger_btn.setEnabled(False)
                    self.trigger_combo.setEnabled(False)
                    self.frame_rate_spin.setEnabled(False)
                    self.exposure_spin.setEnabled(False)
                    self.gain_spin.setEnabled(False)
                    self.apply_params_btn.setEnabled(False)
                else:
                    self.show_error("断开相机失败")
            except Exception as e:
                self.show_error(f"断开相机时发生错误: {str(e)}")
                traceback.print_exc()
    
    def start_grabbing(self):
        """开始图像采集"""
        try:
            if self.camera is None or not self.camera.is_open():
                self.show_error("相机未连接")
                return
                
            # 设置触发模式
            self.change_trigger_mode()
                
            if self.camera.start_grabbing():
                self.log_status("开始图像采集")
                self.is_running = True
                
                # 更新按钮状态
                self.start_grab_btn.setEnabled(False)
                self.stop_grab_btn.setEnabled(True)
                
                # 根据触发模式决定是否启用触发按钮
                trigger_mode = self.trigger_combo.currentIndex()
                self.trigger_btn.setEnabled(trigger_mode > 0)
            else:
                self.show_error("开始图像采集失败")
        except Exception as e:
            self.show_error(f"开始图像采集时发生错误: {str(e)}")
            traceback.print_exc()
    
    def stop_grabbing(self):
        """停止图像采集"""
        try:
            if self.camera is None:
                return
                
            if self.camera.is_grabbing():
                if self.camera.stop_grabbing():
                    self.log_status("停止图像采集")
                    self.is_running = False
                    
                    # 更新按钮状态
                    self.start_grab_btn.setEnabled(True)
                    self.stop_grab_btn.setEnabled(False)
                    self.trigger_btn.setEnabled(False)
                else:
                    self.show_error("停止图像采集失败")
        except Exception as e:
            self.show_error(f"停止图像采集时发生错误: {str(e)}")
            traceback.print_exc()
    
    def change_trigger_mode(self):
        """改变触发模式"""
        try:
            if self.camera is None or not self.camera.is_open():
                return
                
            trigger_mode = self.trigger_combo.currentIndex()
            mode_str = ["连续采集", "软触发", "硬触发"][trigger_mode]
            
            if self.camera.set_trigger_mode(trigger_mode):
                self.log_status(f"触发模式已更改为: {mode_str}")
                self.trigger_btn.setEnabled(trigger_mode > 0 and self.camera.is_grabbing())
            else:
                self.show_error(f"设置触发模式失败: {mode_str}")
        except Exception as e:
            self.show_error(f"更改触发模式时发生错误: {str(e)}")
            traceback.print_exc()
    
    def trigger_once(self):
        """软触发一次"""
        try:
            if self.camera is None or not self.camera.is_open():
                return
                
            if self.camera.trigger_once():
                self.log_status("已发送软触发命令")
            else:
                self.show_error("软触发失败")
        except Exception as e:
            self.show_error(f"软触发时发生错误: {str(e)}")
            traceback.print_exc()
    
    def update_parameter_display(self):
        """
        更新参数显示
        
        改进版：增加更多相机信息显示
        """
        try:
            if self.camera is None or not self.camera.is_open():
                return
                
            # 获取相机参数
            params = self.camera.get_parameter()
            if not params:
                return
                
            # 更新控件值
            if 'frame_rate' in params:
                self.frame_rate_spin.setValue(params['frame_rate'])
                
            if 'exposure_time' in params:
                self.exposure_spin.setValue(params['exposure_time'])
                
            if 'gain' in params:
                self.gain_spin.setValue(params['gain'])
            
            # 更新状态信息
            model_info = ""
            for device in self.available_devices:
                if device.get('device_id') == self.camera_id or (self.camera_id == "默认设备" and device.get('is_target_model', False)):
                    model_info = f"型号: {device.get('model_name', 'Unknown')}\n"
                    model_info += f"序列号: {device.get('serial_number', 'Unknown')}\n"
                    if device.get('device_type') == "GigE":
                        model_info += f"IP: {device.get('device_ip', 'Unknown')}\n"
                    break
            
            info_text = f"相机ID: {self.camera_id}\n"
            info_text += model_info
            
            if 'width' in params and 'height' in params:
                info_text += f"分辨率: {params['width']}x{params['height']}\n"
            
            info_text += f"帧率: {params.get('frame_rate', 'Unknown')} fps\n"
            info_text += f"曝光: {params.get('exposure_time', 'Unknown')} μs\n"
            info_text += f"增益: {params.get('gain', 'Unknown')}dB"
            
            self.info_label.setText(info_text)
            
        except Exception as e:
            self.log_status(f"更新参数显示失败: {str(e)}")
            traceback.print_exc()
    
    def apply_parameters(self):
        """应用参数设置"""
        try:
            if self.camera is None or not self.camera.is_open():
                self.show_error("相机未连接")
                return
                
            frame_rate = self.frame_rate_spin.value()
            exposure = self.exposure_spin.value()
            gain = self.gain_spin.value()
            
            # 设置参数
            try:
                # 使用统一的set_parameter方法设置所有参数
                if self.camera.set_parameter(frame_rate=frame_rate, exposure_time=exposure, gain=gain):
                    self.log_status("所有参数已应用")
                else:
                    # 尝试单独设置参数
                    success_count = 0
                    
                    # 尝试分别设置曝光和增益（如果没有直接设置帧率的方法）
                    if hasattr(self.camera, 'set_exposure') and self.camera.set_exposure(exposure):
                        success_count += 1
                    
                    if hasattr(self.camera, 'set_gain') and self.camera.set_gain(gain):
                        success_count += 1
                    
                    self.log_status(f"已应用 {success_count}/2 个参数")
            except Exception as e:
                self.log_status(f"应用参数时发生错误: {str(e)}")
                import traceback
                traceback.print_exc()
        except Exception as e:
            self.log_status(f"应用参数时发生错误: {str(e)}")
            traceback.print_exc()
    
    def handle_frame(self, frame, camera_id):
        """处理接收到的图像帧"""
        try:
            # 创建帧的深拷贝，避免在处理过程中被修改
            if frame is not None:
                with self.frame_lock:
                    self.current_frame = frame.copy()
                    self.camera_id = camera_id
                    self.new_frame_available = True
        except Exception as e:
            self.log_status(f"处理图像帧时发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def update_display(self):
        """更新图像显示"""
        try:
            if not self.is_running:
                return
                
            with self.frame_lock:
                if not self.new_frame_available or self.current_frame is None:
                    return
                    
                # 获取当前帧的拷贝
                frame_to_display = self.current_frame.copy()
                self.new_frame_available = False
            
            # 转换为QImage (在锁外进行，提高性能)
            height, width = frame_to_display.shape[:2]
            
            try:
                if len(frame_to_display.shape) == 3:
                    # 彩色图像 (确保使用正确的格式)
                    bytes_per_line = frame_to_display.strides[0]
                    q_image = QImage(frame_to_display.data, width, height, 
                                    bytes_per_line, QImage.Format_BGR888)
                else:
                    # 灰度图像
                    bytes_per_line = frame_to_display.strides[0]
                    q_image = QImage(frame_to_display.data, width, height, 
                                    bytes_per_line, QImage.Format_Grayscale8)
                
                # 创建QPixmap并缓存它
                pixmap = QPixmap.fromImage(q_image)
                scaled_pixmap = pixmap.scaled(
                    self.image_label.width(), self.image_label.height(), 
                    Qt.KeepAspectRatio, Qt.SmoothTransformation)
                
                # 显示图像
                self.image_label.setPixmap(scaled_pixmap)
                
                if hasattr(self, 'fps_count'):
                    self.fps_count += 1
                    
                    if self.fps_count % 10 == 0:
                        # 每10帧更新一次FPS显示
                        now = time.time()
                        if hasattr(self, 'last_fps_time'):
                            elapsed = now - self.last_fps_time
                            if elapsed > 0:
                                fps = 10 / elapsed
                                self.fps_label.setText(f"FPS: {fps:.1f}")
                        self.last_fps_time = now
                        
            except Exception as e:
                logger.error(f"图像转换错误: {str(e)}")
                import traceback
                traceback.print_exc()
                
        except Exception as e:
            logger.error(f"更新显示错误: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def log_status(self, message):
        """记录状态信息"""
        logger.info(message)
        self.status_label.setText(message)
    
    def show_error(self, message):
        """显示错误信息"""
        logger.error(message)
        self.status_label.setText(f"错误: {message}")
        QMessageBox.critical(self, "错误", message)
    
    def closeEvent(self, event):
        """关闭窗口事件"""
        try:
            if self.camera:
                if self.camera.is_grabbing():
                    self.camera.stop_grabbing()
                    
                if self.camera.is_open():
                    self.camera.close()
        except:
            pass
            
        super().closeEvent(event)


def main():
    """主函数"""
    app = QApplication(sys.argv)
    window = CameraTabWidget()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
