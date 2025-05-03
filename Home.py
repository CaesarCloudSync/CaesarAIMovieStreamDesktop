from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QSlider, QComboBox, QLabel, QStackedWidget, QLineEdit
from PyQt5.QtCore import Qt, QTimer
class Home(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        label = QLabel("Welcome to VLC Media Player")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color: #e0e0e0; font-size: 16px;")
        layout.addWidget(label)
        
        info_label = QLabel("Switch to Media Player view to play videos")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("color: #e0e0e0; font-size: 12px;")
        layout.addWidget(info_label)
        
        layout.addStretch()
        self.setLayout(layout)