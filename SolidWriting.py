import base64
import datetime
import locale
import mimetypes
import os
import re
import sys

import chardet
import mammoth
import psutil
import torch
from langdetect import DetectorFactory, detect
from llama_cpp import Llama
from PySide6.QtCore import (QDir, QMargins, QSettings, QSize, QSizeF, QThread,
                            QTimer, QUrl, Signal)
from PySide6.QtGui import (QAction, QColor, QDesktopServices, QFont,
                           QGuiApplication, QIcon, QKeySequence, QPageLayout,
                           QPalette, Qt, QTextCharFormat, QTextCursor,
                           QTextDocument, QTextListFormat, QTransform)
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtPrintSupport import QPrinter, QPrintPreviewDialog
from PySide6.QtWidgets import (QApplication, QColorDialog, QComboBox, QDialog,
                               QFileDialog, QFontDialog, QGraphicsScene,
                               QGraphicsView, QHBoxLayout, QInputDialog,
                               QLabel, QLineEdit, QMainWindow, QMenu,
                               QMessageBox, QPushButton, QScrollArea, QStyle,
                               QTextBrowser, QTextEdit, QToolBar, QVBoxLayout,
                               QWidget, QWidgetAction)

from modules.crypto import CryptoEngine
from modules.globals import fallbackValues, languages, translations
from modules.threading import ThreadingEngine

try:
    from ctypes import windll

    windll.shell32.SetCurrentProcessExplicitAppUserModelID(
        "berkaygediz.SolidWriting.1.5"
    )
except ImportError:
    pass

try:
    settings = QSettings("berkaygediz", "SolidWriting")
    lang = settings.value("appLanguage", "1252")
except:
    pass


class SW_LLMThread(QThread):
    result = Signal(str)

    def __init__(self, prompt, llm, parent=None):
        super(SW_LLMThread, self).__init__(parent)
        self.prompt = prompt
        self.llm = llm

    def run(self):
        response = self.getResponseLLM()
        self.result.emit(response)

    def getResponseLLM(self):
        try:
            response = self.llm.create_chat_completion(
                messages=[{"role": "user", "content": self.prompt}]
            )
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Error: {str(e)}"


class SW_ControlInfo(QMainWindow):
    def __init__(self, parent=None):
        super(SW_ControlInfo, self).__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowIcon(QIcon(fallbackValues["icon"]))
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

        screen = QGuiApplication.primaryScreen().availableGeometry()
        self.setGeometry(
            QStyle.alignedRect(
                Qt.LayoutDirection.LeftToRight,
                Qt.AlignmentFlag.AlignCenter,
                QSize(int(screen.width() * 0.2), int(screen.height() * 0.2)),
                screen,
            )
        )
        self.setStyleSheet("background-color: transparent;")
        self.setWindowOpacity(0.75)

        self.widget_central = QWidget(self)
        self.layout_central = QVBoxLayout(self.widget_central)

        self.title = QLabel("SolidWriting", self)
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setFont(QFont("Roboto", 30))
        self.title.setStyleSheet(
            "background-color: #0D47A1; color: #FFFFFF; font-weight: bold; font-size: 30px; border-radius: 25px; border: 1px solid #021E56;"
        )

        self.layout_central.addWidget(self.title)
        self.setCentralWidget(self.widget_central)

        QTimer.singleShot(500, self.showWS)

    def showWS(self):
        self.hide()
        self.ws_window = SW_Workspace()
        self.ws_window.show()


class SW_About(QMainWindow):
    def __init__(self, parent=None):
        super(SW_About, self).__init__(parent)
        self.setWindowFlags(Qt.Dialog)
        self.setWindowIcon(QIcon(fallbackValues["icon"]))
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setGeometry(
            QStyle.alignedRect(
                Qt.LeftToRight,
                Qt.AlignCenter,
                self.size(),
                QApplication.primaryScreen().availableGeometry(),
            )
        )
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        self.about_label = QLabel()
        self.about_label.setWordWrap(True)
        self.about_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.about_label.setTextFormat(Qt.RichText)
        self.about_label.setText(
            "<center>"
            f"<b>{app.applicationDisplayName()}</b><br><br>"
            "A supercharged word processor with AI integration, supporting real-time computing and advanced formatting.<br><br>"
            "Made by Berkay Gediz<br><br>"
            "GNU General Public License v3.0<br>GNU LESSER GENERAL PUBLIC LICENSE v3.0<br>Mozilla Public License Version 2.0<br><br>"
            "<b>Libraries: </b>mwilliamson/python-mammoth, Mimino666/langdetect, abetlen/llama-cpp-python, <br>"
            "pytorch/pytorch, PySide6, chardet, psutil<br><br>"
            "OpenGL: <b>ON</b>"
            "</center>"
        )
        main_layout.addWidget(self.about_label)

        button_layout = QHBoxLayout()

        self.donate_github = QPushButton("GitHub Sponsors")
        self.donate_github.clicked.connect(lambda: self.donationLink("github"))
        button_layout.addWidget(self.donate_github)

        self.donate_buymeacoffee = QPushButton("Buy Me a Coffee")
        self.donate_buymeacoffee.clicked.connect(
            lambda: self.donationLink("buymeacoffee")
        )
        button_layout.addWidget(self.donate_buymeacoffee)

        main_layout.addLayout(button_layout)

    def donationLink(self, origin):
        if origin == "github":
            QDesktopServices.openUrl(QUrl("https://github.com/sponsors/berkaygediz"))
        elif origin == "buymeacoffee":
            QDesktopServices.openUrl(QUrl("https://buymeacoffee.com/berkaygediz"))


class SW_Help(QMainWindow):
    def __init__(self, parent=None):
        super(SW_Help, self).__init__(parent)
        self.setWindowFlags(Qt.Dialog)
        self.setWindowIcon(QIcon(fallbackValues["icon"]))
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setMinimumSize(540, 460)

        self.setGeometry(
            QStyle.alignedRect(
                Qt.LeftToRight,
                Qt.AlignCenter,
                self.size(),
                QApplication.primaryScreen().availableGeometry(),
            )
        )

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        main_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 20, 0, 0)

        self.help_label = QLabel()
        self.help_label.setWordWrap(True)
        self.help_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.help_label.setTextFormat(Qt.RichText)
        lang = settings.value("appLanguage", "1252")
        self.help_label.setText(
            "<html><head><style>"
            "table {border-collapse: collapse; width: 80%; margin: auto;}"
            "th, td {text-align: left; padding: 8px;}"
            "tr:nth-child(even) {background-color: #f2f2f2;}"
            "tr:hover {background-color: #ddd;}"
            "th {background-color: #0D47A1; color: white;}"
            "body {text-align: center;}"
            "</style></head><body>"
            "<h1>Help</h1>"
            "<table><tr><th>Shortcut</th><th>Function</th></tr>"
            f"<tr><td>Ctrl+N</td><td>{translations[lang]['new_message']}</td></tr>"
            f"<tr><td>Ctrl+O</td><td>{translations[lang]['open_message']}</td></tr>"
            f"<tr><td>Ctrl+S</td><td>{translations[lang]['save_message']}</td></tr>"
            f"<tr><td>Ctrl+Shift+S</td><td>{translations[lang]['save_as_message']}</td></tr>"
            f"<tr><td>Ctrl+P</td><td>{translations[lang]['print_message']}</td></tr>"
            f"<tr><td>Ctrl+Z</td><td>{translations[lang]['undo_message']}</td></tr>"
            f"<tr><td>Ctrl+Y</td><td>{translations[lang]['redo_message']}</td></tr>"
            f"<tr><td>Ctrl+X</td><td>Cut</td></tr>"
            f"<tr><td>Ctrl+C</td><td>Copy</td></tr>"
            f"<tr><td>Ctrl+V</td><td>Paste</td></tr>"
            f"<tr><td>Ctrl+F</td><td>{translations[lang]['find_message']}</td></tr>"
            f"<tr><td>Ctrl+H</td><td>{translations[lang]['replace_message']}</td></tr>"
            f"<tr><td>Ctrl+L</td><td>{translations[lang]['left_message']}</td></tr>"
            f"<tr><td>Ctrl+E</td><td>{translations[lang]['center_message']}</td></tr>"
            f"<tr><td>Ctrl+R</td><td>{translations[lang]['right_message']}</td></tr>"
            f"<tr><td>Ctrl+J</td><td>{translations[lang]['justify_message']}</td></tr>"
            f"<tr><td>Ctrl+Shift+U</td><td>{translations[lang]['bullet']}</td></tr>"
            f"<tr><td>Ctrl+Shift+O</td><td>{translations[lang]['numbered']}</td></tr>"
            f"<tr><td>Ctrl+B</td><td>{translations[lang]['bold_message']}</td></tr>"
            f"<tr><td>Ctrl+I</td><td>{translations[lang]['italic_message']}</td></tr>"
            f"<tr><td>Ctrl+U</td><td>{translations[lang]['underline_message']}</td></tr>"
            f"<tr><td>Ctrl+Shift+F</td><td>{translations[lang]['font_message']}</td></tr>"
            f"<tr><td>Ctrl+Shift+C</td><td>{translations[lang]['font_color_message']}</td></tr>"
            f"<tr><td>Ctrl+Shift+G</td><td>{translations[lang]['contentBackgroundColor_message']}</td></tr>"
            f"<tr><td>Ctrl++</td><td>{translations[lang]['inc_font_message']}</td></tr>"
            f"<tr><td>Ctrl+-</td><td>{translations[lang]['dec_font_message']}</td></tr>"
            f"<tr><td>Ctrl+Shift+=</td><td>Superscript</td></tr>"
            f"<tr><td>Ctrl+=</td><td>Subscript</td></tr>"
            f"<tr><td>Ctrl+Shift+I</td><td>{translations[lang]['image_message']}</td></tr>"
            f"<tr><td>Ctrl+T</td><td>Insert Table</td></tr>"
            f"<tr><td>Ctrl+Scroll</td><td>Zoom In/Out</td></tr>"
            f"<tr><td>F1</td><td>{translations[lang]['help_message']}</td></tr>"
            f"<tr><td>Ctrl+Shift+A</td><td>{translations[lang]['about']}</td></tr>"
            "</table></body></html>"
        )

        layout.addWidget(self.help_label)
        main_widget.setLayout(layout)
        scroll_area.setWidget(main_widget)

        self.setCentralWidget(scroll_area)


class SW_Workspace(QMainWindow):
    def __init__(self, parent=None):
        super(SW_Workspace, self).__init__(parent)
        QTimer.singleShot(0, self.initUI)

    def initUI(self):
        starttime = datetime.datetime.now()
        self.setWindowIcon(QIcon(fallbackValues["icon"]))
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setMinimumSize(1010, 620)
        system_language = locale.getlocale()[1]
        if (
            system_language not in languages.items()
            or settings.value("appLanguage") not in languages.items()
            or settings.value("appLanguage") is None
        ):
            settings.setValue("appLanguage", "1252")
        if settings.value("adaptiveResponse") == None:
            settings.setValue("adaptiveResponse", 1)

        settings.sync()
        centralWidget = QOpenGLWidget(self)

        layout = QVBoxLayout(centralWidget)
        self.hardwareAcceleration = QOpenGLWidget()
        layout.addWidget(self.hardwareAcceleration)
        self.setCentralWidget(centralWidget)

        self.solidwriting_thread = ThreadingEngine(
            adaptiveResponse=settings.value("adaptiveResponse")
        )
        self.solidwriting_thread.update.connect(self.updateStatistics)

        self.themePalette()
        self.selected_file = None
        self.file_name = None
        self.is_saved = None
        self.default_directory = QDir().homePath()
        self.directory = self.default_directory
        self.llm = None
        self.hardwareCore = self.acceleratorHardware()

        self.LLMinitBar()
        self.ai_widget.hide()

        self.status_bar = self.statusBar()

        self.graphicsView = QGraphicsView(self)
        self.graphicsScene = QGraphicsScene(self.graphicsView)
        self.graphicsView.setScene(self.graphicsScene)
        self.graphicsView.setDragMode(QGraphicsView.ScrollHandDrag)
        self.graphicsView.setRenderHints(self.graphicsView.renderHints())
        self.graphicsView.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.graphicsView.setResizeAnchor(QGraphicsView.AnchorUnderMouse)

        self.DocumentArea = QTextBrowser()
        self.DocumentArea.setReadOnly(True)
        self.DocumentArea.setUndoRedoEnabled(True)
        self.DocumentArea.setOpenExternalLinks(True)
        self.DocumentArea.setContextMenuPolicy(Qt.CustomContextMenu)
        self.DocumentArea.anchorClicked.connect(self.handleHyperlink)
        self.DocumentArea.customContextMenuRequested.connect(self.showContextMenu)

        proxy = self.graphicsScene.addWidget(self.DocumentArea)

        self.graphicsView.wheelEvent = self.wheelEventGraphicsView

        self.initArea()
        layout.addWidget(self.graphicsView)

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
        load_llm = settings.value("load_llm")
        if load_llm is True or load_llm is None:
            if self.hardwareCore == "cpu":
                self.LLMwarningCPU()

    def wheelEventGraphicsView(self, event):
        if event.modifiers() == Qt.ControlModifier:
            zoom_in_factor = 1.25
            zoom_out_factor = 1 / zoom_in_factor
            current_transform = self.graphicsView.transform()
            current_scale = current_transform.m11()
            if event.angleDelta().y() > 0:
                new_scale = current_scale * zoom_in_factor
            else:
                new_scale = current_scale * zoom_out_factor
            new_scale = max(0.25, min(new_scale, 5.0))
            self.graphicsView.setTransform(QTransform().scale(new_scale, new_scale))
            event.accept()
            closest_zoom = min(
                [25, 50, 75, 100, 125, 150, 175, 200, 250, 300, 400, 500],
                key=lambda x: abs(x / 100.0 - new_scale),
            )
            self.zoom_level_combobox.blockSignals(True)
            self.zoom_level_combobox.setCurrentText(f"{closest_zoom}%")
            self.zoom_level_combobox.blockSignals(False)
            settings.setValue("zoomLevel", closest_zoom)
        else:
            event.ignore()

    def showContextMenu(self, pos):
        lang = settings.value("appLanguage", "1252")
        selected_text = self.DocumentArea.textCursor().selectedText().strip()
        text_length = len(selected_text)

        show_ai = self.llm is not None and self.llm != ""

        self.context_menu = QMenu(self)

        if text_length == 0 and not self.DocumentArea.isReadOnly():
            cut_action = QAction("Cut", self)
            cut_action.triggered.connect(self.DocumentArea.cut)
            self.context_menu.addAction(cut_action)

            copy_action = QAction("Copy", self)
            copy_action.triggered.connect(self.DocumentArea.copy)
            self.context_menu.addAction(copy_action)

            paste_action = QAction("Paste", self)
            paste_action.triggered.connect(self.DocumentArea.paste)
            self.context_menu.addAction(paste_action)

            delete_action = QAction("Delete", self)
            delete_action.triggered.connect(
                lambda: self.DocumentArea.textCursor().removeSelectedText()
            )
            self.context_menu.addAction(delete_action)

            undo_action = QAction(translations[lang]["undo"], self)
            undo_action.triggered.connect(self.DocumentArea.undo)
            self.context_menu.addAction(undo_action)

            redo_action = QAction(translations[lang]["redo"], self)
            redo_action.triggered.connect(self.DocumentArea.redo)
            self.context_menu.addAction(redo_action)

            image_action = QAction(translations[lang]["image"], self)
            image_action.triggered.connect(self.addImage)
            self.context_menu.addAction(image_action)

        if text_length > 0 and not self.DocumentArea.isReadOnly():
            format_action = QAction("Format", self)
            format_action.setEnabled(False)
            self.context_menu.addAction(format_action)
            self.context_menu.addSeparator()

            format_actions = [
                {
                    "name": "bold",
                    "text": translations[lang]["bold"],
                    "function": self.contentBold,
                },
                {
                    "name": "italic",
                    "text": translations[lang]["italic"],
                    "function": self.contentItalic,
                },
                {
                    "name": "underline",
                    "text": translations[lang]["underline"],
                    "function": self.contentUnderline,
                },
                {
                    "name": "color",
                    "text": translations[lang]["font_color"],
                    "function": self.contentColor,
                },
                {
                    "name": "backgroundcolor",
                    "text": translations[lang]["contentBackgroundColor"],
                    "function": self.contentBGColor,
                },
                {
                    "name": "fontfamily",
                    "text": translations[lang]["font"],
                    "function": self.contentFont,
                },
            ]

            for action in format_actions:
                action_item = QAction(action["text"], self)
                action_item.triggered.connect(action["function"])
                self.context_menu.addAction(action_item)

        if text_length > 0 and show_ai:
            self.context_menu.addSeparator()
            widget_action = QWidgetAction(self)

            label_widget = QLabel("AI")
            label_widget.setStyleSheet(
                """
                font-weight: bold;
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1, 
                                        stop: 0 #6A7F8C, stop: 0.7 #8A9DAD, stop: 1 #1C3D5C); 
                color: black;
                border: 1px solid white;
                border-radius: 10px;
                padding: 5px;
            """
            )

            widget_action.setDefaultWidget(label_widget)

            self.context_menu.addAction(widget_action)
            self.context_menu.addSeparator()

            if text_length < 50:
                self.context_menu.addAction(
                    f"Selected ({text_length})",
                    lambda: self.LLMcontextPredict(""),
                )
                self.context_menu.addAction(
                    "Clarify", lambda: self.LLMcontextPredict("clarify")
                )
            elif 50 <= text_length < 200:
                self.context_menu.addAction(
                    f"Selected ({text_length})",
                    lambda: self.LLMcontextPredict("selected"),
                )
                self.context_menu.addAction(
                    "Summary", lambda: self.LLMcontextPredict("summary")
                )
                self.context_menu.addAction(
                    "Suggestions", lambda: self.LLMcontextPredict("suggestions")
                )
            else:
                self.context_menu.addAction(
                    f"Selected ({text_length})",
                    lambda: self.LLMcontextPredict("selected"),
                )
                self.context_menu.addAction(
                    "Summary", lambda: self.LLMcontextPredict("summary")
                )
                self.context_menu.addAction(
                    "Suggestions", lambda: self.LLMcontextPredict("suggestions")
                )
                self.context_menu.addAction(
                    "Clarify", lambda: self.LLMcontextPredict("clarify")
                )
        elif text_length > 0 and self.DocumentArea.isReadOnly() and show_ai:
            self.context_menu.addSeparator()
            widget_action = QWidgetAction(self)

            label_widget = QLabel("AI")
            label_widget.setStyleSheet(
                """
                font-weight: bold;
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1, 
                                        stop: 0 #6A7F8C, stop: 0.7 #8A9DAD, stop: 1 #1C3D5C); 
                color: black;
                border: 1px solid white;
                border-radius: 10px;
                padding: 5px;
            """
            )

            widget_action.setDefaultWidget(label_widget)

            self.context_menu.addAction(widget_action)
            self.context_menu.addSeparator()

            if text_length < 50:
                self.context_menu.addAction(
                    f"Selected ({text_length})",
                    lambda: self.LLMcontextPredict(""),
                )
                self.context_menu.addAction(
                    "Clarify", lambda: self.LLMcontextPredict("clarify")
                )
            elif 50 <= text_length < 200:
                self.context_menu.addAction(
                    f"Selected ({text_length})",
                    lambda: self.LLMcontextPredict(""),
                )
                self.context_menu.addAction(
                    "Summary", lambda: self.LLMcontextPredict("summary")
                )
                self.context_menu.addAction(
                    "Suggestions", lambda: self.LLMcontextPredict("suggestions")
                )
            else:
                self.context_menu.addAction(
                    f"Selected ({text_length})",
                    lambda: self.LLMcontextPredict(""),
                )
                self.context_menu.addAction(
                    "Summary", lambda: self.LLMcontextPredict("summary")
                )
                self.context_menu.addAction(
                    "Suggestions", lambda: self.LLMcontextPredict("suggestions")
                )
                self.context_menu.addAction(
                    "Clarify", lambda: self.LLMcontextPredict("clarify")
                )

        if self.context_menu.actions():
            self.context_menu.exec(self.DocumentArea.mapToGlobal(pos))

    def closeEvent(self, event):
        lang = settings.value("appLanguage", "1252")
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

    def languageFallbackIndex(self):
        if self.language_combobox.currentIndex() == -1:
            selected_language = settings.value("appLanguage", 1252)
            if selected_language:
                index = self.language_combobox.findData(selected_language)
                if index != -1:
                    self.language_combobox.setCurrentIndex(index)
                else:
                    self.language_combobox.setCurrentIndex(0)
            else:
                self.language_combobox.setCurrentIndex(0)

    def changeLanguage(self):
        settings.setValue("appLanguage", self.language_combobox.currentData())
        settings.sync()
        self.languageFallbackIndex()
        self.toolbarTranslate()
        self.updateStatistics()
        self.updateTitle()

    def updateTitle(self):
        lang = settings.value("appLanguage", "1252")

        file = self.file_name if self.file_name else translations[lang]["new"]
        textMode = ""
        if file.endswith(".docx"):
            if self.DocumentArea.isReadOnly():
                textMode = translations[lang]["readonly"]
        elif self.DocumentArea.isReadOnly():
            textMode = translations[lang]["readonly"]

        if len(textMode) == 0:
            asterisk = "*" if not self.is_saved else ""
        else:
            asterisk = ""

        self.setWindowTitle(
            f"{file}{asterisk}{textMode} — {app.applicationDisplayName()}"
        )

    def threadStart(self):
        if not self.thread_running:
            self.solidwriting_thread.start()
            self.thread_running = True

    def textChanged(self):
        if not self.text_changed_timer.isActive():
            self.text_changed_timer.start()

    def updateStatistics(self):
        self.text_changed_timer.stop()
        self.thread_running = False
        text = self.DocumentArea.toPlainText()

        character_count = len(text)
        word_count = len(text.split())
        line_count = text.count("\n") + 1

        avg_word_length = avg_line_length = uppercase_count = lowercase_count = None
        detected_language = None
        lang = settings.value("appLanguage", "1252")

        if word_count > 0 and line_count > 0 and character_count > 0 and text != "":
            avg_word_length = sum(len(word) for word in text.split()) / word_count
            formatted_avg_word_length = "{:.1f}".format(avg_word_length)

            avg_line_length = (character_count / line_count) - 1
            formatted_avg_line_length = "{:.1f}".format(avg_line_length)

            uppercase_count = sum(1 for char in text if char.isupper())
            lowercase_count = sum(1 for char in text if char.islower())

            if word_count > 20:
                try:
                    DetectorFactory.seed = 0
                    detected_language = detect(text)
                except Exception:
                    detected_language = None

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

        if avg_word_length is not None:
            statistics += f"<th>{translations[lang]['analysis']}</th>"
            statistics += f"<td>{translations[lang]['analysis_message_1'].format(formatted_avg_word_length)}</td>"
            statistics += f"<td>{translations[lang]['analysis_message_2'].format(formatted_avg_line_length)}</td>"
            statistics += f"<td>{translations[lang]['analysis_message_3'].format(uppercase_count)}</td>"
            statistics += f"<td>{translations[lang]['analysis_message_4'].format(lowercase_count)}</td>"
            if detected_language:
                statistics += f"<td>{translations[lang]['analysis_message_5'].format(detected_language)}</td>"

        else:
            self.resetDocumentArea()

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
        encryption = CryptoEngine("SolidWriting")
        encrypted_content = encryption.b64_encrypt(self.DocumentArea.toHtml())

        settings.setValue("windowScale", self.saveGeometry())
        settings.setValue("defaultDirectory", self.directory)
        settings.setValue("fileName", self.file_name)
        settings.setValue("content", encrypted_content)
        settings.setValue("isSaved", self.is_saved)
        settings.setValue(
            "scrollPosition", self.DocumentArea.verticalScrollBar().value()
        )
        settings.setValue(
            "appTheme", "dark" if self.palette() == self.dark_theme else "light"
        )
        settings.setValue("appLanguage", self.language_combobox.currentData())
        settings.setValue("adaptiveResponse", self.adaptiveResponse)
        settings.setValue("zoomLevel", self.zoom_level_combobox.currentText())
        settings.sync()

    def restoreState(self):
        encryption = CryptoEngine("SolidWriting")
        encrypted_content = settings.value("content")

        geometry = settings.value("windowScale")
        self.directory = settings.value("defaultDirectory", self.default_directory)

        if encrypted_content:
            decrypted_content = encryption.b64_decrypt(encrypted_content)
            self.DocumentArea.setHtml(decrypted_content)

        self.is_saved = settings.value("isSaved")
        index = self.language_combobox.findData(lang)
        self.language_combobox.setCurrentIndex(index)

        if geometry:
            self.restoreGeometry(geometry)

        if len(sys.argv) > 1:
            file_to_open = os.path.abspath(sys.argv[1])
            if os.path.exists(file_to_open):
                self.file_name = file_to_open
            else:
                QMessageBox.warning(
                    self, "File Not Found", f"The file '{file_to_open}' does not exist."
                )
                return
        else:
            self.file_name = settings.value("fileName")

        if self.file_name and os.path.exists(self.file_name):
            self.openFile(self.file_name)

        scroll_position = settings.value("scrollPosition")
        if scroll_position is not None:
            self.DocumentArea.verticalScrollBar().setValue(int(scroll_position))
        else:
            self.DocumentArea.verticalScrollBar().setValue(0)

        self.is_saved = bool(self.file_name)

        self.adaptiveResponse = settings.value("adaptiveResponse")
        zoom = settings.value("zoomLevel", 100)
        if isinstance(zoom, str):
            zoom_value = int(zoom.replace("%", ""))
        else:
            zoom_value = zoom

        self.zoom_level_combobox.setCurrentText(f"{zoom_value}%")

        self.zoom_level_combobox.setCurrentText(f"{zoom_value}%")
        self.restoreTheme()
        self.updateTitle()

    def restoreTheme(self):
        if settings.value("appTheme") == "dark":
            self.setPalette(self.dark_theme)
            self.DocumentArea.setStyleSheet("background-color:#50557a; color: #ffffff;")
            self.graphicsView.setStyleSheet("background-color:#000000;")
        else:
            self.setPalette(self.light_theme)
            self.DocumentArea.setStyleSheet("background-color:#ffffff; color: #000000;")
            self.graphicsView.setStyleSheet("background-color:#FDF4DC;")
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
        if self.palette() == self.light_theme:
            self.setPalette(self.dark_theme)
            self.DocumentArea.setStyleSheet("background-color:#50557a; color: #ffffff;")
            self.graphicsView.setStyleSheet("background-color:#000000;")
            settings.setValue("appTheme", "dark")
        else:
            self.setPalette(self.light_theme)
            self.DocumentArea.setStyleSheet("background-color:#ffffff; color: #000000;")
            self.graphicsView.setStyleSheet("background-color:#FDF4DC;")
            settings.setValue("appTheme", "light")
        self.toolbarTheme()

    def toolbarTheme(self):
        palette = self.palette()
        if palette == self.light_theme:
            text_color = QColor(0, 0, 0)
            toolbar_bg = "#F0F0F0"
            button_bg = "#FFFFFF"
            button_hover = "#D0D0D0"
            button_checked = "#ADD8E6"
            button_disabled = "#E0E0E0"
        else:
            text_color = QColor(255, 255, 255)
            toolbar_bg = "#2C2F38"
            button_bg = "#3A3F48"
            button_hover = "#5C6370"
            button_checked = "#0000AF"
            button_disabled = "#555555"

        for toolbar in self.findChildren(QToolBar):
            toolbar.setStyleSheet(
                f"""
                QToolBar {{
                    background-color: {toolbar_bg};
                    border: none;
                    padding: 1px;
                }}
                
                QLabel {{
                    color: {text_color.name()};
                }}
                
                QToolButton {{
                    background-color: {button_bg}; 
                    color: {text_color.name()};
                    border: 1px solid #444;
                    border-radius: 5px;
                    margin: 1px;
                    font-size: 14px;
                    font-weight: bold;
                }}
                
                QToolButton:hover {{
                    background-color: {button_hover};
                    border: 1px solid {button_bg};
                }}
                
                QToolButton:checked {{
                    background-color: {button_checked};
                    border: 1px solid {button_bg};
                }}

                QToolButton:disabled {{
                    background-color: {button_disabled};
                    color: #777;
                    border: 1px solid #444;
                }}
                """
            )

            for action in toolbar.actions():
                if action.text():
                    action_color = QPalette()
                    action_color.setColor(QPalette.ButtonText, text_color)
                    action_color.setColor(QPalette.WindowText, text_color)
                    toolbar.setPalette(action_color)

    def toolbarTranslate(self):
        self.languageFallbackIndex()
        lang = settings.value("appLanguage", "1252")

        actions = {
            self.newaction: ("new", "new_message"),
            self.openaction: ("open", "open_message"),
            self.saveaction: ("save", "save_message"),
            self.saveasaction: ("save_as", "save_as_message"),
            self.printaction: ("print", "print_message"),
            self.undoaction: ("undo", "undo_message"),
            self.redoaction: ("redo", "redo_message"),
            self.theme_action: ("darklight", "darklight_message"),
            self.powersaveraction: ("powersaver", "powersaver_message"),
            self.findaction: ("find", "find_message"),
            self.replaceaction: ("replace", "replace_message"),
            self.helpAction: ("help", "help"),
            self.aboutAction: ("about", "about"),
            self.alignrightevent: ("right", "right_message"),
            self.aligncenterevent: ("center", "center_message"),
            self.alignleftevent: ("left", "left_message"),
            self.alignjustifiedevent: ("justify", "justify_message"),
            self.bold: ("bold", "bold_message"),
            self.italic: ("italic", "italic_message"),
            self.underline: ("underline", "underline_message"),
            self.bulletevent: ("bullet", "bullet"),
            self.numberedevent: (
                "numbered",
                "numbered",
            ),
            self.color: ("font_color", "font_color_message"),
            self.backgroundcolor: (
                "contentBackgroundColor",
                "contentBackgroundColor_message",
            ),
            self.fontfamily: ("font", "font_message"),
            self.addImageAction: ("image", "image_message"),
        }

        for action, (text_key, status_key) in actions.items():
            action.setText(translations[lang][text_key])
            action.setStatusTip(translations[lang][status_key])

        self.translateToolbarLabel(self.file_toolbar, translations[lang]["file"])
        self.translateToolbarLabel(self.ui_toolbar, translations[lang]["ui"])
        self.translateToolbarLabel(self.edit_toolbar, translations[lang]["edit"])
        self.translateToolbarLabel(self.font_toolbar, translations[lang]["font"])
        self.translateToolbarLabel(self.list_toolbar, translations[lang]["list"])
        self.translateToolbarLabel(self.color_toolbar, translations[lang]["color"])
        self.translateToolbarLabel(
            self.multimedia_toolbar, translations[lang]["multimedia"]
        )

    def translateToolbarLabel(self, toolbar, label_key):
        lang = settings.value("appLanguage", "1252")
        self.updateToolbarLabel(
            toolbar, translations[lang].get(label_key, label_key) + ": "
        )

    def updateToolbarLabel(self, toolbar, new_label):
        for widget in toolbar.children():
            if isinstance(widget, QLabel):
                widget.setText(f"<b>{new_label}</b>")
                return

    def initArea(self):
        textDocument = self.DocumentArea.document()
        pageWidth = 24 * 28.35
        pageHeight = 29.7 * 28.35

        textDocument.setPageSize(QSizeF(pageWidth, pageHeight))
        textDocument.setDocumentMargin(2 * 28.35)
        self.DocumentArea.setFixedSize(pageWidth, pageHeight)

        self.resetDocumentArea()

    def loadLLM(self):
        if settings.value("load_llm") == None or settings.value("load_llm") == "true":
            reply = QMessageBox.question(
                None,
                "Load LLM",
                "Do you want to load the LLM model?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )

            if reply == QMessageBox.Yes:
                self._load_model()
                settings.setValue("load_llm", True)

            else:
                pass
        else:
            settings.setValue("load_llm", False)

    def _load_model(self):
        try:
            model_filename, _ = QFileDialog.getOpenFileName(
                None,
                "Select GGUF Model File",
                "",
                "GGUF files (*.gguf)",
            )

            if not model_filename:
                return

            current_directory = os.getcwd()
            model_path = os.path.join(current_directory, model_filename)

            if os.path.exists(model_path):
                if torch.accelerator.is_available() == False:
                    # max_memory = torch.cuda.get_device_properties(0).total_memory / (
                    #     1024**2
                    # )  # x MB VRAM
                    max_memory = 8192
                else:
                    available_memory = psutil.virtual_memory().available
                    max_memory = min(available_memory, 4 * 1024 * 1024 * 1024) / (
                        1024**2
                    )  # 4096 MB

                self.llm = Llama(
                    model_path,
                    n_gpu_layers=-1,
                    offload_kqv=True,
                    flash_attn=True,
                    seed=0,
                    n_threads=4,
                    max_memory=max_memory,
                    device_map="auto",
                    verbose=True,
                )

            else:
                self.llm = None
        except TypeError as e:
            print(f"Error: {str(e)}")
        except Exception as e:
            print(f"{str(e)}")

    def acceleratorHardware(self):
        if torch.cuda.is_available():  # NVIDIA
            QTimer.singleShot(500, self.loadLLM)
            return "cuda"
        elif torch.is_vulkan_available():
            QTimer.singleShot(500, self.loadLLM)
            return "vulkan"
        elif torch.backends.mps.is_available():  # Metal API
            QTimer.singleShot(500, self.loadLLM)
            return "mps"
        elif hasattr(torch.backends, "rocm"):  # AMD
            QTimer.singleShot(500, self.loadLLM)
            return "rocm"
        else:  # CPU
            return "cpu"

    def LLMwarningCPU(self):
        message = (
            "Your device does not have GPU support. Running intensive AI operations on the CPU "
            "may result in high CPU utilization, causing system performance degradation and potential "
            "long-term damage. This could lead to overheating, system instability, or permanent hardware damage. "
            "By proceeding with CPU usage, you acknowledge and accept the risks associated with these operations. "
            "Do you still wish to continue?"
        )

        reply = QMessageBox.question(
            self,
            None,
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            QTimer.singleShot(500, self.loadLLM)

        if reply == QMessageBox.No:
            settings.setValue("load_llm", False)

    def LLMinitBar(self):
        self.statistics_label = QLabel()

        self.ai_widget = QWidget(self)
        self.ai_widget.setObjectName("AI")
        self.ai_widget.setContentsMargins(0, 0, 65, 42)
        screen_height = 515

        self.ai_widget.setMinimumHeight(screen_height)
        self.ai_widget.setMaximumHeight(screen_height)

        ai_widget_width = 500
        self.ai_widget.setMinimumWidth(ai_widget_width)
        self.ai_widget.setMaximumWidth(ai_widget_width)

        self.ai_widget.hide()

        main_layout = QVBoxLayout()

        self.ai_label = QLabel("AI")
        self.ai_label.setStyleSheet(
            "text-align:center; font-weight: bold; color: white; background-color:#666666;"
        )

        self.hide_button = QPushButton("_")
        self.hide_button.setStyleSheet(
            "color: white; font-size: 24px; font-weight: bold; background-color: transparent;"
        )
        self.hide_button.setFixedSize(36, 36)
        self.hide_button.clicked.connect(self.hideAIWidget)

        label_layout = QHBoxLayout()
        label_layout.addWidget(self.ai_label)
        label_layout.addWidget(self.hide_button)

        main_layout.addLayout(label_layout)

        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("...")
        self.input_text.setFixedHeight(80)
        main_layout.addWidget(self.input_text)

        self.predict_button = QPushButton("->")
        self.predict_button.clicked.connect(self.LLMpredict)
        palette = self.palette()

        if palette == self.light_theme:
            text_color = QColor(0, 0, 0)
            button_bg = "#FFFFFF"
            button_hover = "#D0D0D0"
            button_checked = "#ADD8E6"
            button_disabled = "#E0E0E0"
        else:
            text_color = QColor(255, 255, 255)
            button_bg = "#3A3F48"
            button_hover = "#5C6370"
            button_checked = "#0000AF"
            button_disabled = "#555555"

        self.predict_button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {button_bg}; 
                color: {text_color.name()};
                border: 1px solid #444;
                border-radius: 5px;
                margin: 1px;
                font-size: 14px;
                font-weight: bold;
            }}
            
            QPushButton:hover {{
                background-color: {button_hover};
                border: 1px solid {button_bg};
            }}
            
            QPushButton:checked {{
                background-color: {button_checked};
                border: 1px solid {button_bg};
            }}

            QPushButton:disabled {{
                background-color: {button_disabled};
                color: #777;
                border: 1px solid #444;
            }}
            """
        )
        main_layout.addWidget(self.predict_button)

        self.clear_button = QPushButton("DEL")
        self.clear_button.setStyleSheet(
            "background-color: red; color: white; font-weight: bold; border-radius: 5px;"
        )
        self.clear_button.clicked.connect(self.clearMessages)
        main_layout.addWidget(self.clear_button)

        self.scrollableArea = QScrollArea()
        self.scrollableArea.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scrollableArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scrollableArea.setWidgetResizable(True)

        self.messages_layout = QVBoxLayout()

        scroll_contents = QWidget()
        scroll_contents.setLayout(self.messages_layout)
        self.scrollableArea.setWidget(scroll_contents)

        main_layout.addWidget(self.scrollableArea)

        container = QWidget(self.ai_widget)
        container.setLayout(main_layout)
        container.setStyleSheet(
            "background-color: #2f2f2f; border-top-left-radius: 15px; border-top-right-radius: 15px; padding: 5px;"
        )

        self.ai_widget.setLayout(QVBoxLayout())
        self.ai_widget.layout().addWidget(container)

        self.ai_widget.setStyleSheet("background-color: transparent;")
        self.scrollableArea.setStyleSheet("background-color:#000000; color:white;")

    def hideAIWidget(self):
        self.ai_widget.setVisible(False)

    def clearMessages(self):
        for i in range(self.messages_layout.count()):
            widget = self.messages_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

    def LLMmessage(self, text, is_user=True, typing_speed=25):
        DetectorFactory.seed = 0

        language = ""

        if len(text) > 30:
            language = detect(text)

        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        text = text.replace("\n", "<br>")
        text = self.LLMconvertMarkdownHTML(text)

        message_widget = QWidget()
        message_layout = QHBoxLayout()

        if language:
            message_label_content = f"{text}<br><br>({current_time} - {language})"
        else:
            message_label_content = f"{text}<br><br>({current_time})"

        message_label = QLabel(message_label_content)
        message_label.setWordWrap(True)
        message_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        message_label.setTextFormat(Qt.RichText)

        max_width = 400
        message_label.setMaximumWidth(max_width)

        if is_user:
            message_label.setStyleSheet(
                "background-color: #d1e7ff; color: #000; border-radius: 15px; padding: 10px; margin: 5px;"
            )
            message_layout.addWidget(message_label, alignment=Qt.AlignRight)
        else:
            message_label.setStyleSheet(
                "background-color: #f1f1f1; color: #000; border-radius: 15px; padding: 10px; margin: 5px;"
            )
            message_layout.addWidget(message_label, alignment=Qt.AlignLeft)

        message_widget.setLayout(message_layout)

        self.messages_layout.addWidget(message_widget)

        if not is_user:
            self.LLMdynamicMessage(
                message_label, text, typing_speed * self.adaptiveResponse
            )

        if is_user:
            self.full_text = ""

    def LLMdynamicMessage(self, message_label, text, typing_speed):
        words = text.split()

        if not hasattr(self, "full_text"):
            self.full_text = ""

        word_index = 0

        def type_next_word():
            nonlocal word_index
            if word_index < len(words):
                self.full_text += words[word_index] + " "
                message_label.setText(self.full_text)
                word_index += 1
            else:
                self.LLMmessageDatetime(message_label)
                self.typing_timer.stop()

        self.typing_timer = QTimer(self)
        self.typing_timer.timeout.connect(type_next_word)
        self.typing_timer.start(typing_speed)

    def LLMmessageDatetime(self, message_label):
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        language = (
            detect(message_label.text()) if len(message_label.text()) > 30 else ""
        )

        if language:
            new_text = f"{message_label.text()}<br><br>({current_time} - {language})"
        else:
            new_text = f"{message_label.text()}<br><br>({current_time})"

        message_label.setText(new_text)

    def LLMpredict(self):
        prompt = self.input_text.toPlainText().strip()

        if not prompt:
            self.LLMmessage("Please enter a question.", is_user=False)
            return

        self.LLMmessage(prompt, is_user=True)
        self.predict_button.setText("...")
        self.predict_button.setEnabled(False)

        self.llm_thread = SW_LLMThread(prompt, self.llm)
        self.llm_thread.result.connect(self.LLMhandleResponse)
        self.llm_thread.start()

    def LLMhandleResponse(self, response):
        self.LLMmessage(response, is_user=False)
        self.input_text.clear()
        self.predict_button.setText("->")
        self.predict_button.setEnabled(True)

    def LLMcontextPredict(self, action_type):
        selected_text = self.DocumentArea.textCursor().selectedText().strip()

        if action_type:
            prompt = f"{action_type}: {selected_text}"
        else:
            prompt = selected_text

        self.ai_widget.show()
        self.updateAiWidgetPosition()
        self.LLMmessage(prompt, is_user=True)
        self.predict_button.setText("...")
        self.predict_button.setEnabled(False)

        if not selected_text:
            self.LLMmessage("No text selected.", is_user=False)
            return

        self.llm_thread = SW_LLMThread(prompt, self.llm)
        self.llm_thread.result.connect(self.LLMhandleResponse)
        self.llm_thread.start()

    def LLMprompt(self, prompt):
        if prompt:
            response = self.LLMresponse(prompt)
            self.LLMmessage(response, is_user=False)
            self.input_text.clear()
        else:
            self.LLMmessage("Please enter a question.", is_user=False)

        self.predict_button.setText("->")
        self.predict_button.setEnabled(True)

    def LLMresponse(self, prompt):
        try:
            response = self.llm.create_chat_completion(
                messages=[{"role": "user", "content": prompt}]
            )
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            return str(e)

    def LLMconvertMarkdownHTML(self, markdown_text):
        markdown_text = self.LLMconvertCodeHTML(markdown_text)
        markdown_text = self.convertBoldItalic(markdown_text)
        return markdown_text

    def convertBoldItalic(self, text):
        text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)  # **bold**
        text = re.sub(r"__(.*?)__", r"<b>\1</b>", text)  # __bold__
        text = re.sub(r"\*(.*?)\*", r"<i>\1</i>", text)  # *italic*
        text = re.sub(r"_(.*?)_", r"<i>\1</i>", text)  # _italic_
        return text

    def LLMconvertCodeHTML(self, text):
        def replace_code_block(match):
            code = match.group(1).strip()
            return f"<pre><code>{self.LLMescapeHTML(code)}</code></pre>"

        return re.sub(r"```(.*?)```", replace_code_block, text, flags=re.DOTALL)

    def LLMescapeHTML(self, text):
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#039;")
        )

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

    def toggleReadOnly(self):
        current_state = self.DocumentArea.isReadOnly()
        self.DocumentArea.setReadOnly(not current_state)

        self.updateFormattingButtons()
        self.updateTitle()

    def updateFormattingButtons(self):
        if self.DocumentArea.isReadOnly():
            self.toggleFormattingActions(False)
        else:
            self.toggleFormattingActions(True)

    def toggleFormattingActions(self, enable):
        for toolbar in [
            self.font_toolbar,
            self.edit_toolbar,
            self.list_toolbar,
            self.color_toolbar,
            self.multimedia_toolbar,
        ]:
            for action in toolbar.actions():
                action.setEnabled(enable)

    def initActions(self):
        lang = settings.value("appLanguage", "1252")
        action_definitions = [
            {
                "name": "newaction",
                "text": translations[lang]["new"],
                "status_tip": translations[lang]["new_message"],
                "function": self.newFile,
                "shortcut": QKeySequence.New,
            },
            {
                "name": "openaction",
                "text": translations[lang]["open"],
                "status_tip": translations[lang]["open_message"],
                "function": self.openFile,
                "shortcut": QKeySequence.Open,
            },
            {
                "name": "saveaction",
                "text": translations[lang]["save"],
                "status_tip": translations[lang]["save_message"],
                "function": self.saveFile,
                "shortcut": QKeySequence.Save,
            },
            {
                "name": "saveasaction",
                "text": translations[lang]["save_as"],
                "status_tip": translations[lang]["save_as_message"],
                "function": self.saveAs,
                "shortcut": QKeySequence.SaveAs,
            },
            {
                "name": "printaction",
                "text": translations[lang]["print"],
                "status_tip": translations[lang]["print_message"],
                "function": self.printDocument,
                "shortcut": QKeySequence.Print,
            },
            {
                "name": "undoaction",
                "text": translations[lang]["undo"],
                "status_tip": translations[lang]["undo_message"],
                "function": self.DocumentArea.undo,
                "shortcut": QKeySequence.Undo,
            },
            {
                "name": "redoaction",
                "text": translations[lang]["redo"],
                "status_tip": translations[lang]["redo_message"],
                "function": self.DocumentArea.redo,
                "shortcut": QKeySequence.Redo,
            },
            {
                "name": "cutaction",
                "text": "Cut",
                "status_tip": "Cut",
                "function": self.DocumentArea.cut,
                "shortcut": QKeySequence.Cut,
            },
            {
                "name": "copyaction",
                "text": "Copy",
                "status_tip": "Copy",
                "function": self.DocumentArea.copy,
                "shortcut": QKeySequence.Copy,
            },
            {
                "name": "pasteaction",
                "text": "Paste",
                "status_tip": "Paste",
                "function": self.DocumentArea.paste,
                "shortcut": QKeySequence.Paste,
            },
            {
                "name": "findaction",
                "text": translations[lang]["find"],
                "status_tip": translations[lang]["find_message"],
                "function": self.find,
                "shortcut": QKeySequence.Find,
            },
            {
                "name": "replaceaction",
                "text": translations[lang]["replace"],
                "status_tip": translations[lang]["replace_message"],
                "function": self.replace,
                "shortcut": QKeySequence.Replace,
            },
            {
                "name": "alignleftevent",
                "text": translations[lang]["left"],
                "status_tip": translations[lang]["left_message"],
                "function": lambda: self.contentAlign(Qt.AlignLeft),
                "shortcut": QKeySequence("Ctrl+L"),
            },
            {
                "name": "aligncenterevent",
                "text": translations[lang]["center"],
                "status_tip": translations[lang]["center_message"],
                "function": lambda: self.contentAlign(Qt.AlignCenter),
                "shortcut": QKeySequence("Ctrl+E"),
            },
            {
                "name": "alignrightevent",
                "text": translations[lang]["right"],
                "status_tip": translations[lang]["right_message"],
                "function": lambda: self.contentAlign(Qt.AlignRight),
                "shortcut": QKeySequence("Ctrl+R"),
            },
            {
                "name": "alignjustifiedevent",
                "text": translations[lang]["justify"],
                "status_tip": translations[lang]["justify_message"],
                "function": lambda: self.contentAlign(Qt.AlignJustify),
                "shortcut": QKeySequence("Ctrl+J"),
            },
            {
                "name": "bulletevent",
                "text": translations[lang]["bullet"],
                "status_tip": "",
                "function": self.bulletList,
                "shortcut": QKeySequence("Ctrl+Shift+U"),
            },
            {
                "name": "numberedevent",
                "text": translations[lang]["numbered"],
                "status_tip": "",
                "function": self.numberedList,
                "shortcut": QKeySequence("Ctrl+Shift+O"),
            },
            {
                "name": "bold",
                "text": translations[lang]["bold"],
                "status_tip": translations[lang]["bold_message"],
                "function": self.contentBold,
                "shortcut": QKeySequence.Bold,
            },
            {
                "name": "italic",
                "text": translations[lang]["italic"],
                "status_tip": translations[lang]["italic_message"],
                "function": self.contentItalic,
                "shortcut": QKeySequence.Italic,
            },
            {
                "name": "underline",
                "text": translations[lang]["underline"],
                "status_tip": translations[lang]["underline_message"],
                "function": self.contentUnderline,
                "shortcut": QKeySequence.Underline,
            },
            {
                "name": "fontfamily",
                "text": translations[lang]["font"],
                "status_tip": translations[lang]["font_message"],
                "function": self.contentFont,
                "shortcut": QKeySequence("Ctrl+Shift+F"),
            },
            {
                "name": "color",
                "text": translations[lang]["font_color"],
                "status_tip": translations[lang]["font_color_message"],
                "function": self.contentColor,
                "shortcut": QKeySequence("Ctrl+Shift+C"),
            },
            {
                "name": "backgroundcolor",
                "text": translations[lang]["contentBackgroundColor"],
                "status_tip": translations[lang]["contentBackgroundColor_message"],
                "function": self.contentBGColor,
                "shortcut": QKeySequence("Ctrl+Shift+G"),
            },
            {
                "name": "inc_fontaction",
                "text": "A+",
                "status_tip": translations[lang]["inc_font_message"],
                "function": self.incFont,
                "shortcut": QKeySequence("Ctrl++"),
            },
            {
                "name": "dec_fontaction",
                "text": "A-",
                "status_tip": translations[lang]["dec_font_message"],
                "function": self.decFont,
                "shortcut": QKeySequence("Ctrl+-"),
            },
            {
                "name": "superscript",
                "text": "x²",
                "status_tip": "Superscript",
                "function": self.contentSuperscript,
                "shortcut": QKeySequence("Ctrl+Shift+="),
            },
            {
                "name": "subscript",
                "text": "x₂",
                "status_tip": "Subscript",
                "function": self.contentSubscript,
                "shortcut": QKeySequence("Ctrl+="),
            },
            {
                "name": "addImageAction",
                "text": translations[lang]["image"],
                "status_tip": translations[lang]["image_message"],
                "function": self.addImage,
                "shortcut": QKeySequence("Ctrl+Shift+I"),
            },
            {
                "name": "addTableAction",
                "text": "Table",
                "status_tip": "Add Table",
                "function": self.addTable,
                "shortcut": QKeySequence("Ctrl+T"),
            },
            {
                "name": "addHyperlinkAction",
                "text": "Hyperlink",
                "status_tip": "",
                "function": self.addHyperlink,
                "shortcut": None,
            },
            {
                "name": "documentAreaSwap",
                "text": "Document Mode",
                "status_tip": "",
                "function": self.toggleReadOnly,
                "shortcut": None,
            },
            {
                "name": "helpAction",
                "text": translations[lang]["help"],
                "status_tip": translations[lang]["help_message"],
                "function": self.viewHelp,
                "shortcut": QKeySequence("F1"),
            },
            {
                "name": "aboutAction",
                "text": translations[lang]["about"],
                "status_tip": translations[lang]["about"],
                "function": self.viewAbout,
                "shortcut": QKeySequence("Ctrl+Shift+A"),
            },
        ]

        for action_def in action_definitions:
            setattr(
                self,
                action_def["name"],
                self.createAction(
                    action_def["text"],
                    action_def["status_tip"],
                    action_def["function"],
                    action_def["shortcut"],
                ),
            )

    def initToolbar(self):
        lang = settings.value("appLanguage", "1252")

        def add_toolbar(name_key, actions):
            toolbar = self.addToolBar(translations[lang][name_key])
            self.toolbarLabel(toolbar, translations[lang][name_key] + ": ")
            toolbar.addActions(actions)
            return toolbar

        file_actions = [
            self.newaction,
            self.openaction,
            self.saveaction,
            self.saveasaction,
            self.printaction,
            self.undoaction,
            self.redoaction,
        ]
        self.file_toolbar = add_toolbar("file", file_actions)

        self.ui_toolbar = self.addToolBar(translations[lang]["ui"])
        self.toolbarLabel(self.ui_toolbar, translations[lang]["ui"] + ": ")

        self.theme_action = self.createAction(
            translations[lang]["darklight"],
            translations[lang]["darklight_message"],
            self.themeAction,
            QKeySequence("Ctrl+Shift+T"),
            "",
        )
        self.theme_action.setCheckable(True)
        self.theme_action.setChecked(settings.value("appTheme") == "dark")
        self.ui_toolbar.addAction(self.theme_action)

        self.powersaveraction = QAction(
            translations[lang]["powersaver"], self, checkable=True
        )
        self.powersaveraction.setStatusTip(translations[lang]["powersaver_message"])
        self.powersaveraction.toggled.connect(self.hybridSaver)
        self.ui_toolbar.addAction(self.powersaveraction)

        self.hide_ai_dock = self.createAction(
            "AI", "AI", self.toggleDock, QKeySequence("Ctrl+Shift+D"), ""
        )
        self.ui_toolbar.addAction(self.hide_ai_dock)
        self.ui_toolbar.addAction(self.documentAreaSwap)
        self.ui_toolbar.addAction(self.helpAction)
        self.ui_toolbar.addAction(self.aboutAction)

        self.language_combobox = QComboBox(self)
        self.language_combobox.setStyleSheet("background-color:#000000; color:#FFFFFF;")
        for lcid, name in languages.items():
            self.language_combobox.addItem(name, lcid)

        self.languageFallbackIndex()

        self.language_combobox.currentIndexChanged.connect(self.changeLanguage)
        self.ui_toolbar.addWidget(self.language_combobox)
        self.addToolBarBreak()

        edit_actions = [
            self.alignleftevent,
            self.aligncenterevent,
            self.alignrightevent,
            self.alignjustifiedevent,
            self.findaction,
            self.replaceaction,
        ]
        self.edit_toolbar = add_toolbar("edit", edit_actions)

        font_actions = [
            self.bold,
            self.italic,
            self.underline,
            self.fontfamily,
            self.inc_fontaction,
            self.dec_fontaction,
            self.superscript,
            self.subscript,
        ]
        self.font_toolbar = add_toolbar("font", font_actions)

        list_actions = [self.bulletevent, self.numberedevent]
        self.list_toolbar = add_toolbar("list", list_actions)

        self.addToolBarBreak()

        color_actions = [
            self.color,
            self.backgroundcolor,
        ]
        self.color_toolbar = add_toolbar("color", color_actions)
        multimedia_actions = [
            self.addImageAction,
            self.addTableAction,
            self.addHyperlinkAction,
        ]
        self.multimedia_toolbar = add_toolbar("multimedia", multimedia_actions)
        zoom_levels = [25, 50, 75, 100, 125, 150, 175, 200, 250, 300, 350, 400, 500]
        self.zoom_level_combobox = QComboBox(self)
        self.zoom_level_combobox.setStyleSheet(
            "background-color:#000000; color:#FFFFFF;"
        )
        self.zoom_level_combobox.addItems([f"{level}%" for level in zoom_levels])
        self.zoom_level_combobox.setCurrentText(f"{settings.value('zoomLevel', 100)}%")
        self.zoom_level_combobox.currentTextChanged.connect(self.setZoomLevel)
        self.ui_toolbar.addWidget(self.zoom_level_combobox)

        self.updateFormattingButtons()

    def setZoomLevel(self, value):
        if isinstance(value, str):
            value = int(value.replace("%", ""))

        zoom_level = value / 100.0
        self.graphicsView.setTransform(QTransform().scale(zoom_level, zoom_level))

    def addTable(self):
        templates = [
            "Simple",
            "Dual",
            "Minimalist",
            "Colored",
        ]

        alignments = ["left", "center", "right", "justify"]

        template_choice, ok = QInputDialog.getItem(
            self, "Choose a Table Style", "Select a table style:", templates, 0, False
        )

        if ok:
            template_id = templates.index(template_choice)

            alignment_choice, ok = QInputDialog.getItem(
                self,
                "Choose Table Alignment",
                "Select alignment:",
                alignments,
                0,
                False,
            )

            if ok:
                rows, ok = QInputDialog.getInt(
                    self, "Number of Rows", "Enter number of rows:", 3, 1, 100
                )
                if not ok:
                    return

                cols, ok = QInputDialog.getInt(
                    self, "Number of Columns", "Enter number of columns:", 3, 1, 100
                )
                if not ok:
                    return

                table_html = self.tableTemplates(
                    template_id, rows=rows, cols=cols, alignment=alignment_choice
                )

                cursor = self.DocumentArea.textCursor()
                cursor.insertHtml(table_html)
                self.DocumentArea.setTextCursor(cursor)

    def tableTemplates(self, template_id, rows, cols, alignment="center"):
        table_style = "border: 1px solid #ddd; border-collapse: collapse; width: 100%;"
        td_style = "padding: 8px; border: 1px solid #ddd; color: black;"
        th_style = "padding: 10px; border: 1px solid #ddd; color: black; width: 1%;"
        tr_styles = "background-color: #ffffff;"

        templates = {
            "simple_border": {
                "table_style": table_style,
                "td_style": td_style,
                "th_style": th_style,
                "tr_styles": "background-color: #ffffff;",
            },
            "dual_header_color": {
                "table_style": table_style,
                "td_style": "padding: 8px; border: 1px solid #ffcc00; color: black;",
                "th_style": "padding: 10px; border: 1px solid #ffcc00; color: black; background-color: #ffcc00;",
                "tr_styles": "background-color: #fff3e0;",
            },
            "minimalist_lines": {
                "table_style": table_style,
                "td_style": td_style,
                "th_style": "padding: 10px; border: 1px solid #ddd; background-color: #f2f2f2; color: black;",
                "tr_styles": "background-color: #f9f9f9;",
            },
            "colored_rows": {
                "table_style": table_style,
                "td_style": "padding: 8px; border: 1px solid #ffcc00; color: black;",
                "th_style": "padding: 10px; border: 1px solid #ffcc00; color: black; background-color: #ffcc00;",
                "tr_styles": "background-color: #fff3e0;",
            },
        }

        selected_template = templates.get(template_id, templates["simple_border"])
        table_style = selected_template["table_style"]
        td_style = selected_template["td_style"]
        th_style = selected_template["th_style"]
        tr_styles = selected_template["tr_styles"]

        table_html = f"""
            <div style="text-align: {alignment};">
                <table style="{table_style}">
                    <tr>
        """

        for i in range(cols):
            table_html += f'<th style="{th_style}"></th>'

        table_html += "</tr>"

        for i in range(rows):
            table_html += f'<tr style="{tr_styles}">'
            for j in range(cols):
                table_html += f'<td style="{td_style}"></td>'
            table_html += "</tr>"

        table_html += """
                </table>
            </div>
        """

        return table_html

    def updateAiWidgetPosition(self):

        ai_widget_width = 450
        ai_widget_height = self.ai_widget.height()

        self.ai_widget.move(
            self.width() - ai_widget_width, self.height() - ai_widget_height
        )

    def toggleDock(self):
        if self.ai_widget.isHidden():
            self.ai_widget.show()
            self.updateAiWidgetPosition()
        else:
            self.ai_widget.hide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "ai_widget") and self.ai_widget is not None:
            window_width = self.width()
            window_height = self.height()
            right_margin = max(int(window_width * 0.07), 50)
            widget_height = max(515, min(int(window_height * 0.8), 900))
            widget_width = max(500, min(int(window_width * 0.30), 800))
            self.ai_widget.setMinimumHeight(widget_height)
            self.ai_widget.setMaximumHeight(widget_height)
            self.ai_widget.setMinimumWidth(widget_width)
            self.ai_widget.setMaximumWidth(widget_width)
            self.ai_widget.setContentsMargins(0, 0, right_margin, 42)

            if not self.ai_widget.isHidden():
                self.updateAiWidgetPosition()

    def hybridSaver(self, checked):
        settings = QSettings("berkaygediz", "SolidWriting")
        if checked:
            battery = psutil.sensors_battery()
            if battery:
                if battery.percent <= 35 and not battery.power_plugged:
                    # Ultra
                    self.adaptiveResponse = 6
                else:
                    # Standard
                    self.adaptiveResponse = 4
            else:
                # Global Standard
                self.adaptiveResponse = 2
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

    def resetDocumentArea(self):
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

    def newFile(self):
        if self.is_saved:
            self.resetDocumentArea()
            self.directory = self.default_directory
            self.file_name = None
            self.is_saved = False
            self.updateTitle()
        else:
            lang = settings.value("appLanguage", "1252")
            reply = QMessageBox.question(
                self,
                f"{app.applicationDisplayName()}",
                translations[lang]["new_message"],
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                self.resetDocumentArea()
                self.directory = self.default_directory
                self.file_name = None
                self.is_saved = False
                self.updateTitle()

    def openFile(self, file_to_open=None):
        lang = settings.value("appLanguage", "1252")
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly

        if file_to_open:
            selected_file = file_to_open
        else:
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
                automaticEncoding = SW_Workspace.detectEncoding(self.file_name)
            except Exception as e:
                automaticEncoding = "utf-8"

            if self.file_name.endswith(".docx"):
                with open(self.file_name, "rb") as file:
                    try:
                        conversionLayer = mammoth.convert_to_html(file)
                        self.DocumentArea.setHtml(conversionLayer.value)
                    except Exception as e:
                        QMessageBox.warning(self, None, "Conversion failed.")
            else:
                with open(self.file_name, "r", encoding=automaticEncoding) as file:
                    if self.file_name.endswith((".swdoc", ".rsdoc")):
                        self.DocumentArea.setHtml(file.read())
                    elif self.file_name.endswith((".swdoc64")):
                        encryption = CryptoEngine("SolidWriting")
                        self.DocumentArea.setHtml(encryption.b64_decrypt(file.read()))
                    elif self.file_name.endswith((".md")):
                        self.DocumentArea.setMarkdown(file.read())
                    else:
                        self.DocumentArea.setPlainText(file.read())

            self.directory = os.path.dirname(self.file_name)
            self.is_saved = True
            self.updateTitle()

    def saveFile(self):
        if self.is_saved == False:
            self.saveProcess()
        elif self.file_name == None:
            self.saveAs()
        else:
            self.saveProcess()

    def saveAs(self):
        lang = settings.value("appLanguage", "1252")
        options = QFileDialog.Options()
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
            self.saveProcess()
            return True
        else:
            return False

    def saveProcess(self):
        if not self.file_name:
            self.saveAs()
        else:
            try:
                automaticEncoding = SW_Workspace.detectEncoding(self.file_name)
            except Exception as e:
                automaticEncoding = "utf-8"
            if self.file_name.lower().endswith(".docx"):
                pass
            else:
                with open(self.file_name, "w", encoding=automaticEncoding) as file:
                    if self.file_name.lower().endswith((".swdoc")):
                        file.write(self.DocumentArea.toHtml())
                    elif self.file_name.lower().endswith((".swdoc64")):
                        encryption = CryptoEngine("SolidWriting")
                        file.write(encryption.b64_encrypt(self.DocumentArea.toHtml()))
                    elif self.file_name.lower().endswith((".md")):
                        file.write(self.DocumentArea.toMarkdown())
                    else:
                        document = QTextDocument()
                        document.setPlainText(self.DocumentArea.toPlainText())
                        file.write(document.toPlainText())

        self.status_bar.showMessage("Saved.", 2000)
        self.is_saved = True
        self.updateTitle()

    def printDocument(self):
        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageOrientation(QPageLayout.Orientation.Portrait)
        printer.setPageMargins(QMargins(10, 10, 10, 10), QPageLayout.Millimeter)

        printer.setFullPage(True)
        printer.setDocName(self.file_name)

        preview_dialog = QPrintPreviewDialog(printer, self)
        preview_dialog.paintRequested.connect(self.DocumentArea.print_)
        preview_dialog.exec()

    def addImage(self):
        lang = settings.value("appLanguage", "1252")
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
        self.about_window = SW_About()
        self.about_window.show()

    def viewHelp(self):
        help_window = SW_Help(self)
        help_window.show()

    def bulletList(self):
        cursor = self.DocumentArea.textCursor()
        cursor.beginEditBlock()

        selected_text = cursor.selectedText()
        lines = selected_text.split("\n")
        char_format = cursor.charFormat()

        for line in lines:
            if line.strip():
                cursor.insertList(QTextListFormat.ListDisc)
                cursor.insertText(line)
                cursor.insertBlock()
            else:
                cursor.insertBlock()

        cursor.mergeCharFormat(char_format)

        cursor.endEditBlock()

    def numberedList(self):
        cursor = self.DocumentArea.textCursor()
        cursor.beginEditBlock()

        selected_text = cursor.selectedText()

        lines = selected_text.split("\n")

        char_format = cursor.charFormat()

        for line in lines:
            if line.strip():
                cursor.insertList(QTextListFormat.ListDecimal)
                cursor.insertText(line)
                cursor.insertBlock()
            else:
                cursor.insertBlock()

        cursor.mergeCharFormat(char_format)

        cursor.endEditBlock()

    def handleHyperlink(self, url):
        link = url.toString()

        if link.lower().startswith(("http", "https", "mailto", "ftp", "file")):
            QDesktopServices.openUrl(url)
        else:
            pass

    def addHyperlink(self):
        protocol, ok1 = QInputDialog.getItem(
            self,
            "Protocols",
            "Select:",
            ["http", "https", "ftp", "mailto", "file"],
            0,
            False,
        )
        if ok1 and protocol:
            name, ok2 = QInputDialog.getText(self, "Name", "Name:")
            if ok2 and name:
                url, ok3 = QInputDialog.getText(self, "URL", "URL:")
                if ok3 and url:
                    if not url.lower().startswith(
                        ("http", "https", "mailto", "ftp", "file")
                    ):
                        url = protocol + "://" + url

                    html_content = f'<a href="{url}">{name}</a>'

                    cursor = self.DocumentArea.textCursor()
                    cursor.insertHtml(html_content)

                    self.DocumentArea.setTextCursor(cursor)

    def contentAlign(self, alignment):
        self.DocumentArea.setAlignment(alignment)

    def contentBold(self):
        font = self.DocumentArea.currentFont()
        font.setBold(not font.bold())
        self.DocumentArea.setCurrentFont(font)

    def contentItalic(self):
        font = self.DocumentArea.currentFont()
        font.setItalic(not font.italic())
        self.DocumentArea.setCurrentFont(font)

    def contentUnderline(self):
        font = self.DocumentArea.currentFont()
        font.setUnderline(not font.underline())
        self.DocumentArea.setCurrentFont(font)

    def contentColor(self):
        color = QColorDialog.getColor()
        self.DocumentArea.setTextColor(color)

    def contentBGColor(self):
        color = QColorDialog.getColor()
        self.DocumentArea.setTextBackgroundColor(color)

    def contentFont(self):
        # 'ok' (bool), 'font' (QFont)
        ok, font = QFontDialog.getFont(
            self.DocumentArea.currentFont(), self.DocumentArea
        )

        if ok:
            if isinstance(font, QFont):
                self.DocumentArea.setCurrentFont(font)

    def contentSuperscript(self):
        cursor = self.DocumentArea.textCursor()
        if not cursor.hasSelection():
            return

        fmt = QTextCharFormat()
        current_format = cursor.charFormat()

        if (
            current_format.verticalAlignment()
            == QTextCharFormat.VerticalAlignment.AlignSuperScript
        ):
            fmt.setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignBaseline)
        else:
            fmt.setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignSuperScript)

        cursor.mergeCharFormat(fmt)
        self.DocumentArea.mergeCurrentCharFormat(fmt)

    def contentSubscript(self):
        cursor = self.DocumentArea.textCursor()
        if not cursor.hasSelection():
            return

        fmt = QTextCharFormat()
        current_format = cursor.charFormat()

        if (
            current_format.verticalAlignment()
            == QTextCharFormat.VerticalAlignment.AlignSubScript
        ):
            fmt.setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignBaseline)
        else:
            fmt.setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignSubScript)

        cursor.mergeCharFormat(fmt)
        self.DocumentArea.mergeCurrentCharFormat(fmt)

    def incFont(self):
        font = self.DocumentArea.currentFont()
        font.setPointSize(font.pointSize() + 1)
        self.DocumentArea.setCurrentFont(font)

    def decFont(self):
        font = self.DocumentArea.currentFont()
        font.setPointSize(font.pointSize() - 1)
        self.DocumentArea.setCurrentFont(font)

    def find(self):
        lang = settings.value("appLanguage", "1252")
        text, ok = QInputDialog.getText(
            self,
            translations[lang]["find"],
            translations[lang]["find"],
        )

        if ok and text:
            self.findText(text)

    def findText(self, text):
        found = self.DocumentArea.find(text)
        if not found:
            QMessageBox.information(self, translations[lang]["find"], "0")

    def replace(self):
        lang = settings.value("appLanguage", "1252")
        self.replace_dialog = QDialog(self)
        self.replace_dialog.setWindowTitle(translations[lang]["replace"])
        self.replace_dialog.setModal(True)

        layout = QVBoxLayout()

        self.find_label = QLabel(translations[lang]["find"])
        layout.addWidget(self.find_label)

        self.find_input = QLineEdit()
        layout.addWidget(self.find_input)

        self.replace_label = QLabel(translations[lang]["replace"])
        layout.addWidget(self.replace_label)

        self.replace_input = QLineEdit()
        layout.addWidget(self.replace_input)

        self.replace_next_button = QPushButton(translations[lang]["replace"] + " next")
        self.replace_next_button.clicked.connect(self.replace_next)
        layout.addWidget(self.replace_next_button)

        self.replace_all_button = QPushButton(translations[lang]["replace"] + " all")
        self.replace_all_button.clicked.connect(self.replace_all)
        layout.addWidget(self.replace_all_button)

        self.cancel_button = QPushButton(translations[lang]["cancel"])
        self.cancel_button.clicked.connect(self.replace_dialog.reject)
        layout.addWidget(self.cancel_button)

        self.replace_dialog.setLayout(layout)
        self.find_input.setFocus()

        self.replace_dialog.exec()

    def replace_next(self):
        find_text = self.find_input.text()
        replace_text = self.replace_input.text()

        found = self.DocumentArea.find(find_text)
        if found:
            cursor = self.DocumentArea.textCursor()
            cursor.insertText(replace_text)
            self.DocumentArea.setTextCursor(cursor)
        else:
            QMessageBox.information(
                self,
                translations[lang]["replace"],
                "0",
            )

    def replace_all(self):
        find_text = self.find_input.text()
        replace_text = self.replace_input.text()

        cursor = self.DocumentArea.textCursor()
        self.DocumentArea.moveCursor(QTextCursor.Start)
        self.DocumentArea.setTextCursor(cursor)

        count = 0
        while self.DocumentArea.find(find_text):
            cursor = self.DocumentArea.textCursor()
            cursor.insertText(replace_text)
            self.DocumentArea.setTextCursor(cursor)
            count += 1

        if count == 0:
            QMessageBox.information(
                self,
                translations[lang]["replace"],
                f"{count}",
            )
        else:
            QMessageBox.information(
                self,
                translations[lang]["replace"],
                f"{count}",
            )


if __name__ == "__main__":
    if getattr(sys, "frozen", False):
        applicationPath = sys._MEIPASS
    elif __file__:
        applicationPath = os.path.dirname(__file__)
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(os.path.join(applicationPath, fallbackValues["icon"])))
    app.setOrganizationName("berkaygediz")
    app.setApplicationName("SolidWriting")
    app.setApplicationDisplayName("SolidWriting 2025.04")
    app.setApplicationVersion("1.5.2025.04-2")
    ws = SW_ControlInfo()
    ws.show()
    sys.exit(app.exec())
