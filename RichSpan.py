import base64
import datetime
import locale
import mimetypes
import os
import sys

import chardet
import mammoth
import psutil
from langdetect import DetectorFactory, detect
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtOpenGL import *
from PySide6.QtOpenGLWidgets import *
from PySide6.QtPrintSupport import *
from PySide6.QtWidgets import *

from modules.globals import *
from modules.threading import *

try:
    from ctypes import windll

    windll.shell32.SetCurrentProcessExplicitAppUserModelID("berkaygediz.RichSpan.1.5")
except ImportError:
    pass

try:
    settings = QSettings("berkaygediz", "RichSpan")
    lang = settings.value("appLanguage")
except:
    pass


class RS_About(QMainWindow):
    def __init__(self, parent=None):
        super(RS_About, self).__init__(parent)
        self.setWindowFlags(Qt.Dialog)
        self.setWindowIcon(QIcon("richspan_icon.ico"))
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
            "Real-time computing and formatting supported word processor<br><br>"
            "Made by Berkay Gediz<br><br>"
            "GNU General Public License v3.0<br>GNU LESSER GENERAL PUBLIC LICENSE v3.0<br>Mozilla Public License Version 2.0<br><br><b>Libraries: </b>mwilliamson/python-mammoth, Mimino666/langdetect, PySide6, chardet, psutil<br><br>"
            "OpenGL: <b>ON</b></center>"
        )
        self.setCentralWidget(self.about_label)


class RS_Workspace(QMainWindow):
    def __init__(self, parent=None):
        super(RS_Workspace, self).__init__(parent)
        QTimer.singleShot(0, self.initUI)

    def initUI(self):
        starttime = datetime.datetime.now()
        self.setWindowIcon(QIcon("richspan_icon.ico"))
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setMinimumSize(768, 540)
        system_language = locale.getlocale()[1]
        settings = QSettings("berkaygediz", "RichSpan")
        if system_language not in languages.keys():
            settings.setValue("appLanguage", "1252")
            settings.sync()
        if settings.value("adaptiveResponse") == None:
            settings.setValue("adaptiveResponse", 1)
            settings.sync()

        centralWidget = QOpenGLWidget(self)

        layout = QVBoxLayout(centralWidget)
        self.hardwareAcceleration = QOpenGLWidget()
        layout.addWidget(self.hardwareAcceleration)
        self.setCentralWidget(centralWidget)

        self.richspan_thread = ThreadingEngine(
            adaptiveResponse=settings.value("adaptiveResponse")
        )
        self.richspan_thread.update.connect(self.updateStatistics)

        self.themePalette()
        self.selected_file = None
        self.file_name = None
        self.is_saved = None
        self.default_directory = QDir().homePath()
        self.directory = self.default_directory

        self.initDock()
        self.dock_widget.hide()

        self.status_bar = self.statusBar()
        self.DocumentArea = QTextEdit()
        self.initArea()
        layout.addWidget(self.DocumentArea)

        self.DocumentArea.setDisabled(True)
        self.initActions()
        self.initToolbar()
        self.adaptiveResponse = settings.value("adaptiveResponse")

        self.setPalette(self.light_theme)
        self.text_changed_timer = QTimer()
        self.text_changed_timer.setInterval(150 * self.adaptiveResponse)
        self.text_changed_timer.timeout.connect(self.threadStart)
        self.DocumentArea.textChanged.connect(self.textChanged)
        self.thread_running = False

        self.showMaximized()
        self.DocumentArea.setFocus()
        self.DocumentArea.setAcceptRichText(True)

        QTimer.singleShot(50 * self.adaptiveResponse, self.restoreTheme)
        QTimer.singleShot(150 * self.adaptiveResponse, self.restoreState)

        self.DocumentArea.setDisabled(False)
        self.updateTitle()

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
                translations[lang]["exit_message"],
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                self.saveState()
                event.accept()
            else:
                self.saveState()
                event.ignore()
        else:
            self.saveState()
            event.accept()

    def changeLanguage(self):
        settings = QSettings("berkaygediz", "RichSpan")
        settings.setValue("appLanguage", self.language_combobox.currentData())
        settings.sync()
        self.updateTitle()
        self.updateStatistics()
        self.toolbarTranslate()

    def updateTitle(self):
        settings = QSettings("berkaygediz", "RichSpan")
        file = self.file_name if self.file_name else translations[lang]["new"]
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

    def threadStart(self):
        if not self.thread_running:
            self.richspan_thread.start()
            self.thread_running = True

    def textChanged(self):
        if not self.text_changed_timer.isActive():
            self.text_changed_timer.start()

    def updateStatistics(self):
        self.text_changed_timer.stop()
        self.thread_running = False
        settings = QSettings("berkaygediz", "RichSpan")
        text = self.DocumentArea.toPlainText()
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
            statistics += f"<th>{translations[lang]['analysis']}</th>"
            avg_word_length = sum(len(word) for word in text.split()) / word_count
            formatted_avg_word_length = "{:.1f}".format(avg_word_length)
            statistics += f"<td>{translations[lang]['analysis_message_1'].format(formatted_avg_word_length)}</td>"
            avg_line_length = character_count / line_count - 1
            formatted_avg_line_length = "{:.1f}".format(avg_line_length)
            statistics += f"<td>{translations[lang]['analysis_message_2'].format(formatted_avg_line_length)}</td>"
            uppercase_count = sum(1 for char in text if char.isupper())
            lowercase_count = sum(1 for char in text if char.islower())
            statistics += f"<td>{translations[lang]['analysis_message_3'].format(uppercase_count)}</td>"
            statistics += f"<td>{translations[lang]['analysis_message_4'].format(lowercase_count)}</td>"
            if word_count > 20:
                try:
                    DetectorFactory.seed = 0
                    lang = detect(text)
                    statistics += f"<td>{translations[lang]['analysis_message_5'].format(lang)}</td>"
                except:
                    None

        else:
            self.DocumentArea.setFontFamily(fallbackValues["fontFamily"])
            self.DocumentArea.setFontPointSize(fallbackValues["fontSize"])
            self.DocumentArea.setFontWeight(75 if fallbackValues["bold"] else 50)
            self.DocumentArea.setFontItalic(fallbackValues["italic"])
            self.DocumentArea.setFontUnderline(fallbackValues["underline"])
            self.DocumentArea.setAlignment(fallbackValues["contentAlign"])
            self.DocumentArea.setTextColor(QColor(fallbackValues["contentColor"]))
            self.DocumentArea.setTextBackgroundColor(
                QColor(fallbackValues["contentBackgroundColor"])
            )
        statistics += f"<th>{translations[lang]['statistic']}</th>"
        statistics += (
            f"<td>{translations[lang]['statistic_message_1'].format(line_count)}</td>"
        )
        statistics += (
            f"<td>{translations[lang]['statistic_message_2'].format(word_count)}</td>"
        )
        statistics += f"<td>{translations[lang]['statistic_message_3'].format(character_count)}</td>"
        statistics += f"</td><th id='rs-text'>{app.applicationDisplayName()}</th>"
        statistics += "</tr></table></body></html>"

        self.statistics_label.setText(statistics)
        self.status_bar.addPermanentWidget(self.statistics_label)
        self.new_text = self.DocumentArea.toPlainText()
        if self.new_text != fallbackValues["content"]:
            self.is_saved = False
        else:
            self.is_saved = True
        self.updateTitle()

    def saveState(self):
        settings = QSettings("berkaygediz", "RichSpan")
        settings.setValue("windowScale", self.saveGeometry())
        settings.setValue("defaultDirectory", self.directory)
        settings.setValue("fileName", self.file_name)
        settings.setValue("content", self.DocumentArea.toHtml())
        settings.setValue("isSaved", self.is_saved)
        settings.setValue(
            "scrollPosition", self.DocumentArea.verticalScrollBar().value()
        )
        settings.setValue(
            "appTheme", "dark" if self.palette() == self.dark_theme else "light"
        )
        settings.setValue("appLanguage", self.language_combobox.currentData())
        settings.setValue("adaptiveResponse", self.adaptiveResponse)
        settings.sync()

    def restoreState(self):
        settings = QSettings("berkaygediz", "RichSpan")
        self.geometry = settings.value("windowScale")
        self.directory = settings.value("defaultDirectory", self.default_directory)
        self.file_name = settings.value("fileName")
        self.DocumentArea.setHtml(settings.value("content"))
        self.is_saved = settings.value("isSaved")
        index = self.language_combobox.findData(lang)
        self.language_combobox.setCurrentIndex(index)

        if self.geometry is not None:
            self.restoreGeometry(self.geometry)

        if self.file_name and os.path.exists(self.file_name):
            try:
                automaticEncoding = RS_Workspace.detectEncoding(self.file_name)
            except Exception as e:
                automaticEncoding = "utf-8"

            if self.file_name.endswith(".docx"):
                with open(
                    self.file_name,
                    "rb",
                ) as file:
                    try:
                        conversionLayer = mammoth.convert_to_html(file)
                        self.DocumentArea.setHtml(conversionLayer.value)
                    except:
                        None

            else:
                with open(self.file_name, "r", encoding=automaticEncoding) as file:
                    if self.file_name.endswith((".rsdoc")):
                        self.DocumentArea.setHtml(file.read())
                    elif self.file_name.endswith((".html", ".htm")):
                        self.DocumentArea.setHtml(file.read())

                    elif self.file_name.endswith((".md")):
                        self.DocumentArea.setMarkdown(file.read())
                    else:
                        self.DocumentArea.setPlainText(file.read())

        scroll_position = settings.value("scrollPosition")
        if scroll_position is not None:
            self.DocumentArea.verticalScrollBar().setValue(int(scroll_position))
        else:
            self.DocumentArea.verticalScrollBar().setValue(0)

        if self.file_name:
            self.is_saved = True
        else:
            self.is_saved = False

        self.adaptiveResponse = settings.value("adaptiveResponse")
        self.restoreTheme()
        self.updateTitle()

    def restoreTheme(self):
        settings = QSettings("berkaygediz", "RichSpan")
        if settings.value("appTheme") == "dark":
            self.setPalette(self.dark_theme)
        else:
            self.setPalette(self.light_theme)
        self.toolbarTheme()

    def themePalette(self):
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

    def themeAction(self):
        settings = QSettings("berkaygediz", "RichSpan")
        if self.palette() == self.light_theme:
            self.setPalette(self.dark_theme)
            settings.setValue("appTheme", "dark")
        else:
            self.setPalette(self.light_theme)
            settings.setValue("appTheme", "light")
        self.toolbarTheme()

    def toolbarTheme(self):
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

    def toolbarTranslate(self):
        settings = QSettings("berkaygediz", "RichSpan")
        self.newaction.setText(translations[lang]["new"])
        self.newaction.setStatusTip(translations[lang]["new_message"])
        self.openaction.setText(translations[lang]["open"])
        self.openaction.setStatusTip(translations[lang]["open_message"])
        self.saveaction.setText(translations[lang]["save"])
        self.saveaction.setStatusTip(translations[lang]["save_message"])
        self.saveasaction.setText(translations[lang]["save_as"])
        self.saveasaction.setStatusTip(translations[lang]["save_as_message"])
        self.printaction.setText(translations[lang]["print"])
        self.printaction.setStatusTip(translations[lang]["print_message"])
        self.undoaction.setText(translations[lang]["undo"])
        self.undoaction.setStatusTip(translations[lang]["undo_message"])
        self.redoaction.setText(translations[lang]["redo"])
        self.redoaction.setStatusTip(translations[lang]["redo_message"])
        self.theme_action.setText(translations[lang]["darklight"])
        self.theme_action.setStatusTip(translations[lang]["darklight_message"])
        self.powersaveraction.setText(translations[lang]["powersaver"])
        self.powersaveraction.setStatusTip(translations[lang]["powersaver_message"])
        self.hide_dock_widget_action.setText(f"{translations[lang]["help"]} && AI")
        self.hide_dock_widget_action.setStatusTip(translations[lang]["help_message"])
        self.findaction.setText(translations[lang]["find"])
        self.findaction.setStatusTip(translations[lang]["find_message"])
        self.replaceaction.setText(translations[lang]["replace"])
        self.replaceaction.setStatusTip(translations[lang]["replace_message"])
        self.aboutaction.setText(translations[lang]["about"])
        self.aboutaction.setStatusTip(translations[lang]["about"])
        self.alignrightevent.setText(translations[lang]["right"])
        self.alignrightevent.setStatusTip(translations[lang]["right_message"])
        self.aligncenterevent.setText(translations[lang]["center"])
        self.aligncenterevent.setStatusTip(translations[lang]["center_message"])
        self.alignleftevent.setText(translations[lang]["left"])
        self.alignleftevent.setStatusTip(translations[lang]["left_message"])
        self.alignjustifiedevent.setText(translations[lang]["justify"])
        self.alignjustifiedevent.setStatusTip(translations[lang]["justify_message"])
        self.bold.setText(translations[lang]["bold"])
        self.bold.setStatusTip(translations[lang]["bold_message"])
        self.italic.setText(translations[lang]["italic"])
        self.italic.setStatusTip(translations[lang]["italic_message"])
        self.underline.setText(translations[lang]["underline"])
        self.underline.setStatusTip(translations[lang]["underline_message"])
        self.bulletevent.setText(translations[lang]["bullet"])
        self.bulletevent.setStatusTip(translations[lang]["bullet"])
        self.numberedevent.setText(translations[lang]["numbered"])
        self.numberedevent.setStatusTip(translations[lang]["numbered"])
        self.color.setText(translations[lang]["font_color"])
        self.color.setStatusTip(translations[lang]["font_color_message"])
        self.backgroundcolor.setText(translations[lang]["contentBackgroundColor"])
        self.backgroundcolor.setStatusTip(
            translations[lang]["contentBackgroundColor_message"]
        )
        self.fontfamily.setText(translations[lang]["font"])
        self.fontfamily.setStatusTip(translations[lang]["font_message"])
        self.dock_widget.setWindowTitle(translations[lang]["help"] + " && AI")
        self.addimage.setText(translations[lang]["image"])
        self.addimage.setStatusTip(translations[lang]["image_message"])
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
            f"<th>{translations[lang]['help_shortcut']}</th>"
            f"<th>{translations[lang]['help_description']}</th>"
            f"</tr><tr><td>Ctrl+N</td><td>{translations[lang]['new_message']}</td></tr>"
            f"<tr><td>Ctrl+O</td><td>{translations[lang]['open_message']}</td></tr>"
            f"<tr><td>Ctrl+S</td><td>{translations[lang]['save_message']}</td></tr>"
            f"<tr><td>Ctrl+Shift+S</td><td>{translations[lang]['save_as_message']}</td></tr>"
            f"<tr><td>Ctrl+P</td><td>{translations[lang]['print_message']}</td></tr>"
            f"<tr><td>Ctrl+Z</td><td>{translations[lang]['undo_message']}</td></tr>"
            f"<tr><td>Ctrl+Y</td><td>{translations[lang]['redo_message']}</td></tr>"
            f"<tr><td>Ctrl+Shift+T</td><td>{translations[lang]['darklight_message']}</td></tr>"
            f"<tr><td>Ctrl+Shift+D</td><td>{translations[lang]['help_message']}</td></tr>"
            f"<tr><td>Ctrl+Shift+C</td><td>{translations[lang]['font_color_message']}</td></tr>"
            f"<tr><td>Ctrl+Shift+B</td><td>{translations[lang]['contentBackgroundColor_message']}</td></tr>"
            f"<tr><td>Ctrl+Shift+F</td><td>{translations[lang]['font_message']}</td></tr>"
            f"<tr><td>Ctrl++</td><td>{translations[lang]['inc_font_message']}</td></tr>"
            f"<tr><td>Ctrl+-</td><td>{translations[lang]['dec_font_message']}</td></tr>"
            f"<tr><td>Ctrl+Shift+P</td><td>{translations[lang]['image_message']}</td></tr>"
            f"<tr><td>Ctrl+F</td><td>{translations[lang]['find_message']}</td></tr>"
            f"<tr><td>Ctrl+H</td><td>{translations[lang]['replace_message']}</td></tr>"
            f"<tr><td>Ctrl+Shift+U</td><td>{translations[lang]['bullet']}</td></tr>"
            f"<tr><td>Ctrl+Shift+O</td><td>{translations[lang]['numbered']}</td></tr>"
            f"<tr><td>Ctrl+Shift+R</td><td>{translations[lang]['right']}</td></tr>"
            f"<tr><td>Ctrl+Shift+L</td><td>{translations[lang]['left']}</td></tr>"
            f"<tr><td>Ctrl+Shift+E</td><td>{translations[lang]['center']}</td></tr>"
            f"<tr><td>Ctrl+Shift+J</td><td>{translations[lang]['justify']}</td></tr>"
            "</table><center><p>NOTE: <b>AI</b> support planned.</p></center></body></html>"
        )

    def initArea(self):
        self.DocumentArea.setFontFamily(fallbackValues["fontFamily"])
        self.DocumentArea.setFontPointSize(fallbackValues["fontSize"])
        self.DocumentArea.setFontWeight(75 if fallbackValues["bold"] else 50)
        self.DocumentArea.setFontItalic(fallbackValues["italic"])
        self.DocumentArea.setFontUnderline(fallbackValues["underline"])
        self.DocumentArea.setAlignment(fallbackValues["contentAlign"])
        self.DocumentArea.setTextColor(QColor(fallbackValues["contentColor"]))
        self.DocumentArea.setTextBackgroundColor(
            QColor(fallbackValues["contentBackgroundColor"])
        )
        self.DocumentArea.setTabStopDistance(27)
        self.DocumentArea.document().setDocumentMargin(self.width() * 0.25)

    def initDock(self):
        lang = settings.value("appLanguage")
        self.dock_widget = QDockWidget(f"{translations[lang]["help"]} && AI", self)
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
            f"<th>{translations[lang]['help_shortcut']}</th>"
            f"<th>{translations[lang]['help_description']}</th>"
            f"</tr><tr><td>Ctrl+N</td><td>{translations[lang]['new_message']}</td></tr>"
            f"<tr><td>Ctrl+O</td><td>{translations[lang]['open_message']}</td></tr>"
            f"<tr><td>Ctrl+S</td><td>{translations[lang]['save_message']}</td></tr>"
            f"<tr><td>Ctrl+Shift+S</td><td>{translations[lang]['save_as_message']}</td></tr>"
            f"<tr><td>Ctrl+P</td><td>{translations[lang]['print_message']}</td></tr>"
            f"<tr><td>Ctrl+Z</td><td>{translations[lang]['undo_message']}</td></tr>"
            f"<tr><td>Ctrl+Y</td><td>{translations[lang]['redo_message']}</td></tr>"
            f"<tr><td>Ctrl+Shift+T</td><td>{translations[lang]['darklight_message']}</td></tr>"
            f"<tr><td>Ctrl+Shift+D</td><td>{translations[lang]['help_message']}</td></tr>"
            f"<tr><td>Ctrl+Shift+C</td><td>{translations[lang]['font_color_message']}</td></tr>"
            f"<tr><td>Ctrl+Shift+B</td><td>{translations[lang]['contentBackgroundColor_message']}</td></tr>"
            f"<tr><td>Ctrl+Shift+F</td><td>{translations[lang]['font_message']}</td></tr>"
            f"<tr><td>Ctrl++</td><td>{translations[lang]['inc_font_message']}</td></tr>"
            f"<tr><td>Ctrl+-</td><td>{translations[lang]['dec_font_message']}</td></tr>"
            f"<tr><td>Ctrl+Shift+P</td><td>{translations[lang]['image_message']}</td></tr>"
            f"<tr><td>Ctrl+F</td><td>{translations[lang]['find_message']}</td></tr>"
            f"<tr><td>Ctrl+H</td><td>{translations[lang]['replace_message']}</td></tr>"
            f"<tr><td>Ctrl+Shift+U</td><td>{translations[lang]['bullet']}</td></tr>"
            f"<tr><td>Ctrl+Shift+O</td><td>{translations[lang]['numbered']}</td></tr>"
            f"<tr><td>Ctrl+Shift+R</td><td>{translations[lang]['right']}</td></tr>"
            f"<tr><td>Ctrl+Shift+L</td><td>{translations[lang]['left']}</td></tr>"
            f"<tr><td>Ctrl+Shift+E</td><td>{translations[lang]['center']}</td></tr>"
            f"<tr><td>Ctrl+Shift+J</td><td>{translations[lang]['justify']}</td></tr>"
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

    def toolbarLabel(self, toolbar, text):
        label = QLabel(f"<b>{text}</b>")
        toolbar.addWidget(label)

    def createAction(self, text, status_tip, function, shortcut=None, icon=None):
        action = QAction(text, self)
        action.setStatusTip(status_tip)
        action.triggered.connect(function)
        if shortcut:
            action.setShortcut(shortcut)
        if icon:
            action.setIcon(QIcon(""))
        return action

    def initActions(self):
        settings = QSettings("berkaygediz", "RichSpan")
        self.newaction = self.createAction(
            translations[lang]["new"],
            translations[lang]["new_message"],
            self.New,
            QKeySequence.New,
            "",
        )
        self.openaction = self.createAction(
            translations[lang]["open"],
            translations[lang]["open_message"],
            self.Open,
            QKeySequence.Open,
            "",
        )
        self.saveaction = self.createAction(
            translations[lang]["save"],
            translations[lang]["save_message"],
            self.Save,
            QKeySequence.Save,
            "",
        )
        self.saveasaction = self.createAction(
            translations[lang]["save_as"],
            translations[lang]["save_as_message"],
            self.SaveAs,
            QKeySequence.SaveAs,
            "",
        )
        self.printaction = self.createAction(
            translations[lang]["print"],
            translations[lang]["print_message"],
            self.PrintDocument,
            QKeySequence.Print,
            "",
        )
        self.findaction = self.createAction(
            translations[lang]["find"],
            translations[lang]["find_message"],
            self.find,
            QKeySequence.Find,
            "",
        )
        self.replaceaction = self.createAction(
            translations[lang]["replace"],
            translations[lang]["replace_message"],
            self.replace,
            QKeySequence.Replace,
            "",
        )
        self.undoaction = self.createAction(
            translations[lang]["undo"],
            translations[lang]["undo_message"],
            self.DocumentArea.undo,
            QKeySequence.Undo,
            "",
        )
        self.redoaction = self.createAction(
            translations[lang]["redo"],
            translations[lang]["redo_message"],
            self.DocumentArea.redo,
            QKeySequence.Redo,
            "",
        )
        self.alignrightevent = self.createAction(
            translations[lang]["right"],
            translations[lang]["right_message"],
            lambda: self.Align(Qt.AlignRight),
        )
        self.alignleftevent = self.createAction(
            translations[lang]["left"],
            translations[lang]["left_message"],
            lambda: self.Align(Qt.AlignLeft),
        )
        self.aligncenterevent = self.createAction(
            translations[lang]["center"],
            translations[lang]["center_message"],
            lambda: self.Align(Qt.AlignCenter),
        )
        self.alignjustifiedevent = self.createAction(
            translations[lang]["justify"],
            translations[lang]["justify_message"],
            lambda: self.Align(Qt.AlignJustify),
        )
        self.bulletevent = self.createAction(
            translations[lang]["bullet"],
            "",
            self.Bullet,
            QKeySequence("Ctrl+Shift+U"),
            "",
        )
        self.numberedevent = self.createAction(
            translations[lang]["numbered"],
            "",
            self.Numbered,
            QKeySequence("Ctrl+Shift+O"),
            "",
        )
        self.bold = self.createAction(
            translations[lang]["bold"],
            translations[lang]["bold_message"],
            self.ContentBold,
            QKeySequence.Bold,
            "",
        )
        self.italic = self.createAction(
            translations[lang]["italic"],
            translations[lang]["italic_message"],
            self.ContentItalic,
            QKeySequence.Italic,
            "",
        )
        self.underline = self.createAction(
            translations[lang]["underline"],
            translations[lang]["underline_message"],
            self.ContentUnderline,
            QKeySequence.Underline,
            "",
        )
        self.color = self.createAction(
            translations[lang]["font_color"],
            translations[lang]["font_color_message"],
            self.ContentColor,
            QKeySequence("Ctrl+Shift+C"),
            "",
        )
        self.backgroundcolor = self.createAction(
            translations[lang]["contentBackgroundColor"],
            translations[lang]["contentBackgroundColor_message"],
            self.ContentBGColor,
            QKeySequence("Ctrl+Shift+B"),
            "",
        )
        self.fontfamily = self.createAction(
            translations[lang]["font"],
            translations[lang]["font_message"],
            self.ContentFont,
            QKeySequence("Ctrl+Shift+F"),
            "",
        )
        self.inc_fontaction = self.createAction(
            "A+",
            translations[lang]["inc_font_message"],
            self.incFont,
            QKeySequence("Ctrl++"),
        )
        self.dec_fontaction = self.createAction(
            "A-",
            translations[lang]["dec_font_message"],
            self.decFont,
            QKeySequence("Ctrl+-"),
        )
        self.addimage = self.createAction(
            translations[lang]["image"],
            translations[lang]["image_message"],
            self.addImage,
            QKeySequence("Ctrl+Shift+P"),
            "",
        )
        self.aboutaction = self.createAction(
            translations[lang]["about"],
            "",
            self.viewAbout,
            QKeySequence("Ctrl+Shift+I"),
            "",
        )

    def initToolbar(self):
        settings = QSettings("berkaygediz", "RichSpan")
        self.toolbar = self.addToolBar(translations[lang]["file"])
        self.toolbarLabel(
            self.toolbar,
            translations[lang]["file"] + ": ",
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

        self.toolbar = self.addToolBar(translations[lang]["ui"])
        self.toolbarLabel(self.toolbar, translations[lang]["ui"] + ": ")
        self.theme_action = self.createAction(
            translations[lang]["darklight"],
            translations[lang]["darklight_message"],
            self.themeAction,
            QKeySequence("Ctrl+Shift+T"),
            "",
        )
        self.theme_action.setCheckable(True)
        self.theme_action.setChecked(settings.value("appTheme") == "dark")

        self.toolbar.addAction(self.theme_action)
        self.powersaveraction = QAction(
            translations[lang]["powersaver"],
            self,
            checkable=True,
        )
        self.powersaveraction.setStatusTip(translations[lang]["powersaver_message"])
        self.powersaveraction.toggled.connect(self.hybridSaver)

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
        self.hide_dock_widget_action = self.createAction(
            translations[lang]["help"] + " && AI",
            translations[lang]["help_message"],
            self.toggleDock,
            QKeySequence("Ctrl+Shift+D"),
            "",
        )
        self.toolbar.addAction(self.hide_dock_widget_action)
        self.toolbar.addAction(self.aboutaction)
        self.language_combobox = QComboBox(self)
        self.language_combobox.setStyleSheet("background-color:#000000; color:#FFFFFF;")
        for lcid, name in languages.items():
            self.language_combobox.addItem(name, lcid)

        self.language_combobox.currentIndexChanged.connect(self.changeLanguage)
        self.toolbar.addWidget(self.language_combobox)

        self.addToolBarBreak()

        self.toolbar = self.addToolBar(translations[lang]["edit"])
        self.toolbarLabel(
            self.toolbar,
            translations[lang]["edit"] + ": ",
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
        self.toolbarLabel(
            self.toolbar,
            translations[lang]["font"] + ": ",
        )
        self.toolbar.addActions([self.bold, self.italic, self.underline])
        self.toolbar.addSeparator()
        self.toolbar = self.addToolBar(translations[lang]["list"])
        self.toolbarLabel(
            self.toolbar,
            translations[lang]["list"] + ": ",
        )
        self.toolbar.addActions([self.bulletevent, self.numberedevent])
        self.addToolBarBreak()

        self.toolbar = self.addToolBar(translations[lang]["color"])
        self.toolbarLabel(
            self.toolbar,
            translations[lang]["color"] + ": ",
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

        self.toolbar = self.addToolBar(translations[lang]["multimedia"])
        self.toolbarLabel(
            self.toolbar,
            translations[lang]["multimedia"] + ": ",
        )
        self.toolbar.addActions([self.addimage])

    def toggleDock(self):
        if self.dock_widget.isHidden():
            self.dock_widget.show()
        else:
            self.dock_widget.hide()

    def hybridSaver(self, checked):
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

    def detectEncoding(file_path):
        with open(file_path, "rb") as file:
            detector = chardet.universaldetector.UniversalDetector()
            for line in file:
                detector.feed(line)
                if detector.done:
                    break
            detector.close()
        return detector.result["encoding"]

    def New(self):
        settings = QSettings("berkaygediz", "RichSpan")
        if self.is_saved == True:
            self.DocumentArea.clear()
            self.DocumentArea.setFontFamily(fallbackValues["fontFamily"])
            self.DocumentArea.setFontPointSize(fallbackValues["fontSize"])
            self.DocumentArea.setFontWeight(75 if fallbackValues["bold"] else 50)
            self.DocumentArea.setFontItalic(fallbackValues["italic"])
            self.DocumentArea.setFontUnderline(fallbackValues["underline"])
            self.DocumentArea.setAlignment(fallbackValues["contentAlign"])
            self.DocumentArea.setTextColor(QColor(fallbackValues["contentColor"]))
            self.DocumentArea.setTextBackgroundColor(
                QColor(fallbackValues["contentBackgroundColor"])
            )
            self.DocumentArea.setTabStopDistance(27)
            self.directory = self.default_directory
            self.file_name = None
            self.is_saved = False
            self.updateTitle()
        else:
            reply = QMessageBox.question(
                self,
                f"{app.applicationDisplayName()}",
                translations[lang]["new_message"],
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                self.DocumentArea.clear()
                self.DocumentArea.setFontFamily(fallbackValues["fontFamily"])
                self.DocumentArea.setFontPointSize(fallbackValues["fontSize"])
                self.DocumentArea.setFontWeight(75 if fallbackValues["bold"] else 50)
                self.DocumentArea.setFontItalic(fallbackValues["italic"])
                self.DocumentArea.setFontUnderline(fallbackValues["underline"])
                self.DocumentArea.setAlignment(fallbackValues["contentAlign"])
                self.DocumentArea.setTextColor(QColor(fallbackValues["contentColor"]))
                self.DocumentArea.setTextBackgroundColor(
                    QColor(fallbackValues["contentBackgroundColor"])
                )
                self.DocumentArea.setTabStopDistance(27)
                self.directory = self.default_directory
                self.file_name = None
                self.is_saved = False
                self.updateTitle()
            else:
                pass

    def Open(self):
        options = QFileDialog.Options()
        settings = QSettings("berkaygediz", "RichSpan")
        options |= QFileDialog.ReadOnly
        selected_file, _ = QFileDialog.getOpenFileName(
            self,
            translations[lang]["open"] + f" — {app.applicationDisplayName()} ",
            self.directory,
            fallbackValues["readFilter"],
            options=options,
        )
        if selected_file:
            self.file_name = selected_file
            try:
                automaticEncoding = RS_Workspace.detectEncoding(self.selected_file)
            except Exception as e:
                automaticEncoding = "utf-8"
            if self.file_name.endswith(".docx"):
                with open(
                    self.file_name,
                    "rb",
                ) as file:
                    try:
                        conversionLayer = mammoth.convert_to_html(file)
                        self.DocumentArea.setHtml(conversionLayer.value)
                    except:
                        QMessageBox.warning(self, None, "Conversion failed.")
            else:
                with open(self.file_name, "r", encoding=automaticEncoding) as file:
                    if self.file_name.endswith((".rsdoc")):
                        self.DocumentArea.setHtml(file.read())
                    elif self.file_name.endswith((".html", ".htm")):
                        self.DocumentArea.setHtml(file.read())

                    elif self.file_name.endswith((".md")):
                        self.DocumentArea.setMarkdown(file.read())
                    else:
                        self.DocumentArea.setPlainText(file.read())

            self.directory = os.path.dirname(self.file_name)
            self.is_saved = True
            self.updateTitle()
        else:
            pass

    def Save(self):
        if self.is_saved == False:
            self.SaveProcess()
        elif self.file_name == None:
            self.SaveAs()
        else:
            self.SaveProcess()

    def SaveAs(self):
        options = QFileDialog.Options()
        settings = QSettings("berkaygediz", "RichSpan")
        options |= QFileDialog.ReadOnly
        selected_file, _ = QFileDialog.getSaveFileName(
            self,
            translations[lang]["save_as"] + f" — {app.applicationDisplayName()}",
            self.directory,
            fallbackValues["writeFilter"],
            options=options,
        )
        if selected_file:
            self.file_name = selected_file
            self.directory = os.path.dirname(self.file_name)
            self.SaveProcess()
            return True
        else:
            return False

    def SaveProcess(self):
        if not self.file_name:
            self.SaveAs()
        else:
            try:
                automaticEncoding = RS_Workspace.detectEncoding(self.file_name)
            except Exception as e:
                automaticEncoding = "utf-8"
            if self.file_name.lower().endswith(".docx"):
                None
            else:
                with open(self.file_name, "w", encoding=automaticEncoding) as file:
                    if self.file_name.lower().endswith((".rsdoc", ".html", ".htm")):
                        file.write(self.DocumentArea.toHtml())
                    elif self.file_name.lower().endswith((".md")):
                        file.write(self.DocumentArea.toMarkdown())
                    else:
                        document = QTextDocument()
                        document.setPlainText(self.DocumentArea.toPlainText())
                        file.write(document.toPlainText())

        self.status_bar.showMessage("Saved.", 2000)
        self.is_saved = True
        self.updateTitle()

    def PrintDocument(self):
        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageOrientation(QPageLayout.Orientation.Portrait)
        printer.setPageMargins(QMargins(10, 10, 10, 10), QPageLayout.Millimeter)

        printer.setFullPage(True)
        printer.setDocName(self.file_name)

        preview_dialog = QPrintPreviewDialog(printer, self)
        preview_dialog.paintRequested.connect(self.DocumentArea.print_)
        preview_dialog.exec()

    def addImage(self):
        settings = QSettings("berkaygediz", "RichSpan")
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        selected_file, _ = QFileDialog.getOpenFileName(
            self,
            translations[lang]["open"],
            self.directory,
            fallbackValues["mediaFilter"],
            options=options,
        )
        if selected_file:
            mime_type, _ = mimetypes.guess_type(selected_file)
            if mime_type is None:
                mime_type = "image/png"

            with open(selected_file, "rb") as file:
                data = file.read()
                data = base64.b64encode(data).decode("utf-8")
                img_tag = f'<img src="data:{mime_type};base64,{data}"/>'
                self.DocumentArea.insertHtml(img_tag)

    def viewAbout(self):
        self.about_window = RS_About()
        self.about_window.show()

    def Align(self, alignment):
        self.DocumentArea.setAlignment(alignment)

    def Bullet(self):
        cursor = self.DocumentArea.textCursor()
        cursor.beginEditBlock()
        selected_text = cursor.selectedText()
        char_format = cursor.charFormat()
        cursor.removeSelectedText()
        cursor.insertList(QTextListFormat.ListDisc)
        cursor.insertText(selected_text)
        new_cursor = self.DocumentArea.textCursor()
        new_cursor.movePosition(QTextCursor.PreviousBlock)
        new_cursor.mergeCharFormat(char_format)
        cursor.endEditBlock()

    def Numbered(self):
        cursor = self.DocumentArea.textCursor()
        cursor.beginEditBlock()
        selected_text = cursor.selectedText()
        char_format = cursor.charFormat()
        cursor.removeSelectedText()
        cursor.insertList(QTextListFormat.ListDecimal)
        cursor.insertText(selected_text)
        new_cursor = self.DocumentArea.textCursor()
        new_cursor.movePosition(QTextCursor.PreviousBlock)
        new_cursor.mergeCharFormat(char_format)
        cursor.endEditBlock()

    def ContentBold(self):
        font = self.DocumentArea.currentFont()
        font.setBold(not font.bold())
        self.DocumentArea.setCurrentFont(font)

    def ContentItalic(self):
        font = self.DocumentArea.currentFont()
        font.setItalic(not font.italic())
        self.DocumentArea.setCurrentFont(font)

    def ContentUnderline(self):
        font = self.DocumentArea.currentFont()
        font.setUnderline(not font.underline())
        self.DocumentArea.setCurrentFont(font)

    def ContentColor(self):
        color = QColorDialog.getColor()
        self.DocumentArea.setTextColor(color)

    def ContentBGColor(self):
        color = QColorDialog.getColor()
        self.DocumentArea.setTextBackgroundColor(color)

    def ContentFont(self):
        font, ok = QFontDialog.getFont(self.DocumentArea.currentFont(), self)
        if ok:
            self.DocumentArea.setCurrentFont(font)

    def incFont(self):
        font = self.DocumentArea.currentFont()
        font.setPointSize(font.pointSize() + 1)
        self.DocumentArea.setCurrentFont(font)

    def decFont(self):
        font = self.DocumentArea.currentFont()
        font.setPointSize(font.pointSize() - 1)
        self.DocumentArea.setCurrentFont(font)

    def find(self):
        settings = QSettings("berkaygediz", "RichSpan")
        self.find_dialog = QInputDialog(self)
        self.find_dialog.setInputMode(QInputDialog.TextInput)
        app_language = lang
        self.find_dialog.setLabelText(translations[app_language]["find"])
        self.find_dialog.setWindowTitle(translations[app_language]["find"])
        self.find_dialog.setOkButtonText(translations[app_language]["find"])
        self.find_dialog.setCancelButtonText(translations[app_language]["cancel"])
        self.find_dialog.textValueSelected.connect(self.findText)
        self.find_dialog.show()

    def findText(self, text):
        self.DocumentArea.find(text)

    def replace(self):
        settings = QSettings("berkaygediz", "RichSpan")
        self.replace_dialog = QInputDialog(self)
        self.replace_dialog.setInputMode(QInputDialog.TextInput)
        self.replace_dialog.setLabelText(translations[lang]["replace"])
        self.replace_dialog.setWindowTitle(translations[lang]["replace"])
        self.replace_dialog.setOkButtonText(translations[lang]["replace"])
        self.replace_dialog.setCancelButtonText(translations[lang]["cancel"])
        self.replace_dialog.textValueSelected.connect(self.replaceText)
        self.replace_dialog.show()

    def replaceText(self, text):
        self.DocumentArea.find(text)
        self.DocumentArea.insertPlainText(text)


if __name__ == "__main__":
    if getattr(sys, "frozen", False):
        applicationPath = sys._MEIPASS
    elif __file__:
        applicationPath = os.path.dirname(__file__)
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(os.path.join(applicationPath, "richspan_icon.ico")))
    app.setOrganizationName("berkaygediz")
    app.setApplicationName("RichSpan")
    app.setApplicationDisplayName("RichSpan 2024.11")
    app.setApplicationVersion("1.5.2024.11-1")
    ws = RS_Workspace()
    ws.show()
    sys.exit(app.exec())
