"""
错误处理模块

为应用程序提供统一的异常处理机制，包括自定义异常类、
异常捕获和错误报告功能。
"""
import sys
import traceback
import time
from typing import Callable, Optional, Type, Union
import functools

from .logger import get_logger

logger = get_logger()


class ApplicationError(Exception):
    """应用程序基础异常类"""
    def __init__(self, message: str, error_code: int = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class CameraError(ApplicationError):
    """相机操作异常类"""
    pass


class AlgorithmError(ApplicationError):
    """算法处理异常类"""
    pass


class CommunicationError(ApplicationError):
    """通信异常类"""
    pass


class DatabaseError(ApplicationError):
    """数据库操作异常类"""
    pass


class ConfigError(ApplicationError):
    """配置异常类"""
    pass


def handle_exception(func: Callable) -> Callable:
    """
    异常处理装饰器
    
    为函数添加统一异常处理，记录错误日志并返回适当的结果
    
    Args:
        func: 被装饰的函数
        
    Returns:
        装饰后的函数
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ApplicationError as e:
            logger.error(f"{type(e).__name__}: {e.message}")
            if hasattr(e, 'error_code') and e.error_code:
                logger.debug(f"Error code: {e.error_code}")
            return None
        except Exception as e:
            logger.exception(f"未处理的异常 {func.__name__}: {str(e)}")
            return None
    return wrapper


def try_except(exception_types: Union[Type[Exception], tuple] = Exception, 
               default_return=None, log_exception: bool = True) -> Callable:
    """
    更灵活的异常处理装饰器
    
    为函数添加统一异常处理，可指定异常类型、默认返回值和是否记录日志
    
    Args:
        exception_types: 捕获的异常类型，可以是单个类型或元组
        default_return: 异常时的默认返回值
        log_exception: 是否记录异常日志
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exception_types as e:
                if log_exception:
                    logger.exception(f"Exception in {func.__name__}: {str(e)}")
                return default_return
        return wrapper
    return decorator


def global_exception_handler(exctype, value, tb):
    """
    全局未捕获异常处理函数
    
    捕获全局未处理的异常，记录日志并执行适当的恢复操作
    
    Args:
        exctype: 异常类型
        value: 异常值
        tb: 异常追踪信息
    """
    # 获取完整的堆栈跟踪
    exception_details = ''.join(traceback.format_exception(exctype, value, tb))
    
    # 记录异常信息
    logger.critical(f"未捕获的全局异常: {value}")
    logger.critical(f"异常详情: {exception_details}")
    
    # 执行恢复操作，如保存配置、关闭连接等
    try:
        logger.info("执行紧急恢复操作...")
        # 在这里添加保存状态、关闭连接等恢复操作
    except Exception as e:
        logger.error(f"恢复操作失败: {str(e)}")
    
    # 调用原始的异常处理器
    sys.__excepthook__(exctype, value, tb)


def setup_exception_handler():
    """
    设置全局异常处理器
    
    将系统默认的异常处理器替换为我们的全局异常处理器
    """
    sys.excepthook = global_exception_handler
    logger.info("全局异常处理器已设置")


def create_error_report(exception: Exception, context: dict = None) -> dict:
    """
    创建错误报告
    
    根据异常信息创建结构化的错误报告
    
    Args:
        exception: 异常对象
        context: 上下文信息
        
    Returns:
        包含错误详情的字典
    """
    # 获取异常跟踪信息
    tb = traceback.extract_tb(exception.__traceback__)
    last_frame = tb[-1] if tb else None
    
    # 创建报告
    report = {
        'error_type': type(exception).__name__,
        'error_message': str(exception),
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'traceback': traceback.format_exception(type(exception), exception, exception.__traceback__),
        'location': {
            'file': last_frame.filename if last_frame else 'Unknown',
            'line': last_frame.lineno if last_frame else 'Unknown',
            'function': last_frame.name if last_frame else 'Unknown',
        }
    }
    
    # 添加上下文信息
    if context:
        report['context'] = context
    
    return report
