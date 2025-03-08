import time

from PySide6.QtCore import *


class ThreadingEngine(QThread):
    update = Signal()

    def __init__(self, adaptiveResponse: float, parent=None):
        super(ThreadingEngine, self).__init__(parent)
        self.adaptiveResponse = adaptiveResponse
        self.running = False

    def run(self):
        if self.running:
            return
        self.running = True
        time.sleep(0.15 * self.adaptiveResponse)
        self.update.emit()
        self.running = False
