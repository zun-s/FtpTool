import json
import os
from typing import List

CONFIG_FILE = "ftp_config.json"

def load_config() -> List[dict]:
    """从本地加载 FTP 服务器配置列表"""
    if not os.path.exists(CONFIG_FILE):
        return []
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return []

def save_config(servers: List[dict]):
    """将 FTP 服务器配置列表保存到本地"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(servers, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving config: {e}")
