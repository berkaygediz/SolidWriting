import base64
import datetime
import os
import sys
import time

import chardet
import mammoth
import psutil
import qtawesome as qta
from langdetect import DetectorFactory, detect
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtOpenGL import *
from PySide6.QtOpenGLWidgets import *
from PySide6.QtPrintSupport import *
from PySide6.QtWidgets import *

from modules.translations import *

fallbackValues = {
    "fontFamily": "Helvetica",
    "fontSize": 14,
    "bold": False,
    "italic": False,
    "underline": False,
    "contentAlign": Qt.AlignmentFlag.AlignLeft,
    "contentColor": "#000000",
    "contentBackgroundColor": "transparent",
    "windowScale": None,
    "defaultDirectory": None,
    "fileName": None,
    "content": None,
    "isSaved": None,
    "scrollPosition": None,
    "appTheme": "light",
    "appLanguage": "English",
    "adaptiveResponse": 1,
    "readFilter": "General File (*.rsdoc *.docx);;HTML (*.html);;Text (*.txt);;Key-Value (*.ini);;LOG (*.log);;JavaScript Object Notation (*.json);;Extensible Markup Language (*.xml);;Javascript (*.js);;Cascading Style Sheets (*.css);;Structured Query Language (*.sql);;Markdown (*.md)",
    "writeFilter": "RichSpan Document (*.rsdoc);;HTML (*.html);;Text (*.txt);;Key-Value (*.ini);;LOG (*.log);;JavaScript Object Notation (*.json);;Extensible Markup Language (*.xml);;Javascript (*.js);;Cascading Style Sheets (*.css);;Structured Query Language (*.sql);;Markdown (*.md)",
    "mediaFilter": "Portable Network Graphics (*.png);;JPEG (*.jpg *.jpeg);;Bitmap (*.bmp);;GIF (*.gif)",
}


class RS_Threading(QThread):
    update_signal = Signal()

    def __init__(self, adaptiveResponse, parent=None):
        super(RS_Threading, self).__init__(parent)
        self.adaptiveResponse = float(adaptiveResponse)
        self.running = False
        self.mutex = QMutex()

    def run(self):
        if not self.running:
            self.mutex.lock()
            self.running = True
            self.mutex.unlock()
            time.sleep(0.15 * self.adaptiveResponse)
            self.update_signal.emit()
            self.mutex.lock()
            self.running = False
            self.mutex.unlock()


class RS_About(QMainWindow):
    def __init__(self, parent=None):
        super(RS_About, self).__init__(parent)
        self.setWindowFlags(Qt.Dialog)
        self.setWindowIcon(QIcon("richspan_icon.png"))
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setGeometry(
            QStyle.alignedRect(
                Qt.LeftToRight,
                Qt.AlignCenter,
                self.size(),
                QApplication.primaryScreen().availableGeometry(),
            )
        )
        self.about_label = QLabel()
        self.about_label.setWordWrap(True)
        self.about_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.about_label.setTextFormat(Qt.RichText)
        self.about_label.setText(
            "<center>"
            f"<b>{app.applicationDisplayName()}</b><br><br>"
            "A word processor application<br>"
            "Made by Berkay Gediz<br><br>"
            "GNU General Public License v3.0<br>GNU LESSER GENERAL PUBLIC LICENSE v3.0<br>Mozilla Public License Version 2.0<br><br><b>Libraries: </b>mwilliamson/python-mammoth, chardet, psutil, qtawesome<br><br>"
            "OpenGL: <b>ON</b></center>"
        )
        self.setCentralWidget(self.about_label)


class RS_Workspace(QMainWindow):
    def __init__(self, parent=None):
        super(RS_Workspace, self).__init__(parent)
        starttime = datetime.datetime.now()
        settings = QSettings("berkaygediz", "RichSpan")
        if settings.value("appLanguage") == None:
            settings.setValue("appLanguage", "English")
            settings.sync()
        if settings.value("adaptiveResponse") == None:
            settings.setValue("adaptiveResponse", 1)
            settings.sync()
        self.setWindowIcon(QIcon("richspan_icon.ico"))
        self.setWindowModality(Qt.ApplicationModal)
        self.setMinimumSize(768, 540)

        centralWidget = QOpenGLWidget(self)

        layout = QVBoxLayout(centralWidget)
        self.hardwareAcceleration = QOpenGLWidget()
        layout.addWidget(self.hardwareAcceleration)
        self.setCentralWidget(centralWidget)

        self.richspan_thread = RS_Threading(
            adaptiveResponse=settings.value("adaptiveResponse")
        )
        self.richspan_thread.update_signal.connect(self.RS_updateStatistics)

        self.RS_themePalette()
        self.selected_file = None
        self.file_name = None
        self.is_saved = None
        self.default_directory = QDir().homePath()
        self.directory = self.default_directory

        self.RS_setupDock()
        self.dock_widget.hide()

        self.status_bar = self.statusBar()
        self.rs_area = QTextEdit()
        self.RS_setupArea()
        layout.addWidget(self.rs_area)

        self.rs_area.setDisabled(True)
        self.RS_setupActions()
        self.RS_setupToolbar()
        self.adaptiveResponse = settings.value("adaptiveResponse")

        self.setPalette(self.light_theme)
        self.text_changed_timer = QTimer()
        self.text_changed_timer.setInterval(150 * self.adaptiveResponse)
        self.text_changed_timer.timeout.connect(self.RS_threadStart)
        self.rs_area.textChanged.connect(self.RS_textChanged)
        self.thread_running = False

        self.showMaximized()
        self.rs_area.setFocus()
        self.rs_area.setAcceptRichText(True)

        QTimer.singleShot(50 * self.adaptiveResponse, self.RS_restoreTheme)
        QTimer.singleShot(150 * self.adaptiveResponse, self.RS_restoreState)

        self.rs_area.setDisabled(False)
        self.RS_updateTitle()

        endtime = datetime.datetime.now()
        self.status_bar.showMessage(
            str((endtime - starttime).total_seconds()) + " ms", 2500
        )

    def closeEvent(self, event):
        settings = QSettings("berkaygediz", "RichSpan")
        if self.is_saved == False:
            reply = QMessageBox.question(
                self,
                f"{app.applicationDisplayName()}",
                translations[settings.value("appLanguage")]["exit_message"],
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                self.RS_saveState()
                event.accept()
            else:
                self.RS_saveState()
                event.ignore()
        else:
            self.RS_saveState()
            event.accept()

    def RS_changeLanguage(self):
        language = self.language_combobox.currentText()
        settings = QSettings("berkaygediz", "RichSpan")
        settings.setValue("appLanguage", language)
        settings.sync()
        self.RS_updateTitle()
        self.RS_updateStatistics()
        self.RS_toolbarTranslate()

    def RS_updateTitle(self):
        settings = QSettings("berkaygediz", "RichSpan")
        file = (
            self.file_name
            if self.file_name
            else translations[settings.value("appLanguage")]["new"]
        )
        if file.endswith(".docx"):
            textMode = " - Read Only"
        else:
            textMode = ""
        if len(textMode) == 0:
            if self.is_saved == True:
                asterisk = ""
            else:
                asterisk = "*"
        else:
            asterisk = ""
        self.setWindowTitle(
            f"{file}{asterisk}{textMode} — {app.applicationDisplayName()}"
        )

    def RS_threadStart(self):
        if not self.thread_running:
            self.richspan_thread.start()
            self.thread_running = True

    def RS_textChanged(self):
        if not self.text_changed_timer.isActive():
            self.text_changed_timer.start()

    def RS_updateStatistics(self):
        self.text_changed_timer.stop()
        self.thread_running = False
        settings = QSettings("berkaygediz", "RichSpan")
        text = self.rs_area.toPlainText()
        character_count = len(text)
        word_count = len(text.split())
        line_count = text.count("\n") + 1

        statistics = f"<html><head><style>"
        statistics += "table {border-collapse: collapse; width: 100%;}"
        statistics += "th, td {text-align: left; padding: 10px;}"
        statistics += "tr:nth-child(even) {background-color: #f2f2f2;}"
        statistics += ".highlight {background-color: #E2E3E1; color: #000000}"
        statistics += "tr:hover {background-color: #ddd;}"
        statistics += "th { background-color: #0379FF; color: white;}"
        statistics += "td { color: white;}"
        statistics += "#rs-text { background-color: #E2E3E1; color: #000000; }"
        statistics += "</style></head><body>"
        statistics += "<table><tr>"
        if word_count > 0 and line_count > 0 and character_count > 0 and text != "":
            statistics += (
                f"<th>{translations[settings.value('appLanguage')]['analysis']}</th>"
            )
            avg_word_length = sum(len(word) for word in text.split()) / word_count
            formatted_avg_word_length = "{:.1f}".format(avg_word_length)
            statistics += f"<td>{translations[settings.value('appLanguage')]['analysis_message_1'].format(formatted_avg_word_length)}</td>"
            avg_line_length = character_count / line_count - 1
            formatted_avg_line_length = "{:.1f}".format(avg_line_length)
            statistics += f"<td>{translations[settings.value('appLanguage')]['analysis_message_2'].format(formatted_avg_line_length)}</td>"
            uppercase_count = sum(1 for char in text if char.isupper())
            lowercase_count = sum(1 for char in text if char.islower())
            statistics += f"<td>{translations[settings.value('appLanguage')]['analysis_message_3'].format(uppercase_count)}</td>"
            statistics += f"<td>{translations[settings.value('appLanguage')]['analysis_message_4'].format(lowercase_count)}</td>"
            if word_count > 8:
                DetectorFactory.seed = 0
                lang = detect(text)
                statistics += f"<td>{translations[settings.value('appLanguage')]['analysis_message_5'].format(lang)}</td>"

        else:
            self.rs_area.setFontFamily(fallbackValues["fontFamily"])
            self.rs_area.setFontPointSize(fallbackValues["fontSize"])
            self.rs_area.setFontWeight(75 if fallbackValues["bold"] else 50)
            self.rs_area.setFontItalic(fallbackValues["italic"])
            self.rs_area.setFontUnderline(fallbackValues["underline"])
            self.rs_area.setAlignment(fallbackValues["contentAlign"])
            self.rs_area.setTextColor(QColor(fallbackValues["contentColor"]))
            self.rs_area.setTextBackgroundColor(
                QColor(fallbackValues["contentBackgroundColor"])
            )
        statistics += (
            f"<th>{translations[settings.value('appLanguage')]['statistic']}</th>"
        )
        statistics += f"<td>{translations[settings.value('appLanguage')]['statistic_message_1'].format(line_count)}</td>"
        statistics += f"<td>{translations[settings.value('appLanguage')]['statistic_message_2'].format(word_count)}</td>"
        statistics += f"<td>{translations[settings.value('appLanguage')]['statistic_message_3'].format(character_count)}</td>"
        statistics += f"</td><th id='rs-text'>{app.applicationDisplayName()}</th>"
        statistics += "</tr></table></body></html>"

        self.statistics_label.setText(statistics)
        self.status_bar.addPermanentWidget(self.statistics_label)
        self.new_text = self.rs_area.toPlainText()
        if self.new_text != fallbackValues["content"]:
            self.is_saved = False
        else:
            self.is_saved = True
        self.RS_updateTitle()

    def RS_saveState(self):
        settings = QSettings("berkaygediz", "RichSpan")
        settings.setValue("windowScale", self.saveGeometry())
        settings.setValue("defaultDirectory", self.directory)
        settings.setValue("fileName", self.file_name)
        settings.setValue("content", self.rs_area.toHtml())
        settings.setValue("isSaved", self.is_saved)
        settings.setValue("scrollPosition", self.rs_area.verticalScrollBar().value())
        settings.setValue(
            "appTheme", "dark" if self.palette() == self.dark_theme else "light"
        )
        settings.setValue("appLanguage", self.language_combobox.currentText())
        settings.setValue("adaptiveResponse", self.adaptiveResponse)
        settings.sync()

    def RS_restoreState(self):
        settings = QSettings("berkaygediz", "RichSpan")
        self.geometry = settings.value("windowScale")
        self.directory = settings.value("defaultDirectory", self.default_directory)
        self.file_name = settings.value("fileName")
        self.rs_area.setHtml(settings.value("content"))
        self.is_saved = settings.value("isSaved")
        self.language_combobox.setCurrentText(settings.value("appLanguage"))

        if self.geometry is not None:
            self.restoreGeometry(self.geometry)

        if self.file_name and os.path.exists(self.file_name):
            automaticEncoding = RS_Workspace.RS_detectEncoding(self.file_name)
            if self.file_name.endswith(".docx"):
                with open(
                    self.file_name,
                    "rb",
                ) as file:
                    try:
                        conversionLayer = mammoth.convert_to_html(file)
                        self.rs_area.setHtml(conversionLayer.value)
                    except:
                        None

            else:
                with open(self.file_name, "r", encoding=automaticEncoding) as file:
                    if self.file_name.endswith((".rsdoc")):
                        self.rs_area.setHtml(file.read())
                    elif self.file_name.endswith((".html", ".htm")):
                        self.rs_area.setHtml(file.read())

                    elif self.file_name.endswith((".md")):
                        self.rs_area.setMarkdown(file.read())
                    else:
                        self.rs_area.setPlainText(file.read())

        scroll_position = settings.value("scrollPosition")
        if scroll_position is not None:
            self.rs_area.verticalScrollBar().setValue(int(scroll_position))
        else:
            self.rs_area.verticalScrollBar().setValue(0)

        if self.file_name:
            self.is_saved = True
        else:
            self.is_saved = False

        self.adaptiveResponse = settings.value("adaptiveResponse")
        self.RS_restoreTheme()
        self.RS_updateTitle()

    def RS_restoreTheme(self):
        settings = QSettings("berkaygediz", "RichSpan")
        if settings.value("appTheme") == "dark":
            self.setPalette(self.dark_theme)
        else:
            self.setPalette(self.light_theme)
        self.RS_toolbarTheme()

    def RS_themePalette(self):
        self.light_theme = QPalette()
        self.dark_theme = QPalette()

        self.light_theme.setColor(QPalette.Window, QColor(3, 65, 135))
        self.light_theme.setColor(QPalette.WindowText, QColor(255, 255, 255))
        self.light_theme.setColor(QPalette.Base, QColor(255, 255, 255))
        self.light_theme.setColor(QPalette.Text, QColor(0, 0, 0))
        self.light_theme.setColor(QPalette.Highlight, QColor(105, 117, 156))
        self.light_theme.setColor(QPalette.Button, QColor(0, 0, 0))
        self.light_theme.setColor(QPalette.ButtonText, QColor(255, 255, 255))

        self.dark_theme.setColor(QPalette.Window, QColor(35, 39, 52))
        self.dark_theme.setColor(QPalette.WindowText, QColor(255, 255, 255))
        self.dark_theme.setColor(QPalette.Base, QColor(80, 85, 122))
        self.dark_theme.setColor(QPalette.Text, QColor(255, 255, 255))
        self.dark_theme.setColor(QPalette.Highlight, QColor(105, 117, 156))
        self.dark_theme.setColor(QPalette.Button, QColor(0, 0, 0))
        self.dark_theme.setColor(QPalette.ButtonText, QColor(255, 255, 255))

    def RS_themeAction(self):
        settings = QSettings("berkaygediz", "RichSpan")
        if self.palette() == self.light_theme:
            self.setPalette(self.dark_theme)
            settings.setValue("appTheme", "dark")
        else:
            self.setPalette(self.light_theme)
            settings.setValue("appTheme", "light")
        self.RS_toolbarTheme()

    def RS_toolbarTheme(self):
        palette = self.palette()
        if palette == self.light_theme:
            text_color = QColor(255, 255, 255)
        else:
            text_color = QColor(255, 255, 255)

        for toolbar in self.findChildren(QToolBar):
            for action in toolbar.actions():
                if action.text():
                    action_color = QPalette()
                    action_color.setColor(QPalette.ButtonText, text_color)
                    action_color.setColor(QPalette.WindowText, text_color)
                    toolbar.setPalette(action_color)

    def RS_toolbarTranslate(self):
        settings = QSettings("berkaygediz", "RichSpan")
        self.newaction.setText(translations[settings.value("appLanguage")]["new"])
        self.newaction.setStatusTip(
            translations[settings.value("appLanguage")]["new_message"]
        )
        self.openaction.setText(translations[settings.value("appLanguage")]["open"])
        self.openaction.setStatusTip(
            translations[settings.value("appLanguage")]["open_message"]
        )
        self.saveaction.setText(translations[settings.value("appLanguage")]["save"])
        self.saveaction.setStatusTip(
            translations[settings.value("appLanguage")]["save_message"]
        )
        self.saveasaction.setText(
            translations[settings.value("appLanguage")]["save_as"]
        )
        self.saveasaction.setStatusTip(
            translations[settings.value("appLanguage")]["save_as_message"]
        )
        self.printaction.setText(translations[settings.value("appLanguage")]["print"])
        self.printaction.setStatusTip(
            translations[settings.value("appLanguage")]["print_message"]
        )
        self.undoaction.setText(translations[settings.value("appLanguage")]["undo"])
        self.undoaction.setStatusTip(
            translations[settings.value("appLanguage")]["undo_message"]
        )
        self.redoaction.setText(translations[settings.value("appLanguage")]["redo"])
        self.redoaction.setStatusTip(
            translations[settings.value("appLanguage")]["redo_message"]
        )
        self.theme_action.setText(
            translations[settings.value("appLanguage")]["darklight"]
        )
        self.theme_action.setStatusTip(
            translations[settings.value("appLanguage")]["darklight_message"]
        )
        self.findaction.setText(translations[settings.value("appLanguage")]["find"])
        self.findaction.setStatusTip(
            translations[settings.value("appLanguage")]["find_message"]
        )
        self.replaceaction.setText(
            translations[settings.value("appLanguage")]["replace"]
        )
        self.replaceaction.setStatusTip(
            translations[settings.value("appLanguage")]["replace_message"]
        )
        self.aboutaction.setText(translations[settings.value("appLanguage")]["about"])
        self.aboutaction.setStatusTip(
            translations[settings.value("appLanguage")]["about"]
        )
        self.alignrightevent.setText(
            translations[settings.value("appLanguage")]["right"]
        )
        self.alignrightevent.setStatusTip(
            translations[settings.value("appLanguage")]["right_message"]
        )
        self.aligncenterevent.setText(
            translations[settings.value("appLanguage")]["center"]
        )
        self.aligncenterevent.setStatusTip(
            translations[settings.value("appLanguage")]["center_message"]
        )
        self.alignleftevent.setText(translations[settings.value("appLanguage")]["left"])
        self.alignleftevent.setStatusTip(
            translations[settings.value("appLanguage")]["left_message"]
        )
        self.alignjustifiedevent.setText(
            translations[settings.value("appLanguage")]["justify"]
        )
        self.alignjustifiedevent.setStatusTip(
            translations[settings.value("appLanguage")]["justify_message"]
        )
        self.color.setText(translations[settings.value("appLanguage")]["font_color"])
        self.color.setStatusTip(
            translations[settings.value("appLanguage")]["font_color_message"]
        )
        self.backgroundcolor.setText(
            translations[settings.value("appLanguage")]["contentBackgroundColor"]
        )
        self.backgroundcolor.setStatusTip(
            translations[settings.value("appLanguage")][
                "contentBackgroundColor_message"
            ]
        )
        self.dock_widget.setWindowTitle(
            translations[settings.value("appLanguage")]["help"] + " && AI"
        )
        self.dock_widget.setWidget(self.helpText)
        self.helpText.setText(
            "<html><head><style>"
            "table { width: 100%; }"
            "th, td {text-align: left; padding: 8px;}"
            "tr:nth-child(even) {background-color: #f2f2f2;}"
            "tr:hover {background-color: #ddd;}"
            "th {background-color: #4CAF50; color: white;}"
            "td {background-color: #000000; color: white;}"
            "p {background-color: red; color: white; padding: 12px; }"
            "</style></head><body>"
            "<table width='100%'><tr>"
            f"<th>{translations[settings.value('appLanguage')]['help_shortcut']}</th>"
            f"<th>{translations[settings.value('appLanguage')]['help_description']}</th>"
            f"</tr><tr><td>Ctrl+N</td><td>{translations[settings.value('appLanguage')]['new_message']}</td></tr>"
            f"<tr><td>Ctrl+O</td><td>{translations[settings.value('appLanguage')]['open_message']}</td></tr>"
            f"<tr><td>Ctrl+S</td><td>{translations[settings.value('appLanguage')]['save_message']}</td></tr>"
            f"<tr><td>Ctrl+Shift+S</td><td>{translations[settings.value('appLanguage')]['save_as_message']}</td></tr>"
            f"<tr><td>Ctrl+P</td><td>{translations[settings.value('appLanguage')]['print_message']}</td></tr>"
            f"<tr><td>Ctrl+Z</td><td>{translations[settings.value('appLanguage')]['undo_message']}</td></tr>"
            f"<tr><td>Ctrl+Y</td><td>{translations[settings.value('appLanguage')]['redo_message']}</td></tr>"
            f"<tr><td>Ctrl+Shift+T</td><td>{translations[settings.value('appLanguage')]['darklight_message']}</td></tr>"
            f"<tr><td>Ctrl+Shift+D</td><td>{translations[settings.value('appLanguage')]['help_message']}</td></tr>"
            f"<tr><td>Ctrl+Shift+C</td><td>{translations[settings.value('appLanguage')]['font_color_message']}</td></tr>"
            f"<tr><td>Ctrl+Shift+B</td><td>{translations[settings.value('appLanguage')]['contentBackgroundColor_message']}</td></tr>"
            f"<tr><td>Ctrl+Shift+F</td><td>{translations[settings.value('appLanguage')]['font_message']}</td></tr>"
            f"<tr><td>Ctrl++</td><td>{translations[settings.value('appLanguage')]['inc_font_message']}</td></tr>"
            f"<tr><td>Ctrl+-</td><td>{translations[settings.value('appLanguage')]['dec_font_message']}</td></tr>"
            f"<tr><td>Ctrl+Shift+P</td><td>{translations[settings.value('appLanguage')]['image_message']}</td></tr>"
            f"<tr><td>Ctrl+F</td><td>{translations[settings.value('appLanguage')]['find_message']}</td></tr>"
            f"<tr><td>Ctrl+H</td><td>{translations[settings.value('appLanguage')]['replace_message']}</td></tr>"
            f"<tr><td>Ctrl+Shift+U</td><td>{translations[settings.value('appLanguage')]['bullet']}</td></tr>"
            f"<tr><td>Ctrl+Shift+O</td><td>{translations[settings.value('appLanguage')]['numbered']}</td></tr>"
            f"<tr><td>Ctrl+Shift+R</td><td>{translations[settings.value('appLanguage')]['right']}</td></tr>"
            f"<tr><td>Ctrl+Shift+L</td><td>{translations[settings.value('appLanguage')]['left']}</td></tr>"
            f"<tr><td>Ctrl+Shift+E</td><td>{translations[settings.value('appLanguage')]['center']}</td></tr>"
            f"<tr><td>Ctrl+Shift+J</td><td>{translations[settings.value('appLanguage')]['justify']}</td></tr>"
            "</table><center><p>NOTE: <b>AI</b> support planned.</p></center></body></html>"
        )

    def RS_setupArea(self):
        self.rs_area.setFontFamily(fallbackValues["fontFamily"])
        self.rs_area.setFontPointSize(fallbackValues["fontSize"])
        self.rs_area.setFontWeight(75 if fallbackValues["bold"] else 50)
        self.rs_area.setFontItalic(fallbackValues["italic"])
        self.rs_area.setFontUnderline(fallbackValues["underline"])
        self.rs_area.setAlignment(fallbackValues["contentAlign"])
        self.rs_area.setTextColor(QColor(fallbackValues["contentColor"]))
        self.rs_area.setTextBackgroundColor(
            QColor(fallbackValues["contentBackgroundColor"])
        )
        self.rs_area.setTabStopDistance(27)
        self.rs_area.document().setDocumentMargin(self.width() * 0.25)

    def RS_setupDock(self):
        settings = QSettings("berkaygediz", "RichSpan")
        settings.sync()
        self.dock_widget = QDockWidget(
            translations[settings.value("appLanguage")]["help"] + " && AI", self
        )
        self.dock_widget.setObjectName("Help & AI")
        self.dock_widget.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_widget)

        self.scrollableArea = QScrollArea()
        self.AI_QVBox = QVBoxLayout()
        self.statistics_label = QLabel()
        self.helpText = QLabel()
        self.helpText.setWordWrap(True)
        self.helpText.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.helpText.setTextFormat(Qt.RichText)
        self.helpText.setText(
            "<html><head><style>"
            "table { width: 100%; }"
            "th, td {text-align: left; padding: 8px;}"
            "tr:nth-child(even) {background-color: #f2f2f2;}"
            "tr:hover {background-color: #ddd;}"
            "th {background-color: #4CAF50; color: white;}"
            "td {background-color: #000000; color: white;}"
            "p {background-color: red; color: white; padding: 12px; }"
            "</style></head><body>"
            "<table width='100%'><tr>"
            f"<th>{translations[settings.value('appLanguage')]['help_shortcut']}</th>"
            f"<th>{translations[settings.value('appLanguage')]['help_description']}</th>"
            f"</tr><tr><td>Ctrl+N</td><td>{translations[settings.value('appLanguage')]['new_message']}</td></tr>"
            f"<tr><td>Ctrl+O</td><td>{translations[settings.value('appLanguage')]['open_message']}</td></tr>"
            f"<tr><td>Ctrl+S</td><td>{translations[settings.value('appLanguage')]['save_message']}</td></tr>"
            f"<tr><td>Ctrl+Shift+S</td><td>{translations[settings.value('appLanguage')]['save_as_message']}</td></tr>"
            f"<tr><td>Ctrl+P</td><td>{translations[settings.value('appLanguage')]['print_message']}</td></tr>"
            f"<tr><td>Ctrl+Z</td><td>{translations[settings.value('appLanguage')]['undo_message']}</td></tr>"
            f"<tr><td>Ctrl+Y</td><td>{translations[settings.value('appLanguage')]['redo_message']}</td></tr>"
            f"<tr><td>Ctrl+Shift+T</td><td>{translations[settings.value('appLanguage')]['darklight_message']}</td></tr>"
            f"<tr><td>Ctrl+Shift+D</td><td>{translations[settings.value('appLanguage')]['help_message']}</td></tr>"
            f"<tr><td>Ctrl+Shift+C</td><td>{translations[settings.value('appLanguage')]['font_color_message']}</td></tr>"
            f"<tr><td>Ctrl+Shift+B</td><td>{translations[settings.value('appLanguage')]['contentBackgroundColor_message']}</td></tr>"
            f"<tr><td>Ctrl+Shift+F</td><td>{translations[settings.value('appLanguage')]['font_message']}</td></tr>"
            f"<tr><td>Ctrl++</td><td>{translations[settings.value('appLanguage')]['inc_font_message']}</td></tr>"
            f"<tr><td>Ctrl+-</td><td>{translations[settings.value('appLanguage')]['dec_font_message']}</td></tr>"
            f"<tr><td>Ctrl+Shift+P</td><td>{translations[settings.value('appLanguage')]['image_message']}</td></tr>"
            f"<tr><td>Ctrl+F</td><td>{translations[settings.value('appLanguage')]['find_message']}</td></tr>"
            f"<tr><td>Ctrl+H</td><td>{translations[settings.value('appLanguage')]['replace_message']}</td></tr>"
            f"<tr><td>Ctrl+Shift+U</td><td>{translations[settings.value('appLanguage')]['bullet']}</td></tr>"
            f"<tr><td>Ctrl+Shift+O</td><td>{translations[settings.value('appLanguage')]['numbered']}</td></tr>"
            f"<tr><td>Ctrl+Shift+R</td><td>{translations[settings.value('appLanguage')]['right']}</td></tr>"
            f"<tr><td>Ctrl+Shift+L</td><td>{translations[settings.value('appLanguage')]['left']}</td></tr>"
            f"<tr><td>Ctrl+Shift+E</td><td>{translations[settings.value('appLanguage')]['center']}</td></tr>"
            f"<tr><td>Ctrl+Shift+J</td><td>{translations[settings.value('appLanguage')]['justify']}</td></tr>"
            "</table><center><p>NOTE: <b>AI</b> support planned.</p></center></body></html>"
        )
        self.AI_QVBox.addWidget(self.helpText)

        self.dock_widget.setObjectName("Help")
        self.dock_widget.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_widget)

        self.dock_widget.setWidget(self.scrollableArea)

        self.dock_widget.setFeatures(
            QDockWidget.NoDockWidgetFeatures | QDockWidget.DockWidgetClosable
        )
        self.dock_widget.setWidget(self.scrollableArea)
        self.scrollableArea.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scrollableArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scrollableArea.setWidgetResizable(True)
        scroll_contents = QWidget()
        scroll_contents.setLayout(self.AI_QVBox)
        self.scrollableArea.setWidget(scroll_contents)

    def RS_toolbarLabel(self, toolbar, text):
        label = QLabel(f"<b>{text}</b>")
        toolbar.addWidget(label)

    def RS_createAction(self, text, status_tip, function, shortcut=None, icon=None):
        action = QAction(text, self)
        action.setStatusTip(status_tip)
        action.triggered.connect(function)
        if shortcut:
            action.setShortcut(shortcut)
        if icon:
            action.setIcon(
                QIcon("")
            )  # qtawesome is library based on qt5 --> icon = Qt5.QtGui.QIcon
        return action

    def RS_setupActions(self):
        settings = QSettings("berkaygediz", "RichSpan")
        icon_theme = "white"
        if self.palette() == self.light_theme:
            icon_theme = "black"
        actionicon = qta.icon("fa5.file", color=icon_theme)
        self.newaction = self.RS_createAction(
            translations[settings.value("appLanguage")]["new"],
            translations[settings.value("appLanguage")]["new_message"],
            self.new,
            QKeySequence.New,
            actionicon,
        )
        actionicon = qta.icon("fa5.folder-open", color="gold")
        self.openaction = self.RS_createAction(
            translations[settings.value("appLanguage")]["open"],
            translations[settings.value("appLanguage")]["open_message"],
            self.open,
            QKeySequence.Open,
            actionicon,
        )
        actionicon = qta.icon("fa5s.save", color="#00BFFF")
        self.saveaction = self.RS_createAction(
            translations[settings.value("appLanguage")]["save"],
            translations[settings.value("appLanguage")]["save_message"],
            self.save,
            QKeySequence.Save,
            actionicon,
        )
        actionicon = qta.icon("fa5.save", color="#00BFFF")
        self.saveasaction = self.RS_createAction(
            translations[settings.value("appLanguage")]["save_as"],
            translations[settings.value("appLanguage")]["save_as_message"],
            self.saveAs,
            QKeySequence.SaveAs,
            actionicon,
        )
        actionicon = qta.icon("fa5s.print", color=icon_theme)
        self.printaction = self.RS_createAction(
            translations[settings.value("appLanguage")]["print"],
            translations[settings.value("appLanguage")]["print_message"],
            self.print,
            QKeySequence.Print,
            actionicon,
        )
        actionicon = qta.icon("fa5s.search", color=icon_theme)
        self.findaction = self.RS_createAction(
            translations[settings.value("appLanguage")]["find"],
            translations[settings.value("appLanguage")]["find_message"],
            self.find,
            QKeySequence.Find,
            actionicon,
        )
        actionicon = qta.icon("fa5s.exchange-alt", color=icon_theme)
        self.replaceaction = self.RS_createAction(
            translations[settings.value("appLanguage")]["replace"],
            translations[settings.value("appLanguage")]["replace_message"],
            self.replace,
            QKeySequence.Replace,
            actionicon,
        )
        actionicon = qta.icon("fa5s.undo-alt", color=icon_theme)
        self.undoaction = self.RS_createAction(
            translations[settings.value("appLanguage")]["undo"],
            translations[settings.value("appLanguage")]["undo_message"],
            self.rs_area.undo,
            QKeySequence.Undo,
            actionicon,
        )
        actionicon = qta.icon("fa5s.redo-alt", color=icon_theme)
        self.redoaction = self.RS_createAction(
            translations[settings.value("appLanguage")]["redo"],
            translations[settings.value("appLanguage")]["redo_message"],
            self.rs_area.redo,
            QKeySequence.Redo,
            actionicon,
        )
        self.alignrightevent = self.RS_createAction(
            translations[settings.value("appLanguage")]["right"],
            translations[settings.value("appLanguage")]["right_message"],
            lambda: self.align(Qt.AlignRight),
        )
        self.alignleftevent = self.RS_createAction(
            translations[settings.value("appLanguage")]["left"],
            translations[settings.value("appLanguage")]["left_message"],
            lambda: self.align(Qt.AlignLeft),
        )
        self.aligncenterevent = self.RS_createAction(
            translations[settings.value("appLanguage")]["center"],
            translations[settings.value("appLanguage")]["center_message"],
            lambda: self.align(Qt.AlignCenter),
        )
        self.alignjustifiedevent = self.RS_createAction(
            translations[settings.value("appLanguage")]["justify"],
            translations[settings.value("appLanguage")]["justify_message"],
            lambda: self.align(Qt.AlignJustify),
        )
        actionicon = qta.icon("fa5s.list-ul", color=icon_theme)
        self.bulletevent = self.RS_createAction(
            translations[settings.value("appLanguage")]["bullet"],
            "",
            self.bullet,
            QKeySequence("Ctrl+Shift+U"),
            actionicon,
        )
        actionicon = qta.icon("fa5s.list-ol", color=icon_theme)
        self.numberedevent = self.RS_createAction(
            translations[settings.value("appLanguage")]["numbered"],
            "",
            self.numbered,
            QKeySequence("Ctrl+Shift+O"),
            actionicon,
        )
        actionicon = qta.icon("fa5s.bold", color=icon_theme)
        self.bold = self.RS_createAction(
            translations[settings.value("appLanguage")]["bold"],
            translations[settings.value("appLanguage")]["bold_message"],
            self.contentBold,
            QKeySequence.Bold,
            actionicon,
        )
        actionicon = qta.icon("fa5s.italic", color=icon_theme)
        self.italic = self.RS_createAction(
            translations[settings.value("appLanguage")]["italic"],
            translations[settings.value("appLanguage")]["italic_message"],
            self.contentItalic,
            QKeySequence.Italic,
            actionicon,
        )
        actionicon = qta.icon("fa5s.underline", color=icon_theme)
        self.underline = self.RS_createAction(
            translations[settings.value("appLanguage")]["underline"],
            translations[settings.value("appLanguage")]["underline_message"],
            self.contentUnderline,
            QKeySequence.Underline,
            actionicon,
        )
        actionicon = qta.icon("fa5s.palette", color=icon_theme)
        self.color = self.RS_createAction(
            translations[settings.value("appLanguage")]["font_color"],
            translations[settings.value("appLanguage")]["font_color_message"],
            self.contentColor,
            QKeySequence("Ctrl+Shift+C"),
            actionicon,
        )
        actionicon = qta.icon("fa5s.fill-drip", color=icon_theme)
        self.backgroundcolor = self.RS_createAction(
            translations[settings.value("appLanguage")]["contentBackgroundColor"],
            translations[settings.value("appLanguage")][
                "contentBackgroundColor_message"
            ],
            self.contentBGColor,
            QKeySequence("Ctrl+Shift+B"),
            actionicon,
        )
        actionicon = qta.icon("fa5s.font", color=icon_theme)
        self.fontfamily = self.RS_createAction(
            translations[settings.value("appLanguage")]["font"],
            translations[settings.value("appLanguage")]["font_message"],
            self.contentFont,
            QKeySequence("Ctrl+Shift+F"),
            actionicon,
        )
        self.inc_fontaction = self.RS_createAction(
            "A+",
            translations[settings.value("appLanguage")]["inc_font_message"],
            self.inc_font,
            QKeySequence("Ctrl++"),
        )
        self.dec_fontaction = self.RS_createAction(
            "A-",
            translations[settings.value("appLanguage")]["dec_font_message"],
            self.dec_font,
            QKeySequence("Ctrl+-"),
        )
        actionicon = qta.icon("fa5s.image", color=icon_theme)
        self.addimage = self.RS_createAction(
            translations[settings.value("appLanguage")]["image"],
            translations[settings.value("appLanguage")]["image_message"],
            self.contentAddImage,
            QKeySequence("Ctrl+Shift+P"),
            actionicon,
        )
        actionicon = qta.icon("fa5s.info-circle", color=icon_theme)
        self.aboutaction = self.RS_createAction(
            translations[settings.value("appLanguage")]["about"],
            "",
            self.showAbout,
            QKeySequence("Ctrl+Shift+I"),
            actionicon,
        )

    def RS_setupToolbar(self):
        settings = QSettings("berkaygediz", "RichSpan")
        self.toolbar = self.addToolBar(
            translations[settings.value("appLanguage")]["file"]
        )
        self.RS_toolbarLabel(
            self.toolbar,
            translations[settings.value("appLanguage")]["file"] + ": ",
        )
        self.toolbar.addActions(
            [
                self.newaction,
                self.openaction,
                self.saveaction,
                self.saveasaction,
                self.printaction,
                self.undoaction,
                self.redoaction,
                self.findaction,
                self.replaceaction,
            ]
        )

        self.toolbar = self.addToolBar(
            translations[settings.value("appLanguage")]["ui"]
        )
        self.RS_toolbarLabel(
            self.toolbar, translations[settings.value("appLanguage")]["ui"] + ": "
        )
        actionicon = qta.icon("fa5b.affiliatetheme", color="#acadac")
        self.theme_action = self.RS_createAction(
            translations[settings.value("appLanguage")]["darklight"],
            translations[settings.value("appLanguage")]["darklight_message"],
            self.RS_themeAction,
            QKeySequence("Ctrl+Shift+T"),
            actionicon,
        )
        self.theme_action.setCheckable(True)
        self.theme_action.setChecked(settings.value("appTheme") == "dark")

        self.toolbar.addAction(self.theme_action)
        actionicon = qta.icon("fa5s.leaf", color="lime")
        self.powersaveraction = QAction("Hybrid Power Saver", self, checkable=True)
        # self.powersaveraction.setIcon(QIcon(actionicon))
        self.powersaveraction.setStatusTip("Hybrid (Ultra/Standard) power saver.")
        self.powersaveraction.toggled.connect(self.RS_hybridSaver)

        self.toolbar.addAction(self.powersaveraction)
        if settings.value("adaptiveResponse") == None:
            response_exponential = settings.setValue(
                "adaptiveResponse", fallbackValues["adaptiveResponse"]
            )
        else:
            response_exponential = settings.value(
                "adaptiveResponse",
            )

        self.powersaveraction.setChecked(response_exponential > 1)
        self.toolbar.addAction(self.powersaveraction)
        actionicon = qta.icon("fa.connectdevelop", color="white")
        self.hide_dock_widget_action = self.RS_createAction(
            translations[settings.value("appLanguage")]["help"] + " && AI",
            translations[settings.value("appLanguage")]["help_message"],
            self.RS_toggleDock,
            QKeySequence("Ctrl+Shift+D"),
            actionicon,
        )
        self.toolbar.addAction(self.hide_dock_widget_action)
        self.toolbar.addAction(self.aboutaction)
        self.language_combobox = QComboBox(self)
        self.language_combobox.setStyleSheet("background-color:#000000; color:#FFFFFF;")
        self.language_combobox.addItems(
            [
                "English",
                "Deutsch",
                "Español",
                "Türkçe",
                "Azərbaycanca",
                "Uzbek",
                "Chinese",
                "Korean",
                "Japanese",
                "Arabic",
                "Russian",
                "French",
                "Greek",
            ]
        )
        self.language_combobox.currentIndexChanged.connect(self.RS_changeLanguage)
        self.toolbar.addWidget(self.language_combobox)

        self.addToolBarBreak()

        self.toolbar = self.addToolBar(
            translations[settings.value("appLanguage")]["edit"]
        )
        self.RS_toolbarLabel(
            self.toolbar,
            translations[settings.value("appLanguage")]["edit"] + ": ",
        )
        self.toolbar.addActions(
            [
                self.alignrightevent,
                self.aligncenterevent,
                self.alignleftevent,
                self.alignjustifiedevent,
            ]
        )
        self.toolbar.addSeparator()
        self.RS_toolbarLabel(
            self.toolbar,
            translations[settings.value("appLanguage")]["font"] + ": ",
        )
        self.toolbar.addActions([self.bold, self.italic, self.underline])
        self.toolbar.addSeparator()
        self.toolbar = self.addToolBar(
            translations[settings.value("appLanguage")]["list"]
        )
        self.RS_toolbarLabel(
            self.toolbar,
            translations[settings.value("appLanguage")]["list"] + ": ",
        )
        self.toolbar.addActions([self.bulletevent, self.numberedevent])
        self.addToolBarBreak()

        self.toolbar = self.addToolBar(
            translations[settings.value("appLanguage")]["color"]
        )
        self.RS_toolbarLabel(
            self.toolbar,
            translations[settings.value("appLanguage")]["color"] + ": ",
        )
        self.toolbar.addActions(
            [
                self.color,
                self.backgroundcolor,
                self.fontfamily,
                self.inc_fontaction,
                self.dec_fontaction,
            ]
        )

        self.toolbar = self.addToolBar(
            translations[settings.value("appLanguage")]["multimedia"]
        )
        self.RS_toolbarLabel(
            self.toolbar,
            translations[settings.value("appLanguage")]["multimedia"] + ": ",
        )
        self.toolbar.addActions([self.addimage])

    def RS_toggleDock(self):
        if self.dock_widget.isHidden():
            self.dock_widget.show()
        else:
            self.dock_widget.hide()

    def RS_hybridSaver(self, checked):
        settings = QSettings("berkaygediz", "RichSpan")
        if checked:
            battery = psutil.sensors_battery()
            if battery:
                if battery.percent <= 35 and not battery.power_plugged:
                    # Ultra
                    self.adaptiveResponse = 12
                else:
                    # Standard
                    self.adaptiveResponse = 6
            else:
                # Global Standard
                self.adaptiveResponse = 3
        else:
            self.adaptiveResponse = fallbackValues["adaptiveResponse"]

        settings.setValue("adaptiveResponse", self.adaptiveResponse)
        settings.sync()

    def RS_detectEncoding(file_path):
        with open(file_path, "rb") as file:
            detector = chardet.universaldetector.UniversalDetector()
            for line in file:
                detector.feed(line)
                if detector.done:
                    break
            detector.close()
        return detector.result["encoding"]

    def new(self):
        settings = QSettings("berkaygediz", "RichSpan")
        if self.is_saved == True:
            self.rs_area.clear()
            self.rs_area.setFontFamily(fallbackValues["fontFamily"])
            self.rs_area.setFontPointSize(fallbackValues["fontSize"])
            self.rs_area.setFontWeight(75 if fallbackValues["bold"] else 50)
            self.rs_area.setFontItalic(fallbackValues["italic"])
            self.rs_area.setFontUnderline(fallbackValues["underline"])
            self.rs_area.setAlignment(fallbackValues["contentAlign"])
            self.rs_area.setTextColor(QColor(fallbackValues["contentColor"]))
            self.rs_area.setTextBackgroundColor(
                QColor(fallbackValues["contentBackgroundColor"])
            )
            self.rs_area.setTabStopDistance(27)
            self.directory = self.default_directory
            self.file_name = None
            self.is_saved = False
            self.RS_updateTitle()
        else:
            reply = QMessageBox.question(
                self,
                f"{app.applicationDisplayName()}",
                translations[settings.value("appLanguage")]["new_message"],
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                self.rs_area.clear()
                self.rs_area.setFontFamily(fallbackValues["fontFamily"])
                self.rs_area.setFontPointSize(fallbackValues["fontSize"])
                self.rs_area.setFontWeight(75 if fallbackValues["bold"] else 50)
                self.rs_area.setFontItalic(fallbackValues["italic"])
                self.rs_area.setFontUnderline(fallbackValues["underline"])
                self.rs_area.setAlignment(fallbackValues["contentAlign"])
                self.rs_area.setTextColor(QColor(fallbackValues["contentColor"]))
                self.rs_area.setTextBackgroundColor(
                    QColor(fallbackValues["contentBackgroundColor"])
                )
                self.rs_area.setTabStopDistance(27)
                self.directory = self.default_directory
                self.file_name = None
                self.is_saved = False
                self.RS_updateTitle()
            else:
                pass

    def open(self):
        options = QFileDialog.Options()
        settings = QSettings("berkaygediz", "RichSpan")
        options |= QFileDialog.ReadOnly
        selected_file, _ = QFileDialog.getOpenFileName(
            self,
            translations[settings.value("appLanguage")]["open"]
            + f" — {app.applicationDisplayName()} ",
            self.directory,
            fallbackValues["readFilter"],
            options=options,
        )
        if selected_file:
            self.file_name = selected_file
            automaticEncoding = RS_Workspace.RS_detectEncoding(selected_file)
            if self.file_name.endswith(".docx"):
                with open(
                    self.file_name,
                    "rb",
                ) as file:
                    try:
                        conversionLayer = mammoth.convert_to_html(file)
                        self.rs_area.setHtml(conversionLayer.value)
                    except:
                        QMessageBox.warning(self, None, "Conversion failed.")
            else:
                with open(self.file_name, "r", encoding=automaticEncoding) as file:
                    if self.file_name.endswith((".rsdoc")):
                        self.rs_area.setHtml(file.read())
                    elif self.file_name.endswith((".html", ".htm")):
                        self.rs_area.setHtml(file.read())

                    elif self.file_name.endswith((".md")):
                        self.rs_area.setMarkdown(file.read())
                    else:
                        self.rs_area.setPlainText(file.read())

            self.directory = os.path.dirname(self.file_name)
            self.is_saved = True
            self.RS_updateTitle()
        else:
            pass

    def save(self):
        if self.is_saved == False:
            self.saveFile()
        elif self.file_name == None:
            self.saveAs()
        else:
            self.saveFile()

    def saveAs(self):
        options = QFileDialog.Options()
        settings = QSettings("berkaygediz", "RichSpan")
        options |= QFileDialog.ReadOnly
        selected_file, _ = QFileDialog.getSaveFileName(
            self,
            translations[settings.value("appLanguage")]["save_as"]
            + f" — {app.applicationDisplayName()}",
            self.directory,
            fallbackValues["writeFilter"],
            options=options,
        )
        if selected_file:
            self.file_name = selected_file
            self.directory = os.path.dirname(self.file_name)
            self.saveFile()
            return True
        else:
            return False

    def saveFile(self):
        if not self.file_name:
            self.saveAs()
        else:
            automaticEncoding = RS_Workspace.RS_detectEncoding(self.file_name)
            if self.file_name.lower().endswith(".docx"):
                None
            else:
                with open(self.file_name, "w", encoding=automaticEncoding) as file:
                    if self.file_name.lower().endswith((".rsdoc", ".html", ".htm")):
                        file.write(self.rs_area.toHtml())
                    elif self.file_name.lower().endswith((".md")):
                        file.write(self.rs_area.toMarkdown())
                    else:
                        document = QTextDocument()
                        document.setPlainText(self.rs_area.toPlainText())
                        file.write(document.toPlainText())

        self.status_bar.showMessage("Saved.", 2000)
        self.is_saved = True
        self.RS_updateTitle()

    def print(self):
        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageOrientation(QPageLayout.Orientation.Portrait)
        printer.setPageMargins(QMargins(10, 10, 10, 10), QPageLayout.Millimeter)

        printer.setFullPage(True)
        printer.setDocName(self.file_name)

        preview_dialog = QPrintPreviewDialog(printer, self)
        preview_dialog.paintRequested.connect(self.rs_area.print_)
        preview_dialog.exec()

    def showAbout(self):
        self.about_window = RS_About()
        self.about_window.show()

    def align(self, alignment):
        self.rs_area.setAlignment(alignment)

    def bullet(self):
        cursor = self.rs_area.textCursor()
        cursor.beginEditBlock()
        selected_text = cursor.selectedText()
        char_format = cursor.charFormat()
        cursor.removeSelectedText()
        cursor.insertList(QTextListFormat.ListDisc)
        cursor.insertText(selected_text)
        new_cursor = self.rs_area.textCursor()
        new_cursor.movePosition(QTextCursor.PreviousBlock)
        new_cursor.mergeCharFormat(char_format)
        cursor.endEditBlock()

    def numbered(self):
        cursor = self.rs_area.textCursor()
        cursor.beginEditBlock()
        selected_text = cursor.selectedText()
        char_format = cursor.charFormat()
        cursor.removeSelectedText()
        cursor.insertList(QTextListFormat.ListDecimal)
        cursor.insertText(selected_text)
        new_cursor = self.rs_area.textCursor()
        new_cursor.movePosition(QTextCursor.PreviousBlock)
        new_cursor.mergeCharFormat(char_format)
        cursor.endEditBlock()

    def contentBold(self):
        font = self.rs_area.currentFont()
        font.setBold(not font.bold())
        self.rs_area.setCurrentFont(font)

    def contentItalic(self):
        font = self.rs_area.currentFont()
        font.setItalic(not font.italic())
        self.rs_area.setCurrentFont(font)

    def contentUnderline(self):
        font = self.rs_area.currentFont()
        font.setUnderline(not font.underline())
        self.rs_area.setCurrentFont(font)

    def contentColor(self):
        color = QColorDialog.getColor()
        self.rs_area.setTextColor(color)

    def contentBGColor(self):
        color = QColorDialog.getColor()
        self.rs_area.setTextBackgroundColor(color)

    def contentFont(self):
        font, ok = QFontDialog.getFont(self.rs_area.currentFont(), self)
        if ok:
            self.rs_area.setCurrentFont(font)

    def contentAddImage(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        selected_file, _ = QFileDialog.getOpenFileName(
            self, "Open", self.directory, fallbackValues["mediaFilter"], options=options
        )
        if selected_file:
            with open(selected_file, "rb") as file:
                data = file.read()
                data = base64.b64encode(data)
                data = data.decode("utf-8")
                self.rs_area.insertHtml(f'<img src="data:image/png;base64,{data}"/>')

    def inc_font(self):
        font = self.rs_area.currentFont()
        font.setPointSize(font.pointSize() + 1)
        self.rs_area.setCurrentFont(font)

    def dec_font(self):
        font = self.rs_area.currentFont()
        font.setPointSize(font.pointSize() - 1)
        self.rs_area.setCurrentFont(font)

    def find(self):
        settings = QSettings("berkaygediz", "RichSpan")
        self.find_dialog = QInputDialog(self)
        self.find_dialog.setInputMode(QInputDialog.TextInput)
        app_language = settings.value("appLanguage")
        self.find_dialog.setLabelText(translations[app_language]["find"])
        self.find_dialog.setWindowTitle(translations[app_language]["find"])
        self.find_dialog.setOkButtonText(translations[app_language]["find"])
        self.find_dialog.setCancelButtonText(translations[app_language]["cancel"])
        self.find_dialog.textValueSelected.connect(self.findText)
        self.find_dialog.show()

    def findText(self, text):
        self.rs_area.find(text)

    def replace(self):
        settings = QSettings("berkaygediz", "RichSpan")
        self.replace_dialog = QInputDialog(self)
        self.replace_dialog.setInputMode(QInputDialog.TextInput)
        self.replace_dialog.setLabelText(
            translations[settings.value("appLanguage")]["replace"]
        )
        self.replace_dialog.setWindowTitle(
            translations[settings.value("appLanguage")]["replace"]
        )
        self.replace_dialog.setOkButtonText(
            translations[settings.value("appLanguage")]["replace"]
        )
        self.replace_dialog.setCancelButtonText(
            translations[settings.value("appLanguage")]["cancel"]
        )
        self.replace_dialog.textValueSelected.connect(self.replaceText)
        self.replace_dialog.show()

    def replaceText(self, text):
        self.rs_area.find(text)
        self.rs_area.insertPlainText(text)


if __name__ == "__main__":
    if getattr(sys, "frozen", False):
        applicationPath = sys._MEIPASS
    elif __file__:
        applicationPath = os.path.dirname(__file__)
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(os.path.join(applicationPath, "richspan_icon.png")))
    app.setOrganizationName("berkaygediz")
    app.setApplicationName("RichSpan")
    app.setApplicationDisplayName("RichSpan 2024.08")
    app.setApplicationVersion("1.4.2024.08-1")
    ws = RS_Workspace()
    ws.show()
    sys.exit(app.exec())
