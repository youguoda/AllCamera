# 相机模块使用指南

## 概述

本模块实现了一个灵活的相机接口架构，采用适配器模式和工厂模式，支持多种相机类型的统一接口操作。目前主要集成了海康威视相机SDK，同时提供模拟模式用于开发和测试。

## 架构设计

### 设计模式

- **适配器模式**：将不同厂商相机SDK的特定API适配到统一的相机接口
- **工厂模式**：通过工厂类创建不同类型的相机实例
- **单例模式**：信号管理器采用单例模式，确保全局唯一
- **装饰器模式**：使用异常处理装饰器简化错误处理

### 核心组件

- `CameraInterface`：相机操作的抽象接口
- `CameraFactory`：相机工厂的抽象接口
- `CameraFactoryManager`：管理所有注册的相机工厂
- `HikvisionCamera`：海康威视相机的具体实现
- `signal_manager`：用于图像数据传递的信号管理器

## 使用流程

### 1. 初始化相机

```python
from core.camera.camera_factory import CameraFactoryManager

# 创建海康威视相机实例
camera = CameraFactoryManager.create_camera("hikvision")
```

### 2. 枚举和选择相机

```python
# 获取可用相机列表
devices = camera.enumerate_devices()
print(f"找到 {len(devices)} 个相机设备")

# 打开指定相机(假设使用第一个相机)
if devices:
    camera.open(devices[0]['device_id'])
```

### 3. 配置相机参数

```python
# 设置基本参数
camera.set_parameter(
    frame_rate=30.0,      # 帧率
    exposure_time=10000,  # 曝光时间(微秒)
    gain=0.0             # 增益
)

# 设置触发模式(可选)
camera.set_trigger_mode(False)  # False为连续采集，True为触发模式
```

### 4. 开始图像采集

```python
# 启动图像采集
camera.start_grabbing()
```

### 5. 获取图像数据

有两种方式获取图像：

#### 方式一：直接获取

```python
# 获取一帧图像
frame = camera.get_frame()
```

#### 方式二：信号槽机制（推荐）

```python
from core.utils.signal_manager import signal_manager

# 定义图像处理函数
def handle_frame(frame, camera_id):
    # 处理图像
    pass

# 连接信号
signal_manager.frame_ready_signal.connect(handle_frame)
```

### 6. 停止采集和释放资源

```python
# 停止采集
camera.stop_grabbing()

# 关闭相机
camera.close()
```

## 高级功能

### 模拟模式

当SDK不可用或需要在没有实际相机的环境中开发时：

```python
# 创建相机实例
camera = CameraFactoryManager.create_camera("hikvision")

# 启用模拟模式
camera._is_simulation = True
```

### 触发模式

```python
# 设置为触发模式
camera.set_trigger_mode(True)

# 软触发一次
camera.trigger_once()
```

### 获取相机参数

```python
# 获取当前相机参数
params = camera.get_parameter()
print(f"帧率: {params['frame_rate']}")
print(f"曝光时间: {params['exposure_time']}")
print(f"增益: {params['gain']}")
```

## 错误处理

相机模块使用了统一的异常处理机制：

```python
try:
    camera.open("invalid_id")
except CameraError as e:
    print(f"相机操作错误: {str(e)}")
```

## 扩展新相机类型

要添加新的相机类型支持，需要：

1. 实现`CameraInterface`接口
2. 创建对应的工厂类
3. 注册工厂类到`CameraFactoryManager`

```python
# 1. 实现接口
class NewCamera(CameraInterface):
    # 实现所有抽象方法
    pass

# 2. 创建工厂类
class NewCameraFactory(CameraFactory):
    def create_camera(self) -> CameraInterface:
        return NewCamera()

# 3. 注册工厂类
CameraFactoryManager.register_factory("new_camera", NewCameraFactory)
```

## 示例代码

完整的相机使用示例可参考 `tests/camera_test_improved_v3.py`，该示例提供了完整的GUI界面用于测试相机的各项功能。

## 注意事项

1. 确保在使用前正确安装相机SDK
2. 相机资源需要正确释放，建议使用try-finally结构
3. 多线程环境下注意图像数据的线程安全性
4. 模拟模式下不需要实际相机连接，但功能有限

