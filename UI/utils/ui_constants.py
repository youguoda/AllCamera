"""
UI常量定义
---------
定义全局UI常量，包括颜色代码、图标路径等
"""

# 颜色代码 - 浅色主题
LIGHT_COLORS = {
    # 主色调
    "PRIMARY": "#2980b9",
    "PRIMARY_LIGHT": "#3498db",
    "PRIMARY_DARK": "#1a5276",
    "SECONDARY": "#2ecc71",
    
    # 背景色
    "BACKGROUND": "#f5f5f5",
    "SURFACE": "#ffffff",
    "BORDER": "#e0e0e0",
    
    # 文本色
    "TEXT_PRIMARY": "#2c3e50",
    "TEXT_SECONDARY": "#7f8c8d",
    
    # 状态色
    "SUCCESS": "#27ae60",
    "SUCCESS_LIGHT": "#2ecc71",
    "SUCCESS_DARK": "#16a085",
    "WARNING": "#f39c12",
    "DANGER": "#e74c3c",
    "INFO": "#3498db",
    "INFO_LIGHT": "#2980b9",
    "INFO_DARK": "#1a5276",
    "DANGER_LIGHT": "#c0392b",
    "WARNING_LIGHT": "#f1c40f",
    "WARNING_DARK": "#d35400",
    "SECONDARY_DARK": "#27ae60",

    # 辅助色
    "DISABLED": "#bdc3c7",
    "TEXT_DISABLED": "#7f8c8d",
    "SECONDARY_LIGHT":"#2980b9",
}

# 颜色代码 - 深色主题
DARK_COLORS = {
    # 主色调
    "PRIMARY": "#3498db",
    "PRIMARY_LIGHT": "#2980b9",
    "PRIMARY_DARK": "#1a5276",
    "SECONDARY_DARK": "#27ae60",
    
    # 背景色
    "BACKGROUND": "#2c3e50",
    "SURFACE": "#34495e",
    "BORDER": "#1a2530",
    
    # 文本色
    "TEXT_PRIMARY": "#ecf0f1",
    "TEXT_SECONDARY": "#bdc3c7",
    
    # 状态色
    "SUCCESS": "#2ecc71",
    "WARNING": "#f39c12",
    "DANGER": "#e74c3c",
    "INFO": "#3498db",
    "WARNING_DARK": "#d35400",
}

# 字体设置
FONTS = {
    "DEFAULT": "微软雅黑, Segoe UI, Roboto, sans-serif",
    "SIZE_SMALL": 10,
    "SIZE_NORMAL": 12,
    "SIZE_LARGE": 14,
    "SIZE_TITLE": 16,
    "SIZE_HEADER": 18,
}

# 间距和尺寸
SPACING = {
    "SMALL": 4,
    "MEDIUM": 8,
    "LARGE": 16,
    "XLARGE": 24,
    
    # 控件尺寸
    "BUTTON_HEIGHT": 32,
    "BUTTON_WIDTH_SMALL": 80,
    "BUTTON_WIDTH_MEDIUM": 120,
    "BUTTON_WIDTH_LARGE": 160,
    
    # 表格行高
    "TABLE_ROW_HEIGHT": 28,
}

# 动画时长（毫秒）
ANIMATION = {
    "FAST": 150,
    "NORMAL": 300,
    "SLOW": 500,
}

# 刷新频率（毫秒）
REFRESH_RATES = {
    "VERY_FAST": 100,   # 10fps
    "FAST": 200,        # 5fps
    "NORMAL": 500,      # 2fps
    "SLOW": 1000,       # 1fps
    "VERY_SLOW": 5000,  # 0.2fps
}

# 显示模式
DISPLAY_MODES = {
    "COMPACT": "compact",
    "NORMAL": "normal",
    "EXPANDED": "expanded",
}

# 图标路径
ICON_PATHS = {
    "APP_ICON": "ui/icons/app_icon.png",
    "CONNECT": "ui/icons/connect.png",
    "DISCONNECT": "ui/icons/disconnect.png",
    "START": "ui/icons/start.png",
    "STOP": "ui/icons/stop.png",
    "SETTINGS": "ui/icons/settings.png",
    "REFRESH": "ui/icons/refresh.png",
    "CAMERA": "ui/icons/camera.png",
    "ALGORITHM": "ui/icons/algorithm.png",
    "PLC": "ui/icons/plc.png",
    "RESULTS": "ui/icons/results.png",
    "DASHBOARD": "ui/icons/dashboard.png",
    "EXPORT": "ui/icons/export.png",
    "SAVE": "ui/icons/save.png",
    "LOAD": "ui/icons/load.png",
    "SUCCESS": "ui/icons/success.png",
    "WARNING": "ui/icons/warning.png",
    "ERROR": "ui/icons/error.png",
    "INFO": "ui/icons/info.png",
    "LIGHT_THEME": "ui/icons/light_theme.png",
    "DARK_THEME": "ui/icons/dark_theme.png",
}

# 图标大小
ICON_SIZES = {
    "SMALL": 16,
    "MEDIUM": 24,
    "LARGE": 32,
    "XLARGE": 48,
}

# 标签页索引
TAB_INDICES = {
    "DASHBOARD": 0,
    "CAMERA": 1,
    "ALGORITHM": 2,
    "PLC": 3,
    "RESULTS": 4,
    "SETTINGS": 5,
}

# 状态常量
STATUS = {
    "CONNECTED": "connected",
    "DISCONNECTED": "disconnected",
    "RUNNING": "running",
    "STOPPED": "stopped",
    "ERROR": "error",
    "WARNING": "warning",
    "READY": "ready",
    "BUSY": "busy",
    "IDLE": "idle",
}
