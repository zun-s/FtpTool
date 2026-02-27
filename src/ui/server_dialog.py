from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QCheckBox

class ServerDialog(QDialog):
    def __init__(self, parent=None, server_data=None):
        super().__init__(parent)
        self.setWindowTitle("FTP 服务器配置")
        self.resize(300, 250)
        self.server_data = server_data or {}
        
        layout = QVBoxLayout(self)
        
        self.name_edit = QLineEdit(self.server_data.get("name", ""))
        self.name_edit.setPlaceholderText("例如: 生产服务器1")
        
        self.host_edit = QLineEdit(self.server_data.get("host", ""))
        self.host_edit.setPlaceholderText("IP 或域名")
        
        self.port_edit = QLineEdit(str(self.server_data.get("port", 21)))
        
        self.user_edit = QLineEdit(self.server_data.get("username", "anonymous"))
        
        self.pass_edit = QLineEdit(self.server_data.get("password", ""))
        self.pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.dir_edit = QLineEdit(self.server_data.get("remote_dir", ""))
        self.dir_edit.setPlaceholderText("留空则使用全局默认路径")
        
        self.passive_cb = QCheckBox("被动模式 (Passive Mode)")
        self.passive_cb.setChecked(self.server_data.get("passive_mode", True))
        
        layout.addWidget(QLabel("别名 (可选):"))
        layout.addWidget(self.name_edit)
        layout.addWidget(QLabel("服务器地址 (Host):"))
        layout.addWidget(self.host_edit)
        layout.addWidget(QLabel("端口 (Port):"))
        layout.addWidget(self.port_edit)
        layout.addWidget(QLabel("用户名 (Username):"))
        layout.addWidget(self.user_edit)
        layout.addWidget(QLabel("密码 (Password):"))
        layout.addWidget(self.pass_edit)
        layout.addWidget(QLabel("自定义上传路径 (Remote Dir):"))
        layout.addWidget(self.dir_edit)
        layout.addWidget(self.passive_cb)
        
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.accept_data)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
    def accept_data(self):
        if not self.host_edit.text().strip():
            QMessageBox.warning(self, "错误", "服务器地址不能为空！")
            return
        
        try:
            port = int(self.port_edit.text().strip())
        except ValueError:
            QMessageBox.warning(self, "错误", "端口必须是数字！")
            return
            
        self.server_data = {
            "name": self.name_edit.text().strip() or self.host_edit.text().strip(),
            "host": self.host_edit.text().strip(),
            "port": port,
            "username": self.user_edit.text().strip() or "anonymous",
            "password": self.pass_edit.text(),
            "remote_dir": self.dir_edit.text().strip(),
            "passive_mode": self.passive_cb.isChecked()
        }
        self.accept()
        
    def get_data(self):
        return self.server_data
