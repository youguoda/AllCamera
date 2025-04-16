"""
UI间距常量定义
-----------
包含用于UI组件间距的标准值
"""

# 基础间距单位（像素）
BASE_UNIT = 4

# 标准间距值
SPACING = {
    "NONE": 0,
    "XXS": BASE_UNIT,          # 4px - 极小间距
    "XS": BASE_UNIT * 2,       # 8px - 超小间距
    "SMALL": BASE_UNIT * 3,    # 12px - 小间距
    "MEDIUM": BASE_UNIT * 4,   # 16px - 中等间距
    "LARGE": BASE_UNIT * 6,    # 24px - 大间距
    "XL": BASE_UNIT * 8,       # 32px - 超大间距
    "XXL": BASE_UNIT * 12,     # 48px - 极大间距
}

# 内边距值
PADDING = {
    "NONE": 0,
    "XXS": BASE_UNIT,          # 4px - 极小内边距
    "XS": BASE_UNIT * 2,       # 8px - 超小内边距
    "SMALL": BASE_UNIT * 3,    # 12px - 小内边距
    "MEDIUM": BASE_UNIT * 4,   # 16px - 中等内边距
    "LARGE": BASE_UNIT * 6,    # 24px - 大内边距
    "XL": BASE_UNIT * 8,       # 32px - 超大内边距
    "XXL": BASE_UNIT * 12,     # 48px - 极大内边距
}

# 边距值
MARGIN = {
    "NONE": 0,
    "XXS": BASE_UNIT,          # 4px - 极小边距
    "XS": BASE_UNIT * 2,       # 8px - 超小边距
    "SMALL": BASE_UNIT * 3,    # 12px - 小边距
    "MEDIUM": BASE_UNIT * 4,   # 16px - 中等边距
    "LARGE": BASE_UNIT * 6,    # 24px - 大边距
    "XL": BASE_UNIT * 8,       # 32px - 超大边距
    "XXL": BASE_UNIT * 12,     # 48px - 极大边距
}

# 布局间距
LAYOUT_SPACING = {
    "NONE": 0,
    "XXS": BASE_UNIT * 2,      # 8px - 极小布局间距
    "XS": BASE_UNIT * 4,       # 16px - 超小布局间距
    "SMALL": BASE_UNIT * 6,    # 24px - 小布局间距
    "MEDIUM": BASE_UNIT * 8,   # 32px - 中等布局间距
    "LARGE": BASE_UNIT * 12,   # 48px - 大布局间距
    "XL": BASE_UNIT * 16,      # 64px - 超大布局间距
    "XXL": BASE_UNIT * 24,     # 96px - 极大布局间距
}

# 图标尺寸
ICON_SIZE = {
    "XXS": 12,                 # 12px - 极小图标
    "XS": 16,                  # 16px - 超小图标
    "SMALL": 20,               # 20px - 小图标
    "MEDIUM": 24,              # 24px - 中等图标
    "LARGE": 32,               # 32px - 大图标
    "XL": 48,                  # 48px - 超大图标
    "XXL": 64,                 # 64px - 极大图标
}

# 圆角半径
BORDER_RADIUS = {
    "NONE": 0,                 # 0px - 无圆角 
    "XXS": 2,                  # 2px - 极小圆角
    "XS": 4,                   # 4px - 超小圆角
    "SMALL": 6,                # 6px - 小圆角
    "MEDIUM": 8,               # 8px - 中等圆角
    "LARGE": 12,               # 12px - 大圆角
    "XL": 16,                  # 16px - 超大圆角
    "XXL": 24,                 # 24px - 极大圆角
    "CIRCLE": 9999,            # 圆形
}
