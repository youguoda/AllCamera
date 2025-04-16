"""
配置管理模块

提供统一的配置管理系统，支持JSON、YAML等多种格式的配置文件。
实现配置的读取、保存和实时更新功能。
"""
import os
import json
import yaml
from typing import Any, Dict, Optional, Union
import threading

class ConfigManager:
    """
    配置管理器类
    
    实现了单例模式，确保全局配置访问的一致性。
    支持多种格式的配置文件，提供统一的配置访问接口。
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ConfigManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self, config_dir: str = None):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件目录，默认为resources/configs
        """
        if self._initialized:
            return
            
        self._initialized = True
        self._config_dir = config_dir or os.path.join('resources', 'configs')
        self._configs = {}
        self._watched_files = {}
        self._load_default_configs()
    
    def _load_default_configs(self):
        """加载默认配置文件"""
        # 确保配置目录存在
        os.makedirs(self._config_dir, exist_ok=True)
        
        # 加载主配置文件
        main_config_path = os.path.join(self._config_dir, 'config.json')
        if os.path.exists(main_config_path):
            print(f"有文件 {main_config_path}")
            self._configs['main'] = self.load_config(main_config_path)
        else:
            # 创建默认主配置
            default_config = {
                'app': {
                    'name': 'INNOTIME智能视觉检测系统',
                    'version': '1.0.0',
                    'debug': True
                },
                'camera': {
                    'default_type': 'hikvision',
                    'timeout': 5000,
                    'auto_reconnect': True
                },
                'algorithm': {
                    'default': 'opencv',
                    'yolo': {
                        'model_path': 'resources/models/yolov10.pt',
                        'conf_threshold': 0.25,
                        'iou_threshold': 0.45
                    },
                    'opencv': {
                        'rectangle_threshold_value': 205,
                        'rectangle_area_threshold': 15,
                        'delete_threshold_value': 180,
                        'delete_min_area_threshold': 10,
                        'distance_threshold': 40,
                        'gradient_threshold': -20.0,
                        'contour_length_threshold': 400
                    }
                },
                'communication': {
                    'modbus': {
                        'host': '127.0.0.1',    # Modbus TCP服务器IP地址
                        'port': 502,    # Modbus TCP端口
                        'slave_id': 1, # Modbus从站ID
                        'heartbeat_timeout': 5.0 # 心跳超时时间（秒）
                    }
                },
                'data': {
                    'image_save_path': 'data/images',
                    'save_original': True,
                    'save_processed': True,
                    'image_format': 'jpg',
                    'database': {
                        'type': 'mongodb',
                        'host': 'localhost',
                        'port': 27017,
                        'db_name': 'innotime_vision'
                    }
                },
                'ui': {
                    'theme': 'dark',
                    'language': 'zh_CN',
                    'fullscreen': False
                }
            }
            self._configs['main'] = default_config
            self.save_config(main_config_path, default_config)
    
    def load_config(self, file_path: str) -> Dict:
        """
        加载配置文件
        
        Args:
            file_path: 配置文件路径
            
        Returns:
            配置字典
        """
        if not os.path.exists(file_path):
            return {}
            
        file_ext = os.path.splitext(file_path)[1].lower()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_ext == '.json':
                    return json.load(f)
                elif file_ext in ['.yaml', '.yml']:
                    return yaml.safe_load(f)
                else:
                    raise ValueError(f"不支持的配置文件格式: {file_ext}")
        except Exception as e:
            print(f"加载配置文件 {file_path} 失败: {str(e)}")
            return {}
    
    def save_config(self, file_path: str, config: Dict) -> bool:
        """
        保存配置到文件
        
        Args:
            file_path: 配置文件路径
            config: 配置字典
            
        Returns:
            是否保存成功
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            file_ext = os.path.splitext(file_path)[1].lower()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                if file_ext == '.json':
                    json.dump(config, f, ensure_ascii=False, indent=4)
                elif file_ext in ['.yaml', '.yml']:
                    yaml.dump(config, f, default_flow_style=False)
                else:
                    raise ValueError(f"不支持的配置文件格式: {file_ext}")
            
            # 更新内存中的配置
            config_name = os.path.splitext(os.path.basename(file_path))[0]
            self._configs[config_name] = config
            
            return True
        except Exception as e:
            print(f"保存配置文件 {file_path} 失败: {str(e)}")
            return False
    
    def get(self, config_name: str, key_path: str = None, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            config_name: 配置名称
            key_path: 配置键路径，使用.分隔，如 app.debug
            default: 默认值，当配置不存在时返回
            
        Returns:
            配置值或默认值
        """
        if config_name not in self._configs:
            return default
            
        config = self._configs[config_name]
        
        if key_path is None:
            return config
            
        # 按路径查找配置
        keys = key_path.split('.')
        for key in keys:
            if isinstance(config, dict) and key in config:
                config = config[key]
            else:
                return default
                
        return config
    
    def set(self, config_name: str, key_path: str, value: Any) -> bool:
        """
        设置配置值
        
        Args:
            config_name: 配置名称
            key_path: 配置键路径，使用.分隔，如 app.debug
            value: 要设置的值
            
        Returns:
            是否设置成功
        """
        if config_name not in self._configs:
            self._configs[config_name] = {}
            
        config = self._configs[config_name]
        
        # 按路径设置配置
        keys = key_path.split('.')
        for i, key in enumerate(keys[:-1]):
            if key not in config or not isinstance(config[key], dict):
                config[key] = {}
            config = config[key]
                
        config[keys[-1]] = value
        
        # 保存到文件
        if config_name == 'main':
            file_path = os.path.join(self._config_dir, 'config.json')
        else:
            file_path = os.path.join(self._config_dir, f"{config_name}.json")
            
        return self.save_config(file_path, self._configs[config_name])
    
    def get_main_config(self) -> Dict:
        """
        获取主配置
        
        Returns:
            主配置字典
        """
        return self.get('main')
        
    def reload(self, config_name: str = None) -> bool:
        """
        重新加载配置
        
        Args:
            config_name: 配置名称，为None时重新加载所有配置
            
        Returns:
            是否重新加载成功
        """
        try:
            if config_name is None:
                # 重新加载所有配置
                self._configs.clear()
                self._load_default_configs()
            else:
                # 重新加载指定配置
                if config_name == 'main':
                    file_path = os.path.join(self._config_dir, 'config.json')
                else:
                    file_path = os.path.join(self._config_dir, f"{config_name}.json")
                
                if os.path.exists(file_path):
                    self._configs[config_name] = self.load_config(file_path)
                    
            return True
        except Exception as e:
            print(f"重新加载配置失败: {str(e)}")
            return False
