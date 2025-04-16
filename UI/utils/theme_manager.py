"""
主题管理工具
------------
负责主题样式的加载、切换和应用
"""

import os
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QApplication


class ThemeManager(QObject):
    """主题管理器 - 单例模式"""
    
    # 定义信号 - 主题变更时发出
    theme_changed = pyqtSignal(str)
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ThemeManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        super().__init__()
        self._initialized = True
        self._current_theme = "light"  # 默认为浅色主题
        self._themes_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "themes")
        self._themes = {
            "light": os.path.join(self._themes_dir, "light_theme.qss"),
            "dark": os.path.join(self._themes_dir, "dark_theme.qss")
        }
    
    @property
    def current_theme(self):
        """获取当前主题名称"""
        return self._current_theme
    
    def get_theme_path(self, theme_name):
        """获取主题文件路径"""
        return self._themes.get(theme_name)
    
    def apply_theme(self, theme_name):
        """应用指定主题"""
        if theme_name not in self._themes:
            print(f"主题 '{theme_name}' 不存在")
            return False
            
        theme_path = self._themes[theme_name]
        if not os.path.exists(theme_path):
            print(f"主题文件 '{theme_path}' 不存在")
            return False
            
        try:
            # 读取主题样式表文件
            with open(theme_path, "r", encoding="utf-8") as f:
                stylesheet = f.read()
                
            # 应用样式表到应用程序
            QApplication.instance().setStyleSheet(stylesheet)
            self._current_theme = theme_name
            
            # 发出主题变更信号
            self.theme_changed.emit(theme_name)
            
            print(f"已应用主题: {theme_name}")
            return True
        except Exception as e:
            print(f"应用主题时出错: {str(e)}")
            return False
    
    def toggle_theme(self):
        """切换主题 (浅色/深色)"""
        new_theme = "dark" if self._current_theme == "light" else "light"
        return self.apply_theme(new_theme)

        
    def load_theme(self, theme_name):
        """
        加载主题样式表
        
        Args:
            theme_name: 主题名称 (light/dark)
        """
        try:
            theme_path = os.path.join("../UI/themes/", f"{theme_name}_theme.qss")
            with open(theme_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"加载主题失败: {str(e)}")
            return ""
