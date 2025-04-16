"""
增强型图像查看器
-------------
提供图像显示、缩放、平移、ROI选择、测量功能，支持高性能渲染和图像处理
"""

from enum import Enum, auto
import weakref
import time
from functools import lru_cache

from PyQt5.QtCore import Qt, QRectF, QPointF, pyqtSignal, QLineF, QSize, QTimer ,QRectF
from PyQt5.QtGui import (QPixmap, QPainter, QPen, QBrush, QColor,
                        QImage, QFont, QTransform, QPainterPath, QCursor)
from PyQt5.QtWidgets import (QWidget, QGraphicsView, QGraphicsScene, 
                            QGraphicsPixmapItem, QGraphicsRectItem, QGraphicsLineItem,
                            QGraphicsPathItem, QGraphicsTextItem,
                            QMenu, QAction, QLabel, QVBoxLayout, QFrame,
                            QToolTip, QActionGroup, QSlider, QHBoxLayout)

from UI.utils.ui_constants import LIGHT_COLORS


class InteractionMode(Enum):
    """交互模式枚举"""
    VIEW = auto()            # 查看模式 - 允许缩放和平移
    SELECT_ROI = auto()      # ROI选择模式
    MEASURE = auto()         # 测量模式
    MULTI_ROI = auto()       # 多ROI模式
    COLOR_PICKER = auto()    # 颜色拾取模式
    ANNOTATIONS = auto()     # 注释模式


class EnhancedImageViewer(QGraphicsView):
    """
    增强型图像查看器
    提供图像显示、缩放、平移、ROI选择、测量功能，支持高性能渲染和图像处理
    """
    
    # 自定义信号
    roi_selected = pyqtSignal(QRectF)  # ROI选择完成信号
    zoom_changed = pyqtSignal(float)   # 缩放比例变化信号
    mouse_position = pyqtSignal(QPointF)  # 鼠标位置信号
    color_picked = pyqtSignal(QColor, QPointF)  # 颜色拾取信号
    measurements_updated = pyqtSignal(list)  # 测量更新信号
    multiple_rois_selected = pyqtSignal(list)  # 多ROI选择信号
    
    def __init__(self, parent=None):
        """初始化图像查看器"""
        super().__init__(parent)
        
        # 创建场景
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        
        # 图像项
        self._pixmap_item = None
        self._image = QImage()
        self._original_image = QImage()
        
        # 性能优化
        self._image_cache = {}  # 缓存最近使用的图像
        self._cache_size = 5    # 缓存大小
        self._last_render_time = 0  # 最后渲染时间
        self._render_timer = QTimer(self)  # 延迟渲染计时器
        self._render_timer.setSingleShot(True)
        self._render_timer.timeout.connect(self._delayed_render)
        self._viewport_only = True  # 仅渲染可见区域
        
        # ROI相关
        self._roi_rect = None
        self._roi_start = QPointF()
        self._roi_end = QPointF()
        self._roi_is_drawing = False
        self._multi_rois = []  # 存储多个ROI
        
        # 测量相关
        self._measure_lines = []  # 测量线段列表
        self._measure_start = QPointF()
        self._measure_points = []  # 测量点列表
        self._current_measure = None  # 当前正在绘制的测量
        self._measure_texts = []  # 测量文本列表
        self._pixel_size_mm = 1.0  # 每像素的物理尺寸(mm)
        
        # 标注相关
        self._annotations = []  # 标注列表
        self._current_annotation = None  # 当前正在编辑的标注
        
        # 缩放相关
        self._zoom_factor = 1.0
        self._min_zoom = 0.1
        self._max_zoom = 20.0  # 增加最大缩放比例
        self._zoom_speed = 1.25  # 缩放速度因子
        
        # 状态和配置
        self._interaction_mode = InteractionMode.VIEW
        self._show_info = True
        self._show_grid = False
        self._grid_size = 50
        self._grid_color = QColor(200, 200, 200, 100)
        self._crosshair_enabled = False  # 十字线
        
        # 设置视图属性
        self.setRenderHint(QPainter.Antialiasing, True)
        self.setRenderHint(QPainter.SmoothPixmapTransform, True)
        self.setOptimizationFlag(QGraphicsView.DontAdjustForAntialiasing, True)
        self.setOptimizationFlag(QGraphicsView.DontSavePainterState, True)
        self.setViewportUpdateMode(QGraphicsView.SmartViewportUpdate)
        self.setCacheMode(QGraphicsView.CacheBackground)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet("""
            QGraphicsView {
                border: 1px solid #e0e0e0;
                background-color: #f5f5f5;
            }
        """)
        
        # 设置右键菜单
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
        # 初始化LRU缓存装饰器
        self._initialize_caches()
    
    def _initialize_caches(self):
        """初始化缓存机制"""
        # 使用lru_cache装饰内部方法以提高性能
        self._cached_convert_scene_to_image = lru_cache(maxsize=10)(self._convert_scene_to_image)
        self._cached_compute_grid = lru_cache(maxsize=5)(self._compute_grid)
    
    def _delayed_render(self):
        """延迟渲染，用于提高性能"""
        self.viewport().update()
    
    def _convert_scene_to_image(self, width, height):
        """将当前场景转换为图像 (被缓存)"""
        if not self._pixmap_item:
            return QImage()
            
        # 创建目标图像
        result = QImage(width, height, QImage.Format_ARGB32_Premultiplied)
        result.fill(Qt.transparent)
        
        # 设置绘制参数
        painter = QPainter(result)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        
        # 绘制场景到图像
        self._scene.render(painter)
        painter.end()
        
        return result
        
    def capture_view(self):
        """捕获当前视图为图像"""
        viewport_rect = self.viewport().rect()
        return self._cached_convert_scene_to_image(viewport_rect.width(), viewport_rect.height())
    
    def _compute_grid(self, left, top, right, bottom, grid_size):
        """计算网格线 (被缓存)"""
        lines = []
        # 垂直线
        x = left - (left % grid_size)
        while x < right:
            lines.append(QLineF(QPointF(x, top), 
                               QPointF(x, bottom)))
            x += grid_size
        
        # 水平线
        y = top - (top % grid_size)
        while y < bottom:
            lines.append(QLineF(QPointF(left, y), 
                               QPointF(right, y)))
            y += grid_size
            
        return lines
    
    def set_image(self, image):
        """
        设置显示图像，支持多种输入格式，并优化性能
        
        Args:
            image: QImage或QPixmap或numpy数组
        """
        # 记录开始时间，用于性能分析
        start_time = time.time()
        
        # 清除当前图像
        if self._pixmap_item:
            self._scene.removeItem(self._pixmap_item)
            self._pixmap_item = None
        
        if self._roi_rect:
            self._scene.removeItem(self._roi_rect)
            self._roi_rect = None
        
        # 清除多ROI
        for roi in self._multi_rois:
            if roi in self._scene.items():
                self._scene.removeItem(roi)
        self._multi_rois.clear()
        
        # 清除测量线
        for line in self._measure_lines:
            if line in self._scene.items():
                self._scene.removeItem(line)
        self._measure_lines.clear()
        
        for text in self._measure_texts:
            if text in self._scene.items():
                self._scene.removeItem(text)
        self._measure_texts.clear()
        
        # 转换图像格式
        if isinstance(image, QPixmap):
            pixmap = image
            self._image = pixmap.toImage()
        elif isinstance(image, QImage):
            self._image = image
            pixmap = QPixmap.fromImage(image)
        elif image is None:
            self._scene.clear()
            self._image = QImage()
            self._original_image = QImage()
            return
        else:
            # 尝试从numpy数组转换
            try:
                import numpy as np
                import cv2
                if isinstance(image, np.ndarray):
                    # 检查是否已在缓存中
                    cache_key = id(image)
                    if cache_key in self._image_cache:
                        pixmap = self._image_cache[cache_key]
                        self._image = pixmap.toImage()
                    else:
                        # 根据通道数确定格式
                        if len(image.shape) == 2:  # 灰度图
                            height, width = image.shape
                            self._image = QImage(image.data, width, height, width, QImage.Format_Grayscale8)
                        else:  # 彩色图
                            # OpenCV是BGR顺序，Qt需要RGB顺序
                            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                            height, width, channels = rgb_image.shape
                            bytes_per_line = channels * width
                            self._image = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format_RGB888)
                        
                        # 将图像转换为QPixmap并缓存
                        pixmap = QPixmap.fromImage(self._image)
                        self._update_cache(cache_key, pixmap)
                else:
                    return  # 不支持的格式
            except ImportError:
                print("Warning: numpy or cv2 not available for image conversion")
                return
        
        # 保存原始图像
        self._original_image = self._image
        
        # 创建新的图像项
        self._pixmap_item = QGraphicsPixmapItem(pixmap)
        self._scene.addItem(self._pixmap_item)
        
        # 启用交互
        self._pixmap_item.setAcceptHoverEvents(True)
        
        # 调整场景大小
        self._scene.setSceneRect(QRectF(pixmap.rect()))
        
        # 重置视图
        self.fit_in_view()
        
        # 记录性能指标
        self._last_render_time = time.time() - start_time
        
    def _update_cache(self, key, pixmap):
        """更新图像缓存，保持缓存大小限制"""
        # 如果缓存已满，移除最早的条目
        if len(self._image_cache) >= self._cache_size:
            # 移除一个最早的键
            oldest_key = next(iter(self._image_cache))
            del self._image_cache[oldest_key]
        
        # 添加新项到缓存
        self._image_cache[key] = pixmap
    
    def get_image(self):
        """获取当前显示的图像"""
        return self._image
    
    def pixmap(self):
        """获取当前显示的图像Pixmap，如果没有则返回None"""
        if self._pixmap_item:
            return self._pixmap_item.pixmap()
        return None
        
    def fit_in_view(self):
        """将图像适应视图大小"""
        if not self._pixmap_item:
            return
            
        self.fitInView(self._scene.sceneRect(), Qt.KeepAspectRatio)
        self._zoom_factor = 1.0
        self.zoom_changed.emit(self._zoom_factor)
    
    def set_interaction_mode(self, mode):
        """
        设置交互模式
        
        Args:
            mode: InteractionMode枚举值
        """
        self._interaction_mode = mode
        
        # 根据模式设置光标和拖动模式
        if mode == InteractionMode.VIEW:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            self.setCursor(Qt.OpenHandCursor)
        elif mode == InteractionMode.SELECT_ROI:
            self.setDragMode(QGraphicsView.NoDrag)
            self.setCursor(Qt.CrossCursor)
        elif mode == InteractionMode.MEASURE:
            self.setDragMode(QGraphicsView.NoDrag)
            self.setCursor(Qt.CrossCursor)
        elif mode == InteractionMode.MULTI_ROI:
            self.setDragMode(QGraphicsView.NoDrag)
            self.setCursor(Qt.CrossCursor)
        elif mode == InteractionMode.COLOR_PICKER:
            self.setDragMode(QGraphicsView.NoDrag)
            self.setCursor(Qt.CrossCursor)
        elif mode == InteractionMode.ANNOTATIONS:
            self.setDragMode(QGraphicsView.NoDrag)
            self.setCursor(Qt.CrossCursor)
    
    def reset_view(self):
        """重置视图（原始大小和位置）"""
        self.resetTransform()
        self._zoom_factor = 1.0
        self.zoom_changed.emit(self._zoom_factor)
    
    def clear_roi(self):
        """清除ROI选择框"""
        if self._roi_rect:
            self._scene.removeItem(self._roi_rect)
            self._roi_rect = None
    
    def clear_measurements(self):
        """清除所有测量"""
        for line in self._measure_lines:
            if line in self._scene.items():
                self._scene.removeItem(line)
        
        for text in self._measure_texts:
            if text in self._scene.items():
                self._scene.removeItem(text)
        
        self._measure_lines.clear()
        self._measure_texts.clear()
        self._current_measure = None
        
        # 发出空的测量列表信号
        self.measurements_updated.emit([])
    
    def clear_multi_rois(self):
        """清除所有多ROI"""
        for roi in self._multi_rois:
            if roi in self._scene.items():
                self._scene.removeItem(roi)
        
        self._multi_rois.clear()
        
        # 发出空的多ROI列表信号
        self.multiple_rois_selected.emit([])
    
    def clear_all(self):
        """清除所有ROI、测量和标注"""
        self.clear_roi()
        self.clear_measurements()
        self.clear_multi_rois()
    
    def toggle_grid(self, show):
        """
        切换网格显示
        
        Args:
            show: 是否显示网格
        """
        self._show_grid = show
        self.viewport().update()
    
    def set_grid_size(self, size):
        """
        设置网格大小
        
        Args:
            size: 网格大小（像素）
        """
        self._grid_size = max(10, size)
        if self._show_grid:
            self.viewport().update()
    
    def wheelEvent(self, event):
        """鼠标滚轮事件 - 用于缩放"""
        if self._interaction_mode != InteractionMode.VIEW:
            return
            
        # 获取鼠标位置和当前场景位置
        view_pos = event.pos()
        scene_pos = self.mapToScene(view_pos)
        
        # 计算缩放因子
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor
        
        # 获取缩放方向
        if event.angleDelta().y() > 0:
            # 放大
            zoom_factor = zoom_in_factor
            self._zoom_factor *= zoom_factor
        else:
            # 缩小
            zoom_factor = zoom_out_factor
            self._zoom_factor *= zoom_factor
        
        # 限制缩放范围
        self._zoom_factor = max(self._min_zoom, min(self._max_zoom, self._zoom_factor))
        
        # 执行缩放
        self.scale(zoom_factor, zoom_factor)
        
        # 发出缩放变化信号
        self.zoom_changed.emit(self._zoom_factor)
        
        # 防止事件传递
        event.accept()
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            if self._interaction_mode == InteractionMode.SELECT_ROI:
                # 开始绘制ROI
                self._roi_start = self.mapToScene(event.pos())
                self._roi_end = self._roi_start
                self._roi_is_drawing = True
                
                # 创建或更新ROI矩形
                if self._roi_rect:
                    self._scene.removeItem(self._roi_rect)
                
                self._roi_rect = QGraphicsRectItem(QRectF(self._roi_start, self._roi_end))
                self._roi_rect.setPen(QPen(QColor(LIGHT_COLORS["PRIMARY"]), 2, Qt.DashLine))
                self._roi_rect.setBrush(QBrush(QColor(LIGHT_COLORS["PRIMARY"] + "40")))  # 半透明填充
                self._scene.addItem(self._roi_rect)
                
                event.accept()
                return
            elif self._interaction_mode == InteractionMode.VIEW:
                # 设置拖动光标
                self.setCursor(Qt.ClosedHandCursor)
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        scene_pos = self.mapToScene(event.pos())
        self.mouse_position.emit(scene_pos)
        
        # 如果启用了十字线，在鼠标移动时更新显示
        if self._crosshair_enabled:
            self.viewport().update()
        
        if self._interaction_mode == InteractionMode.SELECT_ROI and self._roi_is_drawing:
            # 更新ROI结束点
            self._roi_end = scene_pos
            
            # 计算矩形坐标
            rect = QRectF(self._roi_start, self._roi_end).normalized()
            
            # 更新ROI矩形
            if self._roi_rect:
                self._roi_rect.setRect(rect)
            
            event.accept()
            return
        elif self._interaction_mode == InteractionMode.MULTI_ROI and self._roi_is_drawing:
            # 更新ROI结束点
            self._roi_end = scene_pos
            
            # 计算矩形坐标
            rect = QRectF(self._roi_start, self._roi_end).normalized()
            
            # 更新当前ROI矩形
            if self._roi_rect:
                self._roi_rect.setRect(rect)
                
            event.accept()
            return
        elif self._interaction_mode == InteractionMode.MEASURE and self._current_measure:
            # 更新测量线
            line = QLineF(self._measure_start, scene_pos)
            self._current_measure.setLine(line)
            
            # 计算长度（像素和物理单位）
            length_px = ((line.x2() - line.x1())**2 + (line.y2() - line.y1())**2)**0.5
            length_mm = length_px * self._pixel_size_mm
            
            # 更新文本
            idx = self._measure_lines.index(self._current_measure)
            if idx < len(self._measure_texts):
                text = f"{length_px:.1f} px"
                if self._pixel_size_mm != 1.0:
                    text += f" ({length_mm:.2f} mm)"
                    
                self._measure_texts[idx].setPlainText(text)
                
                # 更新位置
                mid_x = (line.x1() + line.x2()) / 2
                mid_y = (line.y1() + line.y2()) / 2
                self._measure_texts[idx].setPos(mid_x + 5, mid_y - 15)
            
            event.accept()
            return
        elif self._interaction_mode == InteractionMode.COLOR_PICKER:
            # 更新颜色提示
            if self._pixmap_item and not self._image.isNull():
                color = self.pick_color(scene_pos)
                if color:
                    tip_text = f"RGB: ({color.red()}, {color.green()}, {color.blue()})"
                    QToolTip.showText(event.globalPos(), tip_text)
            
            event.accept()
            return
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton:
            if self._interaction_mode == InteractionMode.SELECT_ROI and self._roi_is_drawing:
                # 完成ROI绘制
                self._roi_end = self.mapToScene(event.pos())
                self._roi_is_drawing = False
                
                # 计算最终矩形并发出信号
                rect = QRectF(self._roi_start, self._roi_end).normalized()
                if rect.width() > 5 and rect.height() > 5:  # 忽略太小的选择
                    self.roi_selected.emit(rect)
                
                event.accept()
                return
            elif self._interaction_mode == InteractionMode.MULTI_ROI and self._roi_is_drawing:
                # 完成ROI绘制
                self._roi_end = self.mapToScene(event.pos())
                self._roi_is_drawing = False
                
                # 计算最终矩形
                rect = QRectF(self._roi_start, self._roi_end).normalized()
                if rect.width() > 5 and rect.height() > 5:  # 忽略太小的选择
                    # 保存到多ROI列表
                    self._multi_rois.append(self._roi_rect)
                    
                    # 发出多ROI信号
                    roi_list = []
                    for roi_item in self._multi_rois:
                        roi_list.append(roi_item.rect())
                    
                    self.multiple_rois_selected.emit(roi_list)
                else:
                    # 移除太小的ROI
                    if self._roi_rect and self._roi_rect in self._scene.items():
                        self._scene.removeItem(self._roi_rect)
                
                # 清空当前ROI指针，允许下次继续绘制
                self._roi_rect = None
                
                event.accept()
                return
            elif self._interaction_mode == InteractionMode.MEASURE:
                # 完成测量
                self._current_measure = None
                
                # 更新并发出测量信号
                self._update_measurements()
                
                event.accept()
                return
            elif self._interaction_mode == InteractionMode.VIEW:
                # 恢复光标
                self.setCursor(Qt.OpenHandCursor)
        
        super().mouseReleaseEvent(event)
    
    def _show_context_menu(self, pos):
        """显示右键菜单"""
        menu = QMenu(self)
        
        # 添加菜单项
        fit_action = QAction("适应窗口", self)
        fit_action.triggered.connect(self.fit_in_view)
        menu.addAction(fit_action)
        
        reset_action = QAction("原始大小", self)
        reset_action.triggered.connect(self.reset_view)
        menu.addAction(reset_action)
        
        menu.addSeparator()
        
        # 交互模式子菜单
        mode_menu = QMenu("交互模式", self)
        
        view_action = QAction("查看模式", self)
        view_action.setCheckable(True)
        view_action.setChecked(self._interaction_mode == InteractionMode.VIEW)
        view_action.triggered.connect(lambda: self.set_interaction_mode(InteractionMode.VIEW))
        mode_menu.addAction(view_action)
        
        roi_action = QAction("ROI选择模式", self)
        roi_action.setCheckable(True)
        roi_action.setChecked(self._interaction_mode == InteractionMode.SELECT_ROI)
        roi_action.triggered.connect(lambda: self.set_interaction_mode(InteractionMode.SELECT_ROI))
        mode_menu.addAction(roi_action)
        
        measure_action = QAction("测量模式", self)
        measure_action.setCheckable(True)
        measure_action.setChecked(self._interaction_mode == InteractionMode.MEASURE)
        measure_action.triggered.connect(lambda: self.set_interaction_mode(InteractionMode.MEASURE))
        mode_menu.addAction(measure_action)
        
        multi_roi_action = QAction("多ROI模式", self)
        multi_roi_action.setCheckable(True)
        multi_roi_action.setChecked(self._interaction_mode == InteractionMode.MULTI_ROI)
        multi_roi_action.triggered.connect(lambda: self.set_interaction_mode(InteractionMode.MULTI_ROI))
        mode_menu.addAction(multi_roi_action)
        
        color_picker_action = QAction("颜色拾取模式", self)
        color_picker_action.setCheckable(True)
        color_picker_action.setChecked(self._interaction_mode == InteractionMode.COLOR_PICKER)
        color_picker_action.triggered.connect(lambda: self.set_interaction_mode(InteractionMode.COLOR_PICKER))
        mode_menu.addAction(color_picker_action)
        
        annotations_action = QAction("注释模式", self)
        annotations_action.setCheckable(True)
        annotations_action.setChecked(self._interaction_mode == InteractionMode.ANNOTATIONS)
        annotations_action.triggered.connect(lambda: self.set_interaction_mode(InteractionMode.ANNOTATIONS))
        mode_menu.addAction(annotations_action)
        
        menu.addMenu(mode_menu)
        
        # 网格显示
        grid_action = QAction("显示网格", self)
        grid_action.setCheckable(True)
        grid_action.setChecked(self._show_grid)
        grid_action.triggered.connect(lambda checked: self.toggle_grid(checked))
        menu.addAction(grid_action)
        
        # 显示菜单
        menu.exec_(self.mapToGlobal(pos))
    
    def drawForeground(self, painter, rect):
        """绘制前景"""
        super().drawForeground(painter, rect)
        
        # 绘制网格
        if self._show_grid and self._pixmap_item:
            painter.save()
            
            # 设置网格笔
            painter.setPen(QPen(self._grid_color, 1, Qt.DotLine))
            
            # 获取场景矩形
            scene_rect = self._scene.sceneRect()
            
            # 使用缓存计算网格线，使用矩形的数值属性而不是QRectF对象
            grid_lines = self._cached_compute_grid(
                scene_rect.left(), scene_rect.top(), 
                scene_rect.right(), scene_rect.bottom(), 
                self._grid_size
            )
            
            # 绘制网格线
            painter.drawLines(grid_lines)
            
            painter.restore()
        
        # 绘制十字线
        if self._crosshair_enabled and self._pixmap_item:
            painter.save()
            
            # 获取鼠标位置
            view_pos = self.mapFromGlobal(QCursor.pos())
            if self.rect().contains(view_pos):
                scene_pos = self.mapToScene(view_pos)
                
                # 设置十字线笔
                painter.setPen(QPen(QColor(255, 0, 0, 150), 1, Qt.DashLine))
                
                # 获取场景矩形
                scene_rect = self._scene.sceneRect()
                
                # 绘制水平和垂直线
                painter.drawLine(QPointF(scene_rect.left(), scene_pos.y()), 
                                QPointF(scene_rect.right(), scene_pos.y()))
                painter.drawLine(QPointF(scene_pos.x(), scene_rect.top()), 
                                QPointF(scene_pos.x(), scene_rect.bottom()))
            
            painter.restore()
        
        # 绘制信息
        if self._show_info and self._image and not self._image.isNull():
            painter.save()
            
            # 设置字体和颜色
            font = QFont("Arial", 8)
            painter.setFont(font)
            painter.setPen(QPen(QColor(LIGHT_COLORS["TEXT_PRIMARY"])))
            
            # 绘制图像信息
            info_text = f"尺寸: {self._image.width()} x {self._image.height()} px"
            info_text += f" | 缩放: {self._zoom_factor:.2f}x"
            
            # 获取鼠标位置
            view_pos = self.mapFromGlobal(QCursor.pos())
            if self.rect().contains(view_pos):
                scene_pos = self.mapToScene(view_pos)
                image_x = int(scene_pos.x())
                image_y = int(scene_pos.y())
                
                if (image_x >= 0 and image_x < self._image.width() and
                    image_y >= 0 and image_y < self._image.height()):
                    info_text += f" | 坐标: ({image_x}, {image_y})"
                    
                    # 如果是彩色图像，显示像素颜色
                    if self._image.depth() > 8:
                        color = QColor(self._image.pixel(image_x, image_y))
                        info_text += f" | RGB: ({color.red()}, {color.green()}, {color.blue()})"
            
            # 绘制信息文本
            painter.drawText(QPointF(10, 20), info_text)
            
            painter.restore()
    
    def get_roi(self):
        """获取当前ROI矩形"""
        if self._roi_rect:
            return self._roi_rect.rect()
        return None
    
    def set_roi(self, rect):
        """
        设置ROI矩形
        
        Args:
            rect: QRectF矩形
        """
        # 清除现有ROI
        self.clear_roi()
        
        # 创建新ROI矩形
        self._roi_rect = QGraphicsRectItem(rect)
        self._roi_rect.setPen(QPen(QColor(LIGHT_COLORS["PRIMARY"]), 2, Qt.DashLine))
        self._roi_rect.setBrush(QBrush(QColor(LIGHT_COLORS["PRIMARY"] + "40")))  # 半透明填充
        self._scene.addItem(self._roi_rect)
        
        # 更新起止点
        self._roi_start = rect.topLeft()
        self._roi_end = rect.bottomRight()

    def set_pixel_size(self, mm_per_pixel):
        """设置每像素的物理尺寸(毫米)，用于精确测量"""
        self._pixel_size_mm = max(0.001, mm_per_pixel)
        
        # 更新已有测量
        self._update_measurements()
        
    def _update_measurements(self):
        """更新所有测量标记的显示"""
        for i, line in enumerate(self._measure_lines):
            if i < len(self._measure_texts):
                # 更新测量文本
                text_item = self._measure_texts[i]
                line_obj = line.line()
                
                # 计算长度（像素和物理单位）
                length_px = ((line_obj.x2() - line_obj.x1())**2 + 
                           (line_obj.y2() - line_obj.y1())**2)**0.5
                length_mm = length_px * self._pixel_size_mm
                
                # 更新文本
                text = f"{length_px:.1f} px"
                if self._pixel_size_mm != 1.0:
                    text += f" ({length_mm:.2f} mm)"
                    
                text_item.setPlainText(text)
                
                # 更新位置
                mid_x = (line_obj.x1() + line_obj.x2()) / 2
                mid_y = (line_obj.y1() + line_obj.y2()) / 2
                text_item.setPos(mid_x + 5, mid_y - 15)
        
        # 发出测量更新信号
        measurements = []
        for line in self._measure_lines:
            line_obj = line.line()
            start = QPointF(line_obj.x1(), line_obj.y1())
            end = QPointF(line_obj.x2(), line_obj.y2())
            length_px = ((line_obj.x2() - line_obj.x1())**2 + 
                       (line_obj.y2() - line_obj.y1())**2)**0.5
            length_mm = length_px * self._pixel_size_mm
            
            measurements.append({
                'start': start,
                'end': end,
                'length_px': length_px,
                'length_mm': length_mm
            })
            
        self.measurements_updated.emit(measurements)
    
    def toggle_crosshair(self, enabled=None):
        """切换十字线显示"""
        if enabled is None:
            self._crosshair_enabled = not self._crosshair_enabled
        else:
            self._crosshair_enabled = enabled
        self.viewport().update()
    
    def pick_color(self, pos):
        """提取指定位置的颜色"""
        if not self._image or self._image.isNull():
            return None
            
        # 转换为图像坐标
        if isinstance(pos, QPointF):
            image_x = int(pos.x())
            image_y = int(pos.y())
        else:
            scene_pos = self.mapToScene(pos)
            image_x = int(scene_pos.x())
            image_y = int(scene_pos.y())
            
        # 检查范围
        if (image_x < 0 or image_x >= self._image.width() or
            image_y < 0 or image_y >= self._image.height()):
            return None
            
        # 获取颜色
        color = QColor(self._image.pixel(image_x, image_y))
        
        # 发出信号
        self.color_picked.emit(color, QPointF(image_x, image_y))
        
        return color
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            if self._interaction_mode == InteractionMode.SELECT_ROI:
                # 开始绘制ROI
                self._roi_start = self.mapToScene(event.pos())
                self._roi_end = self._roi_start
                self._roi_is_drawing = True
                
                # 创建或更新ROI矩形
                if self._roi_rect:
                    self._scene.removeItem(self._roi_rect)
                
                self._roi_rect = QGraphicsRectItem(QRectF(self._roi_start, self._roi_end))
                self._roi_rect.setPen(QPen(QColor(LIGHT_COLORS["PRIMARY"]), 2, Qt.DashLine))
                self._roi_rect.setBrush(QBrush(QColor(LIGHT_COLORS["PRIMARY"] + "40")))  # 半透明填充
                self._scene.addItem(self._roi_rect)
                
                event.accept()
                return
            elif self._interaction_mode == InteractionMode.MULTI_ROI:
                # 开始绘制多ROI
                self._roi_start = self.mapToScene(event.pos())
                self._roi_end = self._roi_start
                self._roi_is_drawing = True
                
                # 创建新的ROI矩形
                new_roi = QGraphicsRectItem(QRectF(self._roi_start, self._roi_end))
                new_roi.setPen(QPen(QColor(LIGHT_COLORS["ACCENT"]), 2, Qt.DashLine))
                new_roi.setBrush(QBrush(QColor(LIGHT_COLORS["ACCENT"] + "40")))  # 半透明填充
                self._scene.addItem(new_roi)
                
                # 暂存当前绘制的ROI
                self._roi_rect = new_roi
                
                event.accept()
                return
            elif self._interaction_mode == InteractionMode.MEASURE:
                # 开始测量
                self._measure_start = self.mapToScene(event.pos())
                
                # 创建新的测量线
                line = QGraphicsLineItem(QLineF(self._measure_start, self._measure_start))
                line.setPen(QPen(QColor(LIGHT_COLORS["SUCCESS"]), 2, Qt.SolidLine))
                self._scene.addItem(line)
                
                # 创建测量文本
                text = QGraphicsTextItem("0 px")
                text.setDefaultTextColor(QColor(LIGHT_COLORS["SUCCESS"]))
                font = QFont("Arial", 8)
                font.setBold(True)
                text.setFont(font)
                self._scene.addItem(text)
                
                # 保存当前测量项
                self._current_measure = line
                self._measure_lines.append(line)
                self._measure_texts.append(text)
                
                event.accept()
                return
            elif self._interaction_mode == InteractionMode.COLOR_PICKER:
                # 拾取颜色
                scene_pos = self.mapToScene(event.pos())
                self.pick_color(scene_pos)
                event.accept()
                return
            elif self._interaction_mode == InteractionMode.VIEW:
                # 设置拖动光标
                self.setCursor(Qt.ClosedHandCursor)
        
        super().mousePressEvent(event)


class ImageViewerWidget(QWidget):
    """
    图像查看器控件
    包装EnhancedImageViewer并添加额外UI元素
    """
    
    # 自定义信号
    roi_selected = pyqtSignal(QRectF)  # ROI选择信号
    multiple_rois_selected = pyqtSignal(list)  # 多ROI选择信号
    color_picked = pyqtSignal(QColor, QPointF)  # 颜色拾取信号
    measurements_updated = pyqtSignal(list)  # 测量更新信号
    
    def __init__(self, parent=None):
        """初始化图像查看器控件"""
        super().__init__(parent)
        
        # 创建布局
        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        
        # 图像查看器
        self._viewer = EnhancedImageViewer()
        self._layout.addWidget(self._viewer)
        
        # 状态栏
        self._status_bar = QLabel()
        self._status_bar.setObjectName("viewer_status_bar")
        self._status_bar.setStyleSheet(f"""
            #viewer_status_bar {{
                background-color: {LIGHT_COLORS["BACKGROUND"]};
                border-top: 1px solid {LIGHT_COLORS["BORDER"]};
                padding: 2px 5px;
                color: {LIGHT_COLORS["TEXT_SECONDARY"]};
            }}
        """)
        self._layout.addWidget(self._status_bar)
        
        self.setLayout(self._layout)
        
        # 连接信号
        self._viewer.mouse_position.connect(self._update_position_info)
        self._viewer.zoom_changed.connect(self._update_zoom_info)
        self._viewer.roi_selected.connect(self._on_roi_selected)
        self._viewer.multiple_rois_selected.connect(self._on_multiple_rois_selected)
        self._viewer.color_picked.connect(self._on_color_picked)
        self._viewer.measurements_updated.connect(self._on_measurements_updated)
    
    def _update_position_info(self, pos):
        """更新鼠标位置信息"""
        if not self._viewer.get_image().isNull():
            x, y = int(pos.x()), int(pos.y())
            
            # 检查是否在图像范围内
            img = self._viewer.get_image()
            if 0 <= x < img.width() and 0 <= y < img.height():
                # 构建位置信息
                status_text = f"位置: ({x}, {y})"
                
                # 对于彩色图像，添加颜色信息
                if img.depth() > 8:
                    color = QColor(img.pixel(x, y))
                    status_text += f" | RGB: ({color.red()}, {color.green()}, {color.blue()})"
                
                self._status_bar.setText(status_text)
    
    def _update_zoom_info(self, zoom_factor):
        """更新缩放信息"""
        current_text = self._status_bar.text()
        zoom_text = f"缩放: {zoom_factor:.2f}x"
        
        # 如果已有位置信息，追加缩放信息
        if current_text and "位置:" in current_text:
            parts = current_text.split(" | ")
            new_parts = [parts[0]] + [zoom_text] + parts[1:]
            self._status_bar.setText(" | ".join(new_parts))
        else:
            self._status_bar.setText(zoom_text)
    
    def _on_roi_selected(self, rect):
        """ROI选择处理"""
        # 转发ROI选择信号
        self.roi_selected.emit(rect)
    
    def _on_multiple_rois_selected(self, rois):
        """多ROI选择处理"""
        # 转发多ROI选择信号
        self.multiple_rois_selected.emit(rois)
    
    def _on_color_picked(self, color, pos):
        """颜色拾取处理"""
        # 转发颜色拾取信号
        self.color_picked.emit(color, pos)
        # 更新状态栏显示
        self._status_bar.setText(f"拾取颜色 - 位置: ({int(pos.x())}, {int(pos.y())}) | RGB: ({color.red()}, {color.green()}, {color.blue()})")
    
    def _on_measurements_updated(self, measurements):
        """测量更新处理"""
        # 转发测量更新信号
        self.measurements_updated.emit(measurements)
        
        # 更新状态栏显示最后一次测量
        if measurements:
            last_measure = measurements[-1]
            px_length = last_measure['length_px']
            mm_length = last_measure['length_mm']
            self._status_bar.setText(f"测量: {px_length:.1f} px ({mm_length:.2f} mm)")
    
    def set_image(self, image):
        """设置图像"""
        self._viewer.set_image(image)
    
    def get_image(self):
        """获取当前图像"""
        return self._viewer.get_image()
    
    def get_viewer(self):
        """获取内部图像查看器对象"""
        return self._viewer
    
    def set_interaction_mode(self, mode):
        """设置交互模式"""
        self._viewer.set_interaction_mode(mode)
    
    def clear_roi(self):
        """清除ROI"""
        self._viewer.clear_roi()
    
    def clear_measurements(self):
        """清除测量"""
        self._viewer.clear_measurements()
    
    def clear_multi_rois(self):
        """清除多ROI"""
        self._viewer.clear_multi_rois()
    
    def clear_all(self):
        """清除所有标记"""
        self._viewer.clear_all()
    
    def fit_in_view(self):
        """图像适应窗口"""
        self._viewer.fit_in_view()
    
    def toggle_grid(self, show=None):
        """切换网格显示"""
        if show is None:
            current = self._viewer._show_grid
            self._viewer.toggle_grid(not current)
        else:
            self._viewer.toggle_grid(show)
    
    def toggle_crosshair(self, show=None):
        """切换十字线显示"""
        self._viewer.toggle_crosshair(show)
    
    def set_pixel_size(self, mm_per_pixel):
        """设置像素物理尺寸(mm)"""
        self._viewer.set_pixel_size(mm_per_pixel)
    
    def capture_view(self):
        """捕获当前视图为图像"""
        return self._viewer.capture_view()
