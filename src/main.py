import sys
import os

# 将项目根目录 (src 的上一级) 添加到 sys.path 中
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
    qss_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "style.qss")
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
