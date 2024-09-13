import time

from PySide6.QtCore import *


class ThreadingEngine(QThread):
    update = Signal()

    def __init__(self, adaptiveResponse, parent=None):
        super(ThreadingEngine, self).__init__(parent)
        self.adaptiveResponse = float(adaptiveResponse)
        self.running = False
        self.mutex = QMutex()

    def run(self):
        if not self.running:
            self.mutex.lock()
            self.running = True
            self.mutex.unlock()
            time.sleep(0.15 * self.adaptiveResponse)
            self.update.emit()
            self.mutex.lock()
            self.running = False
            self.mutex.unlock()
