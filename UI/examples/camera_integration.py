"""
相机集成示例

展示如何在应用程序中集成相机模型、视图和控制器
"""
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget

from UI.models.camera_model import CameraModel
from UI.views.camera_view import CameraView
from UI.controllers.camera_controller import CameraController
from core.utils.logger import get_logger


class CameraIntegrationApp(QMainWindow):
    """
    相机集成示例应用
    展示如何在应用程序中集成相机MVC组件
    """
    
    def __init__(self):
        """初始化示例应用"""
        super().__init__()
        self.logger = get_logger()
        
        # 设置窗口属性
        self.setWindowTitle("相机集成示例")
        self.resize(1200, 800)
        
        # 创建中央窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建MVC组件
        self._setup_mvc()
        
        # 将视图添加到主布局
        main_layout.addWidget(self._camera_view)
        
    def _setup_mvc(self):
        """创建和连接MVC组件"""
        # 创建模型
        self._camera_model = CameraModel()
        
        # 创建视图
        self._camera_view = CameraView()
        
        # 创建控制器
        self._camera_controller = CameraController(self._camera_model)
        
        # 连接视图和控制器
        self._camera_controller.setup_view_connections(self._camera_view)
        
        # 连接视图的通用事件信号
        self._camera_view.event_signal.connect(self._handle_view_event)
        
    
    def _handle_view_event(self, event_type, event_data):
        """
        处理来自视图的通用事件
        
        Args:
            event_type: 事件类型
            event_data: 事件数据
        """
        self.logger.info(f"处理事件: {event_type}, 数据: {event_data}")
        
        if event_type == "refresh_camera_list":
            # 刷新相机列表
            self._camera_controller.enumerate_devices()


def main():
    """应用程序入口点"""
    app = QApplication(sys.argv)
    
    # 创建并显示应用窗口
    window = CameraIntegrationApp()
    window.show()
    
    # 运行应用
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
