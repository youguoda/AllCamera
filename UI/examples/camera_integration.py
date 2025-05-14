"""
相机集成示例

展示如何在应用程序中集成相机模型、视图和控制器
"""
import sys
import os
from typing import Optional # Added for type hinting

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PyQt5.QtCore import QTimer # For delayed cleanup if needed

from UI.models.camera_model import CameraModel
from UI.views.camera_view import CameraView
from UI.controllers.camera_controller import CameraController
from core.utils.logger import get_logger # Assuming setup_logging is done elsewhere or not needed for example

class CameraIntegrationApp(QMainWindow):
    """
    相机集成示例应用
    展示如何在应用程序中集成相机MVC组件
    """

    def __init__(self):
        """初始化示例应用"""
        super().__init__()
        self.logger = get_logger()
        self.logger.info("Starting CameraIntegrationApp...")

        self.setWindowTitle("相机 MVC 集成示例")
        self.resize(1280, 720)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self._camera_model: Optional[CameraModel] = None
        self._camera_view: Optional[CameraView] = None
        self._camera_controller: Optional[CameraController] = None
        
        self._setup_mvc()

        if self._camera_view:
            main_layout.addWidget(self._camera_view)
        else:
            self.logger.error("CameraView was not initialized during _setup_mvc.")
            error_label = QLabel("错误：相机视图未能初始化。请检查日志。")
            main_layout.addWidget(error_label)

    def _setup_mvc(self):
        """创建和连接MVC组件"""
        self.logger.info("Setting up MVC components...")
        try:
            self._camera_model = CameraModel()
            self._camera_view = CameraView() # View is instantiated
            
            # Controller takes model and view, and sets up connections internally
            self._camera_controller = CameraController(model=self._camera_model, view=self._camera_view)
            
            # The CameraController's __init__ and _connect_signals methods should handle
            # all necessary signal/slot connections between Model, View, and Controller.
            # Any application-level specific connections or event handling beyond MVC can be done here.
            # For example, if the view had a very generic signal not directly tied to camera actions:
            # self._camera_view.some_generic_view_signal.connect(self._handle_generic_view_event)
            
            self.logger.info("MVC components set up successfully.")

        except Exception as e:
            self.logger.error(f"Error during MVC setup: {e}", exc_info=True)
            # Fallback or error display if MVC setup fails critically
            # Ensure layout exists before trying to add widget to it
            layout = self.centralWidget().layout()
            if layout is not None:
                 error_label = QLabel(f"MVC 初始化失败: {e}")
                 layout.addWidget(error_label)
            # Or re-raise the exception if this is a critical failure
            # raise


    # def _handle_generic_view_event(self, data):
    #     """Example handler for a generic event from the view."""
    #     self.logger.info(f"App received generic view event with data: {data}")

    def closeEvent(self, event):
        """处理窗口关闭事件，确保资源得到清理。"""
        self.logger.info("CameraIntegrationApp closing...")
        if self._camera_controller:
            if hasattr(self._camera_controller, 'cleanup') and callable(self._camera_controller.cleanup):
                self.logger.info("Cleaning up CameraController...")
                self._camera_controller.cleanup()
        
        if self._camera_model:
            if hasattr(self._camera_model, 'cleanup') and callable(self._camera_model.cleanup):
                self.logger.info("Cleaning up CameraModel...")
                self._camera_model.cleanup()
        
        # View cleanup is usually handled by Qt's parent-child mechanism if it's a QWidget
        
        super().closeEvent(event)
        self.logger.info("CameraIntegrationApp closed.")


def main():
    """应用程序入口点"""
    # It's good practice to setup logging as early as possible.
    # from core.utils.logger import setup_logging # Example import
    # setup_logging(level="INFO") # Example setup

    app = QApplication(sys.argv)
    
    window = CameraIntegrationApp()
    window.show()
    
    exit_code = app.exec_()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
