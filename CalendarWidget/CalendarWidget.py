import sys
import os
import json
import zipfile
import requests
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout,
    QLabel
)
from PyQt5.QtCore import Qt
class CalendarWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        label = QLabel("Calendar Widget")
        label.setStyleSheet("color: #FFFFFF; font-size: 24px;")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        self.setLayout(layout)