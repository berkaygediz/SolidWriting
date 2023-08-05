import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtPrintSupport import *


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

        self.selected_file = None
        self.is_saved = False
        self.file_name = None
        self.default_directory = QDir().homePath()
        self.directory = self.default_directory

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

    def strike(self):
        if self.text_editor.fontStrikeOut():
            self.text_editor.setFontStrikeOut(False)
        else:
            self.text_editor.setFontStrikeOut(True)

    def color(self):
        color = QColorDialog.getColor()
        self.text_editor.setTextColor(color)

    def backgroundcolor(self):
        color = QColorDialog.getColor()
        self.text_editor.setTextBackgroundColor(color)

    def actionprepare(self):
        self.alignrightevent = QAction('Right', statusTip='Text rightward.',
                                       triggered=self.alignrightevent, checkable=False, shortcut='Alt+R')
        self.alignleftevent = QAction('Left', statusTip='Text leftward.',
                                      triggered=self.alignleftevent, checkable=False, shortcut='Alt+L')
        self.aligncenterevent = QAction('Center', statusTip='Text centered.',
                                        triggered=self.aligncenterevent, checkable=False, shortcut='Alt+C')
        self.alignjustifiedevent = QAction('Justify', statusTip='Text justified.',
                                           triggered=self.alignjustifiedevent, checkable=False, shortcut='Alt+J')
        self.bold = QAction('Bold', statusTip='Text bold.',
                            triggered=self.bold, checkable=False, shortcut='Alt+B')
        self.italic = QAction('Italic', statusTip='Text italic.',
                              triggered=self.italic, checkable=False, shortcut='Alt+I')
        self.underline = QAction('Underline', statusTip='Text underline.',
                                 triggered=self.underline, checkable=False, shortcut='Alt+U')
        self.strike = QAction('Strike', statusTip='Text strike.',
                              triggered=self.strike, checkable=False, shortcut='Alt+S')
        self.color = QAction('Color', statusTip='Text color.',
                             triggered=self.color, checkable=False, shortcut='Alt+C+O')
        self.backgroundcolor = QAction('Background Color', statusTip='Text background color.',
                                       triggered=self.backgroundcolor, checkable=False, shortcut='Alt+B+G')
        self.openaction = QAction(
            'Open', statusTip='Open file.', triggered=self.open, shortcut=QKeySequence.Open)
        self.saveaction = QAction(
            'Save', statusTip='Save file.', triggered=self.save, shortcut=QKeySequence.Save)
        self.saveasaction = QAction(
            'Save As', statusTip='Save file as.', triggered=self.save_as, shortcut=QKeySequence.SaveAs)
        self.printaction = QAction(
            'Print', statusTip='Print file.', triggered=self.print, shortcut=QKeySequence.Print)
        self.exitaction = QAction(
            'Exit', statusTip='Exit application.', triggered=self.exit, shortcut=QKeySequence.Quit)
        self.undoaction = QAction(
            'Undo', statusTip='Undo last action.', triggered=self.undo, shortcut=QKeySequence.Undo)
        self.redoaction = QAction(
            'Redo', statusTip='Redo last action.', triggered=self.redo, shortcut=QKeySequence.Redo)

    def toolbar(self):
        self.toolbar = self.addToolBar('File')
        self.toolbar.addWidget(QLabel("<b>File:</b>"))
        self.toolbar.addAction(self.openaction)
        self.toolbar.addAction(self.saveaction)
        self.toolbar.addAction(self.saveasaction)
        self.toolbar.addAction(self.printaction)
        self.toolbar.addAction(self.exitaction)
        self.toolbar.addAction(self.undoaction)
        self.toolbar.addAction(self.redoaction)
        self.addToolBarBreak()
        self.toolbar = self.addToolBar('Format')
        self.toolbar.addWidget(QLabel("<b>Alignment:</b>"))
        self.toolbar.addAction(self.alignrightevent)
        self.toolbar.addAction(self.alignleftevent)
        self.toolbar.addAction(self.aligncenterevent)
        self.toolbar.addAction(self.alignjustifiedevent)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(QLabel("<b>Font:</b>"))
        self.toolbar.addAction(self.bold)
        self.toolbar.addAction(self.italic)
        self.toolbar.addAction(self.underline)
        self.toolbar.addAction(self.strike)
        self.addToolBarBreak()
        self.toolbar = self.addToolBar('Color')
        self.toolbar.addWidget(QLabel("<b>Color:</b>"))
        self.toolbar.addAction(self.color)
        self.toolbar.addAction(self.backgroundcolor)

    def savepermament(self):
        F = open(self.file_name, 'w')
        if os.path.splitext(self.file_name)[1] == ".html":
            F.write(self.text_editor.toHtml())
        else:
            F.write(self.text_editor.toPlainText())
        F.close()
        self.status_bar.showMessage("Saved.", 2000)
        self.is_saved = True
        self.update_window_title()

    def save_as(self):
        file = self.file_name if self.file_name else self.directory
        selected_file, _ = QFileDialog.getSaveFileName(self, app.applicationName() + " - Save As", file,
                                                       "HTML Files (*.html);;Text Files (*.txt)")

        if selected_file:
            self.file_name = selected_file
            self.savepermament()
            self.save_directory = os.path.dirname(self.file_name)
            return True
        else:
            return False

    def save(self):
        if self.is_saved:
            self.savepermament()
        elif self.file_name:
            self.savepermament()
        else:
            self.save_as()

    def open(self):
        file = self.file_name if self.file_name else self.directory
        selected_file, _ = QFileDialog.getOpenFileName(self, app.applicationName() + " - Open", file,
                                                       "HTML Files (*.html);;Text Files (*.txt)")

        if selected_file:
            self.file_name = selected_file
            self.openpermament()
            self.save_directory = os.path.dirname(self.file_name)
            return True
        else:
            return False

    def openpermament(self):
        F = open(self.file_name, 'r')
        if os.path.splitext(self.file_name)[1] == ".html":
            self.text_editor.setHtml(F.read())
        else:
            self.text_editor.setPlainText(F.read())
        F.close()
        self.status_bar.showMessage("Opened.", 2000)
        self.is_saved = True
        self.update_window_title()

    def print(self):
        printer = QPrinter(QPrinter.HighResolution)
        dialog = QPrintDialog(printer, self)
        if dialog.exec_() == QPrintDialog.Accepted:
            self.text_editor.print_(printer)

    def exit(self):
        if self.is_saved:
            sys.exit()
        else:
            reply = QMessageBox.question(self, 'Message',
                                         "Are you sure to quit without saving?", QMessageBox.Yes |
                                         QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.Yes:
                sys.exit()
            else:
                pass

    def undo(self):
        self.text_editor.undo()

    def redo(self):
        self.text_editor.redo()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    app.setOrganizationName("BG")
    app.setApplicationName("BG Text Editor")
    app.setApplicationVersion("0.2")
    main_window.show()
    sys.exit(app.exec_())
