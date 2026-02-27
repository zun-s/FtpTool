from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QLineEdit, QLabel, QMessageBox,
                             QMenu, QFileDialog, QProgressDialog, QApplication)
from PyQt6.QtCore import Qt
import os
from src.core.ftp_manager import FtpManager, FtpServerConfig

class RemoteBrowserWidget(QWidget):
    def __init__(self, ftp_manager: FtpManager):
        super().__init__()
        self.ftp_manager = ftp_manager
        self.current_config = None
        self.current_path = ""
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # --- Top Navigation Bar ---
        nav_layout = QHBoxLayout()
        
        self.btn_up = QPushButton("⬆️ 上一级")
        self.btn_up.clicked.connect(self.go_up)
        
        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        self.path_edit.setStyleSheet("background-color: #F3F4F6; color: #374151;")
        
        self.btn_refresh = QPushButton("刷新")
        self.btn_refresh.clicked.connect(self.refresh_current_dir)
        
        nav_layout.addWidget(self.btn_up)
        nav_layout.addWidget(self.path_edit, stretch=1)
        nav_layout.addWidget(self.btn_refresh)
        
        # --- File Table ---
        self.server_label = QLabel("当前未连接任何服务器")
        self.server_label.setStyleSheet("font-weight: bold; color: #1F2937; padding: 2px 0;")
        
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["名称", "大小", "类型", "修改时间"])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.resizeSection(0, 250)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.cellDoubleClicked.connect(self.on_item_double_clicked)
        
        # Context Menu
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addLayout(nav_layout)
        layout.addWidget(self.server_label)
        layout.addWidget(self.table)
        
    def load_server(self, config: FtpServerConfig):
        """加载指定的服务器，开启浏览"""
        self.current_config = config
        self.server_label.setText(f"🖥️ 当前所在的服务器: {config.name} ({config.host})")
        
        self.path_edit.setText(f"[{config.name}] Connecting...")
        target_dir = config.remote_dir.strip() if config.remote_dir else "/"
        self.load_directory(target_dir)
        
    def load_directory(self, path: str):
        if not self.current_config:
            return
            
        self.path_edit.setText(f"Loading {path} ...")
        self.table.setRowCount(0)
        
        success, items, actual_path = self.ftp_manager.list_directory(self.current_config, path)
        if success:
            self.current_path = actual_path
            self.path_edit.setText(actual_path)
            self.populate_table(items)
        else:
            self.path_edit.setText(self.current_path) # 回退显示之前的路径
            QMessageBox.warning(self, "浏览失败", f"无法加载目录内容:\n{actual_path}")
            
    def populate_table(self, items):
        self.table.setRowCount(len(items))
        for row, item in enumerate(items):
            # Name
            name_item = QTableWidgetItem(item['name'])
            if item['type'] == 'dir':
                name_item.setData(Qt.ItemDataRole.UserRole, 'dir')
                name_item.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_DirIcon))
            else:
                name_item.setData(Qt.ItemDataRole.UserRole, 'file')
                name_item.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_FileIcon))
                
            # Size
            size_str = self.format_size(item['size']) if item['size'] else ""
            size_item = QTableWidgetItem(size_str)
            
            # Type
            type_str = "文件夹" if item['type'] == 'dir' else "文件"
            type_item = QTableWidgetItem(type_str)
            
            # Modify
            mod_item = QTableWidgetItem(item['modify'])
            
            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, size_item)
            self.table.setItem(row, 2, type_item)
            self.table.setItem(row, 3, mod_item)

    def go_up(self):
        if not self.current_path or self.current_path == "/":
            return
            
        # 简单的父目录计算
        parts = self.current_path.rstrip('/').split('/')
        if len(parts) <= 1:
            parent_dir = "/"
        else:
            parent_dir = "/".join(parts[:-1])
            if not parent_dir:
                parent_dir = "/"
                
        self.load_directory(parent_dir)
        
    def refresh_current_dir(self):
        if self.current_path:
            self.load_directory(self.current_path)
            
    def on_item_double_clicked(self, row, col):
        name_item = self.table.item(row, 0)
        if not name_item:
            return
            
        item_type = name_item.data(Qt.ItemDataRole.UserRole)
        if item_type == 'dir':
            folder_name = name_item.text()
            # 拼接路径
            if self.current_path.endswith('/'):
                new_path = f"{self.current_path}{folder_name}"
            else:
                new_path = f"{self.current_path}/{folder_name}"
            
            self.load_directory(new_path)
        
    def format_size(self, size_bytes_str):
        try:
            size_bytes = int(size_bytes_str)
            if size_bytes < 1024:
                return f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                return f"{size_bytes / 1024:.1f} KB"
            elif size_bytes < 1024 * 1024 * 1024:
                return f"{size_bytes / (1024 * 1024):.1f} MB"
            else:
                return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
        except (ValueError, TypeError):
            return size_bytes_str

    def show_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if not item:
            return
            
        row = item.row()
        name_item = self.table.item(row, 0)
        
        menu = QMenu(self)
        download_action = menu.addAction("⬇️ 下载")
        delete_action = menu.addAction("❌ 删除")
        
        action = menu.exec(self.table.mapToGlobal(pos))
        if action == download_action:
            self.download_selected(row, name_item)
        elif action == delete_action:
            self.delete_selected(row, name_item)
            
    def _get_remote_path_for_item(self, filename: str) -> str:
        if self.current_path.endswith('/'):
            return f"{self.current_path}{filename}"
        else:
            return f"{self.current_path}/{filename}"
            
    def download_selected(self, row, name_item):
        filename = name_item.text()
        is_dir = name_item.data(Qt.ItemDataRole.UserRole) == 'dir'
        remote_path = self._get_remote_path_for_item(filename)
        
        # User selects local save directory
        local_dir = QFileDialog.getExistingDirectory(self, f"选择保存目录下载: {filename}")
        if not local_dir:
            return
            
        progress_dialog = QProgressDialog("正在下载...", "稍候", 0, 100, self)
        progress_dialog.setWindowTitle(f"下载 [{filename}]")
        progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        progress_dialog.setAutoClose(True)
        progress_dialog.setAutoReset(True)
        
        def _prog_cb(host, downloaded, total_size):
            if total_size > 0:
                pct = int((downloaded / total_size) * 100)
                progress_dialog.setValue(pct)
            else:
                progress_dialog.setValue(0) # indeterminate-like behavior if unknown size
            QApplication.processEvents()
                
        progress_dialog.show()
        success, msg = self.ftp_manager.download_path(self.current_config, remote_path, local_dir, is_dir, _prog_cb)
        progress_dialog.setValue(100)
        
        if success:
            QMessageBox.information(self, "下载完成", f"已成功下载至:\n{local_dir}")
        else:
            QMessageBox.critical(self, "下载失败", f"下载错误:\n{msg}")
            
    def delete_selected(self, row, name_item):
        filename = name_item.text()
        is_dir = name_item.data(Qt.ItemDataRole.UserRole) == 'dir'
        remote_path = self._get_remote_path_for_item(filename)
        
        reply = QMessageBox.question(self, "确认删除", f"确定要彻底删除该远端 {'目录' if is_dir else '文件'} 吗？\n{remote_path}\n此操作不可逆！", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            success, msg = self.ftp_manager.delete_path(self.current_config, remote_path, is_dir)
            if success:
                self.refresh_current_dir()
            else:
                QMessageBox.critical(self, "删除失败", f"删除遇到错误:\n{msg}")
