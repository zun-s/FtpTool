import sys
import os

def get_base_path():
    """获取项目根目录或 PyInstaller 运行时的临时目录"""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

base_path = get_base_path()

# 将项目根目录 (src 的上一级) 添加到 sys.path 中
sys.path.append(base_path)

from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.utils.logger import setup_logger

def main():
    # 初始化全局日志
    setup_logger()
    
    app = QApplication(sys.argv)
    
    # Optional: Enable high DPI scaling
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    
    app.setStyle("Fusion")
    
    # Load custom QSS styles
    qss_path = os.path.join(base_path, "assets", "style.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    # Need Qt module to set HighDpiScaling
    from PyQt6.QtCore import Qt
    main()
