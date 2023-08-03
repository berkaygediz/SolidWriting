import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.default_values = {
            'font_family': 'Arial',
            'font_size': 10,
            'bold': False,
            'italic': False,
            'underline': False,
            'alignment': Qt.AlignLeft,
            'text_color': '#000000',
            'background_color': '#FFFFFF',
        }

        self.is_saved = False
        self.file_name = None
        self.default_directory = QDir().homePath()

        self.text_editor = QTextEdit()
        self.text_editor.setFontFamily(self.default_values['font_family'])
        self.text_editor.setFontPointSize(self.default_values['font_size'])
        self.text_editor.setTextColor(
            QColor(self.default_values['text_color']))
        self.text_editor.setTextBackgroundColor(
            QColor(self.default_values['background_color']))
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Loading...", 2000)

        self.dock_widget = QDockWidget("Details", self)
        self.statistics_label = QLabel()
        self.dock_widget.setWidget(self.statistics_label)
        self.dock_widget.setAllowedAreas(Qt.LeftDockWidgetArea)
        self.dock_widget.setObjectName("Details")
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_widget)
        self.setCentralWidget(self.text_editor)

        self.update_statistics()
        self.text_editor.textChanged.connect(self.update_statistics)

        self.actionprepare()
        self.toolbar()

    def update_window_title(self):
        file = self.file_name if self.file_name else "New File"
        asterisk = "*" if self.is_saved else ""
        self.setWindowTitle(f"{file}{asterisk} - BG Text Editor")

    def update_statistics(self):
        text = self.text_editor.toPlainText()
        character_count = len(text)
        word_count = len(text.split())
        line_count = text.count(chr(10)) + 1
        statistics = f"<table><tr><td><b>Character Count:</b></td><td>{character_count}</td></tr><tr><td><b>Word Count:</b></td><td>{word_count}</td></tr><tr><td><b>Line Count:</b></td><td>{line_count}</td></tr></table>"
        self.statistics_label.setText(statistics)
        self.is_saved = False
        self.update_window_title()

    def alignrightevent(self):
        if self.text_editor.alignment() == Qt.AlignRight:
            self.text_editor.setAlignment(Qt.AlignLeft)
        else:
            self.text_editor.setAlignment(Qt.AlignRight)

    def alignleftevent(self):
        if self.text_editor.alignment() == Qt.AlignLeft:
            self.text_editor.setAlignment(Qt.AlignLeft)
        else:
            self.text_editor.setAlignment(Qt.AlignLeft)

    def aligncenterevent(self):
        if self.text_editor.alignment() == Qt.AlignCenter:
            self.text_editor.setAlignment(Qt.AlignLeft)
        else:
            self.text_editor.setAlignment(Qt.AlignCenter)

    def alignjustifiedevent(self):
        if self.text_editor.alignment() == Qt.AlignJustify:
            self.text_editor.setAlignment(Qt.AlignLeft)
        else:
            self.text_editor.setAlignment(Qt.AlignJustify)

    def bold(self):
        if self.text_editor.fontWeight() == QFont.Bold:
            self.text_editor.setFontWeight(QFont.Normal)
        else:
            self.text_editor.setFontWeight(QFont.Bold)

    def italic(self):
        if self.text_editor.fontItalic():
            self.text_editor.setFontItalic(False)
        else:
            self.text_editor.setFontItalic(True)

    def underline(self):
        if self.text_editor.fontUnderline():
            self.text_editor.setFontUnderline(False)
        else:
            self.text_editor.setFontUnderline(True)

    def actionprepare(self):
        self.alignrightevent = QAction('Align Right', statusTip='Text rightward.',
                                       triggered=self.alignrightevent, checkable=False, shortcut='Alt+R')
        self.alignleftevent = QAction('Align Left', statusTip='Text leftward.',
                                      triggered=self.alignleftevent, checkable=False, shortcut='Alt+L')
        self.aligncenterevent = QAction('Align Center', statusTip='Text centered.',
                                        triggered=self.aligncenterevent, checkable=False, shortcut='Alt+C')
        self.alignjustifiedevent = QAction('Align Justify', statusTip='Text justified.',
                                           triggered=self.alignjustifiedevent, checkable=False, shortcut='Alt+J')
        self.bold = QAction('Bold', statusTip='Text bold.',
                            triggered=self.bold, checkable=False, shortcut='Alt+B')
        self.italic = QAction('Italic', statusTip='Text italic.',
                              triggered=self.italic, checkable=False, shortcut='Alt+I')
        self.underline = QAction('Underline', statusTip='Text underline.',
                                 triggered=self.underline, checkable=False, shortcut='Alt+U')

    def toolbar(self):
        self.toolbar = self.addToolBar('Toolbar')
        self.setObjectName("Toolbar")
        self.toolbar.addAction(self.alignrightevent)
        self.toolbar.addAction(self.alignleftevent)
        self.toolbar.addAction(self.aligncenterevent)
        self.toolbar.addAction(self.alignjustifiedevent)
        self.toolbar.addAction(self.bold)
        self.toolbar.addAction(self.italic)
        self.toolbar.addAction(self.underline)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    app.setOrganizationName("BG")
    app.setApplicationName("BG Text Editor")
    app.setApplicationVersion("0.1")
    main_window.show()
    sys.exit(app.exec_())
