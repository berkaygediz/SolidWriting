import sys
import os
import platform
import datetime
import base64
import time
import sqlite3
import re
import webbrowser
import qtawesome as qta
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtTest import *
from PyQt5.QtPrintSupport import *
from modules.translations import *
from modules.secrets import *


default_values = {
    'font_family': 'Arial',
    'font_size': 14,
    'bold': False,
    'italic': False,
    'underline': False,
    'alignment': Qt.AlignmentFlag.AlignLeft,
    'text_color': '#000000',
    'background_color': '#FFFFFF',
    'theme': 'light',
    'window_geometry': None,
    'default_directory': None,
    'file_name': None,
    'text_content': None,
    'is_saved': None,
    'scroll_position': None,
    'current_theme': 'light',
    'current_language': 'English'
}


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


class RS_About(QMainWindow):
    def __init__(self, parent=None):
        super(RS_About, self).__init__(parent)
        self.setWindowFlags(Qt.Dialog)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setGeometry(QStyle.alignedRect(Qt.LeftToRight, Qt.AlignCenter, self.size(
        ), QApplication.desktop().availableGeometry()))
        self.about_label = QLabel()
        self.about_label.setWordWrap(True)
        self.about_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.about_label.setTextFormat(Qt.RichText)
        self.about_label.setText("<center>"
                                 "<b>RichSpan</b><br>"
                                 "A word processor application<br>"
                                 "Made by Berkay Gediz<br>"
                                 "Apache License 2.0</center>")
        self.setCentralWidget(self.about_label)


class RS_ControlInfo(QMainWindow):
    def __init__(self, parent=None):
        super(RS_ControlInfo, self).__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        settings = QSettings("berkaygediz", "RichSpan")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        screen = QGuiApplication.primaryScreen().availableGeometry()
        self.setGeometry(
            QStyle.alignedRect(
                Qt.LayoutDirection.LeftToRight,
                Qt.AlignmentFlag.AlignCenter,
                QSize(int(screen.width() * 0.2),
                      int(screen.height() * 0.2)),
                screen
            )
        )

        if settings.value("current_language") == None:
            settings.setValue("current_language", "English")
            settings.sync()
        self.language = settings.value("current_language")
        self.setStyleSheet("background-color: transparent;")
        self.setWindowOpacity(0.75)
        self.widget_central = QWidget()
        self.layout_central = QVBoxLayout(self.widget_central)
        self.widget_central.setStyleSheet(
            "background-color: #6F61C0; border-radius: 50px; border: 1px solid #A084E8; border-radius: 10px;")

        self.title = QLabel("RichSpan", self)
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setFont(QFont('Roboto', 30))
        self.title.setStyleSheet(
            "background-color: #A084E8; color: #FFFFFF; font-weight: bold; font-size: 30px; border-radius: 25px; border: 1px solid #000000;")
        self.layout_central.addWidget(self.title)

        self.label_status = QLabel("...", self)
        self.label_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_status.setFont(QFont('Roboto', 10))
        self.layout_central.addWidget(self.label_status)

        self.setCentralWidget(self.widget_central)

        if serverconnect():
            sqlite_file = os.path.join(os.path.dirname(
                os.path.abspath(__file__)), 'richspan.db')
            sqlitedb = sqlite3.connect(sqlite_file)
            sqlitecursor = sqlitedb.cursor()
            sqlitecursor.execute(
                "CREATE TABLE IF NOT EXISTS profile (nametag TEXT, email TEXT, password TEXT)")
            sqlitecursor.execute(
                "CREATE TABLE IF NOT EXISTS apps (richspan INTEGER DEFAULT 0, email TEXT)")
            sqlitecursor.execute(
                "CREATE TABLE IF NOT EXISTS log (email TEXT, devicename TEXT, product NVARCHAR(100), activity NVARCHAR(100), log TEXT, logdate TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")

            profile_email = sqlitecursor.execute(
                "SELECT email FROM profile").fetchone()
            profile_pw = sqlitecursor.execute(
                "SELECT password FROM profile").fetchone()

            if profile_email is not None and profile_pw is not None:
                local_email = profile_email[0]
                local_pw = profile_pw[0]
                mysql_connection = serverconnect()
                if mysql_connection:
                    mysqlcursor = mysql_connection.cursor()
                    mysqlcursor.execute(
                        "SELECT * FROM profile WHERE email = %s", (local_email,))
                    user_result = mysqlcursor.fetchone()
                    if user_result is not None:
                        if local_email == user_result[1] and local_pw == user_result[3]:
                            mysqlcursor.execute(
                                "INSERT INTO log (email, devicename, product, activity, log) VALUES (%s, %s, %s, %s, %s)", (user_result[1], platform.node(), "RichSpan", "Login", "Verified"))
                            mysql_connection.commit()
                            mysqlcursor.execute(
                                "SELECT * FROM user_settings WHERE email = %s AND product = %s", (local_email, "RichSpan"))
                            user_settings = mysqlcursor.fetchone()
                            if user_settings is not None:
                                settings.setValue(
                                    "current_theme", user_settings[3])
                                settings.setValue(
                                    "current_language", user_settings[4])
                                settings.sync()
                            else:
                                settings.setValue(
                                    "current_theme", "light")
                                settings.setValue(
                                    "current_language", "English")
                                settings.sync()
                            self.label_status.setStyleSheet(
                                "background-color: #7900FF; color: #FFFFFF; font-weight: bold; font-size: 16px; border-radius: 30px; border: 1px solid #000000;")
                            self.label_status.setText(
                                "💡" + local_email.split('@')[0])
                            RS_Workspace().show()
                            QTimer.singleShot(1250, self.hide)
                        else:
                            def logout():
                                sqlite_file = os.path.join(os.path.dirname(
                                    os.path.abspath(__file__)), 'richspan.db')
                                sqliteConnection = sqlite3.connect(sqlite_file)
                                sqlitecursor = sqliteConnection.cursor()
                                sqlitecursor.execute(
                                    "DROP TABLE IF EXISTS profile")
                                sqlitecursor.connection.commit()
                                sqlitecursor.execute(
                                    "DROP TABLE IF EXISTS apps")
                                sqlitecursor.connection.commit()
                                sqlitecursor.execute(
                                    "DROP TABLE IF EXISTS log")
                                sqlitecursor.connection.commit()
                                sqlitecursor.execute(
                                    "DROP TABLE IF EXISTS user_settings")
                                sqlitecursor.connection.commit()
                                RS_ControlInfo().show()
                                QTimer.singleShot(0, self.hide)
                            self.label_status.setStyleSheet(
                                "background-color: #252525; color: #FFFFFF; font-weight: bold; font-size: 16px; border-radius: 30px; border: 1px solid #000000;")
                            self.label_status.setText(
                                translations[settings.value("current_language")]["wrong_password"])
                            mysqlcursor.execute(
                                "INSERT INTO log (email, devicename, product, activity, log) VALUES (%s, %s, %s, %s, %s)", (local_email, platform.node(), "RichSpan", "Login", "Failed"))
                            mysql_connection.commit()
                            logoutbutton = QPushButton(translations[settings.value(
                                "current_language")]["logout"])
                            logoutbutton.setStyleSheet(
                                "background-color: #7900FF; color: #FFFFFF; font-weight: bold; font-size: 16px; border-radius: 30px; border: 1px solid #000000;")
                            logoutbutton.clicked.connect(logout)
                            self.layout_central.addWidget(logoutbutton)
                    else:
                        self.label_status.setStyleSheet(
                            "background-color: #252525; color: #FFFFFF; font-weight: bold; font-size: 16px; border-radius: 30px; border: 1px solid #000000;")
                        self.label_status.setText(
                            translations[settings.value("current_language")]["no_account"])
                        logoutbutton = QPushButton(translations[settings.value(
                            "current_language")]["register"])
                        logoutbutton.setStyleSheet(
                            "background-color: #7900FF; color: #FFFFFF; font-weight: bold; font-size: 16px; border-radius: 30px; border: 1px solid #000000;")
                        logoutbutton.clicked.connect(RS_Welcome().show)
                        self.layout_central.addWidget(logoutbutton)
                        self.close_button = QPushButton(translations[settings.value(
                            "current_language")]["exit"])
                        self.close_button.setStyleSheet(
                            "background-color: #7900FF; color: #FFFFFF; font-weight: bold; font-size: 16px; border-radius: 30px; border: 1px solid #000000;")
                        self.close_button.clicked.connect(sys.exit)
                        self.layout_central.addWidget(self.close_button)

                else:
                    self.label_status.setText(
                        translations[settings.value("current_language")]["connection_denied"])
                    logoutbutton = QPushButton(translations[settings.value(
                        "current_language")]["register"])
                    logoutbutton.setStyleSheet(
                        "background-color: #7900FF; color: #FFFFFF; font-weight: bold; font-size: 16px; border-radius: 30px; border: 1px solid #000000;")
                    logoutbutton.clicked.connect(RS_Welcome().show)
                    self.layout_central.addWidget(logoutbutton)
            else:
                RS_Welcome().show()
                QTimer.singleShot(0, self.hide)
        else:
            self.label_status.setText(translations[settings.value(
                "current_language")]["connection_denied"])
            self.label_status.setStyleSheet(
                "background-color: #252525; color: #FFFFFF; font-weight: bold; font-size: 16px; border-radius: 30px; border: 1px solid #000000;")
            QTimer.singleShot(10000, sys.exit)


class RS_Welcome(QMainWindow):
    def __init__(self, parent=None):
        super(RS_Welcome, self).__init__(parent)
        starttime = datetime.datetime.now()
        settings = QSettings("berkaygediz", "RichSpan")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        screen = QGuiApplication.primaryScreen().availableGeometry()
        self.setGeometry(
            QStyle.alignedRect(
                Qt.LayoutDirection.LeftToRight,
                Qt.AlignmentFlag.AlignCenter,
                QSize(int(screen.width() * 0.4),
                      int(screen.height() * 0.5)),
                screen
            )
        )

        if settings.value("current_language") == None:
            settings.setValue("current_language", "English")
            settings.sync()
        self.language = settings.value("current_language")

        self.setStyleSheet("background-color: #F9E090;")
        self.setWindowTitle(translations[settings.value(
            "current_language")]["welcome-title"])
        introduction = QVBoxLayout()
        self.statusBar().setStyleSheet(
            "background-color: #F9E090; color: #000000; font-weight: bold; font-size: 12px; border-radius: 10px; border: 1px solid #000000;")
        product_label = QLabel("RichSpan 🎉")
        product_label.setStyleSheet(
            "background-color: #DFBB9D; color: #000000; font-size: 28px; font-weight: bold; border-radius: 10px; border: 1px solid #000000;")
        product_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        intro_label = QLabel(translations[settings.value(
            "current_language")]["intro"])
        intro_label.setStyleSheet(
            "background-color: #F7E2D6; color: #000000; font-size: 12px; border-radius: 10px; border: 1px solid #000000;")
        intro_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        intro_label.setFixedHeight(50)

        def RS_changeLanguage():
            language = self.language_combobox.currentText()
            settings = QSettings("berkaygediz", "RichSpan")
            settings.setValue("current_language", language)
            settings.sync()

        self.language_combobox = QComboBox()
        self.language_combobox.setStyleSheet(
            "background-color: #B3E8E5; color: #000000; border-radius: 10px; border: 1px solid #000000; margin: 10px; margin-left: 0px; margin-right: 0px; padding: 0px; font-size: 16px;")
        self.language_combobox.addItems(
            ["English", "Türkçe", "Azərbaycanca", "Deutsch", "Español"])
        self.language_combobox.currentTextChanged.connect(RS_changeLanguage)
        self.language_combobox.setCurrentText(
            settings.value("current_language"))

        introduction.addWidget(product_label)
        introduction.addWidget(intro_label)
        introduction.addWidget(self.language_combobox)
        label_email = QLabel(
            translations[settings.value("current_language")]["email"] + ":")
        label_email.setStyleSheet(
            "color: #A72461; font-weight: bold; font-size: 16px; margin: 10px; margin-left: 0px; margin-right: 0px; padding: 0px;")
        textbox_email = QLineEdit()
        textbox_email.setStyleSheet(
            "background-color: #B3E8E5; color: #000000; border-radius: 10px; border: 1px solid #000000; margin: 10px; margin-left: 0px; margin-right: 0px; padding: 0px; font-size: 16px;")

        label_password = QLabel(
            translations[settings.value("current_language")]["password"] + ":")
        label_password.setStyleSheet(
            "color: #A72461; font-weight: bold; font-size: 16px; margin: 10px; margin-left: 0px; margin-right: 0px; padding: 0px;")
        textbox_password = QLineEdit()
        textbox_password.setStyleSheet(
            "background-color: #B3E8E5; color: #000000; border-radius: 10px; border: 1px solid #000000; margin: 10px; margin-left: 0px; margin-right: 0px; padding: 0px; font-size: 16px;")
        textbox_password.setEchoMode(QLineEdit.EchoMode.Password)

        label_exception = QLabel()
        label_exception.setStyleSheet(
            "color: #A72461; font-weight: bold; font-size: 16px; margin: 10px; margin-left: 0px; margin-right: 0px; padding: 0px;")
        label_exception.setAlignment(Qt.AlignmentFlag.AlignCenter)

        bottom_layout = QVBoxLayout()
        bottom_layout.addWidget(label_email)
        bottom_layout.addWidget(textbox_email)
        bottom_layout.addWidget(label_password)
        bottom_layout.addWidget(textbox_password)
        bottom_layout.addWidget(label_exception)

        button_layout = QHBoxLayout()

        button_login = QPushButton(
            translations[settings.value("current_language")]["login"])
        button_login.setStyleSheet(
            "background-color: #A72461; color: #FFFFFF; font-weight: bold; padding: 10px; border-radius: 10px; border: 1px solid #000000; margin: 10px;")

        def is_valid_email(email):
            email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
            return re.match(email_regex, email)

        def register():
            email = textbox_email.text()
            password = textbox_password.text()

            if email == "" or password == "":
                label_exception.setText(translations[settings.value(
                    "current_language")]["fill_all"])
            elif not is_valid_email(textbox_email.text()):
                label_exception.setText(translations[settings.value(
                    "current_language")]["invalid_email"])
            else:
                mysqlserver = serverconnect()
                mysqlcursor = mysqlserver.cursor()
                sqlite_file = os.path.join(os.path.dirname(
                    os.path.abspath(__file__)), 'richspan.db')
                sqliteConnection = sqlite3.connect(sqlite_file)
                mysqlcursor.execute(
                    "SELECT email FROM profile WHERE email = %s", (email,))
                user_result = mysqlcursor.fetchone()

                if user_result == None:
                    mysqlcursor.execute("INSERT INTO profile (email, password) VALUES (%s, %s)", (
                        email, password))
                    mysqlserver.commit()
                    mysqlcursor.execute(
                        "INSERT INTO log (email, devicename, product, activity, log) VALUES (%s, %s, %s, %s, %s)", (email, platform.node(), "RichSpan", "Register", "Success"))
                    mysqlserver.commit()
                    mysqlcursor.execute(
                        "INSERT INTO apps (richspan, email) VALUES (%s, %s)", (0, email))
                    mysqlserver.commit()
                    language = settings.value("current_language")
                    mysqlcursor.execute(
                        "INSERT INTO user_settings (email, product, theme, language) VALUES (%s, %s, %s, %s)", (email, "RichSpan", "light", language))
                    mysqlserver.commit()
                    sqliteConnection.execute("DROP TABLE IF EXISTS profile")
                    sqliteConnection.commit()
                    sqliteConnection.execute("DROP TABLE IF EXISTS apps")
                    sqliteConnection.commit()
                    sqliteConnection.execute("DROP TABLE IF EXISTS log")
                    sqliteConnection.commit()
                    sqliteConnection.execute(
                        "CREATE TABLE IF NOT EXISTS profile (email TEXT, password TEXT)")
                    sqliteConnection.commit()
                    sqliteConnection.execute(
                        "CREATE TABLE IF NOT EXISTS apps (richspan INTEGER DEFAULT 0, email TEXT)")
                    sqliteConnection.commit()
                    sqliteConnection.execute(
                        "CREATE TABLE IF NOT EXISTS log (email TEXT, devicename TEXT, log TEXT, logdate TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
                    sqliteConnection.commit()
                    sqliteConnection.execute(
                        "CREATE TABLE IF NOT EXISTS user_settings (email TEXT, theme TEXT, language TEXT)")
                    sqliteConnection.commit()
                    sqliteConnection.execute("INSERT INTO profile (nametag, email, password) VALUES (?, ?, ?)", (
                        email.split('@')[0], email, password))
                    sqliteConnection.commit()
                    sqliteConnection.execute(
                        "INSERT INTO apps (richspan, email) VALUES (?, ?)", (0, email))
                    sqliteConnection.commit()
                    sqliteConnection.execute(
                        "INSERT INTO log (email, devicename, product, activity, log) VALUES (?, ?, ?, ?, ?)", (email, platform.node(), "RichSpan", "Register", "Success"))
                    sqliteConnection.commit()
                    sqliteConnection.execute(
                        "INSERT INTO user_settings (email, theme, language) VALUES (?, ?, ?)", (email, "light", language))
                    sqliteConnection.commit()
                    time.sleep(1)
                    label_exception.setText(translations[settings.value(
                        "current_language")]["register_success"])
                    QTimer.singleShot(3500, self.hide)
                    RS_Workspace().show()
                else:
                    label_exception.setText(
                        translations[settings.value("current_language")]["already_registered"])

        def login():
            email = textbox_email.text()
            password = textbox_password.text()

            if email == "" or password == "":
                label_exception.setText(translations[settings.value(
                    "current_language")]["fill_all"])
            elif not is_valid_email(email):
                label_exception.setText(translations[settings.value(
                    "current_language")]["invalid_email"])
            else:
                mysqlserver = serverconnect()
                mysqlcursor = mysqlserver.cursor()
                sqlite_file = os.path.join(os.path.dirname(
                    os.path.abspath(__file__)), 'richspan.db')
                sqliteConnection = sqlite3.connect(sqlite_file).cursor()
                mysqlcursor.execute(
                    "SELECT email FROM profile WHERE email = %s", (email,))
                user_result = mysqlcursor.fetchone()
                mysqlcursor.execute(
                    "SELECT password FROM profile WHERE password = %s", (password,))
                pw_result = mysqlcursor.fetchone()

                if user_result and pw_result:
                    mysqlcursor.execute("INSERT INTO log (email, devicename, product, activity, log) VALUES (%s, %s, %s, %s, %s)", (
                        email, platform.node(), "RichSpan", "Login", "Success"))
                    mysqlserver.commit()
                    sqliteConnection.execute("DROP TABLE IF EXISTS profile")
                    sqliteConnection.connection.commit()
                    sqliteConnection.execute("DROP TABLE IF EXISTS apps")
                    sqliteConnection.connection.commit()
                    sqliteConnection.execute("DROP TABLE IF EXISTS log")
                    sqliteConnection.connection.commit()
                    sqliteConnection.execute(
                        "DROP TABLE IF EXISTS user_settings")
                    sqliteConnection.execute(
                        "CREATE TABLE IF NOT EXISTS profile (nametag TEXT, email TEXT, password TEXT)")
                    sqliteConnection.connection.commit()
                    sqliteConnection.execute(
                        "CREATE TABLE IF NOT EXISTS apps (richspan INTEGER DEFAULT 0, email TEXT)")
                    sqliteConnection.connection.commit()
                    sqliteConnection.execute(
                        "CREATE TABLE IF NOT EXISTS log (email TEXT, devicename TEXT, product NVARCHAR(100), activity NVARCHAR(100), log TEXT, logdate TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
                    sqliteConnection.connection.commit()
                    sqliteConnection.execute(
                        "CREATE TABLE IF NOT EXISTS user_settings (email TEXT, theme TEXT, language TEXT)")
                    sqliteConnection.connection.commit()
                    sqliteConnection.execute(
                        "INSERT INTO profile (nametag, email, password) VALUES (?, ?, ?)", (email.split('@')[0], email, password))
                    sqliteConnection.connection.commit()
                    sqliteConnection.execute(
                        "INSERT INTO apps (richspan, email) VALUES (?, ?)", (0, email))
                    sqliteConnection.connection.commit()
                    sqliteConnection.execute(
                        "INSERT INTO user_settings (email, theme, language) VALUES (?, ?, ?)", (email, "light", "English"))
                    sqliteConnection.connection.commit()
                    sqliteConnection.execute(
                        "INSERT INTO log (email, devicename, product, activity, log) VALUES (?, ?, ?, ?, ?)", (email, platform.node(), "RichSpan", "Login", "Success"))
                    sqliteConnection.connection.commit()
                    time.sleep(1)
                    textbox_email.setText("")
                    textbox_password.setText("")
                    label_exception.setText("")
                    QTimer.singleShot(3500, self.hide)
                    RS_Workspace().show()
                else:
                    settings.setValue("current_language", "English")
                    label_exception.setText(
                        translations[settings.value("current_language")]["wrong_credentials"])

        button_login.clicked.connect(login)
        button_register = QPushButton(translations[settings.value(
            "current_language")]["register"])
        button_register.setStyleSheet(
            "background-color: #A72461; color: #FFFFFF; font-weight: bold; padding: 10px; border-radius: 10px; border: 1px solid #000000; margin: 10px;")
        button_register.clicked.connect(register)

        button_layout.addWidget(button_login)
        button_layout.addWidget(button_register)

        introduction.addLayout(bottom_layout)
        introduction.addLayout(button_layout)

        central_widget = QWidget()
        central_widget.setLayout(introduction)

        self.setCentralWidget(central_widget)
        endtime = datetime.datetime.now()
        self.statusBar().showMessage(
            str((endtime - starttime).total_seconds()) + " ms", 2500)


class RS_ActivationStatus(QMainWindow):
    def __init__(self, parent=None):
        super(RS_ActivationStatus, self).__init__(parent)
        self.setWindowFlags(Qt.Dialog)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setGeometry(QStyle.alignedRect(Qt.LeftToRight, Qt.AlignCenter, self.size(
        ), QApplication.desktop().availableGeometry()))

        layout = QVBoxLayout()

        self.activation_label = QLabel()
        self.activation_label.setWordWrap(True)
        self.activation_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.activation_label.setTextFormat(Qt.RichText)
        self.activation_label.setText("<center>"
                                      "<b>RichSpan</b><br>"
                                      "Activate your product or delete your account<br><br>"
                                      "</center>")
        button_layout = QHBoxLayout()

        self.activation_button = QPushButton("Activate")
        self.activation_button.setStyleSheet(
            "background-color: #7900FF; color: #FFFFFF; font-weight: bold; font-size: 16px; border-radius: 30px; border: 1px solid #000000;")

        def activateSite():
            webbrowser.open('http://localhost/bg-ecosystem-web/activate.php')
        self.activation_button.clicked.connect(activateSite)

        self.delete_button = QPushButton("Delete")
        self.delete_button.setStyleSheet(
            "background-color: #7900FF; color: #FFFFFF; font-weight: bold; font-size: 16px; border-radius: 30px; border: 1px solid #000000;")

        def deleteAccount():
            webbrowser.open('http://localhost/bg-ecosystem-web/profile.php')
        self.delete_button.clicked.connect(deleteAccount)

        self.logout_button = QPushButton("Logout")
        self.logout_button.setStyleSheet(
            "background-color: #7900FF; color: #FFFFFF; font-weight: bold; font-size: 16px; border-radius: 30px; border: 1px solid #000000;")

        def logout():
            sqlite_file = os.path.join(os.path.dirname(
                os.path.abspath(__file__)), 'richspan.db')
            sqliteConnection = sqlite3.connect(sqlite_file)
            sqlitecursor = sqliteConnection.cursor()
            sqlitecursor.execute("DROP TABLE IF EXISTS profile")
            sqlitecursor.connection.commit()
            sqlitecursor.execute("DROP TABLE IF EXISTS apps")
            sqlitecursor.connection.commit()
            sqlitecursor.execute("DROP TABLE IF EXISTS log")
            sqlitecursor.connection.commit()
            sqlitecursor.execute("DROP TABLE IF EXISTS user_settings")
            sqlitecursor.connection.commit()
            RS_ControlInfo().show()
            QTimer.singleShot(0, self.hide)
        self.logout_button.clicked.connect(logout)

        button_layout.addWidget(self.activation_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.logout_button)

        layout.addWidget(self.activation_label)
        layout.addLayout(button_layout)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)


class RS_Workspace(QMainWindow):
    def __init__(self, parent=None):
        super(RS_Workspace, self).__init__(parent)
        starttime = datetime.datetime.now()
        settings = QSettings("berkaygediz", "RichSpan")
        self.setWindowIcon(QIcon("icon.png"))
        self.setWindowModality(Qt.ApplicationModal)
        sqlite_file = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), 'richspan.db')
        sqlitedb = sqlite3.connect(sqlite_file)
        sqlitecursor = sqlitedb.cursor()
        user_email = sqlitecursor.execute(
            "SELECT email FROM profile").fetchone()[0]
        mysqlserver = serverconnect()
        mysqlcursor = mysqlserver.cursor()
        mysqlcursor.execute(
            "SELECT richspan FROM apps WHERE richspan = '1' AND email = %s", (user_email,))
        auth = mysqlcursor.fetchone()
        sqlitedb.close()
        mysqlserver.close()
        if auth is not None:
            self.richspan_thread = RS_Threading()
            self.richspan_thread.update_signal.connect(
                self.RS_updateStatistics)
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
            self.rs_area.setDisabled(True)
            self.RS_setupActions()
            self.RS_setupToolbar()
            self.setPalette(self.light_theme)
            self.rs_area.textChanged.connect(self.richspan_thread.start)
            self.showMaximized()
            self.rs_area.setFocus()
            self.rs_area.setAcceptRichText(True)
            QTimer.singleShot(50, self.RS_restoreTheme)
            QTimer.singleShot(150, self.RS_restoreState)
            self.rs_area.setDisabled(False)
            self.RS_updateTitle()
            endtime = datetime.datetime.now()
            self.status_bar.showMessage(
                str((endtime - starttime).total_seconds()) + " ms", 2500)
        else:
            activation = RS_ActivationStatus()
            activation.show()
            QTimer.singleShot(0, self.hide)

    def closeEvent(self, event):
        settings = QSettings("berkaygediz", "RichSpan")
        if self.is_saved == False:
            reply = QMessageBox.question(self, 'RichSpan',
                                         translations[settings.value("current_language")]["exit_message"], QMessageBox.Yes |
                                         QMessageBox.No, QMessageBox.No)

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
        settings.setValue("current_language", language)
        settings.sync()
        self.RS_updateTitle()
        self.RS_updateStatistics()
        self.RS_toolbarTranslate()

    def RS_updateTitle(self):
        settings = QSettings("berkaygediz", "RichSpan")
        if settings.value("current_language") == None:
            settings.setValue("current_language", "English")
            settings.sync()
        file = self.file_name if self.file_name else translations[settings.value(
            "current_language")]["new"]
        if self.is_saved == True:
            asterisk = ""
        else:
            asterisk = "*"
        self.setWindowTitle(f"{file}{asterisk} — RichSpan")

    def RS_updateStatistics(self):
        settings = QSettings("berkaygediz", "RichSpan")
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
            statistics += f"<th>{translations[settings.value(
                'current_language')]['analysis']}</th>"
            avg_word_length = sum(len(word)
                                  for word in text.split()) / word_count
            statistics += f"<td>{translations[settings.value(
                'current_language')]['analysis_message_1'].format(avg_word_length)}</td>"
            avg_line_length = character_count / line_count - 1
            statistics += f"<td>{translations[settings.value(
                'current_language')]['analysis_message_2'].format(avg_line_length)}</td>"
            uppercase_count = sum(1 for char in text if char.isupper())
            lowercase_count = sum(1 for char in text if char.islower())
            statistics += f"<td>{translations[settings.value(
                'current_language')]['analysis_message_3'].format(uppercase_count)}</td>"
            statistics += f"<td>{translations[settings.value(
                'current_language')]['analysis_message_4'].format(lowercase_count)}</td>"
        statistics += f"<th>{translations[settings.value(
            'current_language')]['statistic']}</th>"
        statistics += f"<td>{translations[settings.value(
            'current_language')]['statistic_message_1'].format(line_count)}</td>"
        statistics += f"<td>{translations[settings.value(
            'current_language')]['statistic_message_2'].format(word_count)}</td>"
        statistics += f"<td>{translations[settings.value(
            'current_language')]['statistic_message_3'].format(character_count)}</td>"
        statistics += f"<td>{translations[settings.value(
            'current_language')]['statistic_message_4'].format(page_count)}</td>"
        statistics += "</td><th id='rs-text'>RichSpan</th>"
        statistics += "</tr></table></body></html>"

        self.statistics_label.setText(statistics)
        self.status_bar.addPermanentWidget(self.statistics_label)
        self.new_text = self.rs_area.toPlainText()
        if self.new_text != default_values['text_content']:
            self.is_saved = False
        else:
            self.is_saved = True
        self.RS_updateTitle()

    def RS_saveState(self):
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
        settings.setValue("current_language",
                          self.language_combobox.currentText())
        settings.sync()

    def RS_restoreState(self):
        settings = QSettings("berkaygediz", "RichSpan")
        self.geometry = settings.value("window_geometry")
        self.directory = settings.value(
            "default_directory", self.default_directory)
        self.file_name = settings.value("file_name")
        self.rs_area.setPlainText(settings.value("text_content"))
        self.is_saved = settings.value("is_saved")
        self.language_combobox.setCurrentText(
            settings.value("current_language"))

        if self.geometry is not None:
            self.restoreGeometry(self.geometry)

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

        self.RS_restoreTheme()
        self.RS_updateTitle()

    def RS_restoreTheme(self):
        settings = QSettings("berkaygediz", "RichSpan")
        if settings.value("current_theme") == 'dark':
            self.setPalette(self.dark_theme)
        else:
            self.setPalette(self.light_theme)
        self.RS_toolbarTheme()

    def RS_themePalette(self):
        self.light_theme = QPalette()
        self.dark_theme = QPalette()

        self.light_theme.setColor(QPalette.Window, QColor(89, 111, 183))
        self.light_theme.setColor(QPalette.WindowText, QColor(37, 38, 39))
        self.light_theme.setColor(QPalette.Base, QColor(255, 255, 255))
        self.light_theme.setColor(QPalette.Text, QColor(0, 0, 0))
        self.light_theme.setColor(QPalette.Highlight, QColor(221, 216, 184))
        self.light_theme.setColor(QPalette.ButtonText, QColor(37, 38, 39))

        self.dark_theme.setColor(QPalette.Window, QColor(58, 68, 93))
        self.dark_theme.setColor(QPalette.WindowText, QColor(239, 213, 195))
        self.dark_theme.setColor(QPalette.Base, QColor(94, 87, 104))
        self.dark_theme.setColor(QPalette.Text, QColor(255, 255, 255))
        self.dark_theme.setColor(QPalette.Highlight, QColor(221, 216, 184))

    def RS_themeAction(self):
        settings = QSettings("berkaygediz", "RichSpan")
        if self.palette() == self.light_theme:
            self.setPalette(self.dark_theme)
            settings.setValue("current_theme", "dark")
        else:
            self.setPalette(self.light_theme)
            settings.setValue("current_theme", "light")
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
        self.newaction.setText(translations[settings.value(
            "current_language")]["new"])
        self.newaction.setStatusTip(translations[settings.value(
            "current_language")]["new_message"])
        self.openaction.setText(translations[settings.value(
            "current_language")]["open"])
        self.openaction.setStatusTip(translations[settings.value(
            "current_language")]["open_message"])
        self.saveaction.setText(translations[settings.value(
            "current_language")]["save"])
        self.saveaction.setStatusTip(translations[settings.value(
            "current_language")]["save_message"])
        self.saveasaction.setText(translations[settings.value(
            "current_language")]["save_as"])
        self.saveasaction.setStatusTip(translations[settings.value(
            "current_language")]["save_as_message"])
        self.printaction.setText(translations[settings.value(
            "current_language")]["print"])
        self.printaction.setStatusTip(translations[settings.value(
            "current_language")]["print_message"])
        self.undoaction.setText(translations[settings.value(
            "current_language")]["undo"])
        self.undoaction.setStatusTip(translations[settings.value(
            "current_language")]["undo_message"])
        self.redoaction.setText(translations[settings.value(
            "current_language")]["redo"])
        self.redoaction.setStatusTip(translations[settings.value(
            "current_language")]["redo_message"])
        self.toggle_view_action.setText(translations[settings.value(
            "current_language")]["viewmode"])
        self.toggle_view_action.setStatusTip(translations[settings.value(
            "current_language")]["viewmode_message"])
        self.theme_action.setText(translations[settings.value(
            "current_language")]["darklight"])
        self.theme_action.setStatusTip(translations[settings.value(
            "current_language")]["darklight_message"])
        self.saveworkspaceaction.setText(translations[settings.value(
            "current_language")]["save_workspace"])
        self.saveworkspaceaction.setStatusTip(translations[settings.value(
            "current_language")]["save_workspace_message"])
        self.findaction.setText(translations[settings.value(
            "current_language")]["find"])
        self.findaction.setStatusTip(translations[settings.value(
            "current_language")]["find_message"])
        self.replaceaction.setText(translations[settings.value(
            "current_language")]["replace"])
        self.replaceaction.setStatusTip(translations[settings.value(
            "current_language")]["replace_message"])
        self.aboutaction.setText(translations[settings.value(
            "current_language")]["about"])
        self.aboutaction.setStatusTip(translations[settings.value(
            "current_language")]["about"])
        self.logoutaction.setText(translations[settings.value(
            "current_language")]["logout"])
        self.logoutaction.setStatusTip(translations[settings.value(
            "current_language")]["logout"])
        self.syncsettingsaction.setText(translations[settings.value(
            "current_language")]["sync_settings"])
        self.syncsettingsaction.setStatusTip(translations[settings.value(
            "current_language")]["sync_settings"])
        self.alignrightevent.setText(translations[settings.value(
            "current_language")]["right"])
        self.alignrightevent.setStatusTip(translations[settings.value(
            "current_language")]["right_message"])
        self.aligncenterevent.setText(translations[settings.value(
            "current_language")]["center"])
        self.aligncenterevent.setStatusTip(translations[settings.value(
            "current_language")]["center_message"])
        self.alignleftevent.setText(translations[settings.value(
            "current_language")]["left"])
        self.alignleftevent.setStatusTip(translations[settings.value(
            "current_language")]["left_message"])
        self.alignjustifiedevent.setText(translations[settings.value(
            "current_language")]["justify"])
        self.alignjustifiedevent.setStatusTip(translations[settings.value(
            "current_language")]["justify_message"])
        self.color.setText(translations[settings.value(
            "current_language")]["font_color"])
        self.color.setStatusTip(translations[settings.value(
            "current_language")]["font_color_message"])
        self.backgroundcolor.setText(translations[settings.value(
            "current_language")]["background_color"])
        self.backgroundcolor.setStatusTip(translations[settings.value(
            "current_language")]["background_color_message"])
        self.dock_widget.setWindowTitle(translations[settings.value(
            "current_language")]["help"])
        self.dock_widget.setWidget(self.help_label)
        self.help_label.setText("<html><head><style>"
                                "table {border-collapse: collapse; width: 100%;}"
                                "th, td {text-align: left; padding: 8px;}"
                                "tr:nth-child(even) {background-color: #f2f2f2;}"
                                "tr:hover {background-color: #ddd;}"
                                "th {background-color: #4CAF50; color: white;}"
                                "</style></head><body>"
                                "<table><tr>"
                                f"<th>{translations[settings.value(
                                    'current_language')]['help_shortcut']}</th>"
                                f"<th>{translations[settings.value(
                                    'current_language')]['help_description']}</th>"
                                f"</tr><tr><td>Ctrl+N</td><td>{
                                    translations[settings.value('current_language')]['new_message']}</td></tr>"
                                f"<tr><td>Ctrl+O</td><td>{translations[settings.value(
                                    'current_language')]['open_message']}</td></tr>"
                                f"<tr><td>Ctrl+S</td><td>{translations[settings.value(
                                    'current_language')]['save_message']}</td></tr>"
                                f"<tr><td>Ctrl+Shift+S</td><td>{translations[settings.value(
                                    'current_language')]['save_as_message']}</td></tr>"
                                f"<tr><td>Ctrl+P</td><td>{translations[settings.value(
                                    'current_language')]['print_message']}</td></tr>"
                                f"<tr><td>Ctrl+Z</td><td>{translations[settings.value(
                                    'current_language')]['undo_message']}</td></tr>"
                                f"<tr><td>Ctrl+Y</td><td>{translations[settings.value(
                                    'current_language')]['redo_message']}</td></tr>"
                                f"<tr><td>Ctrl+Shift+V</td><td>{translations[settings.value(
                                    'current_language')]['viewmode_message']}</td></tr>"
                                f"<tr><td>Ctrl+Shift+T</td><td>{translations[settings.value(
                                    'current_language')]['darklight_message']}</td></tr>"
                                f"<tr><td>Ctrl+Shift+D</td><td>{
                                    translations[settings.value('current_language')]['help_message']}</td></tr>"
                                f"<tr><td>Ctrl+Shift+C</td><td>{translations[settings.value(
                                    'current_language')]['font_color_message']}</td></tr>"
                                f"<tr><td>Ctrl+Shift+B</td><td>{translations[settings.value(
                                    'current_language')]['background_color_message']}</td></tr>"
                                f"<tr><td>Ctrl+Shift+F</td><td>{
                                    translations[settings.value('current_language')]['font_message']}</td></tr>"
                                f"<tr><td>Ctrl++</td><td>{translations[settings.value(
                                    'current_language')]['inc_font_message']}</td></tr>"
                                f"<tr><td>Ctrl+-</td><td>{translations[settings.value(
                                    'current_language')]['dec_font_message']}</td></tr>"
                                f"<tr><td>Ctrl+Shift+P</td><td>{translations[settings.value(
                                    'current_language')]['image_message']}</td></tr>"
                                f"<tr><td>Ctrl+Shift+W+S</td><td>{translations[settings.value(
                                    'current_language')]['save_workspace_message']}</td></tr>"
                                f"<tr><td>Ctrl+F</td><td>{translations[settings.value(
                                    'current_language')]['find_message']}</td></tr>"
                                f"<tr><td>Ctrl+H</td><td>{translations[settings.value(
                                    'current_language')]['replace_message']}</td></tr>"
                                f"<tr><td>Ctrl+Shift+U</td><td>{translations[settings.value(
                                    'current_language')]['bullet']}</td></tr>"
                                f"<tr><td>Ctrl+Shift+O</td><td>{translations[settings.value(
                                    'current_language')]['numbered']}</td></tr>"
                                f"<tr><td>Ctrl+Shift+R</td><td>{translations[settings.value(
                                    'current_language')]['right']}</td></tr>"
                                f"<tr><td>Ctrl+Shift+L</td><td>{translations[settings.value(
                                    'current_language')]['left']}</td></tr>"
                                f"<tr><td>Ctrl+Shift+E</td><td>{translations[settings.value(
                                    'current_language')]['center']}</td></tr>"
                                f"<tr><td>Ctrl+Shift+J</td><td>{translations[settings.value(
                                    'current_language')]['justify']}</td></tr>"
                                "</table></body></html>")

    def RS_setupArea(self):
        self.rs_area.setFontFamily(default_values['font_family'])
        self.rs_area.setFontPointSize(default_values['font_size'])
        self.rs_area.setFontWeight(
            75 if default_values['bold'] else 50)
        self.rs_area.setFontItalic(default_values['italic'])
        self.rs_area.setFontUnderline(default_values['underline'])
        self.rs_area.setAlignment(default_values['alignment'])
        self.rs_area.setTextColor(
            QColor(default_values['text_color']))
        self.rs_area.setTextBackgroundColor(
            QColor(default_values['background_color']))
        self.rs_area.setTabStopWidth(33)
        self.rs_area.document().setDocumentMargin(self.width() * 0.25)

        self.setCentralWidget(self.rs_area)

    def RS_setupDock(self):
        settings = QSettings("berkaygediz", "RichSpan")
        settings.setValue("current_language", "English")
        settings.sync()
        self.dock_widget = QDockWidget(translations[settings.value(
            "current_language")]["help"], self)
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
                                f"<th>{translations[settings.value(
                                    'current_language')]['help_shortcut']}</th>"
                                f"<th>{translations[settings.value(
                                    'current_language')]['help_description']}</th>"
                                f"</tr><tr><td>Ctrl+N</td><td>{
                                    translations[settings.value('current_language')]['new_message']}</td></tr>"
                                f"<tr><td>Ctrl+O</td><td>{translations[settings.value(
                                    'current_language')]['open_message']}</td></tr>"
                                f"<tr><td>Ctrl+S</td><td>{translations[settings.value(
                                    'current_language')]['save_message']}</td></tr>"
                                f"<tr><td>Ctrl+Shift+S</td><td>{translations[settings.value(
                                    'current_language')]['save_as_message']}</td></tr>"
                                f"<tr><td>Ctrl+P</td><td>{translations[settings.value(
                                    'current_language')]['print_message']}</td></tr>"
                                f"<tr><td>Ctrl+Z</td><td>{translations[settings.value(
                                    'current_language')]['undo_message']}</td></tr>"
                                f"<tr><td>Ctrl+Y</td><td>{translations[settings.value(
                                    'current_language')]['redo_message']}</td></tr>"
                                f"<tr><td>Ctrl+Shift+V</td><td>{translations[settings.value(
                                    'current_language')]['viewmode_message']}</td></tr>"
                                f"<tr><td>Ctrl+Shift+T</td><td>{translations[settings.value(
                                    'current_language')]['darklight_message']}</td></tr>"
                                f"<tr><td>Ctrl+Shift+D</td><td>{
                                    translations[settings.value('current_language')]['help_message']}</td></tr>"
                                f"<tr><td>Ctrl+Shift+C</td><td>{translations[settings.value(
                                    'current_language')]['font_color_message']}</td></tr>"
                                f"<tr><td>Ctrl+Shift+B</td><td>{translations[settings.value(
                                    'current_language')]['background_color_message']}</td></tr>"
                                f"<tr><td>Ctrl+Shift+F</td><td>{
                                    translations[settings.value('current_language')]['font_message']}</td></tr>"
                                f"<tr><td>Ctrl++</td><td>{translations[settings.value(
                                    'current_language')]['inc_font_message']}</td></tr>"
                                f"<tr><td>Ctrl+-</td><td>{translations[settings.value(
                                    'current_language')]['dec_font_message']}</td></tr>"
                                f"<tr><td>Ctrl+Shift+P</td><td>{translations[settings.value(
                                    'current_language')]['image_message']}</td></tr>"
                                f"<tr><td>Ctrl+Shift+W+S</td><td>{translations[settings.value(
                                    'current_language')]['save_workspace_message']}</td></tr>"
                                f"<tr><td>Ctrl+F</td><td>{translations[settings.value(
                                    'current_language')]['find_message']}</td></tr>"
                                f"<tr><td>Ctrl+H</td><td>{translations[settings.value(
                                    'current_language')]['replace_message']}</td></tr>"
                                f"<tr><td>Ctrl+Shift+U</td><td>{translations[settings.value(
                                    'current_language')]['bullet']}</td></tr>"
                                f"<tr><td>Ctrl+Shift+O</td><td>{translations[settings.value(
                                    'current_language')]['numbered']}</td></tr>"
                                f"<tr><td>Ctrl+Shift+R</td><td>{translations[settings.value(
                                    'current_language')]['right']}</td></tr>"
                                f"<tr><td>Ctrl+Shift+L</td><td>{translations[settings.value(
                                    'current_language')]['left']}</td></tr>"
                                f"<tr><td>Ctrl+Shift+E</td><td>{translations[settings.value(
                                    'current_language')]['center']}</td></tr>"
                                f"<tr><td>Ctrl+Shift+J</td><td>{translations[settings.value(
                                    'current_language')]['justify']}</td></tr>"
                                "</table></body></html>")

        self.dock_widget.setWidget(self.help_label)
        self.dock_widget.setObjectName("Help")
        self.dock_widget.setAllowedAreas(
            Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_widget)

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
            action.setIcon(QIcon(icon))
        return action

    def RS_setupActions(self):
        settings = QSettings("berkaygediz", "RichSpan")
        icon_theme = "white"
        if self.palette() == self.light_theme:
            icon_theme = "black"
        actionicon = qta.icon('fa5.file', color=icon_theme)
        self.newaction = self.RS_createAction(
            translations[settings.value("current_language")]["new"], translations[settings.value("current_language")]["new_message"], self.new, QKeySequence.New, actionicon)
        actionicon = qta.icon('fa5.folder-open', color=icon_theme)
        self.openaction = self.RS_createAction(
            translations[settings.value("current_language")]["open"], translations[settings.value("current_language")]["open_message"], self.open, QKeySequence.Open, actionicon)
        actionicon = qta.icon('fa5s.save', color=icon_theme)
        self.saveaction = self.RS_createAction(
            translations[settings.value("current_language")]["save"], translations[settings.value("current_language")]["save_message"], self.save, QKeySequence.Save, actionicon)
        actionicon = qta.icon('fa5.save', color=icon_theme)
        self.saveasaction = self.RS_createAction(
            translations[settings.value("current_language")]["save_as"], translations[settings.value("current_language")]["save_as_message"], self.saveAs, QKeySequence.SaveAs, actionicon)
        actionicon = qta.icon('fa5s.print', color=icon_theme)
        self.printaction = self.RS_createAction(
            translations[settings.value("current_language")]["print"], translations[settings.value("current_language")]["print_message"], self.print, QKeySequence.Print, actionicon)
        self.saveworkspaceaction = self.RS_createAction(
            translations[settings.value("current_language")]["save_workspace"], translations[settings.value("current_language")]["save_workspace_message"], self.RS_saveState, QKeySequence("Ctrl+Shift+W+S"))
        actionicon = qta.icon('fa5s.search', color=icon_theme)
        self.findaction = self.RS_createAction(
            translations[settings.value("current_language")]["find"], translations[settings.value("current_language")]["find_message"], self.find, QKeySequence.Find, actionicon)
        actionicon = qta.icon('fa5s.exchange-alt', color=icon_theme)
        self.replaceaction = self.RS_createAction(
            translations[settings.value("current_language")]["replace"], translations[settings.value("current_language")]["replace_message"], self.replace, QKeySequence.Replace, actionicon)
        actionicon = qta.icon('fa5s.undo-alt', color=icon_theme)
        self.undoaction = self.RS_createAction(
            translations[settings.value("current_language")]["undo"], translations[settings.value("current_language")]["undo_message"], self.rs_area.undo, QKeySequence.Undo, actionicon)
        actionicon = qta.icon('fa5s.redo-alt', color=icon_theme)
        self.redoaction = self.RS_createAction(
            translations[settings.value("current_language")]["redo"], translations[settings.value("current_language")]["redo_message"], self.rs_area.redo, QKeySequence.Redo, actionicon)
        self.alignrightevent = self.RS_createAction(
            translations[settings.value("current_language")]["right"], translations[settings.value("current_language")]["right_message"], lambda: self.align(Qt.AlignRight))
        self.alignleftevent = self.RS_createAction(
            translations[settings.value("current_language")]["left"], translations[settings.value("current_language")]["left_message"], lambda: self.align(Qt.AlignLeft))
        self.aligncenterevent = self.RS_createAction(
            translations[settings.value("current_language")]["center"], translations[settings.value("current_language")]["center_message"], lambda: self.align(Qt.AlignCenter))
        self.alignjustifiedevent = self.RS_createAction(
            translations[settings.value("current_language")]["justify"], translations[settings.value("current_language")]["justify_message"], lambda: self.align(Qt.AlignJustify))
        actionicon = qta.icon('fa5s.list-ul', color=icon_theme)
        self.bulletevent = self.RS_createAction(translations[settings.value(
            "current_language")]["bullet"], "", self.bullet, QKeySequence("Ctrl+Shift+U"), actionicon)
        actionicon = qta.icon('fa5s.list-ol', color=icon_theme)
        self.numberedevent = self.RS_createAction(translations[settings.value(
            "current_language")]["numbered"], "", self.numbered, QKeySequence("Ctrl+Shift+O"), actionicon)
        actionicon = qta.icon('fa5s.bold', color=icon_theme)
        self.bold = self.RS_createAction(
            translations[settings.value("current_language")]["bold"], translations[settings.value("current_language")]["bold_message"], self.contentBold, QKeySequence.Bold, actionicon)
        actionicon = qta.icon('fa5s.italic', color=icon_theme)
        self.italic = self.RS_createAction(
            translations[settings.value("current_language")]["italic"], translations[settings.value("current_language")]["italic_message"], self.contentItalic, QKeySequence.Italic, actionicon)
        actionicon = qta.icon('fa5s.underline', color=icon_theme)
        self.underline = self.RS_createAction(
            translations[settings.value("current_language")]["underline"], translations[settings.value("current_language")]["underline_message"], self.contentUnderline, QKeySequence.Underline, actionicon)
        actionicon = qta.icon('fa5s.palette', color=icon_theme)
        self.color = self.RS_createAction(
            translations[settings.value("current_language")]["font_color"], translations[settings.value("current_language")]["font_color_message"], self.contentColor, QKeySequence("Ctrl+Shift+C"), actionicon)
        actionicon = qta.icon('fa5s.fill-drip', color=icon_theme)
        self.backgroundcolor = self.RS_createAction(
            translations[settings.value("current_language")]["background_color"], translations[settings.value("current_language")]["background_color_message"], self.contentBGColor, QKeySequence("Ctrl+Shift+B"), actionicon)
        actionicon = qta.icon('fa5s.font', color=icon_theme)
        self.fontfamily = self.RS_createAction(
            translations[settings.value("current_language")]["font"], translations[settings.value("current_language")]["font_message"], self.contentFont, QKeySequence("Ctrl+Shift+F"), actionicon)
        self.inc_fontaction = self.RS_createAction(
            "A+", translations[settings.value("current_language")]["inc_font_message"], self.inc_font, QKeySequence("Ctrl++"))
        self.dec_fontaction = self.RS_createAction(
            "A-", translations[settings.value("current_language")]["dec_font_message"], self.dec_font, QKeySequence("Ctrl+-"))
        actionicon = qta.icon('fa5s.image', color=icon_theme)
        self.addimage = self.RS_createAction(
            translations[settings.value("current_language")]["image"], translations[settings.value("current_language")]["image_message"], self.contentAddImage, QKeySequence("Ctrl+Shift+P"), actionicon)
        actionicon = qta.icon('fa5s.info-circle', color=icon_theme)
        self.aboutaction = self.RS_createAction(
            translations[settings.value("current_language")]["about"], "", self.showAbout, QKeySequence("Ctrl+Shift+I"), actionicon)
        actionicon = qta.icon('fa5s.sign-out-alt', color=icon_theme)
        self.logoutaction = self.RS_createAction(
            translations[settings.value("current_language")]["logout"], "", self.logout, QKeySequence("Ctrl+Shift+L"), actionicon)
        actionicon = qta.icon('fa5s.sync', color=icon_theme)
        self.syncsettingsaction = self.RS_createAction(translations[settings.value(
            "current_language")]["sync_settings"], "", self.syncsettings, QKeySequence("Ctrl+Shift+S+Y"), actionicon)

    def syncsettings(self):
        settings = QSettings("berkaygediz", "RichSpan")
        sqlite_file = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), 'richspan.db')
        sqliteConnection = sqlite3.connect(sqlite_file).cursor()
        user_email = sqliteConnection.execute(
            "SELECT email FROM profile").fetchone()[0]
        sqliteConnection.connection.commit()
        sqliteConnection.connection.close()
        try:
            mysqlserver = serverconnect()
            mysqlcursor = mysqlserver.cursor()

            mysqlcursor.execute("UPDATE user_settings SET theme = %s, language = %s WHERE email = %s AND product = %s", (
                settings.value("current_theme"), settings.value("current_language"), user_email, "RichSpan"))
            mysqlserver.commit()
            mysqlserver.close()
            QMessageBox.information(self, "RichSpan",
                                    "Settings synced successfully.")
        except:
            QMessageBox.critical(self, "RichSpan",
                                 "Error while syncing settings. Please try again later.")

    def logout(self):
        sqlite_file = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), 'richspan.db')
        sqliteConnection = sqlite3.connect(sqlite_file).cursor()
        sqliteConnection.execute("DROP TABLE IF EXISTS profile")
        sqliteConnection.connection.commit()
        sqliteConnection.execute("DROP TABLE IF EXISTS apps")
        sqliteConnection.connection.commit()
        sqliteConnection.execute("DROP TABLE IF EXISTS log")
        sqliteConnection.connection.commit()
        try:
            settings = QSettings("berkaygediz", "RichSpan")
            settings.clear()
            settings.sync()
        except:
            pass
        QTimer.singleShot(0, self.hide)
        QTimer.singleShot(750, RS_ControlInfo().show)

    def RS_setupToolbar(self):
        settings = QSettings("berkaygediz", "RichSpan")

        self.toolbar = self.addToolBar(
            translations[settings.value("current_language")]["file"])
        self.RS_toolbarLabel(self.toolbar, translations[settings.value(
            "current_language")]["file"] + ": ")
        self.toolbar.addActions([self.newaction, self.openaction, self.saveaction, self.saveasaction,
                                self.printaction, self.undoaction, self.redoaction, self.findaction, self.replaceaction, self.saveworkspaceaction])

        self.toolbar = self.addToolBar(
            translations[settings.value("current_language")]["ui"])
        self.RS_toolbarLabel(
            self.toolbar, translations[settings.value("current_language")]["ui"] + ": ")
        actionicon = qta.icon('fa5b.affiliatetheme', color="white")
        self.theme_action = self.RS_createAction(
            translations[settings.value("current_language")]["darklight"], translations[settings.value("current_language")]["darklight_message"], self.RS_themeAction, QKeySequence("Ctrl+Shift+T"), actionicon)
        self.toolbar.addAction(self.theme_action)
        actionicon = qta.icon('fa5s.question-circle', color="white")
        self.hide_dock_widget_action = self.RS_createAction(
            translations[settings.value("current_language")]["help"], translations[settings.value("current_language")]["help_message"], self.RS_toggleDock, QKeySequence("Ctrl+Shift+D"), actionicon)
        self.toolbar.addAction(self.hide_dock_widget_action)
        actionicon = qta.icon('fa5s.eye', color="white")
        self.toggle_view_action = self.RS_createAction(
            translations[settings.value("current_language")]["viewmode"], translations[settings.value("current_language")]["viewmode_message"], self.RS_toggleViewmode, QKeySequence("Ctrl+Shift+V"), actionicon)
        self.toolbar.addAction(self.toggle_view_action)
        self.language_combobox = QComboBox(self)
        self.language_combobox.addItems(
            ["English", "Türkçe", "Azərbaycanca", "Deutsch", "Español"])
        self.language_combobox.currentIndexChanged.connect(
            self.RS_changeLanguage)
        self.toolbar.addWidget(self.language_combobox)

        sqlite_file = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), 'richspan.db')
        sqliteConnection = sqlite3.connect(sqlite_file).cursor()
        user_email = sqliteConnection.execute(
            "SELECT email FROM profile").fetchone()[0]
        sqliteConnection.connection.commit()
        sqliteConnection.connection.close()
        mysqlserver = serverconnect()
        mysqlcursor = mysqlserver.cursor()
        mysqlcursor.execute(
            "SELECT * FROM user_settings WHERE email = %s AND product = %s", (user_email, "RichSpan"))
        user_settings = mysqlcursor.fetchone()
        mysqlserver.close()
        if user_settings is not None:
            settings.setValue("current_theme", user_settings[3])
            settings.setValue("current_language", user_settings[4])
            self.language_combobox.setCurrentText(user_settings[4])
            settings.sync()
        else:
            settings.setValue("current_theme", "light")
            settings.setValue("current_language", "English")
            settings.sync()

        self.aboutaction = self.RS_createAction(
            translations[settings.value("current_language")]["about"], "", self.showAbout)
        self.toolbar.addAction(self.aboutaction)

        self.toolbar = self.addToolBar(translations[settings.value(
            "current_language")]["account"])
        self.RS_toolbarLabel(self.toolbar, translations[settings.value(
            "current_language")]["account"] + ": ")
        sqlite_file = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), 'richspan.db')
        sqliteConnection = sqlite3.connect(sqlite_file).cursor()
        user_email = sqliteConnection.execute(
            "SELECT email FROM profile").fetchone()[0]
        self.user_name = QLabel(user_email)
        self.user_name.setStyleSheet("color: white; font-weight: bold;")
        self.toolbar.addWidget(self.user_name)
        self.toolbar.addAction(self.logoutaction)
        self.toolbar.addAction(self.syncsettingsaction)
        self.addToolBarBreak()

        self.toolbar = self.addToolBar(
            translations[settings.value("current_language")]["edit"])
        self.RS_toolbarLabel(self.toolbar, translations[settings.value(
            "current_language")]["edit"] + ": ")
        self.toolbar.addActions(
            [self.alignrightevent, self.aligncenterevent, self.alignleftevent, self.alignjustifiedevent])
        self.toolbar.addSeparator()
        self.RS_toolbarLabel(self.toolbar, translations[settings.value(
            "current_language")]["font"] + ": ")
        self.toolbar.addActions([self.bold, self.italic, self.underline])
        self.toolbar.addSeparator()
        self.toolbar = self.addToolBar(translations[settings.value(
            "current_language")]["list"])
        self.RS_toolbarLabel(
            self.toolbar, translations[settings.value("current_language")]["list"] + ": ")
        self.toolbar.addActions([self.bulletevent, self.numberedevent])
        self.addToolBarBreak()

        self.toolbar = self.addToolBar(
            translations[settings.value("current_language")]["color"])
        self.RS_toolbarLabel(self.toolbar, translations[settings.value(
            "current_language")]["color"] + ": ")
        self.toolbar.addActions(
            [self.color, self.backgroundcolor, self.fontfamily, self.inc_fontaction, self.dec_fontaction])

        self.toolbar = self.addToolBar(
            translations[settings.value("current_language")]["multimedia"])
        self.RS_toolbarLabel(self.toolbar, translations[settings.value(
            "current_language")]["multimedia"] + ": ")
        self.toolbar.addActions([self.addimage])

    def RS_toggleDock(self):
        if self.dock_widget.isHidden():
            self.dock_widget.show()
        else:
            self.dock_widget.hide()

    def RS_toggleViewmode(self):
        if self.rs_area.isReadOnly():
            self.rs_area.setReadOnly(False)
            self.rs_area.setHtml(self.rs_area.toPlainText())
            self.toggle_view_action.setText("Rich Text")
        else:
            self.rs_area.setReadOnly(True)
            self.rs_area.setPlainText(self.rs_area.toHtml())
            self.toggle_view_action.setText("Plain Text")

    def new(self):
        settings = QSettings("berkaygediz", "RichSpan")
        if self.is_saved == True:
            self.rs_area.clear()
            self.rs_area.setFontFamily(default_values['font_family'])
            self.rs_area.setFontPointSize(default_values['font_size'])
            self.rs_area.setFontWeight(
                75 if default_values['bold'] else 50)
            self.rs_area.setFontItalic(default_values['italic'])
            self.rs_area.setFontUnderline(default_values['underline'])
            self.rs_area.setAlignment(default_values['alignment'])
            self.rs_area.setTextColor(
                QColor(default_values['text_color']))
            self.rs_area.setTextBackgroundColor(
                QColor(default_values['background_color']))
            self.rs_area.setTabStopWidth(33)
            self.directory = self.default_directory
            self.file_name = None
            self.is_saved = False
            self.RS_updateTitle()
        else:
            reply = QMessageBox.question(self, 'RichSpan',
                                         translations[settings.value("current_language")]["new_message"], QMessageBox.Yes |
                                         QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.Yes:
                self.rs_area.clear()
                self.rs_area.setFontFamily(default_values['font_family'])
                self.rs_area.setFontPointSize(default_values['font_size'])
                self.rs_area.setFontWeight(
                    75 if default_values['bold'] else 50)
                self.rs_area.setFontItalic(default_values['italic'])
                self.rs_area.setFontUnderline(default_values['underline'])
                self.rs_area.setAlignment(default_values['alignment'])
                self.rs_area.setTextColor(
                    QColor(default_values['text_color']))
                self.rs_area.setTextBackgroundColor(
                    QColor(default_values['background_color']))
                self.rs_area.setTabStopWidth(33)
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
        file_filter = f"{translations[settings.value(
            'current_language')]['rsdoc']} (*.rsdoc);;HTML (*.html);;Text (*.txt);;Key-Value (*.ini);;LOG (*.log);;JavaScript Object Notation (*.json);;Extensible Markup Language (*.xml);;Javascript (*.js);;Cascading Style Sheets (*.css);;Structured Query Language (*.sql);;Markdown (*.md)"
        selected_file, _ = QFileDialog.getOpenFileName(
            self, translations[settings.value("current_language")]["open"] + " — RichSpan ", self.directory, file_filter, options=options)
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
        file_filter = f"{translations[settings.value(
            'current_language')]['rsdoc']} (*.rsdoc);;HTML (*.html);;Text (*.txt);;Key-Value (*.ini);;LOG (*.log);;JavaScript Object Notation (*.json);;Extensible Markup Language (*.xml);;Javascript (*.js);;Cascading Style Sheets (*.css);;Structured Query Language (*.sql);;Markdown (*.md)"
        selected_file, _ = QFileDialog.getSaveFileName(
            self, translations[settings.value("current_language")]["save_as"] + " — RichSpan ", self.directory, file_filter, options=options)
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
            with open(self.file_name, 'w', encoding='utf-8') as file:
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
        printer.setOrientation(QPrinter.Portrait)
        printer.setPageMargins(10, 10, 10, 10, QPrinter.Millimeter)
        printer.setFullPage(True)
        printer.setDocName(self.file_name)

        preview_dialog = QPrintPreviewDialog(printer, self)
        preview_dialog.paintRequested.connect(self.rs_area.print_)
        preview_dialog.exec_()

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
        file_filter = "Portable Network Graphics (*.png);;JPEG (*.jpg *.jpeg);;Bitmap (*.bmp);;GIF (*.gif)"
        selected_file, _ = QFileDialog.getOpenFileName(
            self, "Open", self.directory, file_filter, options=options)
        if selected_file:
            with open(selected_file, 'rb') as file:
                data = file.read()
                data = base64.b64encode(data)
                data = data.decode('utf-8')
                self.rs_area.insertHtml(
                    f'<img src="data:image/png;base64,{data}"/>')

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
        self.find_dialog.setLabelText(
            translations[settings.value("current_language")]["find"])
        self.find_dialog.setWindowTitle(
            translations[settings.value("current_language")]["find"])
        self.find_dialog.setOkButtonText(
            translations[settings.value("current_language")]["find"])
        self.find_dialog.setCancelButtonText(
            translations[settings.value("current_language")]["cancel"])
        self.find_dialog.textValueSelected.connect(self.findText)
        self.find_dialog.show()

    def findText(self, text):
        self.rs_area.find(text)

    def replace(self):
        settings = QSettings("berkaygediz", "RichSpan")
        self.replace_dialog = QInputDialog(self)
        self.replace_dialog.setInputMode(QInputDialog.TextInput)
        self.replace_dialog.setLabelText(
            translations[settings.value("current_language")]["replace"])
        self.replace_dialog.setWindowTitle(
            translations[settings.value("current_language")]["replace"])
        self.replace_dialog.setOkButtonText(
            translations[settings.value("current_language")]["replace"])
        self.replace_dialog.setCancelButtonText(
            translations[settings.value("current_language")]["cancel"])
        self.replace_dialog.textValueSelected.connect(self.replaceText)
        self.replace_dialog.show()

    def replaceText(self, text):
        self.rs_area.find(text)
        self.rs_area.insertPlainText(text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setOrganizationName("berkaygediz")
    app.setApplicationName("RichSpan")
    app.setApplicationDisplayName("RichSpan")
    app.setApplicationVersion("1.3.10")
    ci = RS_ControlInfo()
    ci.show()
    sys.exit(app.exec_())
