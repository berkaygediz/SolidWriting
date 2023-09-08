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
        self.setup_text_editor()
        self.setup_status_bar()
        self.setup_dock_widget()
        self.update_statistics()
        self.text_editor.textChanged.connect(self.update_statistics)
        self.setup_actions()
        self.setup_toolbar()
        self.light_theme = QPalette()
        self.dark_theme = QPalette()
        self.light_theme.setColor(QPalette.Window, QColor(255, 255, 255))
        self.light_theme.setColor(QPalette.WindowText, QColor(0, 0, 0))
        self.dark_theme.setColor(QPalette.Window, QColor(0, 0, 0))
        self.dark_theme.setColor(QPalette.WindowText, QColor(255, 255, 255))
        self.setPalette(self.light_theme)
        self.restore_previous_state()
        self.restore_theme()

    def setup_text_editor(self):
        self.text_editor.setFontFamily(self.default_values['font_family'])
        self.text_editor.setFontPointSize(self.default_values['font_size'])
        self.text_editor.setTextColor(
            QColor(self.default_values['text_color']))
        self.text_editor.setTextBackgroundColor(
            QColor(self.default_values['background_color']))
        self.setCentralWidget(self.text_editor)

    def setup_status_bar(self):
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Loading...", 2000)

    def setup_dock_widget(self):
        self.dock_widget = QDockWidget("Details", self)
        self.statistics_label = QLabel()
        self.dock_widget.setWidget(self.statistics_label)
        self.dock_widget.setAllowedAreas(Qt.LeftDockWidgetArea)
        self.dock_widget.setObjectName("Details")
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_widget)

    def update_window_title(self):
        file = self.file_name if self.file_name else "New File"
        asterisk = "*" if not self.is_saved else ""
        self.setWindowTitle(f"{file}{asterisk} - RichSpan")

    def update_statistics(self):
        text = self.text_editor.toPlainText()
        character_count = len(text)
        word_count = len(text.split())
        line_count = text.count('\n') + 1
        non_space_count = len(text.replace(' ', '').replace('\n', ''))

        statistics = f"<html><head><style>"
        statistics += "table { border-collapse: collapse; width: 100%; }"
        statistics += "th, td { text-align: left; padding: 8px; }"
        statistics += "tr:nth-child(odd) { background-color: #f2f2f2; }"
        statistics += "th { background-color: #333; color: white; }"
        statistics += ".highlight { background-color: #FFFF00; font-weight: bold; }"
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
        self.is_saved = False
        self.update_window_title()

    def align_text(self, alignment):
        self.text_editor.setAlignment(alignment)

    def toggle_bold(self):
        font = self.text_editor.currentFont()
        font.setBold(not font.bold())
        self.text_editor.setCurrentFont(font)

    def toggle_italic(self):
        font = self.text_editor.currentFont()
        font.setItalic(not font.italic())
        self.text_editor.setCurrentFont(font)

    def toggle_underline(self):
        font = self.text_editor.currentFont()
        font.setUnderline(not font.underline())
        self.text_editor.setCurrentFont(font)

    def set_text_color(self):
        color = QColorDialog.getColor()
        self.text_editor.setTextColor(color)

    def set_background_color(self):
        color = QColorDialog.getColor()
        self.text_editor.setTextBackgroundColor(color)

    def toggle_theme(self):
        if self.palette() == self.light_theme:
            self.setPalette(self.dark_theme)
        else:
            self.setPalette(self.light_theme)

        self.update_toolbar_text_color()

    def update_toolbar_text_color(self):
        palette = self.palette()

        if palette == self.light_theme:
            text_color = QColor(0, 0, 0)
        else:
            text_color = QColor(255, 255, 255)

        for toolbar in self.findChildren(QToolBar):
            for action in toolbar.actions():
                if action.text() and action.text() != "Theme:":
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
            "Save and Exit Workspace", "Save and Exit workspace", self.exit, QKeySequence.Quit)
        self.undoaction = self.create_action(
            "Undo", "Undo last action", self.text_editor.undo, QKeySequence.Undo)
        self.redoaction = self.create_action(
            "Redo", "Redo last action", self.text_editor.redo, QKeySequence.Redo)

        self.alignrightevent = self.create_action(
            "Align Right", "Align text right", lambda: self.align_text(Qt.AlignRight))
        self.alignleftevent = self.create_action(
            "Align Left", "Align text left", lambda: self.align_text(Qt.AlignLeft))
        self.aligncenterevent = self.create_action(
            "Align Center", "Align text center", lambda: self.align_text(Qt.AlignCenter))
        self.alignjustifiedevent = self.create_action(
            "Align Justify", "Align text justify", lambda: self.align_text(Qt.AlignJustify))

        self.bold = self.create_action(
            "Bold", "Bold text", self.toggle_bold, QKeySequence.Bold)
        self.italic = self.create_action(
            "Italic", "Italicize text", self.toggle_italic, QKeySequence.Italic)
        self.underline = self.create_action(
            "Underline", "Underline text", self.toggle_underline, QKeySequence.Underline)

        self.color = self.create_action(
            "Text Color", "Set text color", self.set_text_color)
        self.backgroundcolor = self.create_action(
            "Background Color", "Set background color", self.set_background_color)

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
            "Toggle Theme", "Toggle between light and dark themes", self.toggle_theme)
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
        self.toolbar.addActions([self.color, self.backgroundcolor])

    def add_toolbar_label(self, toolbar, text):
        label = QLabel(f"<b>{text}</b>")
        toolbar.addWidget(label)

    def save_current_state(self):
        settings = QSettings("berkaygediz", "RichSpan")
        settings.setValue("window_geometry", self.saveGeometry())
        settings.setValue("default_directory", self.directory)
        settings.setValue("file_name", self.file_name)
        settings.setValue("text_content", self.text_editor.toPlainText())
        settings.setValue("scroll_position",
                          self.text_editor.verticalScrollBar().value())
        settings.setValue("current_theme", "dark" if self.palette()
                          == self.dark_theme else "light")

    def restore_theme(self):
        settings = QSettings("berkaygediz", "RichSpan")
        saved_theme = settings.value("current_theme")

        if saved_theme == "dark":
            self.setPalette(self.dark_theme)
        else:
            self.setPalette(self.light_theme)

    def restore_previous_state(self):
        settings = QSettings("berkaygediz", "RichSpan")
        geometry = settings.value("window_geometry")
        self.directory = settings.value(
            "default_directory", self.default_directory)
        self.file_name = settings.value("file_name")

        if geometry is not None:
            self.restoreGeometry(geometry)

        if self.file_name and os.path.exists(self.file_name):
            with open(self.file_name, 'r', encoding='utf-8') as file:
                if self.file_name.endswith((".html", ".htm")):
                    self.text_editor.setHtml(file.read())
                else:
                    self.text_editor.setPlainText(file.read())

        scroll_position = settings.value("scroll_position")
        if scroll_position is not None:
            self.text_editor.verticalScrollBar().setValue(int(scroll_position))

        self.restore_theme()

    def new_file(self):
        self.text_editor.clear()
        self.file_name = None
        self.is_saved = False
        self.update_window_title()

    def save_process(self):
        if not self.file_name:
            self.save_as()
        if self.file_name:
            with open(self.file_name, 'w', encoding='utf-8') as file:
                if self.file_name.endswith((".html", ".htm")):
                    file.write(self.text_editor.toHtml())
                else:
                    file.write(self.text_editor.toPlainText())
            self.status_bar.showMessage("Saved.", 2000)
            self.is_saved = True
            self.update_window_title()

    def save_as(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_filter = "HTML Files (*.html);;Text Files (*.txt)"
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
        file_filter = "All Files (*);;HTML Files (*.html);;Text Files (*.txt);;HTM Files (*.htm)"
        selected_file, _ = QFileDialog.getOpenFileName(
            self, "Open File", self.directory, file_filter, options=options)
        if selected_file:
            self.file_name = selected_file
            with open(self.file_name, 'r', encoding='utf-8') as file:
                if self.file_name.endswith((".html", ".htm")):
                    self.text_editor.setHtml(file.read())
                else:
                    self.text_editor.setPlainText(file.read())
            self.status_bar.showMessage("Opened.", 2000)
            self.is_saved = True
            self.update_window_title()
            self.directory = os.path.dirname(self.file_name)

    def exit(self):
        if self.is_saved:
            self.save_current_state()
            sys.exit()
        else:
            reply = QMessageBox.question(self, 'Message',
                                         "Are you sure to quit without saving?", QMessageBox.Yes |
                                         QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.Yes:
                self.save_current_state()
                sys.exit()
            else:
                pass

    def print(self):
        printer = QPrinter(QPrinter.HighResolution)
        dialog = QPrintDialog(printer, self)
        if dialog.exec_() == QPrintDialog.Accepted:
            self.text_editor.print_(printer)

    def undo(self):
        self.text_editor.undo()

    def redo(self):
        self.text_editor.redo()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    app.setOrganizationName("berkaygediz")
    app.setApplicationName("RichSpan")
    app.setApplicationVersion("1.0.0")
    main_window.show()
    sys.exit(app.exec_())
