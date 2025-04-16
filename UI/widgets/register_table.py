"""
寄存器表格控件
------------
用于PLC通信模块中显示和编辑寄存器数据
"""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QBrush
from PyQt5.QtWidgets import (QWidget, QTableWidget, QTableWidgetItem, 
                           QVBoxLayout, QHBoxLayout, QPushButton,
                             QHeaderView)

from gui001.ui.utils.ui_constants import LIGHT_COLORS


class RegisterTable(QTableWidget):
    """
    寄存器表格
    用于显示和编辑PLC寄存器数据
    """
    
    # 自定义信号
    register_value_changed = pyqtSignal(int, str, int, int)  # 寄存器值变化信号 (从站ID, 区块名称, 地址, 新值)
    
    def __init__(self, parent=None):
        """初始化寄存器表格"""
        super().__init__(parent)
        
        # 配置表格基本属性
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels(["从站", "区块", "地址", "值", "操作"])
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.EditKeyPressed)
        
        # 设置列宽
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 从站
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 区块
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)  # 地址
        self.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)  # 值
        self.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)  # 操作
        
        # 设置样式
        self.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid {LIGHT_COLORS["BORDER"]};
                background-color: {LIGHT_COLORS["SURFACE"]};
                gridline-color: {LIGHT_COLORS["BORDER"]};
            }}
            
            QTableWidget::item:selected {{
                background-color: {LIGHT_COLORS["PRIMARY"] + "40"};
                color: {LIGHT_COLORS["TEXT_PRIMARY"]};
            }}
            
            QTableWidget::item:alternate {{
                background-color: {LIGHT_COLORS["BACKGROUND"]};
            }}
        """)
        
        # 连接单元格变化信号
        self.cellChanged.connect(self._on_cell_changed)
    
    def add_register(self, slave_id, block_name, address, value):
        """
        添加寄存器到表格
        
        Args:
            slave_id: 从站ID
            block_name: 区块名称
            address: 寄存器地址
            value: 寄存器值
        """
        # 获取当前行数
        row = self.rowCount()
        self.insertRow(row)
        
        # 创建单元格项目
        slave_item = QTableWidgetItem(str(slave_id))
        slave_item.setFlags(slave_item.flags() & ~Qt.ItemIsEditable)  # 不可编辑
        
        block_item = QTableWidgetItem(block_name)
        block_item.setFlags(block_item.flags() & ~Qt.ItemIsEditable)  # 不可编辑
        
        address_item = QTableWidgetItem(str(address))
        address_item.setFlags(address_item.flags() & ~Qt.ItemIsEditable)  # 不可编辑
        
        value_item = QTableWidgetItem(str(value))
        
        # 设置单元格项目
        self.setItem(row, 0, slave_item)
        self.setItem(row, 1, block_item)
        self.setItem(row, 2, address_item)
        self.setItem(row, 3, value_item)
        
        # 添加操作按钮
        self._add_action_button(row)
    
    def update_register_value(self, slave_id, block_name, address, value):
        """
        更新寄存器值
        
        Args:
            slave_id: 从站ID
            block_name: 区块名称
            address: 寄存器地址
            value: 新的寄存器值
        
        Returns:
            bool: 是否成功更新
        """
        # 查找匹配的行
        for row in range(self.rowCount()):
            found_slave = self.item(row, 0) and self.item(row, 0).text() == str(slave_id)
            found_block = self.item(row, 1) and self.item(row, 1).text() == block_name
            found_addr = self.item(row, 2) and self.item(row, 2).text() == str(address)
            
            if found_slave and found_block and found_addr:
                # 暂时断开单元格变化信号
                self.cellChanged.disconnect(self._on_cell_changed)
                
                # 更新值
                value_item = QTableWidgetItem(str(value))
                self.setItem(row, 3, value_item)
                
                # 高亮显示新值
                value_item.setBackground(QBrush(QColor(LIGHT_COLORS["PRIMARY"] + "20")))
                
                # 重新连接单元格变化信号
                self.cellChanged.connect(self._on_cell_changed)
                return True
        
        return False
    
    def clear_registers(self):
        """清空寄存器表格"""
        self.setRowCount(0)
    
    def _add_action_button(self, row):
        """
        为指定行添加操作按钮
        
        Args:
            row: 行索引
        """
        # 创建操作按钮
        write_button = QPushButton("写入")
        write_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {LIGHT_COLORS["PRIMARY"]};
                color: white;
                border: none;
                padding: 3px 8px;
                border-radius: 3px;
                min-width: 60px;
            }}
            
            QPushButton:hover {{
                background-color: {LIGHT_COLORS["PRIMARY_LIGHT"]};
            }}
            
            QPushButton:pressed {{
                background-color: {LIGHT_COLORS["PRIMARY_DARK"]};
            }}
        """)
        
        # 创建按钮容器
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(4, 2, 4, 2)
        button_layout.addWidget(write_button)
        
        # 设置单元格小部件
        self.setCellWidget(row, 4, button_widget)
        
        # 连接信号槽
        write_button.clicked.connect(lambda: self._on_write_button_clicked(row))
    
    def _on_write_button_clicked(self, row):
        """
        写入按钮点击事件处理
        
        Args:
            row: 按钮所在行
        """
        # 获取寄存器信息
        slave_id = int(self.item(row, 0).text())
        block_name = self.item(row, 1).text()
        address = int(self.item(row, 2).text())
        value = int(self.item(row, 3).text())
        
        # 发送寄存器值变化信号
        self.register_value_changed.emit(slave_id, block_name, address, value)
    
    def _on_cell_changed(self, row, column):
        """
        单元格内容变化事件处理
        
        Args:
            row: 行索引
            column: 列索引
        """
        # 只处理值列的变化
        if column == 3:
            # 获取寄存器信息
            slave_id = int(self.item(row, 0).text())
            block_name = self.item(row, 1).text()
            address = int(self.item(row, 2).text())
            
            # 获取新值
            try:
                value = int(self.item(row, 3).text())
            except ValueError:
                # 输入不是有效整数，恢复为0
                value = 0
                self.item(row, 3).setText(str(value))
            
            # 发送寄存器值变化信号
            self.register_value_changed.emit(slave_id, block_name, address, value)


class RegisterTableWidget(QWidget):
    """
    寄存器表格控件
    包装RegisterTable并添加额外UI元素
    """
    
    # 自定义信号
    register_value_changed = pyqtSignal(int, str, int, int)  # 寄存器值变化信号 (从站ID, 区块名称, 地址, 新值)
    refresh_clicked = pyqtSignal()  # 刷新按钮点击信号
    
    def __init__(self, parent=None):
        """初始化寄存器表格控件"""
        super().__init__(parent)
        
        # 创建布局
        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(5)
        
        # 工具栏
        self._toolbar = QWidget()
        self._toolbar_layout = QHBoxLayout(self._toolbar)
        self._toolbar_layout.setContentsMargins(0, 0, 0, 0)
        
        # 刷新按钮
        self._refresh_button = QPushButton("刷新寄存器")
        self._refresh_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {LIGHT_COLORS["INFO"]};
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 4px;
            }}
            
            QPushButton:hover {{
                background-color: {LIGHT_COLORS["PRIMARY_LIGHT"]};
            }}
            
            QPushButton:pressed {{
                background-color: {LIGHT_COLORS["PRIMARY_DARK"]};
            }}
        """)
        
        # 添加到工具栏
        self._toolbar_layout.addWidget(self._refresh_button)
        self._toolbar_layout.addStretch()
        
        # 寄存器表格
        self._register_table = RegisterTable()
        
        # 添加到主布局
        self._layout.addWidget(self._toolbar)
        self._layout.addWidget(self._register_table)
        
        self.setLayout(self._layout)
        
        # 连接信号槽
        self._refresh_button.clicked.connect(self.refresh_clicked)
        self._register_table.register_value_changed.connect(self.register_value_changed)
    
    def add_register(self, slave_id, block_name, address, value):
        """添加寄存器"""
        self._register_table.add_register(slave_id, block_name, address, value)
    
    def update_register_value(self, slave_id, block_name, address, value):
        """更新寄存器值"""
        return self._register_table.update_register_value(slave_id, block_name, address, value)
    
    def clear_registers(self):
        """清空寄存器"""
        self._register_table.clear_registers()
