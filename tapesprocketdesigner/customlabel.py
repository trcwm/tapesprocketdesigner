# Copyright 2023 - 2023, Niels Moseley and the pyrigremote contributors
# SPDX-License-Identifier: GPL-3.0-only

from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *

class CustomLabel(QLabel):

    enter = Signal()
    leave = Signal()

    def __init__(self, name : str):
        super(CustomLabel, self).__init__(name)
        self.originalStyle = self.styleSheet()

    def enterEvent(self, enterEvent : QEvent):
        self.setStyleSheet("background-color: lightgreen ")
        #self.setStyleSheet("border-width: 1px; border-style: solid; border-color: green")
        self.enter.emit()

    def leaveEvent(self, leaveEvent : QEvent):
        self.setStyleSheet(self.originalStyle)
        self.leave.emit()

#border-width: 1px; border-style: solid; border-color:  red white black black;border-top-style:none;