import sys
import os
import datetime
import base64
import time
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtPrintSupport import *

class RS_Threading(QThread):
    update_signal = pyqtSignal()

    def __init__(self, parent=None):
        super(RS_Threading, self).__init__(parent)
        self.running = False

    def run(self):
        if not self.running:
            self.running = True
            time.sleep(0.15)
            self.update_signal.emit()
            self.running = False

class RS_Workspace(QMainWindow):
    def __init__(self, parent=None):
        super(RS_Workspace, self).__init__(parent)
        starttime = datetime.datetime.now()
        self.richspan_thread = RS_Threading()
        self.richspan_thread.update_signal.connect(self.update_statistics)
        self.default_values = {
            'font_family': 'Arial',
            'font_size': 14,
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
        self.rs_area = QTextEdit()
        self.setup_rs_area()
        self.status_bar = self.statusBar()
        self.setup_dock()
        self.dock_widget.hide()
        self.update_statistics()
        self.rs_area.textChanged.connect(self.richspan_thread.start)
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
        self.rs_restorestate()
        self.rs_restoretheme()
        self.update_title()
        self.setUnifiedTitleAndToolBarOnMac(True)
        self.setWindowIcon(QIcon("icon.png"))
        self.showMaximized()
        self.rs_area.setFocus()
        self.rs_area.setAcceptRichText(True)
        endtime = datetime.datetime.now()
        self.status_bar.showMessage(str((endtime - starttime).total_seconds()) + " ms", 2500)

        self.rs_area.selectAll()

    def closeEvent(self, event):
        if self.is_saved == False:
            reply = QMessageBox.question(self, 'RichSpan',
                                         "Are you sure to save RichSpan?", QMessageBox.Yes |
                                         QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.Yes:
                self.rs_savestate()
                event.accept()
            else:
                event.ignore()
        else:
            self.rs_savestate()
            event.accept()

    def rs_savestate(self):
        settings = QSettings("berkaygediz", "RichSpan")
        settings.setValue("window_geometry", self.saveGeometry())
        settings.setValue("default_directory", self.directory)
        settings.setValue("file_name", self.file_name)
        settings.setValue("text_content", self.rs_area.toPlainText())
        settings.setValue("is_saved", self.is_saved)
        settings.setValue("scroll_position",
                          self.rs_area.verticalScrollBar().value())
        settings.setValue("current_theme", "dark" if self.palette()
                          == self.dark_theme else "light")
        settings.sync()

    def rs_restorestate(self):
        settings = QSettings("berkaygediz", "RichSpan")
        geometry = settings.value("window_geometry")
        self.directory = settings.value(
            "default_directory", self.default_directory)
        self.file_name = settings.value("file_name")
        self.rs_area.setPlainText(settings.value("text_content"))
        self.is_saved = settings.value("is_saved")

        if geometry is not None:
            self.restoreGeometry(geometry)

        if self.file_name and os.path.exists(self.file_name):
            with open(self.file_name, 'r', encoding='utf-8') as file:
                if self.file_name.endswith((".rsdoc")):
                    self.rs_area.setHtml(file.read())
                elif self.file_name.endswith((".html", ".htm")):
                    self.rs_area.setHtml(file.read())
                elif self.file_name.endswith((".md")):
                    self.rs_area.setMarkdown(file.read())
                else:
                    self.rs_area.setPlainText(file.read())

        scroll_position = settings.value("scroll_position")
        if scroll_position is not None:
            self.rs_area.verticalScrollBar().setValue(int(scroll_position))
        else:
            self.rs_area.verticalScrollBar().setValue(0)

        if self.file_name:
            self.is_saved = True
        else:
            self.is_saved = False

        self.rs_restoretheme()
        self.update_title()

    def rs_themechange(self):
        if self.palette() == self.light_theme:
            self.setPalette(self.dark_theme)
        else:
            self.setPalette(self.light_theme)

        self.rs_toolbartheme()

    def rs_toolbartheme(self):
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

    def rs_restoretheme(self):
        settings = QSettings("berkaygediz", "RichSpan")
        theme = settings.value("current_theme")
        if theme == "dark":
            self.setPalette(self.dark_theme)
        else:
            self.setPalette(self.light_theme)
        self.rs_toolbartheme()

    def new(self):
        if self.is_saved == True:
            self.rs_area.clear()
            self.rs_area.setFontFamily(self.default_values['font_family'])
            self.rs_area.setFontPointSize(self.default_values['font_size'])
            self.rs_area.setFontWeight(
                    75 if self.default_values['bold'] else 50)
            self.rs_area.setFontItalic(self.default_values['italic'])
            self.rs_area.setFontUnderline(self.default_values['underline'])
            self.rs_area.setAlignment(self.default_values['alignment'])
            self.rs_area.setTextColor(
                    QColor(self.default_values['text_color']))
            self.rs_area.setTextBackgroundColor(
                    QColor(self.default_values['background_color']))
            self.rs_area.setTabStopWidth(33)
            self.directory = self.default_directory
            self.file_name = None
            self.is_saved = False
            self.update_title()
        else:
            reply = QMessageBox.question(self, 'Message - RichSpan',
                                         "Are you sure to create a new file without saving?", QMessageBox.Yes |
                                         QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.Yes:
                self.rs_area.clear()
                self.rs_area.setFontFamily(self.default_values['font_family'])
                self.rs_area.setFontPointSize(self.default_values['font_size'])
                self.rs_area.setFontWeight(
                    75 if self.default_values['bold'] else 50)
                self.rs_area.setFontItalic(self.default_values['italic'])
                self.rs_area.setFontUnderline(self.default_values['underline'])
                self.rs_area.setAlignment(self.default_values['alignment'])
                self.rs_area.setTextColor(
                    QColor(self.default_values['text_color']))
                self.rs_area.setTextBackgroundColor(
                    QColor(self.default_values['background_color']))
                self.rs_area.setTabStopWidth(33)
                self.directory = self.default_directory
                self.file_name = None
                self.is_saved = False
                self.update_title()
            else:
                pass
    
    def open(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_filter = "RichSpan Document (*.rsdoc);;HTML (*.html);;Text (*.txt);;Key-Value (*.ini);;LOG (*.log);;JavaScript Object Notation (*.json);;Extensible Markup Language (*.xml);;Javascript (*.js);;Cascading Style Sheets (*.css);;Structured Query Language (*.sql);;Markdown (*.md)"
        selected_file, _ = QFileDialog.getOpenFileName(self, "Open - RichSpan", self.directory, file_filter, options=options)
        if selected_file:
            self.file_name = selected_file
            with open(self.file_name, 'r', encoding='utf-8') as file:
                file_content = file.read()
                if self.file_name.endswith((".rsdoc")):
                    self.rs_area.setHtml(file_content)
                elif self.file_name.endswith((".html", ".htm")):
                    self.rs_area.setHtml(file_content)
                elif self.file_name.endswith((".md")):
                    self.rs_area.setMarkdown(file_content)
                else:
                    self.rs_area.setPlainText(file_content)
            self.directory = os.path.dirname(self.file_name)
            self.is_saved = True
            self.update_title()
        else:
            pass

    def save(self):
        if self.is_saved == False:
            self.savefile()
        elif self.file_name == None:
            self.saveas()
        else:
            self.savefile()

    def saveas(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_filter = "RichSpan Document (*.rsdoc);;HTML (*.html);;Text (*.txt);;Key-Value (*.ini);;LOG (*.log);;JavaScript Object Notation (*.json);;Extensible Markup Language (*.xml);;Javascript (*.js);;Cascading Style Sheets (*.css);;Structured Query Language (*.sql);;Markdown (*.md)"
        selected_file, _ = QFileDialog.getSaveFileName(
            self, "Save As - RichSpan", self.file_name, file_filter, options=options)
        if selected_file:
            self.file_name = selected_file
            self.savefile()
            self.directory = os.path.dirname(self.file_name)
            return True
        return False

    def savefile(self):
        if not self.file_name:
            self.saveas()
        else:
            with open(self.file_name, 'w', encoding='utf-8') as file:
                if self.file_name.endswith((".rsdoc")):
                    file.write(self.rs_area.toHtml())
                elif self.file_name.endswith((".html", ".htm")):
                    file.write(self.rs_area.toHtml())
                elif self.file_name.endswith((".md")):
                    file.write(self.rs_area.toMarkdown())
                else:
                    file.write(self.rs_area.toPlainText())
            self.status_bar.showMessage("Saved.", 2000)
            self.is_saved = True
            self.update_title()

    def print(self):
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOrientation(QPrinter.Portrait)
        printer.setPageMargins(10, 10, 10, 10, QPrinter.Millimeter)
        printer.setFullPage(True)
        printer.setDocName(self.file_name)
        printer.pageLayout()
        dialog = QPrintDialog(printer, self)
        if dialog.exec_() == QPrintDialog.Accepted:
            self.rs_area.print_(printer)

    def setup_rs_area(self):
        self.rs_area.setFontFamily(self.default_values['font_family'])
        self.rs_area.setFontPointSize(self.default_values['font_size'])
        self.rs_area.setFontWeight(
            75 if self.default_values['bold'] else 50)
        self.rs_area.setFontItalic(self.default_values['italic'])
        self.rs_area.setFontUnderline(self.default_values['underline'])
        self.rs_area.setAlignment(self.default_values['alignment'])
        self.rs_area.setTextColor(
            QColor(self.default_values['text_color']))
        self.rs_area.setTextBackgroundColor(
            QColor(self.default_values['background_color']))
        self.rs_area.setTabStopWidth(33)
        self.rs_area.document().setDocumentMargin(self.width() * 0.25)

        self.setCentralWidget(self.rs_area)

    def setup_dock(self):
        self.dock_widget = QDockWidget("Help",self)
        self.statistics_label = QLabel()
        self.help_label = QLabel()
        self.help_label.setWordWrap(True)
        self.help_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.help_label.setTextFormat(Qt.RichText)
        self.help_label.setText("<html><head><style>"   
                                "table {border-collapse: collapse; width: 100%;}"
                                "th, td {text-align: left; padding: 8px;}"
                                "tr:nth-child(even) {background-color: #f2f2f2;}"
                                "tr:hover {background-color: #ddd;}"
                                "th {background-color: #4CAF50; color: white;}"
                                "</style></head><body>"
                                "<table><tr>"
                                "<th>Shortcut</th>"
                                "<th>Description</th>"
                                "</tr><tr><td>Ctrl+N</td><td>New</td></tr>"
                                "<tr><td>Ctrl+O</td><td>Open</td></tr>"
                                "<tr><td>Ctrl+S</td><td>Save</td></tr>"
                                "<tr><td>Ctrl+Shift+S</td><td>Save As</td></tr>"
                                "<tr><td>Ctrl+P</td><td>Print</td></tr>"
                                "<tr><td>Ctrl+Z</td><td>Undo</td></tr>"
                                "<tr><td>Ctrl+Y</td><td>Redo</td></tr>"
                                "<tr><td>Ctrl+Shift+T</td><td>Change Theme</td></tr>"
                                "<tr><td>Ctrl+Shift+D</td><td>Hide or Show Help</td></tr>"
                                "<tr><td>Ctrl+Shift+C</td><td>Set Text Color</td></tr>"
                                "<tr><td>Ctrl+Shift+B</td><td>Set Background Color</td></tr>"
                                "<tr><td>Ctrl+Shift+F</td><td>Set Font Family</td></tr>"
                                "<tr><td>Ctrl++</td><td>Increase Font Size</td></tr>"
                                "<tr><td>Ctrl+-</td><td>Decrease Font Size</td></tr>"
                                "<tr><td>Ctrl+Shift+P</td><td>Add Photo</td></tr>"
                                "<tr><td>Ctrl+Shift+W+S</td><td>Save Workspace</td></tr>"
                                "<tr><td>Ctrl+F</td><td>Find</td></tr>"
                                "<tr><td>Ctrl+H</td><td>Replace</td></tr>"
                                "</table></body></html>")
        
        self.dock_widget.setWidget(self.help_label)
        self.dock_widget.setObjectName("Help")
        self.dock_widget.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_widget)

    def toolbarlabel(self, toolbar, text):
        label = QLabel(f"<b>{text}</b>")
        toolbar.addWidget(label)

    def setup_toolbar(self):
        self.toolbar = self.addToolBar('File')
        self.toolbarlabel(self.toolbar, "File: ")
        self.toolbar.addActions([self.newaction, self.openaction, self.saveaction, self.saveasaction,
                                self.printaction, self.saveworkspaceaction, self.undoaction, self.redoaction, self.findaction, self.replaceaction])

        self.toolbar = self.addToolBar('Interface')
        self.toolbarlabel(self.toolbar, "UI: ")
        self.theme_action = self.create_action(
            "Dark/Light", "Change theme dark or light", self.rs_themechange, QKeySequence("Ctrl+Shift+T"), )
        self.toolbar.addAction(self.theme_action)
        self.hide_dock_widget = self.create_action(
            "Help", "Hide or show Help", self.toggle_dock, QKeySequence("Ctrl+Shift+H"), )
        self.toolbar.addAction(self.hide_dock_widget)
        self.toggle_view_action = self.create_action(
            "View Mode", "Toggle view mode", self.toggle_view, )
        self.toolbar.addAction(self.toggle_view_action)

        self.addToolBarBreak()

        self.toolbar = self.addToolBar('Format')
        self.toolbarlabel(self.toolbar, "Alignment: ")
        self.toolbar.addActions(
            [self.alignrightevent, self.alignleftevent, self.aligncenterevent, self.alignjustifiedevent])
        self.toolbar.addSeparator()
        self.toolbarlabel(self.toolbar, "Font: ")
        self.toolbar.addActions([self.bold, self.italic, self.underline])
        self.addToolBarBreak()

        self.toolbar = self.addToolBar('Color')
        self.toolbarlabel(self.toolbar, "Color: ")
        self.toolbar.addActions([self.color, self.backgroundcolor, self.fontfamily, self.inc_font, self.dec_font])

        self.toolbar = self.addToolBar('Multimedia')
        self.toolbarlabel(self.toolbar, "Multimedia: ")
        self.toolbar.addActions([self.addimage])

    def create_action(self, text, status_tip, function, shortcut=None):
        action = QAction(text, self)
        action.setStatusTip(status_tip)
        action.triggered.connect(function)
        if shortcut:
            action.setShortcut(shortcut)
        return action

    def setup_actions(self):
        self.newaction = self.create_action(
            "New", "Create a new document", self.new, QKeySequence.New)
        self.openaction = self.create_action(
            "Open", "Open file", self.open, QKeySequence.Open)
        self.saveaction = self.create_action(
            "Save", "Save file", self.save, QKeySequence.Save)
        self.saveasaction = self.create_action(
            "Save As", "Save file as", self.saveas, QKeySequence.SaveAs)
        self.printaction = self.create_action(
            "Print", "Print file", self.print, QKeySequence.Print)
        self.saveworkspaceaction = self.create_action(
            "Save Workspace", "Save Workspace", self.rs_savestate, QKeySequence("Ctrl+Shift+W+S"))
        self.findaction = self.create_action(
            "Find", "Find text", self.find, QKeySequence.Find)
        self.replaceaction = self.create_action(
            "Replace", "Replace text", self.replace, QKeySequence.Replace)
        self.undoaction = self.create_action(
            "Undo", "Undo last action", self.rs_area.undo, QKeySequence.Undo)
        self.redoaction = self.create_action(
            "Redo", "Redo last action", self.rs_area.redo, QKeySequence.Redo)


        self.alignrightevent = self.create_action(
            "Right", "Align text right", lambda: self.align(Qt.AlignRight))
        self.alignleftevent = self.create_action(
            "Left", "Align text left", lambda: self.align(Qt.AlignLeft))
        self.aligncenterevent = self.create_action(
            "Center", "Align text center", lambda: self.align(Qt.AlignCenter))
        self.alignjustifiedevent = self.create_action(
            "Justify", "Align text justify", lambda: self.align(Qt.AlignJustify))

        self.bold = self.create_action(
            "Bold", "Bold text", self.toggle_bold, QKeySequence.Bold)
        self.italic = self.create_action(
            "Italic", "Italicize text", self.toggle_italic, QKeySequence.Italic,)
        self.underline = self.create_action(
            "Underline", "Underline text", self.toggle_underline, QKeySequence.Underline)

        self.color = self.create_action(
            "Color", "Set text color", self.toggle_color, QKeySequence("Ctrl+Shift+C"))
        self.backgroundcolor = self.create_action(
            "Background", "Set background color", self.toggle_bgcolor, QKeySequence("Ctrl+Shift+B"))
        self.fontfamily = self.create_action(
            "Font", "Set font family", self.toggle_font, QKeySequence("Ctrl+Shift+F"))
        self.inc_font = self.create_action(
            "A+", "Increase font size", self.inc_font, QKeySequence("Ctrl++"))
        self.dec_font = self.create_action(
            "A-", "Decrease font size", self.dec_font, QKeySequence("Ctrl+-"))
        self.addimage = self.create_action(
            "Image", "Add photo", self.add_image, QKeySequence("Ctrl+Shift+P"))

    def update_title(self):
        file = self.file_name if self.file_name else "Untitled"
        if self.is_saved == True: asterisk = ""
        else: asterisk = "*"
        self.setWindowTitle(f"{file}{asterisk} - RichSpan")

    def update_statistics(self):
        text = self.rs_area.toPlainText()
        character_count = len(text)
        word_count = len(text.split())
        line_count = text.count('\n') + 1

        chars_per_page = 5000
        page_count = character_count // chars_per_page + 1

        statistics = f"<html><head><style>"
        statistics += "table {border-collapse: collapse; width: 100%;}"
        statistics += "th, td {text-align: left; padding: 8px;}"
        statistics += "tr:nth-child(even) {background-color: #f2f2f2;}"
        statistics += ".highlight {background-color: #E2E3E1; color: #000000}"
        statistics += "tr:hover {background-color: #ddd;}"
        statistics += "th {background-color: #4CAF50; color: white;}"
        statistics += "#rs-text { background-color: #E2E3E1; color: #000000; }"
        statistics += "</style></head><body>"
        statistics += "<table><tr>"
        if word_count > 0 and line_count > 0 and character_count > 0 and page_count > 0 and text != "":
            statistics += "<th>Analysis</th>"
            avg_word_length = sum(len(word) for word in text.split()) / word_count
            statistics += f"<td>Average Word: {avg_word_length:.2f}</td>"
            avg_line_length = character_count / line_count - 1
            statistics += f"<td>Average Line: {avg_line_length:.2f}</td>"
            uppercase_count = sum(1 for char in text if char.isupper())
            lowercase_count = sum(1 for char in text if char.islower())
            statistics += f"<td>Uppercase Characters: {uppercase_count}</td>"
            statistics += f"<td>Lowercase Characters: {lowercase_count}</td>"
        statistics += "<th>Statistics</th>"
        statistics += f"<td>Characters: {character_count}</td>"
        statistics += f"<td>Word: {word_count}</td>"
        statistics += f"<td>Line: {line_count}</td>"
        statistics += f"<td>Page: ~{page_count}</td>"
        statistics += "</td><th id='rs-text'>RichSpan</th>"
        statistics += "</tr></table></body></html>"

        self.statistics_label.setText(statistics)
        self.status_bar.addPermanentWidget(self.statistics_label)
        self.new_text = self.rs_area.toPlainText()
        if self.new_text != self.default_values['text_content']:
            self.is_saved = False
        else:
            self.is_saved = True
        self.update_title()
    
    def toggle_dock(self):
        if self.dock_widget.isHidden():
            self.dock_widget.show()
        else:
            self.dock_widget.hide()

    def align(self, alignment):
        self.rs_area.setAlignment(alignment)

    def toggle_view(self):
        if self.rs_area.isReadOnly():
            self.rs_area.setReadOnly(False)
            self.rs_area.setHtml(self.rs_area.toPlainText())
            self.toggle_view_action.setText("Rich Text")
        else:
            self.rs_area.setReadOnly(True)
            self.rs_area.setPlainText(self.rs_area.toHtml())
            self.toggle_view_action.setText("Plain Text")

    def toggle_bold(self):
        font = self.rs_area.currentFont()
        font.setBold(not font.bold())
        self.rs_area.setCurrentFont(font)

    def toggle_italic(self):
        font = self.rs_area.currentFont()
        font.setItalic(not font.italic())
        self.rs_area.setCurrentFont(font)

    def toggle_underline(self):
        font = self.rs_area.currentFont()
        font.setUnderline(not font.underline())
        self.rs_area.setCurrentFont(font)

    def toggle_color(self):
        color = QColorDialog.getColor()
        self.rs_area.setTextColor(color)

    def toggle_bgcolor(self):
        color = QColorDialog.getColor()
        self.rs_area.setTextBackgroundColor(color)
    
    def toggle_font(self):
        font, ok = QFontDialog.getFont(self.rs_area.currentFont(), self)
        if ok:
            self.rs_area.setCurrentFont(font)

    def inc_font(self):
        font = self.rs_area.currentFont()
        font.setPointSize(font.pointSize() + 1)
        self.rs_area.setCurrentFont(font)

    def dec_font(self):
        font = self.rs_area.currentFont()
        font.setPointSize(font.pointSize() - 1)
        self.rs_area.setCurrentFont(font)

    def add_image(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_filter = "Portable Network Graphics (*.png);;JPEG (*.jpg *.jpeg);;Bitmap (*.bmp);;GIF (*.gif)"
        selected_file, _ = QFileDialog.getOpenFileName(
            self, "Open", self.directory, file_filter, options=options)
        if selected_file:
            with open(selected_file, 'rb') as file:
                data = file.read()
                data = base64.b64encode(data)
                data = data.decode('utf-8')
                self.rs_area.insertHtml(f'<img src="data:image/png;base64,{data}"/>')

    def find(self):
        self.find_dialog = QInputDialog(self)
        self.find_dialog.setInputMode(QInputDialog.TextInput)
        self.find_dialog.setLabelText("Find:")
        self.find_dialog.setWindowTitle("Find")
        self.find_dialog.setOkButtonText("Find")
        self.find_dialog.setCancelButtonText("Cancel")
        self.find_dialog.textValueSelected.connect(self.find_text)
        self.find_dialog.show()

    def find_text(self, text):
        self.rs_area.find(text)

    def replace(self):
        self.replace_dialog = QInputDialog(self)
        self.replace_dialog.setInputMode(QInputDialog.TextInput)
        self.replace_dialog.setLabelText("Find:")
        self.replace_dialog.setWindowTitle("Replace")
        self.replace_dialog.setOkButtonText("Replace")
        self.replace_dialog.setCancelButtonText("Cancel")
        self.replace_dialog.textValueSelected.connect(self.replace_text)
        self.replace_dialog.show()
    
    def replace_text(self, text):
        self.rs_area.find(text)
        self.rs_area.insertPlainText(text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    core = RS_Workspace()
    app.setOrganizationName("berkaygediz")
    app.setApplicationName("RichSpan")
    app.setApplicationDisplayName("RichSpan")
    app.setApplicationVersion("1.2.0")
    core.show()
    sys.exit(app.exec_())
