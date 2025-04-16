#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海康威视相机工厂模块

实现海康威视相机的工厂类，用于创建海康威视相机对象。
"""
from .camera_factory import CameraFactory, CameraFactoryManager
from .hikvision_camera import HikvisionCamera
from .camera_interface import CameraInterface
from core.utils.logger import get_logger

logger = get_logger()


class HikvisionCameraFactory(CameraFactory):
    """
    海康威视相机工厂类
    
    负责创建海康威视相机对象，实现CameraFactory接口。
    """
    
    def create_camera(self) -> CameraInterface:
        """
        创建海康威视相机对象
        
        Returns:
            海康威视相机接口对象
        """
        logger.info("创建海康威视相机实例")
        return HikvisionCamera()


# 注册海康威视相机工厂到工厂管理器
CameraFactoryManager.register_factory("hikvision", HikvisionCameraFactory)
