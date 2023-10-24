import sys
import os
import datetime
import base64
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtPrintSupport import *

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        starttime = datetime.datetime.now()
        self.richspan_thread = RichSpanThreading()
        self.richspan_thread.update_signal.connect(self.update_statistics)
        self.default_values = {
            'font_family': 'Arial',
            'font_size': 12,
            'bold': False,
            'italic': False,
            'underline': False,
            'alignment': Qt.AlignLeft,
            'text_color': '#000000',
            'background_color': '#FFFFFF',
            'theme': 'light',
            'window_geometry': None,
            'default_directory': None,
            'file_name': None,
            'text_content': None,
            'is_saved': None,
            'scroll_position': None,
            'current_theme': None,
        }
        self.selected_file = None
        self.file_name = None
        self.is_saved = None
        self.default_directory = QDir().homePath()
        self.directory = self.default_directory
        self.richspan_area = QTextEdit()
        self.setup_richspan_area()
        self.status_bar = self.statusBar()
        self.setup_dock_widget()
        self.update_statistics()
        self.richspan_area.textChanged.connect(self.richspan_thread.start)
        self.setup_actions()
        self.setup_toolbar()
        self.light_theme = QPalette()
        self.dark_theme = QPalette()
        self.light_theme.setColor(QPalette.Window, QColor(255, 255, 255))
        self.light_theme.setColor(QPalette.WindowText, QColor(37, 38, 39))
        self.dark_theme.setColor(QPalette.Window, QColor(37, 38, 39))
        self.dark_theme.setColor(QPalette.WindowText, QColor(255, 255, 255))
        self.light_theme.setColor(QPalette.Base, QColor(255, 255, 255))
        self.light_theme.setColor(QPalette.Text, QColor(42, 43, 44))
        self.dark_theme.setColor(QPalette.Base, QColor(42, 43, 44))
        self.dark_theme.setColor(QPalette.Text, QColor(255, 255, 255))
        self.light_theme.setColor(QPalette.Highlight, QColor(218, 221, 177))
        self.light_theme.setColor(QPalette.HighlightedText, QColor(42, 43, 44))
        self.dark_theme.setColor(QPalette.Highlight, QColor(218, 221, 177))
        self.dark_theme.setColor(QPalette.HighlightedText, QColor(42, 43, 44))
        self.setPalette(self.light_theme)
        self.restore_previous_state()
        self.restore_theme()
        endtime = datetime.datetime.now()
        self.statusBar().showMessage(str((endtime - starttime).total_seconds()) + " ms", 2000)

    def closeEvent(self, event):
        if self.is_saved == False:
            reply = QMessageBox.question(self, 'RichSpan',
                                         "Are you sure to save workspace?", QMessageBox.Yes |
                                         QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.Yes:
                self.save_current_state()
                event.accept()
            else:
                event.ignore()
        else:
            self.save_current_state()
            event.accept()

    def setup_richspan_area(self):
        self.richspan_area.setFontFamily(self.default_values['font_family'])
        self.richspan_area.setFontPointSize(self.default_values['font_size'])
        self.richspan_area.setFontWeight(
            75 if self.default_values['bold'] else 50)
        self.richspan_area.setFontItalic(self.default_values['italic'])
        self.richspan_area.setFontUnderline(self.default_values['underline'])
        self.richspan_area.setAlignment(self.default_values['alignment'])
        self.richspan_area.setTextColor(
            QColor(self.default_values['text_color']))
        self.richspan_area.setTextBackgroundColor(
            QColor(self.default_values['background_color']))
        self.richspan_area.setTabStopWidth(33)
        self.setCentralWidget(self.richspan_area)

    def setup_dock_widget(self):
        self.dock_widget = QDockWidget("Details",self)
        self.statistics_label = QLabel()
        self.dock_widget.setWidget(self.statistics_label)
        self.dock_widget.setObjectName("Details")
        self.dock_widget.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_widget)

    def update_window_title(self):
        file = self.file_name if self.file_name else "Untitled"
        if self.is_saved == True: asterisk = ""
        else: asterisk = "*"
        self.setWindowTitle(f"{file}{asterisk} - RichSpan")

    def update_statistics(self):
        text = self.richspan_area.toPlainText()
        character_count = len(text)
        word_count = len(text.split())
        line_count = text.count('\n') + 1
        non_space_count = len(text.replace(' ', '').replace('\n', ''))

        statistics = f"<html><head><style>"
        statistics += "table {border-collapse: collapse; width: 100%;}"
        statistics += "th, td {text-align: left; padding: 8px;}"
        statistics += "tr:nth-child(even) {background-color: #f2f2f2;}"
        statistics += ".highlight {background-color: #E2E3E1; color: #000000}"
        statistics += "tr:hover {background-color: #ddd;}"
        statistics += "th {background-color: #4CAF50; color: white;}"
        statistics += "</style></head><body>"
        statistics += "<table>"
        statistics += "<tr><th>Statistic</th></tr>"
        statistics += f"<tr><td>Total Characters:</td><td>{character_count}</td></tr>"
        statistics += f"<tr><td>Total Words:</td><td>{word_count}</td></tr>"
        statistics += f"<tr><td>Total Lines:</td><td>{line_count}</td></tr>"
        statistics += f"<tr><td>Characters (Excluding Spaces):</td><td>{non_space_count}</td></tr>"

        statistics += "<tr><th>Analysis</th></tr>"
        if word_count > 0:
            avg_word_length = sum(len(word)
                                  for word in text.split()) / word_count
            statistics += f"<tr><td>Average Word Length:</td><td>{avg_word_length:.2f} characters</td></tr>"
        if line_count > 0:
            avg_line_length = character_count / line_count
            statistics += f"<tr><td>Average Line Length:</td><td>{avg_line_length:.2f} characters</td></tr>"

        if character_count > 0:
            uppercase_count = sum(1 for char in text if char.isupper())
            lowercase_count = sum(1 for char in text if char.islower())
            statistics += f"<tr><td>Uppercase Characters:</td><td>{uppercase_count}</td></tr>"
            statistics += f"<tr><td>Lowercase Characters:</td><td>{lowercase_count}</td></tr>"

        statistics += "</table></body></html>"

        if character_count > 1000:
            statistics = statistics.replace(
                f"Total Characters:</td><td>{character_count}",
                f"Total Characters:</td><td class='highlight'>{character_count}")

        self.statistics_label.setText(statistics)
        self.new_text = self.richspan_area.toPlainText()
        if self.new_text != self.default_values['text_content']:
            self.is_saved = False
        else:
            self.is_saved = True
        self.update_window_title()

    def new_file(self):
        if self.is_saved == True:
            self.richspan_area.clear()
            self.richspan_area.setFontFamily(self.default_values['font_family'])
            self.richspan_area.setFontPointSize(self.default_values['font_size'])
            self.richspan_area.setFontWeight(
                    75 if self.default_values['bold'] else 50)
            self.richspan_area.setFontItalic(self.default_values['italic'])
            self.richspan_area.setFontUnderline(self.default_values['underline'])
            self.richspan_area.setAlignment(self.default_values['alignment'])
            self.richspan_area.setTextColor(
                    QColor(self.default_values['text_color']))
            self.richspan_area.setTextBackgroundColor(
                    QColor(self.default_values['background_color']))
            self.richspan_area.setTabStopWidth(33)
            self.directory = self.default_directory
            self.file_name = None
            self.is_saved = False
            self.update_window_title()
        else:
            reply = QMessageBox.question(self, 'Message',
                                         "Are you sure to create a new file without saving?", QMessageBox.Yes |
                                         QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.Yes:
                self.richspan_area.clear()
                self.richspan_area.setFontFamily(self.default_values['font_family'])
                self.richspan_area.setFontPointSize(self.default_values['font_size'])
                self.richspan_area.setFontWeight(
                    75 if self.default_values['bold'] else 50)
                self.richspan_area.setFontItalic(self.default_values['italic'])
                self.richspan_area.setFontUnderline(self.default_values['underline'])
                self.richspan_area.setAlignment(self.default_values['alignment'])
                self.richspan_area.setTextColor(
                    QColor(self.default_values['text_color']))
                self.richspan_area.setTextBackgroundColor(
                    QColor(self.default_values['background_color']))
                self.richspan_area.setTabStopWidth(33)
                self.directory = self.default_directory
                self.file_name = None
                self.is_saved = False
                self.update_window_title()
            else:
                pass

    def save_process(self):
        if not self.file_name:
            self.save_as()
        else:
            with open(self.file_name, 'w', encoding='utf-8') as file:
                if self.file_name.endswith((".html", ".htm")):
                    file.write(self.richspan_area.toHtml())
                else:
                    file.write(self.richspan_area.toPlainText())
            self.status_bar.showMessage("Saved.", 2000)
            self.is_saved = True
            self.update_window_title()

    def save_as(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_filter = "HTML Files (*.html);;Text Files (*.txt);;HTM Files (*.htm);;INI Files (*.ini);;LOG Files (*.log);;JSON Files (*.json);;XML Files (*.xml);;JS Files (*.js);;CSS Files (*.css);;SQL Files (*.sql);;Markdown Files (*.md);;"
        selected_file, _ = QFileDialog.getSaveFileName(
            self, "Save As", self.file_name, file_filter, options=options)
        if selected_file:
            self.file_name = selected_file
            self.save_process()
            self.directory = os.path.dirname(self.file_name)
            return True
        return False

    def save(self):
        if self.is_saved:
            self.save_process()
        elif self.file_name:
            self.save_process()
        else:
            self.save_as()

    def open(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_filter = "HTML Files (*.html);;Text Files (*.txt);;HTM Files (*.htm);;INI Files (*.ini);;LOG Files (*.log);;JSON Files (*.json);;XML Files (*.xml);;JS Files (*.js);;CSS Files (*.css);;SQL Files (*.sql);;Markdown Files (*.md);;"
        selected_file, _ = QFileDialog.getOpenFileName(
            self, "Open", self.directory, file_filter, options=options)
        if self.is_saved == True:
            if selected_file:
                self.file_name = selected_file
                with open(self.file_name, 'r', encoding='utf-8') as file:
                    if self.file_name.endswith((".html", ".htm")):
                        self.richspan_area.setHtml(file.read())
                    else:
                        self.richspan_area.setPlainText(file.read())
                self.directory = os.path.dirname(self.file_name)
                self.is_saved = True
                self.update_window_title()
        else:
            pass

    def print(self):
        printer = QPrinter(QPrinter.HighResolution)
        dialog = QPrintDialog(printer, self)
        if dialog.exec_() == QPrintDialog.Accepted:
            self.richspan_area.print_(printer)

    def align_text(self, alignment):
        self.richspan_area.setAlignment(alignment)

    def toggle_bold(self):
        font = self.richspan_area.currentFont()
        font.setBold(not font.bold())
        self.richspan_area.setCurrentFont(font)

    def toggle_italic(self):
        font = self.richspan_area.currentFont()
        font.setItalic(not font.italic())
        self.richspan_area.setCurrentFont(font)

    def toggle_underline(self):
        font = self.richspan_area.currentFont()
        font.setUnderline(not font.underline())
        self.richspan_area.setCurrentFont(font)

    def set_text_color(self):
        color = QColorDialog.getColor()
        self.richspan_area.setTextColor(color)

    def set_background_color(self):
        color = QColorDialog.getColor()
        self.richspan_area.setTextBackgroundColor(color)

    def toggle_theme(self):
        if self.palette() == self.light_theme:
            self.setPalette(self.dark_theme)
        else:
            self.setPalette(self.light_theme)

        self.update_toolbar_text_color()

    def update_toolbar_text_color(self):
        palette = self.palette()
        if palette == self.light_theme:
            text_color = QColor(37, 38, 39)
        else:
            text_color = QColor(255, 255, 255)

        for toolbar in self.findChildren(QToolBar):
            for action in toolbar.actions():
                if action.text():
                    action_color = QPalette()
                    action_color.setColor(QPalette.ButtonText, text_color)
                    action_color.setColor(QPalette.WindowText, text_color)
                    toolbar.setPalette(action_color)

    def setup_actions(self):
        self.newaction = self.create_action(
            "New", "Create a new document", self.new_file, QKeySequence.New)
        self.openaction = self.create_action(
            "Open", "Open file", self.open, QKeySequence.Open)
        self.saveaction = self.create_action(
            "Save", "Save file", self.save, QKeySequence.Save)
        self.saveasaction = self.create_action(
            "Save As", "Save file as", self.save_as, QKeySequence.SaveAs)
        self.printaction = self.create_action(
            "Print", "Print file", self.print, QKeySequence.Print)
        self.exitaction = self.create_action(
            "Save Workspace", "Save workspace", self.save_current_state, QKeySequence("Ctrl+Shift+W+S"))
        self.undoaction = self.create_action(
            "Undo", "Undo last action", self.richspan_area.undo, QKeySequence.Undo)
        self.redoaction = self.create_action(
            "Redo", "Redo last action", self.richspan_area.redo, QKeySequence.Redo)

        self.alignrightevent = self.create_action(
            "Right", "Align text right", lambda: self.align_text(Qt.AlignRight))
        self.alignleftevent = self.create_action(
            "Left", "Align text left", lambda: self.align_text(Qt.AlignLeft))
        self.aligncenterevent = self.create_action(
            "Center", "Align text center", lambda: self.align_text(Qt.AlignCenter))
        self.alignjustifiedevent = self.create_action(
            "Justify", "Align text justify", lambda: self.align_text(Qt.AlignJustify))

        self.bold = self.create_action(
            "Bold", "Bold text", self.toggle_bold, QKeySequence.Bold)
        self.italic = self.create_action(
            "Italic", "Italicize text", self.toggle_italic, QKeySequence.Italic,)
        self.underline = self.create_action(
            "Underline", "Underline text", self.toggle_underline, QKeySequence.Underline)

        self.color = self.create_action(
            "Color", "Set text color", self.set_text_color, QKeySequence("Ctrl+Shift+C"))
        self.backgroundcolor = self.create_action(
            "Background", "Set background color", self.set_background_color, QKeySequence("Ctrl+Shift+B"))
        self.fontfamily = self.create_action(
            "Font", "Set font family", self.set_font_family, QKeySequence("Ctrl+Shift+F"))
        self.fontsizeplus = self.create_action(
            "A+", "Increase font size", self.fontsizeplus, QKeySequence("Ctrl++"))
        self.fontsizeminus = self.create_action(
            "A-", "Decrease font size", self.fontsizeminus, QKeySequence("Ctrl+-"))
        self.addimage = self.create_action(
            "Image", "Add photo", self.add_image, QKeySequence("Ctrl+Shift+P"))

    def fontsizeplus(self):
        font = self.richspan_area.currentFont()
        font.setPointSize(font.pointSize() + 1)
        self.richspan_area.setCurrentFont(font)

    def fontsizeminus(self):
        font = self.richspan_area.currentFont()
        font.setPointSize(font.pointSize() - 1)
        self.richspan_area.setCurrentFont(font)
    
    def set_font_family(self):
        font, ok = QFontDialog.getFont(self.richspan_area.currentFont(), self)
        if ok:
            self.richspan_area.setCurrentFont(font)

    def add_image(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_filter = "Portable Network Graphics (*.png);;JPEG (*.jpg *.jpeg);;Bitmap (*.bmp);;GIF (*.gif);;All Files (*)"
        selected_file, _ = QFileDialog.getOpenFileName(
            self, "Open", self.directory, file_filter, options=options)
        if selected_file:
            with open(selected_file, 'rb') as file:
                data = file.read()
                data = base64.b64encode(data)
                data = data.decode('utf-8')
                self.richspan_area.insertHtml(f'<img src="data:image/png;base64,{data}"/>')

    def create_action(self, text, status_tip, function, shortcut=None):
        action = QAction(text, self)
        action.setStatusTip(status_tip)
        action.triggered.connect(function)
        if shortcut:
            action.setShortcut(shortcut)
        return action

    def setup_toolbar(self):
        self.toolbar = self.addToolBar('File')
        self.add_toolbar_label(self.toolbar, "File:")
        self.toolbar.addActions([self.newaction, self.openaction, self.saveaction, self.saveasaction,
                                self.printaction, self.exitaction, self.undoaction, self.redoaction])

        self.toolbar = self.addToolBar('Theme')
        self.add_toolbar_label(self.toolbar, "Theme:")
        self.theme_action = self.create_action(
            "Dark/Light", "Change theme dark or light", self.toggle_theme, QKeySequence("Ctrl+Shift+T"), )
        self.toolbar.addAction(self.theme_action)

        self.addToolBarBreak()

        self.toolbar = self.addToolBar('Format')
        self.add_toolbar_label(self.toolbar, "Alignment:")
        self.toolbar.addActions(
            [self.alignrightevent, self.alignleftevent, self.aligncenterevent, self.alignjustifiedevent])
        self.toolbar.addSeparator()
        self.add_toolbar_label(self.toolbar, "Font:")
        self.toolbar.addActions([self.bold, self.italic, self.underline])
        self.addToolBarBreak()

        self.toolbar = self.addToolBar('Color')
        self.add_toolbar_label(self.toolbar, "Color:")
        self.toolbar.addActions([self.color, self.backgroundcolor, self.fontfamily, self.fontsizeplus, self.fontsizeminus])

        self.toolbar = self.addToolBar('Multimedia')
        self.add_toolbar_label(self.toolbar, "Multimedia:")
        self.toolbar.addActions([self.addimage])

    def add_toolbar_label(self, toolbar, text):
        label = QLabel(f"<b>{text}</b>")
        toolbar.addWidget(label)

    def save_current_state(self):
        settings = QSettings("berkaygediz", "RichSpan")
        settings.setValue("window_geometry", self.saveGeometry())
        settings.setValue("default_directory", self.directory)
        settings.setValue("file_name", self.file_name)
        settings.setValue("text_content", self.richspan_area.toPlainText())
        settings.setValue("is_saved", self.is_saved)
        settings.setValue("scroll_position",
                          self.richspan_area.verticalScrollBar().value())
        settings.setValue("current_theme", "dark" if self.palette()
                          == self.dark_theme else "light")
        settings.sync()

    def restore_theme(self):
        settings = QSettings("berkaygediz", "RichSpan")
        theme = settings.value("current_theme")
        if theme == "dark":
            self.setPalette(self.dark_theme)
        else:
            self.setPalette(self.light_theme)
        self.update_toolbar_text_color()

    def restore_previous_state(self):
        settings = QSettings("berkaygediz", "RichSpan")
        geometry = settings.value("window_geometry")
        self.directory = settings.value(
            "default_directory", self.default_directory)
        self.file_name = settings.value("file_name")
        self.richspan_area.setPlainText(settings.value("text_content"))
        self.is_saved = settings.value("is_saved")

        if geometry is not None:
            self.restoreGeometry(geometry)

        if self.file_name and os.path.exists(self.file_name):
            with open(self.file_name, 'r', encoding='utf-8') as file:
                if self.file_name.endswith((".html", ".htm")):
                    self.richspan_area.setHtml(file.read())
                else:
                    self.richspan_area.setPlainText(file.read())

        scroll_position = settings.value("scroll_position")
        if scroll_position is not None:
            self.richspan_area.verticalScrollBar().setValue(int(scroll_position))
        else:
            self.richspan_area.verticalScrollBar().setValue(0)

        if self.file_name:
            self.is_saved = True
        else:
            self.is_saved = False

        self.restore_theme()
        self.update_window_title()

class RichSpanThreading(QThread):
    update_signal = pyqtSignal()
    def run(self):
        self.update_signal.emit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    app.setOrganizationName("berkaygediz")
    app.setApplicationName("RichSpan")
    app.setApplicationVersion("1.1.2")
    main_window.show()
    sys.exit(app.exec_())
