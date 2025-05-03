import sys
import os
import requests
import zipfile
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QSlider, QComboBox, QLabel, QStackedWidget, QLineEdit
from PyQt5.QtCore import Qt, QTimer
from MediaPlayer import MediaPlayer
from Home import Home


class TwoViewWidget(QWidget):
    def __init__(self, vlc_instance, vlc_player):
        super().__init__()
        self.instance = vlc_instance
        self.player = vlc_player
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Navigation buttons
        button_layout = QHBoxLayout()
        self.home_button = QPushButton("Home")
        self.mediaplayer_button = QPushButton("Media Player")
        button_layout.addWidget(self.home_button)
        button_layout.addWidget(self.mediaplayer_button)
        layout.addLayout(button_layout)
        
        # Stacked widget for views
        self.stack = QStackedWidget()
        self.home = Home()
        self.mediaplayer = MediaPlayer(self.instance, self.player)
        self.stack.addWidget(self.home)
        self.stack.addWidget(self.mediaplayer)
        layout.addWidget(self.stack)
        
        # Connect buttons
        self.home_button.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.mediaplayer_button.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        
        self.setLayout(layout)

class VLCPlayerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VLC Embedded Media Player with Views")
      # Get screen size and calculate 30% of screen dimensions
        screen = QApplication.primaryScreen().availableGeometry()
        screen_width = screen.width()
        screen_height = screen.height()
        aw = int(screen_width * 0.7)  # 30% of screen width
        ah = int(screen_height * 0.7)  # 30% of screen height
        ax = (screen_width - aw) // 2  # Center horizontally
        ay = (screen_height - ah) // 2  # Center vertically
        self.setGeometry(ax, ay, aw, ah)

        # Base path for script or executable
        self.base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        self.vlc_dir = os.path.join(self.base_path, "vlc-3.0.21")

        # Download and extract VLC if not present
        if not os.path.exists(self.vlc_dir):
            self.download_vlc()

        # Add VLC directory to system PATH
        os.environ["PATH"] = f"{self.vlc_dir};{os.environ.get('PATH', '')}"
        import vlc
        os.environ['VLC_PATH'] = self.vlc_dir

        # VLC setup
        try:
            self.instance = vlc.Instance()
            self.player = self.instance.media_player_new()
        except Exception as e:
            raise RuntimeError(f"Failed to create VLC instance: {str(e)}")

        # Main widget and layout
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)
        self.layout = QVBoxLayout(self.main_widget)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        # Two-view widget
        self.two_view_widget = TwoViewWidget(self.instance, self.player)
        self.layout.addWidget(self.two_view_widget)
        

        # Apply stylesheet
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #1e1e1e;
            }
            QLineEdit, QComboBox {
                background-color: #2a2a2a;
                color: #e0e0e0;
                border: 1px solid #333333;
                border-radius: 5px;
                padding: 5px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                width: 10px;
                height: 10px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: #e0e0e0;
                border: none;
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QSlider::groove:horizontal {
                height: 8px;
                background: #2a2a2a;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #4CAF50;
                width: 16px;
                height: 16px;
                margin: -4px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #45a049;
            }
        """)

    def download_vlc(self):
        try:
            vlc_url = "https://download.videolan.org/pub/videolan/vlc/3.0.21/win64/vlc-3.0.21-win64.zip"
            vlc_zip_path = os.path.join(self.base_path, "vlc.zip")
            response = requests.get(vlc_url, stream=True)
            response.raise_for_status()
            with open(vlc_zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            with zipfile.ZipFile(vlc_zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.base_path)
            os.remove(vlc_zip_path)
        except Exception as e:
            raise RuntimeError(f"Failed to download/extract VLC: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VLCPlayerApp()
    window.show()
    sys.exit(app.exec_())