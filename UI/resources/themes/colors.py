"""
UI颜色常量定义
-----------
包含亮色和暗色主题的颜色定义
"""

# 亮色主题颜色
LIGHT_COLORS = {
    # 基础颜色
    "PRIMARY": "#1976D2",          # 主色调
    "PRIMARY_LIGHT": "#4791DB",    # 主色调亮色
    "PRIMARY_DARK": "#115293",     # 主色调暗色
    "SECONDARY": "#FF5722",        # 次要色调
    "SECONDARY_LIGHT": "#FF8A65",  # 次要色调亮色
    "SECONDARY_DARK": "#E64A19",   # 次要色调暗色
    "BACKGROUND_SECONDARY": "#E0E0E0", # 次要背景色
    "BACKGROUND_PRIMARY": "#FFFFFF", # 主要背景色
    
    # 功能性颜色
    "SUCCESS": "#4CAF50",          # 成功色
    "WARNING": "#FFC107",          # 警告色
    "ERROR": "#F44336",            # 错误色
    "INFO": "#2196F3",             # 信息色
    "INFO_LIGHT": "#80D6FF",  # 信息色亮色
    "INFO_DARK": "#0077C2",   # 信息色暗色
    "SUCCESS_LIGHT": "#81C784",    # 成功色亮色
    "SUCCESS_DARK": "#388E3C",     # 成功色暗色
    
    # 背景色
    "BACKGROUND": "#FFFFFF",       # 主要背景色
    "BACKGROUND_PAPER": "#F5F5F5", # 卡片/纸张背景色
    "BACKGROUND_HOVER": "#E0E0E0", # 悬停背景色
    "BACKGROUND_SELECTED": "#E3F2FD", # 选中背景色
    "HOVER": "#E0E0E0",            # 悬停色
    
    # 文本色
    "TEXT_PRIMARY": "#212121",     # 主要文本色
    "TEXT_SECONDARY": "#757575",   # 次要文本色
    "TEXT_DISABLED": "#9E9E9E",    # 禁用文本色
    "DISABLED": "#BDBDBD",         # 禁用元素色
    
    # 边框色
    "BORDER": "#E0E0E0",           # 边框色
    "DIVIDER": "#EEEEEE",          # 分隔线色
    
    # 状态色
    "CONNECTED": "#4CAF50",        # 已连接状态
    "DISCONNECTED": "#F44336",     # 断开连接状态
    "WAITING": "#FFC107",          # 等待状态
    "DANGER": "#F44336",          # 危险状态
    "DANGER_LIGHT": "#FF8A65",  # 危险状态亮色
    "DANGER_DARK": "#D35400",   # 危险状态暗色
    
    # 图表色
    "CHART_1": "#1976D2",          # 图表色 1
    "CHART_2": "#FF5722",          # 图表色 2 
    "CHART_3": "#4CAF50",          # 图表色 3
    "CHART_4": "#FFC107",          # 图表色 4
    "CHART_5": "#9C27B0",          # 图表色 5
    "CHART_6": "#607D8B",          # 图表色 6
}

# 暗色主题颜色
DARK_COLORS = {
    # 基础颜色
    "PRIMARY": "#42A5F5",          # 主色调
    "PRIMARY_LIGHT": "#80D6FF",    # 主色调亮色
    "PRIMARY_DARK": "#0077C2",     # 主色调暗色
    "SECONDARY": "#FF8A65",        # 次要色调
    "SECONDARY_LIGHT": "#FFB74D",  # 次要色调亮色
    "SECONDARY_DARK": "#E64A19",   # 次要色调暗色
    
    # 功能性颜色
    "SUCCESS": "#66BB6A",          # 成功色
    "WARNING": "#FFCA28",          # 警告色
    "ERROR": "#EF5350",            # 错误色
    "INFO": "#42A5F5",             # 信息色
    
    # 背景色
    "BACKGROUND": "#121212",       # 主要背景色
    "BACKGROUND_PAPER": "#1E1E1E", # 卡片/纸张背景色
    "BACKGROUND_HOVER": "#333333", # 悬停背景色
    "BACKGROUND_SELECTED": "#0D47A1", # 选中背景色
    "HOVER": "#333333",            # 悬停色
    
    # 文本色
    "TEXT_PRIMARY": "#FFFFFF",     # 主要文本色
    "TEXT_SECONDARY": "#B0BEC5",   # 次要文本色
    "TEXT_DISABLED": "#78909C",    # 禁用文本色
    "DISABLED": "#546E7A",         # 禁用元素色
    
    # 边框色
    "BORDER": "#424242",           # 边框色
    "DIVIDER": "#303030",          # 分隔线色
    
    # 状态色
    "CONNECTED": "#66BB6A",        # 已连接状态
    "DISCONNECTED": "#EF5350",     # 断开连接状态
    "WAITING": "#FFCA28",          # 等待状态
    
    # 图表色
    "CHART_1": "#42A5F5",          # 图表色 1
    "CHART_2": "#FF8A65",          # 图表色 2
    "CHART_3": "#66BB6A",          # 图表色 3
    "CHART_4": "#FFCA28",          # 图表色 4
    "CHART_5": "#BA68C8",          # 图表色 5
    "CHART_6": "#78909C",          # 图表色 6
}
