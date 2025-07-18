# 相机控制流程

## 1. 初始化阶段

*   **应用程序启动**:
    *   创建 `QApplication` 实例。
    *   创建 `CameraTabWidget` 主窗口实例 ([`UI/detectTabs/camera_tab.py:1209`](UI/detectTabs/camera_tab.py:1209))。
*   **UI 初始化 (`_init_ui`)**:
    *   构建用户界面的所有元素，包括预览区、控制面板、按钮、滑块、下拉框等 ([`UI/detectTabs/camera_tab.py:114`](UI/detectTabs/camera_tab.py:114))。
    *   设置初始 UI 状态 (例如，禁用某些控件) ([`UI/detectTabs/camera_tab.py:385`](UI/detectTabs/camera_tab.py:385))。
*   **信号与槽连接 (`_connect_signals_to_logic`)**:
    *   将 UI 控件的信号（如按钮点击）连接到相应的处理函数 ([`UI/detectTabs/camera_tab.py:397`](UI/detectTabs/camera_tab.py:397))。
*   **相机核心初始化 (`initialize_camera_core`)**:
    *   延迟调用 (通过 `QTimer.singleShot`) 以避免阻塞 UI ([`UI/detectTabs/camera_tab.py:109`](UI/detectTabs/camera_tab.py:109))。
    *   使用 `CameraFactoryManager` 创建相机实例 (`self.camera`) ([`UI/detectTabs/camera_tab.py:588`](UI/detectTabs/camera_tab.py:588))。
    *   如果初始化成功，尝试刷新设备列表 ([`UI/detectTabs/camera_tab.py:598`](UI/detectTabs/camera_tab.py:598))。
*   **核心信号连接 (`_connect_core_signals`)**:
    *   连接相机核心发出的信号，主要是 `frame_ready_signal` 到 `handle_frame` 方法，用于接收新图像帧 ([`UI/detectTabs/camera_tab.py:429`](UI/detectTabs/camera_tab.py:429))。
*   **显示更新定时器 (`QTimer`)**:
    *   启动一个定时器，周期性调用 `_update_display_and_fps` 来更新图像显示和计算 FPS ([`UI/detectTabs/camera_tab.py:104`](UI/detectTabs/camera_tab.py:104))。

## 2. 设备发现与选择

*   **刷新设备列表 (`refresh_devices`)**:
    *   用户点击“刷新列表”按钮 ([`UI/detectTabs/camera_tab.py:400`](UI/detectTabs/camera_tab.py:400)) 或在初始化/切换模拟模式后自动调用。
    *   调用 `self.camera.enumerate_devices()` 获取可用相机列表 ([`UI/detectTabs/camera_tab.py:620`](UI/detectTabs/camera_tab.py:620))。
    *   更新相机选择下拉框 (`_camera_combo`) ([`UI/detectTabs/camera_tab.py:622`](UI/detectTabs/camera_tab.py:622))。
    *   如果找到特定目标型号的相机 (如 "MV-CI003-GL-N6")，会尝试自动选中它 ([`UI/detectTabs/camera_tab.py:639`](UI/detectTabs/camera_tab.py:639))。
*   **模拟模式切换 (`toggle_simulation_mode`)**:
    *   用户勾选/取消勾选“使用模拟模式”复选框 ([`UI/detectTabs/camera_tab.py:402`](UI/detectTabs/camera_tab.py:402))。
    *   更新 `self.use_simulation` 状态，并相应地更新相机对象的模拟状态 ([`UI/detectTabs/camera_tab.py:672`](UI/detectTabs/camera_tab.py:672))。
    *   切换后会自动刷新设备列表。
*   **用户选择相机**:
    *   用户从下拉框 (`_camera_combo`) 中选择一个相机设备或“自动选择”。

## 3. 连接与断开相机

*   **连接相机 (`toggle_connection` - 连接部分)**:
    *   用户点击“连接相机”按钮 ([`UI/detectTabs/camera_tab.py:401`](UI/detectTabs/camera_tab.py:401))。
    *   确定要连接的设备 ID (根据用户选择或自动选择逻辑) ([`UI/detectTabs/camera_tab.py:713`](UI/detectTabs/camera_tab.py:713))。
    *   调用 `self.camera.open(device_id_to_connect)` ([`UI/detectTabs/camera_tab.py:770`](UI/detectTabs/camera_tab.py:770))。
    *   如果连接成功：
        *   更新 `_camera_connected` 状态为 `True`。
        *   调用 `update_parameter_display()` 从相机读取并显示当前参数 ([`UI/detectTabs/camera_tab.py:777`](UI/detectTabs/camera_tab.py:777))。
        *   调用 `change_trigger_mode()` 应用当前 UI 选定的触发模式 ([`UI/detectTabs/camera_tab.py:778`](UI/detectTabs/camera_tab.py:778))。
        *   更新 UI 状态 (`_update_ui_state`)，例如启用流控制按钮、参数调整控件等 ([`UI/detectTabs/camera_tab.py:791`](UI/detectTabs/camera_tab.py:791))。
*   **断开相机 (`toggle_connection` - 断开部分)**:
    *   用户点击“断开相机”按钮。
    *   如果正在采集图像 (`is_running`)，先调用 `stop_grabbing()` ([`UI/detectTabs/camera_tab.py:691`](UI/detectTabs/camera_tab.py:691))。
    *   调用 `self.camera.close()` ([`UI/detectTabs/camera_tab.py:694`](UI/detectTabs/camera_tab.py:694))。
    *   更新 `_camera_connected` 状态为 `False`。
    *   清空图像显示和相机信息。
    *   更新 UI 状态 (`_update_ui_state`)，例如禁用流控制按钮、参数调整控件等。

## 4. 参数调整

*   **用户调整 UI 控件**:
    *   用户操作曝光、增益、白平衡滑块，或帧率 SpinBox，或自动模式复选框。
    *   滑块值变化时，对应的数值标签会更新 (`_on_exposure_slider_changed`, etc.) ([`UI/detectTabs/camera_tab.py:534`](UI/detectTabs/camera_tab.py:534))。
    *   自动模式复选框状态改变时，会启用/禁用对应的手动滑块 (`_on_auto_exposure_changed`, etc.) ([`UI/detectTabs/camera_tab.py:544`](UI/detectTabs/camera_tab.py:544))。
*   **应用参数 (`apply_parameters`)**:
    *   用户点击“应用参数”按钮 ([`UI/detectTabs/camera_tab.py:422`](UI/detectTabs/camera_tab.py:422))。
    *   通常在相机未进行流式传输时操作。
    *   从 UI 控件收集当前设置的参数值 ([`UI/detectTabs/camera_tab.py:1012`](UI/detectTabs/camera_tab.py:1012))。
    *   调用 `self.camera.set_parameter(**params_to_set)` 将参数应用到相机 ([`UI/detectTabs/camera_tab.py:1049`](UI/detectTabs/camera_tab.py:1049))。
    *   应用后，延迟调用 `update_parameter_display()` 以从相机回读并确认参数是否成功设置 ([`UI/detectTabs/camera_tab.py:1095`](UI/detectTabs/camera_tab.py:1095))。
*   **读取并显示参数 (`update_parameter_display`)**:
    *   在连接成功后或应用参数后调用。
    *   调用 `self.camera.get_parameter()` 从相机获取当前参数 ([`UI/detectTabs/camera_tab.py:905`](UI/detectTabs/camera_tab.py:905))。
    *   更新 UI 上的滑块、标签、复选框等以反映相机的实际参数值 ([`UI/detectTabs/camera_tab.py:920`](UI/detectTabs/camera_tab.py:920))。
    *   更新相机信息标签 (`_camera_info_label`) ([`UI/detectTabs/camera_tab.py:965`](UI/detectTabs/camera_tab.py:965))。

## 5. 视频流控制

*   **开始视频流 (`start_grabbing`)**:
    *   用户点击“开始视频流”按钮 (通过 `toggle_stream` 调用) ([`UI/detectTabs/camera_tab.py:406`](UI/detectTabs/camera_tab.py:406))。
    *   确保触发模式已设置 (`change_trigger_mode()`) ([`UI/detectTabs/camera_tab.py:812`](UI/detectTabs/camera_tab.py:812))。
    *   调用 `self.camera.start_grabbing()` ([`UI/detectTabs/camera_tab.py:817`](UI/detectTabs/camera_tab.py:817))。
    *   如果成功，设置 `is_running = True`，重置 FPS 计数器。
    *   更新 UI 状态 (`_update_ui_state`)。
*   **停止视频流 (`stop_grabbing`)**:
    *   用户点击“停止视频流”按钮 (通过 `toggle_stream` 调用)。
    *   调用 `self.camera.stop_grabbing()` ([`UI/detectTabs/camera_tab.py:839`](UI/detectTabs/camera_tab.py:839))。
    *   如果成功，设置 `is_running = False`。
    *   更新 UI 状态 (`_update_ui_state`)。

## 6. 图像采集与显示

*   **接收帧 (`handle_frame`)**:
    *   当相机核心有新帧准备好时，通过 `frame_ready_signal` 触发此方法 ([`UI/detectTabs/camera_tab.py:432`](UI/detectTabs/camera_tab.py:432))。
    *   在线程锁 (`frame_lock`) 内，复制帧数据到 `self.current_frame`，设置 `self.new_frame_available = True`，并增加 `self.fps_count` ([`UI/detectTabs/camera_tab.py:1109`](UI/detectTabs/camera_tab.py:1109))。
*   **更新显示与 FPS (`_update_display_and_fps`)**:
    *   由定时器周期性调用。
    *   在线程锁内检查 `self.new_frame_available`，如果为 `True`，则获取 `self.current_frame` ([`UI/detectTabs/camera_tab.py:1121`](UI/detectTabs/camera_tab.py:1121))。
    *   将 NumPy 图像帧转换为 `QPixmap` ([`UI/detectTabs/camera_tab.py:1131`](UI/detectTabs/camera_tab.py:1131))。
    *   调用 `self._image_viewer.set_image(pixmap)` 在 UI 上显示图像 ([`UI/detectTabs/camera_tab.py:1152`](UI/detectTabs/camera_tab.py:1152))。
    *   计算并更新 FPS 显示 (`_fps_label`) ([`UI/detectTabs/camera_tab.py:1157`](UI/detectTabs/camera_tab.py:1157))。

## 7. 触发模式与拍照

*   **更改触发模式 (`change_trigger_mode`)**:
    *   用户在“触发模式”下拉框中选择模式 (连续采集、软触发、硬触发) ([`UI/detectTabs/camera_tab.py:426`](UI/detectTabs/camera_tab.py:426))。
    *   调用 `self.camera.set_trigger_mode(trigger_mode_index)` 将模式设置到相机 ([`UI/detectTabs/camera_tab.py:865`](UI/detectTabs/camera_tab.py:865))。
    *   更新 UI 状态 (`_update_ui_state`)，特别是拍照按钮的可用性。
*   **软触发拍照 (`trigger_once`)**:
    *   用户点击“拍照 (软触发)”按钮 ([`UI/detectTabs/camera_tab.py:407`](UI/detectTabs/camera_tab.py:407))。
    *   检查相机是否正在运行视频流且当前不是连续采集模式 ([`UI/detectTabs/camera_tab.py:882`](UI/detectTabs/camera_tab.py:882))。
    *   调用 `self.camera.trigger_once()` 发送软触发命令 ([`UI/detectTabs/camera_tab.py:890`](UI/detectTabs/camera_tab.py:890))。

## 8. ROI (感兴趣区域) 选择

*   **切换 ROI 选择模式 (`_on_roi_button_toggled`)**:
    *   用户点击“选择 ROI”按钮 ([`UI/detectTabs/camera_tab.py:410`](UI/detectTabs/camera_tab.py:410))。
    *   如果按钮被选中，图像查看器进入 ROI 选择模式 (`InteractionMode.SELECT_ROI`) ([`UI/detectTabs/camera_tab.py:517`](UI/detectTabs/camera_tab.py:517))。
    *   如果取消选中，图像查看器返回普通查看模式 (`InteractionMode.VIEW`)。
*   **处理 ROI 选择结果 (`_on_roi_selected_from_viewer`)**:
    *   当用户在图像查看器上完成 ROI 拖拽选择后，此方法被触发 ([`UI/detectTabs/camera_tab.py:411`](UI/detectTabs/camera_tab.py:411))。
    *   自动取消 ROI 按钮的选中状态，并将查看器模式改回 `VIEW` ([`UI/detectTabs/camera_tab.py:526`](UI/detectTabs/camera_tab.py:526))。
    *   获取选择的矩形区域坐标。
    *   **TODO**: 包含将 ROI 设置到相机的逻辑（如果相机支持）([`UI/detectTabs/camera_tab.py:532`](UI/detectTabs/camera_tab.py:532))。

## 9. 状态与错误处理

*   **记录状态 (`log_status`)**:
    *   用于在程序执行关键操作时，将信息记录到日志文件并更新 UI 上的状态标签 (`_status_label`) ([`UI/detectTabs/camera_tab.py:1169`](UI/detectTabs/camera_tab.py:1169))。
*   **显示错误 (`show_error`)**:
    *   用于在发生错误时，将错误信息记录到日志文件，更新状态标签，并可选地弹出错误对话框 ([`UI/detectTabs/camera_tab.py:1174`](UI/detectTabs/camera_tab.py:1174))。

## 10. 关闭应用程序

*   **窗口关闭事件 (`closeEvent`)**:
    *   当用户关闭主窗口时触发 ([`UI/detectTabs/camera_tab.py:1181`](UI/detectTabs/camera_tab.py:1181))。
    *   停止显示更新定时器。
    *   如果相机正在运行，停止采集 (`self.camera.stop_grabbing()`)。
    *   如果相机已连接，关闭相机连接 (`self.camera.close()`)。
    *   执行必要的清理操作。

# 代码详解

### 整合了相机硬件的控制逻辑和用户界面元素

1.  **`__init__(self, parent=None)` (构造函数, 行 70-112)**
    *   **目的:** 初始化 `CameraTabWidget` 这个主窗口。
    *   **过程:**
        *   调用父类 `QMainWindow` 的构造函数。
        *   初始化各种**状态变量**，用于跟踪相机状态（如 `self.camera` 对象、是否正在运行 `self.is_running`、当前帧 `self.current_frame`、相机 ID `self.camera_id`、是否连接 `self._camera_connected` 等）。
        *   初始化用于多线程处理图像帧的锁 (`self.frame_lock`) 和标志 (`self.new_frame_available`)。
        *   初始化用于计算和显示 FPS（每秒帧数）的变量。
        *   设置窗口标题和默认大小。
        *   调用 `_init_ui()` 方法来构建用户界面。
        *   调用 `_connect_signals_to_logic()` 方法将 UI 控件的信号连接到处理逻辑。
        *   调用 `_connect_core_signals()` 方法连接来自相机核心模块的信号。
        *   创建一个 `QTimer` (`self.timer`)，定时调用 `_update_display_and_fps()` 来更新图像显示和计算 FPS。
        *   使用 `QTimer.singleShot(100, self.initialize_camera_core)` 延迟 100 毫秒后调用相机核心初始化函数，避免阻塞 UI 线程。
        *   调用 `_update_ui_state()` 更新 UI 元素的初始状态（例如，禁用某些按钮）。

2.  **`_init_ui(self)` (行 114-386)**
    *   **目的:** 创建和布局窗口中的所有 UI 元素。
    *   **过程:**
        *   创建一个主 `QWidget` 作为中心部件，并设置 `QVBoxLayout` 为主布局。
        *   创建一个 `QSplitter` (`_main_splitter`) 将窗口分为左右两部分：左侧是预览区，右侧是控制面板。
        *   **左侧预览区 (`_preview_widget`):**
            *   包含一个**工具栏 (`_toolbar`)**，上面有按钮：连接/断开相机 (`_connect_button`)、开始/停止视频流 (`_stream_button`)、拍照（软触发） (`_capture_button`)、选择 ROI (`_roi_button`)。按钮应用了自定义样式。
            *   包含一个**图像查看器容器 (`_viewer_container`)**，里面放置了 `ImageViewerWidget` (`_image_viewer`) 用于显示相机图像，并在其右上角覆盖了一个 `QLabel` (`_fps_label`) 来显示 FPS。
        *   **右侧控制面板 (`_control_widget`):**
            *   使用 `QVBoxLayout` 垂直排列多个可折叠面板 (`CollapsiblePanel`)。
            *   **相机连接与选择面板 (`_camera_list_panel`):** 包含设备选择下拉框 (`_camera_combo`)、模拟模式复选框 (`_simulation_check`) 和刷新列表按钮 (`_refresh_button`)。
            *   **相机参数面板 (`_camera_params_panel`):** 包含曝光时间、增益、白平衡的滑块 (`_exposure_slider`, `_gain_slider`, `_wb_slider`)、显示当前值的标签 (`_exposure_value_label`, etc.)、自动模式复选框 (`_auto_exposure_check`, etc.) 和应用参数按钮 (`_apply_params_btn`)。布局使用 `QGridLayout`。
            *   **图像与触发面板 (`_image_settings_panel`):** 包含分辨率下拉框 (`_resolution_combo`)、帧率设置 (`_fps_spin`)、像素格式下拉框 (`_pixel_format_combo`) 和触发模式下拉框 (`_trigger_combo`)。
            *   **状态信息面板 (`_status_panel`):** 包含一个状态标签 (`_status_label`) 显示操作信息或错误，以及一个相机信息标签 (`_camera_info_label`) 显示连接相机的详细信息。
        *   将预览区和控制面板添加到 `QSplitter` 中，并设置初始比例。
        *   将 `QSplitter` 添加到主布局。
        *   最后再次调用 `_update_ui_state()` 确保 UI 初始状态正确。

3.  **`_on_viewer_resize(self, event)` (行 387-395)**
    *   **目的:** 当图像查看器容器大小改变时，重新计算并移动 FPS 标签到右上角。
    *   **触发:** 图像查看器容器 (`_viewer_container`) 的 `resizeEvent`。

4.  **`_connect_signals_to_logic(self)` (行 397-428)**
    *   **目的:** 将 UI 控件发出的信号连接到相应的处理函数（槽函数）。
    *   **过程:** 将各个按钮的 `clicked` 信号、复选框的 `stateChanged` 信号、滑块的 `valueChanged` 信号、下拉框的 `currentIndexChanged` 信号等，连接到 `CameraTabWidget` 类中定义的处理方法（如 `toggle_connection`, `toggle_stream`, `_on_exposure_slider_changed` 等）。

5.  **`_connect_core_signals(self)` (行 429-439)**
    *   **目的:** 连接来自相机核心逻辑（通过 `signal_manager`）的信号。
    *   **过程:** 主要连接 `signal_manager.frame_ready_signal` 到 `handle_frame` 方法，这样当相机核心捕获到新帧时，`handle_frame` 会被调用。包含错误处理以防 `signal_manager` 未正确配置。

6.  **`_update_ui_state(self)` (行 443-507)**
    *   **目的:** 根据相机是否连接 (`_camera_connected`) 和是否正在传输视频流 (`is_running`)，动态更新 UI 控件的启用/禁用状态、文本内容和样式。
    *   **过程:**
        *   更新连接按钮的文本（"连接相机" 或 "断开相机"）和样式（颜色）。
        *   启用/禁用相机选择下拉框、刷新按钮、模拟模式复选框。
        *   更新视频流按钮的文本（"开始视频流" 或 "停止视频流"）、图标和样式。
        *   根据是否连接、是否流式传输以及触发模式，启用/禁用拍照按钮。
        *   根据是否连接且有图像显示，启用/禁用 ROI 按钮。
        *   根据是否连接、是否流式传输以及是否勾选了自动模式，启用/禁用参数滑块、帧率设置、应用参数按钮和自动模式复选框。
        *   启用/禁用图像设置（分辨率、像素格式、触发模式）的相关控件。

7.  **`_on_camera_selection_change(self, index)` (行 508-512)**
    *   **目的:** 处理相机下拉列表选择项改变的事件。
    *   **当前实现:** 为空，因为实际的连接逻辑是在点击“连接”按钮时根据当前选择执行的。

8.  **`_on_roi_button_toggled(self, checked)` (行 514-521)**
    *   **目的:** 处理 ROI（感兴趣区域）选择按钮的点击事件。
    *   **过程:** 如果按钮被选中 (`checked` is True)，则将图像查看器的交互模式设置为 `InteractionMode.SELECT_ROI`，允许用户在图像上拖动选择区域，并记录状态信息。如果取消选中，则将模式设置回 `InteractionMode.VIEW`。

9.  **`_on_roi_selected_from_viewer(self, rect)` (行 523-533)**
    *   **目的:** 当用户在图像查看器中完成 ROI 选择后，处理该事件。
    *   **触发:** 图像查看器 (`_image_viewer.get_viewer()`) 发出的 `roi_selected` 信号。
    *   **过程:**
        *   自动取消选中 ROI 按钮，并将交互模式设置回 `VIEW`。
        *   获取选择的矩形区域坐标 (`rect`)。
        *   记录选择的 ROI 信息。
        *   **TODO:** 这里标记了需要添加将 ROI 设置到实际相机硬件的逻辑（如果相机支持）。

10. **`_on_exposure_slider_changed(self, value)`, `_on_gain_slider_changed(self, value)`, `_on_wb_slider_changed(self, value)` (行 534-542)**
    *   **目的:** 当曝光、增益或白平衡滑块的值改变时，更新旁边显示具体数值的标签。

11. **`_on_auto_exposure_changed(self, state)`, `_on_auto_gain_changed(self, state)`, `_on_auto_wb_changed(self, state)` (行 544-563)**
    *   **目的:** 处理自动曝光/增益/白平衡复选框状态改变的事件。
    *   **过程:**
        *   根据复选框是否被选中 (`state == Qt.Checked`)，禁用或启用对应的手动调节滑块。
        *   **TODO:** 标记了需要添加调用相机方法来实际设置自动模式的逻辑（如果相机支持）。
        *   记录状态信息。

12. **`_on_fps_spin_changed(self, value)` (行 565-569)**
    *   **目的:** 当目标帧率 `QSpinBox` 的值改变时，记录状态信息。
    *   **注意:** 实际应用帧率通常在点击“应用参数”按钮或开始视频流时发生。

13. **`initialize_camera_core(self)` (行 574-604)**
    *   **目的:** 初始化相机核心部分，主要是创建相机对象。
    *   **过程:**
        *   使用 `CameraFactoryManager` 获取可用的相机类型。
        *   优先选择 'hikvision' 类型，否则选择第一个可用的类型。
        *   使用 `CameraFactoryManager.create_camera()` 创建相机实例 (`self.camera`)。
        *   处理创建失败的情况。
        *   根据 UI 复选框设置相机的初始模拟模式状态 (`self.camera._is_simulation`)。
        *   记录初始化成功或失败的状态。
        *   如果成功，调用 `refresh_devices()` 尝试立即列出设备。
        *   包含详细的错误处理和日志记录。

14. **`refresh_devices(self)` (行 606-669)**
    *   **目的:** 查找连接到系统的可用相机设备，并更新 UI 上的下拉列表。
    *   **过程:**
        *   检查相机核心是否已初始化，如果未初始化则尝试初始化。
        *   确保相机的模拟模式与 UI 设置一致。
        *   调用 `self.camera.enumerate_devices()` 获取设备列表。
        *   清空下拉列表 (`_camera_combo`)。
        *   添加 "自动选择" 选项。
        *   遍历找到的设备，提取型号、序列号、设备 ID、IP 地址等信息。
        *   构建要在下拉列表中显示的文本。
        *   **特殊逻辑:** 检查设备型号是否包含 "MV-CI003-GL-N6"（目标相机），如果是，则在文本中添加标记，并尝试自动选中该设备。
        *   将设备信息添加到下拉列表，并将 `device_id` 作为 `userData` 存储，方便后续连接时获取。
        *   处理未找到设备的情况（区分模拟模式是否启用）。
        *   记录找到的设备数量或未找到设备的状态。
        *   包含错误处理和日志记录。
        *   最后调用 `_update_ui_state()` 更新 UI。

15. **`toggle_simulation_mode(self)` (行 670-681)**
    *   **目的:** 响应模拟模式复选框的点击，切换模拟模式状态。
    *   **过程:**
        *   更新 `self.use_simulation` 变量。
        *   如果相机对象已创建，更新其 `_is_simulation` 属性。
        *   记录状态变化。
        *   延迟调用 `refresh_devices()`，因为切换模拟模式后需要重新枚举设备（模拟设备或真实设备）。
        *   调用 `_update_ui_state()`。

16. **`toggle_connection(self)` (行 683-791)**
    *   **目的:** 处理连接/断开相机按钮的点击事件。
    *   **过程:**
        *   **断开连接 (如果 `_camera_connected` 为 True):**
            *   如果正在采集图像 (`is_running`)，先调用 `stop_grabbing()`。
            *   调用 `self.camera.close()` 关闭相机连接。
            *   更新状态变量 (`_camera_connected`, `camera_id`)。
            *   清空图像显示和相机信息标签。
            *   处理关闭失败或异常的情况。
        *   **连接 (如果 `_camera_connected` 为 False):**
            *   确定要连接的 `device_id`：
                *   如果用户在下拉列表中选择了特定设备，则获取其 `userData`（即 `device_id`）。包含从显示文本中解析 ID 的后备逻辑。
                *   如果选择了 "自动选择"：
                    *   若无真实设备但启用了模拟模式，则使用 "simulation_id"。
                    *   若有真实设备，则优先选择标记为 "目标相机" 的设备，否则选择列表中的第一个设备。
                    *   若无设备也未启用模拟模式，则报错。
            *   处理无法确定 `device_id` 的情况。
            *   记录正在连接的状态。
            *   调用 `self.camera.open(device_id_to_connect)` 打开相机连接。
            *   如果成功：
                *   更新状态变量 (`_camera_connected`, `camera_id`)。
                *   发出 `camera_status_changed` 信号。
                *   调用 `update_parameter_display()` 读取并显示相机当前参数。
                *   调用 `change_trigger_mode()` 应用 UI 上选择的初始触发模式。
            *   处理连接失败或异常的情况。
        *   最后调用 `_update_ui_state()` 更新 UI。

17. **`toggle_stream(self)` (行 794-804)**
    *   **目的:** 处理开始/停止视频流按钮的点击事件。
    *   **过程:** 检查相机是否连接，然后根据当前是否正在运行 (`is_running`) 调用 `start_grabbing()` 或 `stop_grabbing()`。

18. **`start_grabbing(self)` (行 805-831)**
    *   **目的:** 开始从相机采集图像。
    *   **过程:**
        *   检查是否已在运行或相机未连接。
        *   确保触发模式已设置 (`change_trigger_mode()`)。
        *   **可选:** 在开始前应用当前参数 (`apply_parameters()`)。
        *   调用 `self.camera.start_grabbing()`。
        *   如果成功，更新 `is_running` 状态，重置 FPS 计数器。
        *   处理失败或异常。
        *   调用 `_update_ui_state()`。

19. **`stop_grabbing(self)` (行 833-854)**
    *   **目的:** 停止从相机采集图像。
    *   **过程:**
        *   检查是否已停止或相机未连接。
        *   调用 `self.camera.stop_grabbing()`。
        *   如果成功，更新 `is_running` 状态。
        *   **可选:** 清除最后显示的图像。
        *   处理失败或异常。
        *   调用 `_update_ui_state()`。

20. **`change_trigger_mode(self)` (行 856-878)**
    *   **目的:** 将 UI 下拉列表中选择的触发模式设置到相机。
    *   **过程:**
        *   检查相机是否连接。
        *   获取下拉列表当前选择的索引和文本。
        *   调用 `self.camera.set_trigger_mode(trigger_mode_index)`。
        *   记录成功或失败的状态。
        *   如果设置成功，立即调用 `_update_ui_state()` 以更新依赖触发模式的控件状态（如拍照按钮）。
        *   如果失败，尝试从相机读回当前模式并恢复下拉列表的选择。
        *   处理异常。

21. **`trigger_once(self)` (行 880-897)**
    *   **目的:** 向相机发送一个软触发命令（用于拍照）。
    *   **过程:**
        *   检查是否正在运行视频流（即使是触发模式，通常也需要先 "start_grabbing"）。
        *   检查当前是否处于连续采集模式（软触发无效）。
        *   调用 `self.camera.trigger_once()`。
        *   记录成功或失败的状态。
        *   处理异常。

22. **`update_parameter_display(self)` (行 898-997)**
    *   **目的:** 从连接的相机读取当前的参数值，并更新 UI 上的滑块、标签、复选框等控件的显示。
    *   **过程:**
        *   检查相机是否连接。
        *   调用 `self.camera.get_parameter()` 获取参数字典。
        *   处理获取失败的情况，并更新相机信息标签。
        *   如果成功获取参数：
            *   **临时阻塞信号:** 阻止 UI 控件在被程序设置值时触发 `valueChanged` 等信号，避免无限循环或不必要的逻辑。
            *   根据从 `params` 字典中获取的值（如 'exposure_time', 'gain', 'frame_rate', 'width', 'height', 'pixel_format' 等），更新对应的滑块 (`setValue`)、标签 (`setText`)、SpinBox (`setValue`)、复选框 (`setChecked`)。包含将值限制在控件范围内的逻辑。
            *   **更新相机信息标签 (`_camera_info_label`):** 显示更详细的相机信息，包括 ID、型号、SN、IP、分辨率、像素格式、帧率、曝光、增益等。
        *   处理异常。
        *   **解除信号阻塞:** 在 `finally` 块中确保信号被解除阻塞。

23. **`apply_parameters(self, log_success=True)` (行 998-1104)**
    *   **目的:** 将用户在 UI 上设置的参数值（曝光、增益、帧率、自动模式等）应用到相机硬件。
    *   **过程:**
        *   检查相机是否连接以及是否正在运行视频流（通常建议停止流再应用参数）。
        *   创建一个空字典 `params_to_set`。
        *   从 UI 控件（滑块、SpinBox、复选框）读取当前值，并将它们添加到 `params_to_set` 字典中，使用相机期望的参数键名（如 'exposure_time', 'gain', 'frame_rate', 'auto_exposure' 等）。
        *   **TODO:** 标记了需要添加读取分辨率和像素格式的代码（如果实现）。
        *   记录将要应用的参数。
        *   **尝试统一设置:** 检查相机对象是否有 `set_parameter` 方法。如果有，则调用 `self.camera.set_parameter(**params_to_set)`，将字典作为关键字参数传递。处理返回的结果（可能是包含各参数成功标志的字典，或整体布尔值）。
        *   **后备方案:** 如果没有统一的 `set_parameter` 方法，则尝试调用单独的设置方法（如 `set_exposure`, `set_gain` 等，如果存在）。记录通过此方式设置的成功率。
        *   记录应用结果（成功、部分失败、整体失败）。
        *   **延迟刷新显示:** 使用 `QTimer.singleShot` 延迟调用 `update_parameter_display()`，以从相机读回实际生效的参数值并更新 UI。
        *   处理异常。
        *   调用 `_update_ui_state()`，因为应用参数（特别是自动模式）可能会影响其他控件的状态。

24. **`handle_frame(self, frame, camera_id)` (行 1106-1116)**
    *   **目的:** 作为槽函数，接收由相机核心通过 `frame_ready_signal` 发送过来的新图像帧。
    *   **触发:** `signal_manager.frame_ready_signal`。
    *   **过程:**
        *   在线程锁 (`frame_lock`) 内执行，保证线程安全。
        *   将接收到的 `frame` 复制一份存储到 `self.current_frame`，避免与相机回调线程的数据冲突。
        *   更新 `self.camera_id`。
        *   设置 `self.new_frame_available = True` 标志，通知 UI 更新线程有新帧可用。
        *   增加帧计数器 `self.fps_count`。

25. **`_update_display_and_fps(self)` (行 1118-1167)**
    
    该方法的主要功能是：
    1.  **安全地更新图像显示**：它从共享变量中获取最新的图像帧，处理不同格式（BGR、BGRA、灰度），并将其转换为 `QPixmap` 以在 Qt UI 的图像查看器中显示。通过使用线程锁（`self.frame_lock`）来确保多线程环境下的数据一致性。
    2.  **计算并显示FPS**：它会定期（默认每秒）计算帧率，并将结果更新到 UI 上的一个标签中。
    
    关键组件和交互包括：
    *   `self.frame_lock`：用于同步对共享帧数据和 FPS 计数器的访问。
    *   `self.current_frame` 和 `self.new_frame_available`：用于在线程间传递最新的图像帧。
    *   图像格式转换逻辑：根据图像的 `shape`（通道数）将其转换为合适的 `QImage` 格式。
    *   `self._image_viewer`：用于显示图像的 UI 控件。
    *   `self._fps_label`：用于显示 FPS 值的 UI 控件。
    *   FPS 计算逻辑：基于时间间隔和接收到的帧数来计算。
    
    重要的模式或技术包括：
    *   **线程安全**：使用锁来保护共享资源。
    *   **UI 更新在主线程**：确保 UI 操作在正确的线程中执行。
    *   **关注点分离**：将帧获取、帧处理和 FPS 计算逻辑分开。
    *   **防御性编程**：错误处理和对不支持格式的检查。

26. **`log_status(self, message)` (行 1169-1172)**
    *   **目的:** 封装记录普通状态信息的操作。
    *   **过程:** 调用 `logger.info()` 记录日志，并更新 UI 上的状态标签 (`_status_label`)。

27. **`show_error(self, message)` (行 1174-1179)**
    *   **目的:** 封装记录和显示错误信息的操作。
    *   **过程:** 调用 `logger.error()` 记录错误日志，更新状态标签显示错误信息，并**可选地**（代码中注释掉了）弹出一个 `QMessageBox` 提示用户。

28. **`closeEvent(self, event)` (行 1181-1198)**
    *   **目的:** 在用户关闭窗口时执行清理操作。
    *   **触发:** 窗口关闭事件。
    *   **过程:**
        *   记录正在关闭的状态。
        *   停止用于更新显示的定时器 (`self.timer.stop()`)。
        *   检查相机对象是否存在。
        *   如果相机正在运行，调用 `stop_grabbing()`。
        *   如果相机已连接，调用 `close()`。
        *   包含相机清理过程中的异常处理。
        *   记录清理完成。
        *   调用父类的 `closeEvent` 以允许窗口正常关闭。

29. **`main()` (行 1202-1211)**
    *   **目的:** 应用程序的入口函数。
    *   **过程:**
        *   创建 `QApplication` 实例。
        *   **可选:** 应用样式。
        *   创建 `CameraTabWidget` 窗口实例。
        *   显示窗口 (`window.show()`)。
        *   启动 Qt 事件循环 (`app.exec_()`)。

30. **`if __name__ == "__main__":` (行 1213-1218)**
    *   **目的:** 确保 `main()` 函数只在直接运行此脚本时执行。
    *   **过程:**
        *   创建日志目录（如果不存在）。
        *   调用 `main()` 函数启动应用。

**总结:**

`camera_tab.py` 实现了一个功能相对完善的相机控制面板。它通过 `CameraTabWidget` 类构建了用户界面，包含了图像预览、参数调整（曝光、增益、帧率、触发模式等）、设备选择、状态显示等功能。代码结构清晰，将 UI 构建、信号连接、状态更新和相机核心逻辑调用分离开来。它利用 `QTimer` 和线程锁来处理来自相机核心的图像帧，并在 UI 线程中安全地更新显示和计算 FPS。同时，它也包含了较好的错误处理和日志记录机制。