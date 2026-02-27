import logging
import os
from datetime import datetime

# 只需要配置全局日志一次
def setup_logger():
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    log_file = os.path.join(log_dir, f"ftp_tool_{datetime.now().strftime('%Y%m%d')}.log")
    
    # 获取 root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # 避免重复添加 Handler
    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(module)s: %(message)s')
        
        # 控制台 Handler (便于开发调试)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.DEBUG)
        
        logger.addHandler(console_handler)

        # 文件 Handler
        try:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.INFO)
            logger.addHandler(file_handler)
        except PermissionError:
            logger.warning(f"无法获取日志文件权限：{log_file}。可能被别的程序占用，本次运行仅在控制台输出日志。")

def get_logger(__name__):
    return logging.getLogger(__name__)
