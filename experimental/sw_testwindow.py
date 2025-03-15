import sys

from PySide6.QtGui import QColor, QPainter, QPen, Qt
from PySide6.QtWidgets import (QApplication, QComboBox, QFrame, QLabel,
                               QSpinBox, QTextEdit, QVBoxLayout, QWidget)


class SW_Ruler(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(30)
        self.setStyleSheet("background-color: lightgray;")
        self.margin_left = 3
        self.margin_right = 1.5
        self.scale_factor = 1
        self.offset = 0
        self.setMouseTracking(True)

        self.drag = False
        self.l_x = 0

    def paintEvent(self, event):
        painter = QPainter(self)
        pen = QPen(QColor(0, 0, 0))
        painter.setPen(pen)
        width = self.width()

        for i in range(-50, int(18 * 100), 10):
            x_position = (i + 500 - self.offset) * self.scale_factor
            if x_position >= 0 and x_position <= width:
                painter.drawLine(x_position, 5, x_position, 20)
                if i % 50 == 0:
                    painter.drawText(x_position + 2, 25, f"{i / 10:.1f} cm")

        pen.setColor(QColor(255, 0, 0))
        pen.setWidth(3)
        painter.setPen(pen)
        painter.drawLine(
            self.margin_left * 10 * self.scale_factor - self.offset,
            5,
            self.margin_left * 10 * self.scale_factor - self.offset,
            20,
        )
        painter.drawLine(
            width - self.margin_right * 10 * self.scale_factor - self.offset,
            5,
            width - self.margin_right * 10 * self.scale_factor - self.offset,
            20,
        )

    def updateScaleFactor(self, factor):
        self.scale_factor = factor
        self.update()

    def setMargins(self, left, right):
        self.margin_left = left
        self.margin_right = right
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag = True
            self.l_x = event.position().x()

    def mouseMoveEvent(self, event):
        if self.drag:
            delta = event.position().x() - self.l_x
            self.offset += delta
            self.l_x = event.position().x()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag = False


class SW_TestWindow(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        self.ruler = SW_Ruler(self)

        self.text_container = QFrame(self)
        self.text_container.setStyleSheet("border: 1px solid black;")
        self.text_layout = QVBoxLayout(self.text_container)

        self.text_edit = QTextEdit(self)
        self.text_edit.setAcceptRichText(True)
        self.text_edit.setLineWrapMode(QTextEdit.WidgetWidth)
        self.text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.text_layout.addWidget(self.text_edit)

        self.margin_left_input = QSpinBox(self)
        self.margin_left_input.setValue(3)
        self.margin_left_input.setRange(0, 20)
        self.margin_left_input.valueChanged.connect(self.updateMargins)

        self.margin_right_input = QSpinBox(self)
        self.margin_right_input.setValue(1.5)
        self.margin_right_input.setRange(0, 20)
        self.margin_right_input.valueChanged.connect(self.updateMargins)

        self.zoom_input = QComboBox(self)
        self.zoom_input.addItems(["100%", "125%", "150%", "200%", "250%"])
        self.zoom_input.currentIndexChanged.connect(self.updateZoomFactor)

        self.setMargins()

        layout.addWidget(self.ruler)
        layout.addWidget(self.text_container)

        layout.addWidget(QLabel("Left Margin (cm):"))
        layout.addWidget(self.margin_left_input)
        layout.addWidget(QLabel("Right Margin (cm):"))
        layout.addWidget(self.margin_right_input)
        layout.addWidget(QLabel("Zoom:"))
        layout.addWidget(self.zoom_input)

        self.setLayout(layout)

        self.setWindowTitle("SolidWriting - Experimental - Ruler & Zoom")
        self.resize(800, 600)

    def setMargins(self):
        self.ruler.setMargins(
            self.margin_left_input.value(), self.margin_right_input.value()
        )

        l_margin = self.margin_left_input.value() * 10
        r_margin = self.margin_right_input.value() * 10

        self.text_container.setStyleSheet(
            f"""
            border: 1px solid #000;
            padding-left: {self.margin_left_input.value()}cm;
            padding-right: {self.margin_right_input.value()}cm;
            """
        )

        self.text_edit.document().setDocumentMargin(l_margin)
        self.text_edit.setFixedWidth(600)

    def updateMargins(self):
        self.setMargins()

    def updateZoomFactor(self):
        zoom_percent = self.zoom_input.currentText()
        zoom_factor = int(zoom_percent.replace("%", ""))

        self.text_edit.setStyleSheet(
            f"""
            border: 1px solid #000;
            margin-left: {self.margin_left_input.value()}cm;
            margin-right: {self.margin_right_input.value()}cm;
            """
        )
        self.text_container.setFixedWidth(600 * (zoom_factor / 100))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SW_TestWindow()
    window.show()
    sys.exit(app.exec())
