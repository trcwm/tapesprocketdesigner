# Copyright 2023 - 2023, Niels Moseley and the pyrigremote contributors
# SPDX-License-Identifier: GPL-3.0-only

from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import Qt, QPointF

class SprocketCanvas(QWidget):

    def __init__(self):
        super().__init__()
        self.lines = []
        self.userOuterRadius = 1000000
        self.circleRadius = 0.0

    def paintEvent(self, paintEvent):
        painter = QPainter(self)
        brush = QBrush()
        brush.setColor(QColor('lightgrey'))
        brush.setStyle(Qt.BrushStyle.SolidPattern)
        painter.fillRect(self.rect(), brush)

        center = self.rect().center()

        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QColor('black'))
        for L in self.lines:
            start = QPointF(center.x() + self.k*L[0][0], center.y() - self.k*L[0][1])
            stop  = QPointF(center.x() + self.k*L[1][0], center.y() - self.k*L[1][1])
            painter.drawLine(start, stop)

        if (self.circleRadius > 0):
            painter.setPen(QPen(QColor('green'), 2))
            painter.drawEllipse(center, self.k*self.circleRadius, self.k*self.circleRadius)
            
    def setCircle(self, radius : float):
        self.circleRadius = radius
        self.update()

    def setLines(self, lines, user_outer_radius):
        self.lines = lines
        self.userOuterRadius = user_outer_radius        
        self.k = ((min(self.width(), self.height()) + 0.0) / (self.userOuterRadius*2.0)) * 0.75
        self.update()

    def getLines(self): 
        return self.lines

    def resizeEvent(self, sizeEvent):
        self.k = ((min(self.width(), self.height()) + 0.0) / (self.userOuterRadius*2.0)) * 0.75
