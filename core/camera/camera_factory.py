"""
相机工厂模块

实现抽象工厂模式，用于创建不同类型的相机对象。
支持扩展以添加新的相机类型。
"""
from typing import Dict, Type, Optional
from abc import ABC, abstractmethod

from .camera_interface import CameraInterface

class CameraFactory(ABC):
    """
    相机工厂抽象类
    
    定义了创建相机对象的接口，具体相机工厂应实现这个接口。
    """
    
    @abstractmethod
    def create_camera(self) -> CameraInterface:
        """
        创建相机对象
        
        Returns:
            相机接口对象
        """
        pass


class CameraFactoryManager:
    """
    相机工厂管理器
    
    管理所有注册的相机工厂，支持根据类型创建相机对象。
    """
    
    _factories: Dict[str, Type[CameraFactory]] = {}
    
    @classmethod
    def register_factory(cls, camera_type: str, factory_class: Type[CameraFactory]) -> None:
        """
        注册相机工厂
        
        Args:
            camera_type: 相机类型名称
            factory_class: 相机工厂类
        """
        cls._factories[camera_type] = factory_class
    
    @classmethod
    def create_camera(cls, camera_type: str) -> Optional[CameraInterface]:
        """
        创建指定类型的相机对象
        
        Args:
            camera_type: 相机类型名称
            
        Returns:
            相机接口对象，类型不存在时返回None
        """
        if camera_type not in cls._factories:
            return None
        
        factory = cls._factories[camera_type]()
        return factory.create_camera()
    
    @classmethod
    def get_available_types(cls) -> list:
        """
        获取所有已注册的相机类型
        
        Returns:
            相机类型列表
        """
        return list(cls._factories.keys())
