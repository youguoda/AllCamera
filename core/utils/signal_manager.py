"""
信号管理器模块

提供集中式的事件和信号管理，使不同模块之间可以松耦合通信。
实现了观察者模式，允许组件订阅和发布事件。
"""
from PyQt5.QtCore import QObject, pyqtSignal
import numpy as np


class SignalManager(QObject):
    """
    信号管理器类
    
    实现了单例模式，确保全局信号通信的一致性。
    定义了各种应用程序需要的信号，用于模块间通信。
    """
    # 单例实例
    _instance = None
    
    # 相机相关信号
    cameraStatusSignal = pyqtSignal(str)  # 相机状态更新信号
    cameraErrorSignal = pyqtSignal(str)  # 相机错误信号
    cameraDevicesSignal = pyqtSignal(list)  # 相机设备列表信号
    cameraModeSignal = pyqtSignal(str)  # 相机模式信号
    cameraParametersSignal = pyqtSignal(dict)  # 相机参数信号
    cameraRoiSignal = pyqtSignal(tuple)  # 相机ROI信号
    cameraTakePhotoSignal = pyqtSignal(np.ndarray)  # 相机拍照信号
    
    # 相机请求信号 - 从视图到控制器
    requestRefreshDevices = pyqtSignal()  # 请求刷新设备列表
    deviceListUpdatedSignal = pyqtSignal(list)  # 设备列表更新信号
    cameraConnectedSignal = pyqtSignal(str)  # 相机连接成功信号
    cameraDisconnectedSignal = pyqtSignal()  # 相机断开连接信号
    cameraStreamingSignal = pyqtSignal(bool)  # 相机采集状态信号
    streamingStartedSignal = pyqtSignal()  # 开始采集信号
    streamingStoppedSignal = pyqtSignal()  # 停止采集信号
    requestConnectCamera = pyqtSignal(int)  # 请求连接相机，参数为设备索引
    requestDisconnectCamera = pyqtSignal()  # 请求断开相机连接
    requestStartStreaming = pyqtSignal()  # 请求开始采集
    requestStopStreaming = pyqtSignal()  # 请求停止采集
    requestSetTriggerMode = pyqtSignal(bool)  # 请求设置触发模式
    requestTriggerOnce = pyqtSignal()  # 请求触发一次采集
    requestTakePhoto = pyqtSignal()  # 请求拍照
    requestSetParameters = pyqtSignal(dict)  # 请求设置相机参数
    requestSetRoi = pyqtSignal(tuple)  # 请求设置ROI
    requestResetRoi = pyqtSignal()  # 请求重置ROI
    updateImageSignal = pyqtSignal(np.ndarray)  # 更新图像信号
    requestSetSimulationMode = pyqtSignal(bool)  # 请求设置模拟模式

    frame_ready_signal = pyqtSignal(np.ndarray, str)  # 帧准备好信号

    # 算法相关信号
    algorithm_result_signal = pyqtSignal(str, np.ndarray, dict)  # 算法结果，参数：结果类型，处理后图像，附加数据
    opencv_result_signal = pyqtSignal(str, np.ndarray)  # OpenCV算法结果，参数：结果类型，处理后图像
    yolo_result_signal = pyqtSignal(str, np.ndarray)  # YOLO算法结果，参数：结果类型，处理后图像
    detection_started_signal = pyqtSignal()  # 检测开始信号
    detection_stopped_signal = pyqtSignal()  # 检测停止信号
    
    # 通信相关信号
    communication_connected_signal = pyqtSignal(str)  # 通信连接成功，参数：连接ID
    communication_disconnected_signal = pyqtSignal(str)  # 通信断开连接，参数：连接ID
    communication_error_signal = pyqtSignal(str, str)  # 通信错误，参数：连接ID，错误信息
    plc_data_received_signal = pyqtSignal(dict)  # 接收到PLC数据，参数：数据字典
    plc_trigger_signal = pyqtSignal()  # PLC触发信号
    communication_disconnected_signal = pyqtSignal(str)  # 通信断开连接，参数：连接ID
    plc_reset_signal = pyqtSignal()  # PLC重置信号
    plc_stop_signal = pyqtSignal()  # PLC停止信号
    plc_start_signal = pyqtSignal()  # PLC启动信号
    plc_ready_signal = pyqtSignal()  # PLC就绪信号
    # 数据管理相关信号
    data_saved_signal = pyqtSignal(str, str)  # 数据保存成功，参数：数据类型，路径
    data_deleted_signal = pyqtSignal(str, str)  # 数据删除成功，参数：数据类型，ID
    
    # UI相关信号
    update_run_time_signal = pyqtSignal(str, str)  # 更新运行时间，参数：当前时间，运行时长
    update_status_signal = pyqtSignal(str)  # 更新状态栏信息
    update_result_signal = pyqtSignal(str)  # 更新检测结果显示
    update_count_signal = pyqtSignal(int, int)  # 更新计数，参数：良品数，不良品数
    
    # 系统相关信号
    system_ready_signal = pyqtSignal()  # 系统就绪信号
    system_shutdown_signal = pyqtSignal()  # 系统关闭信号
    config_changed_signal = pyqtSignal(str, str)  # 配置变更，参数：配置名，键路径
    
    def __new__(cls):
        """
        实现单例模式
        
        Returns:
            SignalManager: 单例实例
        """
        if cls._instance is None:
            cls._instance = super(SignalManager, cls).__new__(cls)
        return cls._instance


# 全局单例实例
signal_manager = SignalManager()
