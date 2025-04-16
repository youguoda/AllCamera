"""
可折叠面板控件
------------
提供可展开/折叠的内容面板，用于分组显示控件和减少界面占用空间
"""

from PyQt5.QtCore import Qt, QPropertyAnimation, pyqtSignal, QSize
from PyQt5.QtWidgets import (QWidget, QFrame, QVBoxLayout, QHBoxLayout,
                            QLabel, QPushButton, QScrollArea, QSizePolicy)

from UI.utils.ui_constants import LIGHT_COLORS, SPACING, ANIMATION, ICON_SIZES


class CollapsiblePanel(QWidget):
    """
    可折叠面板
    提供标题栏、展开/折叠按钮和内容区域
    """
    # 添加信号
    stateChanged = pyqtSignal(bool)  # 状态改变信号，参数为是否折叠
    
    def __init__(self, title, parent=None, collapsed=False):
        """
        初始化可折叠面板
        
        Args:
            title: 面板标题
            parent: 父控件
            collapsed: 初始状态是否折叠
        """
        super().__init__(parent)
        
        self._title = title
        self._collapsed = collapsed
        self._animation_duration = ANIMATION["NORMAL"]
        self._is_animating = False
        
        self._init_ui()
        self._setup_connections()
        self._init_state()
    
    def _init_ui(self):
        """
        初始化UI组件
        """
        # 创建布局
        self._main_layout = QVBoxLayout()
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)
        
        # 创建标题栏
        self._create_header()
        
        # 创建内容区域
        self._create_content_area()
        
        # 添加控件到主布局
        self._main_layout.addWidget(self._header)
        self._main_layout.addWidget(self._content_area)
        
        self.setLayout(self._main_layout)
    
    def _create_header(self):
        """
        创建标题栏
        """
        self._header = QFrame()
        self._header.setObjectName("panel_header")
        self._header.setStyleSheet(f"""
            #panel_header {{
                background-color: {LIGHT_COLORS["SURFACE"]};
                border: 1px solid {LIGHT_COLORS["BORDER"]};
                border-radius: 4px;
            }}
        """)
        self._header.setCursor(Qt.PointingHandCursor)
        
        self._header_layout = QHBoxLayout()
        self._header_layout.setContentsMargins(SPACING["MEDIUM"], SPACING["MEDIUM"], 
                                             SPACING["MEDIUM"], SPACING["MEDIUM"])
        
        # 标题标签
        self._title_label = QLabel(self._title)
        self._title_label.setObjectName("panel_title")
        self._title_label.setStyleSheet(f"""
            #panel_title {{
                font-weight: bold;
                color: {LIGHT_COLORS["PRIMARY"]};
            }}
        """)
        
        # 折叠按钮
        self._toggle_button = QPushButton()
        self._toggle_button.setObjectName("panel_toggle")
        self._toggle_button.setFixedSize(ICON_SIZES["SMALL"], ICON_SIZES["SMALL"])
        self._toggle_button.setCursor(Qt.PointingHandCursor)
        self._toggle_button.setStyleSheet(f"""
            #panel_toggle {{
                background-color: transparent;
                border: none;
            }}
        """)
        
        # 添加控件到标题栏
        self._header_layout.addWidget(self._title_label)
        self._header_layout.addStretch()
        self._header_layout.addWidget(self._toggle_button)
        self._header.setLayout(self._header_layout)
    
    def _create_content_area(self):
        """
        创建内容区域
        """
        self._content_area = QScrollArea()
        self._content_area.setObjectName("panel_content")
        self._content_area.setStyleSheet(f"""
            #panel_content {{
                background-color: {LIGHT_COLORS["SURFACE"]};
                border: 1px solid {LIGHT_COLORS["BORDER"]};
                border-top: none;
                border-bottom-left-radius: 4px;
                border-bottom-right-radius: 4px;
            }}
        """)
        self._content_area.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )
        self._content_area.setWidgetResizable(True)
        
        # 内容容器
        self._content_widget = QWidget()
        self._content_layout = QVBoxLayout()
        self._content_layout.setContentsMargins(SPACING["MEDIUM"], SPACING["MEDIUM"], 
                                              SPACING["MEDIUM"], SPACING["MEDIUM"])
        self._content_widget.setLayout(self._content_layout)
        self._content_area.setWidget(self._content_widget)
        
        # 创建动画
        self._animation = QPropertyAnimation(self._content_area, b"maximumHeight")
        self._animation.setDuration(self._animation_duration)
        self._animation.setStartValue(0)
        self._animation.setEndValue(0)
    
    def _setup_connections(self):
        """
        设置信号连接
        """
        self._header.mousePressEvent = self._handle_header_click
        self._toggle_button.clicked.connect(self._handle_button_click)
        self._animation.finished.connect(self._on_animation_finished)
    
    def _init_state(self):
        """
        初始化状态
        """
        self._update_toggle_button()
        self._update_collapsed_state()
    
    def _handle_header_click(self, event):
        """
        处理标题栏点击事件
        """
        self.toggle()
    
    def _handle_button_click(self):
        """
        处理按钮点击事件
        """
        self.toggle()
    
    def toggle(self):
        """
        切换面板展开/折叠状态
        """
        if self._is_animating:
            return
            
        self._is_animating = True
        self._collapsed = not self._collapsed
        self._update_toggle_button()
        
        # 启动动画
        self._start_animation()
        
        # 发送状态改变信号
        self.stateChanged.emit(self._collapsed)
    
    def _start_animation(self):
        """
        启动动画
        """
        if self._collapsed:
            self._animation.setDirection(QPropertyAnimation.Forward)
            self._animation.setStartValue(self._content_area.height())
            self._animation.setEndValue(0)
        else:
            self._content_area.setMaximumHeight(0)
            self._animation.setDirection(QPropertyAnimation.Backward)
            self._animation.setStartValue(0)
            content_height = self._content_widget.sizeHint().height()
            self._animation.setEndValue(content_height)
            
        self._animation.start()
    
    def _on_animation_finished(self):
        """
        动画完成事件处理
        """
        self._is_animating = False
        self._update_collapsed_state()
    
    def _update_collapsed_state(self):
        """
        更新折叠状态
        """
        if self._collapsed:
            self._content_area.setMaximumHeight(0)
            self._content_area.setVisible(False)
        else:
            self._content_area.setMaximumHeight(16777215)  # QWIDGETSIZE_MAX
            self._content_area.setVisible(True)
    
    def _update_toggle_button(self):
        """
        更新折叠按钮图标
        """
        # 直接用文本替代图标
        self._toggle_button.setText("▼" if self._collapsed else "▲")
            
    def add_widget(self, widget):
        """
        添加控件到内容区域
        """
        self._content_layout.addWidget(widget)
        return widget  # 返回添加的控件，方便链式调用
        
    def add_layout(self, layout):
        """
        添加布局到内容区域
        """
        self._content_layout.addLayout(layout)
        return layout  # 返回添加的布局，方便链式调用
        
    def set_title(self, title):
        """
        设置面板标题
        """
        self._title = title
        self._title_label.setText(title)
    
    def set_state(self, collapsed, animate=True):
        """
        设置面板状态
        
        Args:
            collapsed: True表示折叠，False表示展开
            animate: 是否使用动画效果
        """
        if self._is_animating or self._collapsed == collapsed:
            return
            
        if animate:
            self.toggle()
        else:
            self._collapsed = collapsed
            self._update_toggle_button()
            self._update_collapsed_state()
            self.stateChanged.emit(self._collapsed)
    
    def is_collapsed(self):
        """
        获取当前折叠状态
        """
        return self._collapsed
    
    def is_expanded(self):
        """
        获取当前展开状态
        """
        return not self._collapsed
    
    def set_animation_duration(self, duration):
        """
        设置动画持续时间(毫秒)
        """
        self._animation_duration = duration
        self._animation.setDuration(duration)
    
    # 兼容旧API
    def set_collapsed(self, collapsed):
        """
        设置折叠状态
        """
        self.set_state(collapsed)
    
    def set_expanded(self, expanded):
        """
        设置面板展开状态
        
        Args:
            expanded: True表示展开，False表示折叠
        """
        self.set_state(not expanded)
    
    def sizeHint(self):
        """
        提供推荐尺寸
        """
        width = self._header.sizeHint().width()
        height = self._header.sizeHint().height()
        
        if not self._collapsed:
            height += self._content_widget.sizeHint().height()
            
        return QSize(width, height)
