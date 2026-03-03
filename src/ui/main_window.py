from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QListWidget, QListWidgetItem, QLabel, 
                             QFileDialog, QProgressBar, QMessageBox, QGroupBox, QCheckBox,
                             QSplitter, QMenu)
from PyQt6.QtCore import Qt, QTimer
from src.core.ftp_manager import FtpManager, FtpServerConfig
from src.utils.config import load_config, save_config
from src.ui.server_dialog import ServerDialog
from src.ui.signals import FtpSignals
from src.ui.remote_browser import RemoteBrowserWidget

class ServerListItem(QWidget):
    def __init__(self, config: FtpServerConfig, toggle_callback=None):
        super().__init__()
        self.config = config
        self.toggle_callback = toggle_callback
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        self.enable_cb = QCheckBox()
        self.enable_cb.setChecked(getattr(config, 'enabled', True))
        self.enable_cb.stateChanged.connect(self._on_toggle)
        
        self.name_label = QLabel(f"{config.name} ({config.host}:{config.port})")
        
        self.status_label = QLabel("等待上传")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setFixedWidth(120)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        
        layout.addWidget(self.enable_cb)
        layout.addWidget(self.name_label, stretch=3)
        layout.addWidget(self.progress_bar, stretch=2)
        layout.addWidget(self.status_label, stretch=1)
        
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        
    def _on_toggle(self, state):
        is_checked = state == Qt.CheckState.Checked.value
        if self.toggle_callback:
            self.toggle_callback(self.config, is_checked)

class FileListItem(QWidget):
    def __init__(self, path: str, delete_callback):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)  # Increased top/bottom margins
        
        self.path_label = QLabel(path)
        self.path_label.setToolTip(path)
        
        self.del_btn = QPushButton("删除")
        self.del_btn.setFixedWidth(50)
        self.del_btn.setMinimumHeight(24) # Added minimum height
        self.del_btn.setStyleSheet("color: red; padding: 2px;margin-top: -5px;") # Maintained padding but min-height will ensure text fits
        self.del_btn.clicked.connect(lambda: delete_callback(path))
        
        layout.addWidget(self.path_label, stretch=1)
        layout.addWidget(self.del_btn)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FtpTool - 一键分发工具")
        self.resize(1000, 600)
        
        self.ftp_manager = FtpManager()
        self.load_servers()
        
        self.signals = FtpSignals()
        self.signals.progress.connect(self.update_progress)
        self.signals.status.connect(self.update_status)
        
        self.setup_ui()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_threads)
        self.threads = []
        
    def setup_ui(self):
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(self.splitter)
        
        # --- Left Panel ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # --- File Selection Area ---
        file_group = QGroupBox("1. 选择要分发的文件/文件夹")
        file_layout = QVBoxLayout(file_group)
        
        self.file_list_widget = QListWidget()
        file_layout.addWidget(self.file_list_widget)
        
        btn_file_layout = QHBoxLayout()
        btn_select_files = QPushButton("添加文件...")
        btn_select_files.clicked.connect(self.select_files)
        btn_select_folder = QPushButton("添加文件夹...")
        btn_select_folder.clicked.connect(self.select_folder)
        btn_clear_files = QPushButton("清空列表")
        btn_clear_files.clicked.connect(self.clear_files)
        
        btn_file_layout.addWidget(btn_select_files)
        btn_file_layout.addWidget(btn_select_folder)
        btn_file_layout.addWidget(btn_clear_files)
        
        file_layout.addLayout(btn_file_layout)
        left_layout.addWidget(file_group)
        
        # --- Server List Area ---
        server_group = QGroupBox("2. 目标服务器列表")
        server_layout = QVBoxLayout(server_group)
        
        self.server_list_widget = QListWidget()
        server_layout.addWidget(self.server_list_widget)
        self.refresh_server_list()
        
        btn_server_layout = QHBoxLayout()
        btn_add = QPushButton("添加服务器")
        btn_add.clicked.connect(self.add_server)
        btn_edit = QPushButton("编辑选中")
        btn_edit.clicked.connect(self.edit_server)
        btn_del = QPushButton("删除选中")
        btn_del.clicked.connect(self.delete_server)
        btn_test = QPushButton("测试连接")
        btn_test.clicked.connect(self.test_connection)
        
        btn_server_layout.addWidget(btn_add)
        btn_server_layout.addWidget(btn_edit)
        btn_server_layout.addWidget(btn_del)
        btn_server_layout.addWidget(btn_test)
        
        server_layout.addLayout(btn_server_layout)
        left_layout.addWidget(server_group)
        
        # --- Actions Area ---
        action_layout = QHBoxLayout()
        self.btn_upload = QPushButton("开始上传及分发")
        self.btn_upload.setObjectName("primaryButton")
        self.btn_upload.clicked.connect(self.start_upload)
        action_layout.addWidget(self.btn_upload)
        left_layout.addLayout(action_layout)
        
        # --- Right Panel (Remote Browser) ---
        self.remote_browser = RemoteBrowserWidget(self.ftp_manager)
        self.remote_browser.hide()
        
        self.splitter.addWidget(left_widget)
        self.splitter.addWidget(self.remote_browser)
        self.splitter.setSizes([600, 400])
        
        self.selected_paths = []
        
    def load_servers(self):
        configs = load_config()
        self.ftp_manager.load_servers(configs)
        
    def save_servers(self):
        save_config(self.ftp_manager.get_servers_as_dicts())
        
    def refresh_server_list(self):
        self.server_list_widget.clear()
        
        def on_server_toggled(config, is_enabled):
            config.enabled = is_enabled
            self.save_servers()
            
        for i, config in enumerate(self.ftp_manager.servers):
            item = QListWidgetItem(self.server_list_widget)
            widget = ServerListItem(config, on_server_toggled)
            
            # Setup Context Menu for this row
            widget.customContextMenuRequested.connect(
                lambda pos, cfg=config: self.show_server_context_menu(pos, cfg)
            )
            
            item.setSizeHint(widget.sizeHint())
            
            # Save references mapped by host to update from thread dynamically
            item.setData(Qt.ItemDataRole.UserRole, {
                "host": config.host,
                "progress_bar": widget.progress_bar,
                "status_label": widget.status_label
            })
            
            self.server_list_widget.setItemWidget(item, widget)

    def _reset_progress(self):
        for i in range(self.server_list_widget.count()):
            item = self.server_list_widget.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            data["progress_bar"].setValue(0)
            data["status_label"].setText("等待上传")
            data["status_label"].setStyleSheet("color: black;")

    def show_server_context_menu(self, pos, config: FtpServerConfig):
        menu = QMenu(self)
        browse_action = menu.addAction("🔍 浏览远端目录")
        
        action = menu.exec(self.sender().mapToGlobal(pos))
        if action == browse_action:
            self.open_remote_browser(config)
            
    def open_remote_browser(self, config: FtpServerConfig):
        self.remote_browser.show()
        # If the window is too small, expand it a bit
        if self.width() < 900:
            self.resize(1000, max(self.height(), 600))
        self.remote_browser.load_server(config)

    def select_files(self):
        filenames, _ = QFileDialog.getOpenFileNames(self, "选择要分发的文件", "", "All Files (*)")
        if filenames:
            for f in filenames:
                self.add_file_item(f)
            self._reset_progress()
            
    def select_folder(self):
        foldername = QFileDialog.getExistingDirectory(self, "选择要分发的文件夹")
        if foldername:
            self.add_file_item(foldername)
            self._reset_progress()
            
    def add_file_item(self, path):
        if path not in self.selected_paths:
            self.selected_paths.append(path)
            
            item = QListWidgetItem(self.file_list_widget)
            widget = FileListItem(path, self.remove_file_item)
            item.setSizeHint(widget.sizeHint())
            item.setData(Qt.ItemDataRole.UserRole, path)
            
            self.file_list_widget.setItemWidget(item, widget)
            
    def remove_file_item(self, path):
        if path in self.selected_paths:
            self.selected_paths.remove(path)
            
        for i in range(self.file_list_widget.count()):
            item = self.file_list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == path:
                self.file_list_widget.takeItem(i)
                break
                
    def clear_files(self):
        self.selected_paths.clear()
        self.file_list_widget.clear()
        self._reset_progress()
            
    def add_server(self):
        dlg = ServerDialog(self)
        if dlg.exec():
            data = dlg.get_data()
            config = FtpServerConfig.from_dict(data)
            self.ftp_manager.add_server(config)
            self.save_servers()
            self.refresh_server_list()
            
    def edit_server(self):
        row = self.server_list_widget.currentRow()
        if row < 0:
            QMessageBox.information(self, "提示", "请先选择需要编辑的目标服务器。")
            return
            
        config = self.ftp_manager.servers[row]
        dlg = ServerDialog(self, config.to_dict())
        if dlg.exec():
            data = dlg.get_data()
            self.ftp_manager.servers[row] = FtpServerConfig.from_dict(data)
            self.save_servers()
            self.refresh_server_list()
            
    def delete_server(self):
        row = self.server_list_widget.currentRow()
        if row < 0:
            return
            
        reply = QMessageBox.question(self, "确认", "确定要删除选拔的服务器连接配置吗？",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.ftp_manager.remove_server(row)
            self.save_servers()
            self.refresh_server_list()
            
    def test_connection(self):
        row = self.server_list_widget.currentRow()
        if row < 0:
            QMessageBox.information(self, "提示", "请先选择需要测试连接的服务器。")
            return
            
        config = self.ftp_manager.servers[row]
        success, msg = self.ftp_manager.test_connection(config)
        if success:
            QMessageBox.information(self, "测试结果", f"✅ 成功连接到 {config.name}")
        else:
            QMessageBox.critical(self, "测试结果", f"❌ 无法连接到 {config.name}:\n{msg}")

    def start_upload(self):
        if not self.selected_paths:
            QMessageBox.warning(self, "提示", "请先选择至少一个待上传的文件或文件夹。")
            return
            
        if not self.ftp_manager.servers:
            QMessageBox.warning(self, "提示", "请至少配置并添加一台目标服务器。")
            return
            
        self.btn_upload.setEnabled(False)
        self.btn_upload.setText("资源分发中，请稍后...")
        
        def prog_cb(host, u, t):
            self.signals.progress.emit(host, u, t)
            
        def stat_cb(host, msg, code):
            self.signals.status.emit(host, msg, code)
            
        self.threads = self.ftp_manager.upload_to_all(self.selected_paths, "", prog_cb, stat_cb)
        self.timer.start(500) # Check every 500ms if upload is completely done
        
    def check_threads(self):
        all_done = True
        for th in self.threads:
            if th.is_alive():
                all_done = False
                break
                
        if all_done:
            self.timer.stop()
            self.btn_upload.setEnabled(True)
            self.btn_upload.setText("开始上传及分发")
            QMessageBox.information(self, "完工", "所有分发任务已执行完毕，请看详细状态！")
            
    def update_progress(self, host, uploaded, total):
        for i in range(self.server_list_widget.count()):
            item = self.server_list_widget.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            if data["host"] == host:
                if total > 0:
                    percent = int((uploaded / total) * 100)
                    data["progress_bar"].setValue(percent)
                break
                
    def update_status(self, host, message, status_code):
        for i in range(self.server_list_widget.count()):
            item = self.server_list_widget.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            if data["host"] == host:
                data["status_label"].setText(message)
                if status_code == 1:
                    data["status_label"].setStyleSheet("color: green;")
                elif status_code == -1:
                    data["status_label"].setStyleSheet("color: red;")
                else:
                    data["status_label"].setStyleSheet("color: #FF9800;")
                break
