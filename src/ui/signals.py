from PyQt6.QtCore import QObject, pyqtSignal

class FtpSignals(QObject):
    # host, uploaded_bytes, total_bytes
    progress = pyqtSignal(str, int, int)
    # host, message, status_code (-1: error, 0: in progress, 1: success)
    status = pyqtSignal(str, str, int)
