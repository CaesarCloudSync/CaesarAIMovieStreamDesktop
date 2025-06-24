from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout,
    QLabel
)
from PyQt5.QtCore import Qt
class LibraryWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        label = QLabel("Library Widget")
        label.setStyleSheet("color: #FFFFFF; font-size: 24px;")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        self.setLayout(layout)