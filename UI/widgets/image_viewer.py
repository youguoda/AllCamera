"""
图像查看器组件
-----------
提供图像查看功能，是EnhancedImageViewer的简单封装
"""

from UI.widgets.enhanced_image_viewer import ImageViewerWidget


# 为向后兼容再导出一个ImageViewer类
class ImageViewer(ImageViewerWidget):
    """
    图像查看器
    提供图像显示、缩放、平移等基本功能
    为了与旧代码兼容而存在
    """
    def __init__(self, parent=None):
        super().__init__(parent)

