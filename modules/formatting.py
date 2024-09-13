from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from modules.globals import *


class FormattingEngine:
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

    def inc_font(self):
        font = self.rs_area.currentFont()
        font.setPointSize(font.pointSize() + 1)
        self.rs_area.setCurrentFont(font)

    def dec_font(self):
        font = self.rs_area.currentFont()
        font.setPointSize(font.pointSize() - 1)
        self.rs_area.setCurrentFont(font)
