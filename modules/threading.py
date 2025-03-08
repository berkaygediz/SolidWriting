import time

from PySide6.QtCore import *


class ThreadingEngine(QThread):
    update = Signal()

    def __init__(self, adaptiveResponse: float, parent=None):
        super(ThreadingEngine, self).__init__(parent)
        self.adaptiveResponse = adaptiveResponse
        self.running = False  # Mutex kullanımı gereksiz

    def run(self):
        if self.running:
            return  # Zaten çalışıyorsa tekrar çalıştırma
        self.running = True
        time.sleep(0.15 * self.adaptiveResponse)
        self.update.emit()
        self.running = False  # Thread tamamlandıktan sonra sıfırla
