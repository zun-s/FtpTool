import ftplib
import os
import threading
from typing import List, Callable, Optional, Tuple
from src.utils.logger import get_logger

logger = get_logger(__name__)

class FtpServerConfig:
    def __init__(self, host: str, port: int, username: str, password: str, name: str = "", passive_mode: bool = True, remote_dir: str = "", enabled: bool = True):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.name = name or host
        self.passive_mode = passive_mode
        self.remote_dir = remote_dir
        self.enabled = enabled

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "password": self.password,
            "passive_mode": self.passive_mode,
            "remote_dir": self.remote_dir,
            "enabled": self.enabled
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            host=data.get("host", ""),
            port=data.get("port", 21),
            username=data.get("username", "anonymous"),
            password=data.get("password", ""),
            name=data.get("name", ""),
            passive_mode=data.get("passive_mode", True),
            remote_dir=data.get("remote_dir", ""),
            enabled=data.get("enabled", True)
        )

class FtpManager:
    def __init__(self):
        self.servers: List[FtpServerConfig] = []
        
    def add_server(self, config: FtpServerConfig):
        self.servers.append(config)
        
    def remove_server(self, index: int):
        if 0 <= index < len(self.servers):
            self.servers.pop(index)
            
    def load_servers(self, configs: List[dict]):
        self.servers = [FtpServerConfig.from_dict(c) for c in configs]
        
    def get_servers_as_dicts(self) -> List[dict]:
        return [s.to_dict() for s in self.servers]

    def test_connection(self, config: FtpServerConfig) -> Tuple[bool, str]:
        """测试单个 FTP 服务器的连接状态"""
        try:
            ftp = ftplib.FTP()
            ftp.connect(config.host, config.port, timeout=5)
            ftp.login(config.username, config.password)
            ftp.set_pasv(config.passive_mode)
            ftp.quit()
            return True, "Success"
        except Exception as e:
            logger.error(f"Test connection failed for {config.host}: {e}")
            return False, str(e)

    def _ensure_remote_dir(self, ftp: ftplib.FTP, remote_dir: str):
        if not remote_dir or remote_dir.strip() == "/" or remote_dir.strip() == "":
            return
            
        if remote_dir.startswith("/"):
            ftp.cwd("/")
            
        parts = remote_dir.replace('\\', '/').split('/')
        for part in parts:
            if not part:
                continue
            try:
                ftp.cwd(part)
            except ftplib.error_perm:
                ftp.mkd(part)
                ftp.cwd(part)

    def upload_paths_to_server(self, config: FtpServerConfig, local_paths: List[str], remote_dir: str, progress_callback: Optional[Callable] = None) -> Tuple[bool, str]:
        """上传多个文件/文件夹到单个服务器"""
        try:
            # 1. 计算所有文件的总大小，用于进度条
            total_size = 0
            for path in local_paths:
                if os.path.isfile(path):
                    total_size += os.path.getsize(path)
                elif os.path.isdir(path):
                    for root, _, files in os.walk(path):
                        for file in files:
                            total_size += os.path.getsize(os.path.join(root, file))
                            
            uploaded_size = 0
            
            ftp = ftplib.FTP()
            ftp.connect(config.host, config.port, timeout=30)
            ftp.login(config.username, config.password)
            ftp.set_pasv(config.passive_mode)
            
            # 切换到指定目录 (如果提供了且不是根目录)
            if remote_dir and remote_dir.strip() and remote_dir != "/":
                self._ensure_remote_dir(ftp, remote_dir)
            
            base_remote_dir = ftp.pwd()
            
            def handle_block(block):
                nonlocal uploaded_size
                uploaded_size += len(block)
                if progress_callback:
                    progress_callback(config.host, uploaded_size, total_size)

            def _upload_file(local_file: str, remote_file_name: str):
                logger.info(f"Uploading {local_file} -> {remote_file_name} on {config.host}")
                with open(local_file, 'rb') as f:
                    if ftp.sock:
                        ftp.sock.settimeout(60)
                    ftp.storbinary(f'STOR {remote_file_name}', f, 8192, handle_block)

            def _upload_recursive(current_local_path: str, current_remote_dir: str):
                ftp.cwd(current_remote_dir)
                if os.path.isfile(current_local_path):
                    _upload_file(current_local_path, os.path.basename(current_local_path))
                elif os.path.isdir(current_local_path):
                    # 在远端创建与本地文件夹同名的目录
                    folder_name = os.path.basename(current_local_path)
                    try:
                        ftp.cwd(folder_name)
                    except ftplib.error_perm:
                        ftp.mkd(folder_name)
                        ftp.cwd(folder_name)
                    
                    next_remote_dir = ftp.pwd()
                    
                    # 遍历本地文件夹内容
                    for item in os.listdir(current_local_path):
                        item_local_path = os.path.join(current_local_path, item)
                        _upload_recursive(item_local_path, next_remote_dir)
                        
                    # 恢复层级
                    ftp.cwd(current_remote_dir)

            # 遍历所有被选中的路径分别上传
            for path in local_paths:
                _upload_recursive(path, base_remote_dir)
                
            ftp.quit()
            return True, "Upload Success"
        except Exception as e:
            logger.error(f"Upload failed for {config.host}: {e}", exc_info=True)
            return False, str(e)

    def list_directory(self, config: FtpServerConfig, path: str = "") -> Tuple[bool, List[dict], str]:
        """列出远程目录内容"""
        try:
            ftp = ftplib.FTP()
            ftp.connect(config.host, config.port, timeout=30)
            ftp.login(config.username, config.password)
            ftp.set_pasv(config.passive_mode)
            
            if path and path.strip():
                ftp.cwd(path)
                
            current_path = ftp.pwd()
            items = []
            
            # 尝试使用 mlsd (现代FTP服务器支持，结构化数据更优)
            try:
                for name, facts in ftp.mlsd():
                    if name in ('.', '..'):
                        continue
                    item_type = 'dir' if facts.get('type') in ('dir', 'cdir', 'pdir') else 'file'
                    size = facts.get('size', '')
                    modify = facts.get('modify', '')
                    # 格式化时间 YYYYMMDDHHMMSS -> YYYY-MM-DD HH:MM:SS
                    if modify and len(modify) >= 14:
                        modify = f"{modify[0:4]}-{modify[4:6]}-{modify[6:8]} {modify[8:10]}:{modify[10:12]}:{modify[12:14]}"
                        
                    items.append({
                        'name': name,
                        'type': item_type,
                        'size': size,
                        'modify': modify
                    })
            except Exception as e:
                # 降级：如果不支持 mlsd，尝试解析 dir 输出 (LIST 格式各异，尽力解析)
                logger.warning(f"mlsd not supported by {config.host}, falling back to LIST. Error: {e}")
                lines = []
                ftp.dir(lines.append)
                for line in lines:
                    if not line.strip():
                        continue
                    parts = line.split(None, 8)
                    if len(parts) >= 9:
                        name = parts[-1]
                        if name in ('.', '..'):
                            continue
                        is_dir = line.startswith('d')
                        size = parts[4] if not is_dir else ''
                        modify = f"{parts[5]} {parts[6]} {parts[7]}"
                        items.append({
                            'name': name,
                            'type': 'dir' if is_dir else 'file',
                            'size': size,
                            'modify': modify
                        })
            
            ftp.quit()
            
            # 排序：文件夹在前，文件在后，按字母排序
            items.sort(key=lambda x: (x['type'] == 'file', x['name'].lower()))
            
            return True, items, current_path
            
        except Exception as e:
            logger.error(f"Failed to list directory on {config.host}: {e}", exc_info=True)
            return False, [], str(e)

    def download_path(self, config: FtpServerConfig, remote_path: str, local_save_dir: str, is_dir: bool = False, progress_callback: Optional[Callable] = None) -> Tuple[bool, str]:
        """从服务器下载单个文件或整个目录到本地"""
        try:
            ftp = ftplib.FTP()
            ftp.connect(config.host, config.port, timeout=30)
            ftp.login(config.username, config.password)
            ftp.set_pasv(config.passive_mode)

            def _download_file(r_file: str, l_file: str):
                logger.info(f"Downloading {r_file} -> {l_file}")
                # Ensure local directory exists
                os.makedirs(os.path.dirname(l_file), exist_ok=True)
                
                try:
                    file_size = ftp.size(r_file)
                except Exception:
                    file_size = 0
                    
                downloaded_size = 0
                def handle_block(block):
                    nonlocal downloaded_size
                    f.write(block)
                    downloaded_size += len(block)
                    if progress_callback:
                        progress_callback(config.host, downloaded_size, file_size)

                with open(l_file, 'wb') as f:
                    if ftp.sock:
                        ftp.sock.settimeout(60)
                    try:
                        ftp.voidcmd('TYPE I')
                    except Exception as e:
                        logger.warning(f"Failed to set TYPE I for download: {e}")
                    ftp.retrbinary(f'RETR {r_file}', handle_block)

            def _download_recursive(r_path: str, l_dir: str):
                # Try to list the directory to see its contents
                ftp.cwd(r_path)
                lines = []
                ftp.dir(lines.append)
                
                for line in lines:
                    if not line.strip():
                        continue
                        
                    parts = line.split(None, 8)
                    if len(parts) >= 9:
                        name = parts[-1]
                        if name in ('.', '..'):
                            continue
                            
                        is_folder = line.startswith('d')
                        item_r_path = f"{r_path}/{name}" if r_path != "/" else f"/{name}"
                        item_l_path = os.path.join(l_dir, name)
                        
                        if is_folder:
                            os.makedirs(item_l_path, exist_ok=True)
                            _download_recursive(item_r_path, item_l_path)
                        else:
                            _download_file(item_r_path, item_l_path)
                
                # Go back up
                parts = r_path.rstrip('/').split('/')
                if len(parts) > 1:
                    ftp.cwd("/".join(parts[:-1]) or "/")

            base_name = os.path.basename(remote_path.rstrip('/'))
            if not is_dir:
                # Single file download
                local_file_path = os.path.join(local_save_dir, base_name)
                _download_file(remote_path, local_file_path)
            else:
                # Directory download
                local_folder_path = os.path.join(local_save_dir, base_name)
                os.makedirs(local_folder_path, exist_ok=True)
                _download_recursive(remote_path, local_folder_path)

            ftp.quit()
            return True, "Download Success"
            
        except Exception as e:
            logger.error(f"Failed to download {remote_path} from {config.host}: {e}", exc_info=True)
            return False, str(e)

    def delete_path(self, config: FtpServerConfig, remote_path: str, is_dir: bool = False) -> Tuple[bool, str]:
        """在服务器上删除文件或递归删除整个目录"""
        try:
            ftp = ftplib.FTP()
            ftp.connect(config.host, config.port, timeout=30)
            ftp.login(config.username, config.password)
            ftp.set_pasv(config.passive_mode)

            def _delete_recursive(tgt_dir: str):
                ftp.cwd(tgt_dir)
                lines = []
                ftp.dir(lines.append)
                
                for line in lines:
                    if not line.strip():
                        continue
                    parts = line.split(None, 8)
                    if len(parts) >= 9:
                        name = parts[-1]
                        if name in ('.', '..'):
                            continue
                            
                        is_folder = line.startswith('d')
                        if is_folder:
                            _delete_recursive(name)
                        else:
                            ftp.delete(name)
                            
                # Go back up and remove the dir itself
                ftp.cwd("..")
                folder_name = os.path.basename(tgt_dir.rstrip('/'))
                if folder_name:
                    ftp.rmd(folder_name)

            if not is_dir:
                ftp.delete(remote_path)
            else:
                _delete_recursive(remote_path)

            ftp.quit()
            return True, "Delete Success"
            
        except Exception as e:
            logger.error(f"Failed to delete {remote_path} on {config.host}: {e}", exc_info=True)
            return False, str(e)
            
    def upload_to_all(self, local_paths: List[str], remote_dir: str, 
                      progress_callback: Optional[Callable] = None, 
                      status_callback: Optional[Callable] = None) -> List[threading.Thread]:
        """并发上传多个文件/文件夹到所有被启用的服务器"""
        threads = []
        
        def worker(config: FtpServerConfig):
            if status_callback:
                status_callback(config.host, "Uploading...", 0) # status: 0 for in progress
            
            # 优先使用该服务器自带的独立路径配置，如果没有再使用全局传进来的默认路径
            target_dir = config.remote_dir.strip() if config.remote_dir and config.remote_dir.strip() else remote_dir
                
            success, msg = self.upload_paths_to_server(config, local_paths, target_dir, progress_callback)
            if status_callback:
                status_callback(config.host, f"Success" if success else f"Failed: {msg}", 1 if success else -1)

        for server in self.servers:
            if not getattr(server, 'enabled', True):
                if status_callback:
                    status_callback(server.host, "已跳过 (未启用)", 0)
                continue
            
            t = threading.Thread(target=worker, args=(server,))
            threads.append(t)
            t.start()
            
        return threads
