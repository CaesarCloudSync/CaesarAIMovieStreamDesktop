import sys
import os
import json
import zipfile
import requests
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QLabel, QFrame, QPushButton, QStackedWidget, QLineEdit, QListWidget, QListWidgetItem,QDialog,QGridLayout,
    QDockWidget
)
from PyQt5.QtCore import Qt, QTimer, QUrl, QSize, pyqtSignal, QPoint
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt5.QtGui import QPixmap, QPainter, QPainterPath, QIcon,QCursor
from PyQt5.QtWebSockets import QWebSocket
from MediaPlayer.MediaPlayer import MediaPlayer
# TMDb API key

from HomeWidgets import HomeWidget
from HomeWidgets import AnimeWidget
from DiscoverWidget import DiscoverWidget
from LibraryWidget import LibraryWidget
from CalendarWidget import CalendarWidget
from SeriesWidgets import SeriesWidget
from HomeWidgets import SeriesTVWidget




class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CaesarAIMoviesStream")
        self.setStyleSheet("background-color: #18181b;")
        self.setMinimumSize(1900, 1080)
        self.setWindowIcon(QIcon("imgs/CaesarAIMoviesLogo.png"))  # Replace with your icon path

        # Make the window frameless
        self.setWindowFlags(Qt.FramelessWindowHint)

        # Variables for dragging
        self.dragging = False
        self.drag_position = QPoint()
        self.is_fullscreen = False
        self.previous_index = 0  # Track previous stack index
        self.search_history = []  # Store up to 10 search queries

        # Main widget and layout
        central_widget = QWidget()
        main_layout = QVBoxLayout()  # Changed to QVBoxLayout to accommodate title bar
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Custom title bar
        self.title_bar = QWidget(self)
        self.title_bar.setFixedHeight(40)
        self.title_bar.setStyleSheet("""
            QWidget {
                background-color: #18181b; /* Match app background */
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }
        """)
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)
        title_layout.setSpacing(10)

        # Title bar logo
        logo_label = QLabel()
        logo_label.setFixedSize(30, 30)
        logo_label.setPixmap(QPixmap("imgs/CaesarAIMoviesLogo.png").scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        title_layout.addWidget(logo_label)

        # Title label
        title_label = QLabel("CaesarAIMoviesStream")
        title_label.setStyleSheet("color: #FFFFFF; font-size: 20px; font-weight: bold;font-family:Calibri;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        # Minimize button
        self.minimize_button = QPushButton("🗕")
        self.minimize_button.setFixedSize(30, 30)
        self.minimize_button.setStyleSheet("""
            QPushButton {
                background-color: #18181b; color: #FFFFFF; border: none;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #3a3a3c; }
        """)
        self.minimize_button.clicked.connect(self.showMinimized)
        title_layout.addWidget(self.minimize_button)

        # Maximize/Restore button
        self.maximize_button = QPushButton("🗖")
        self.maximize_button.setFixedSize(30, 30)
        self.maximize_button.setStyleSheet("""
            QPushButton {
                background-color: #18181b; color: #FFFFFF; border: none;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #3a3a3c; }
        """)
        self.maximize_button.clicked.connect(self.toggle_maximize)
        title_layout.addWidget(self.maximize_button)

        # Close button
        self.close_button = QPushButton("🗙")
        self.close_button.setFixedSize(30, 30)
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: #18181b; color: #FFFFFF; border: none;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #ff0000; }
        """)
        self.close_button.clicked.connect(self.close)
        title_layout.addWidget(self.close_button)

        main_layout.addWidget(self.title_bar)

        # Content container (original main layout)
        content_container = QWidget()
        content_main_layout = QHBoxLayout()
        content_main_layout.setSpacing(0)
        content_main_layout.setContentsMargins(0, 0, 0, 0)

        # Left navigation bar
        self.left_nav = QWidget()
        self.left_nav.setFixedWidth(120)
        self.left_nav.setStyleSheet("background-color: #18181b;")

        # Button container for centered layout
        self.button_container = QWidget()
        left_nav_layout = QVBoxLayout()
        left_nav_layout.setContentsMargins(10, 10, 10, 10)
        left_nav_layout.setSpacing(60)
        left_nav_layout.setAlignment(Qt.AlignCenter)

        logo_label = QLabel()
        logo_label.setFixedSize(90, 90)
        logo_label.setPixmap(QPixmap("imgs/CaesarAIMoviesLogo.png").scaled(90, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignCenter)
        left_nav_layout.addWidget(logo_label)

        # Left nav buttons
        nav_buttons = [{"link":"Home","icon":"imgs/home.png"}, {"link":"Discover","icon":"imgs/discover.png"}, {"link":"Library","icon":"imgs/gallery.png"}, {"link":"Calendar","icon":"imgs/calendar.png"}]
        self.left_nav_buttons = []
        for label in nav_buttons:
            btn = QPushButton()
            btn.setFixedSize(90, 90)
            btn.setIcon(QIcon(label["icon"]))
            btn.setIconSize(QSize(50, 50))
            btn.setStyleSheet("""
                QPushButton {
                    color: #FFFFFF;
                    border: none;
                    border-radius: 6px;
                    font-size: 20px;
                    background-color: transparent;
                }
                QPushButton:hover {
                    background-color: #3a3a3c;
                }
                QPushButton:pressed {
                    background-color: #4a4a4c;
                }
                QPushButton:checked {
                    background-color: #252528;
                }
            """)
            btn.setCheckable(True)
            btn.clicked.connect(self.navigate_left_nav_widget)
            left_nav_layout.addWidget(btn)
            self.left_nav_buttons.append(btn)

        self.button_container.setLayout(left_nav_layout)

        # Add button container to left nav
        main_left_nav_layout = QVBoxLayout()
        main_left_nav_layout.setContentsMargins(0, 0, 0, 0)
        main_left_nav_layout.addWidget(self.button_container)
        main_left_nav_layout.addStretch(1)
        self.left_nav.setLayout(main_left_nav_layout)
        content_main_layout.addWidget(self.left_nav)

        # Right content area
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setSpacing(0)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Top navigation bar (search and fullscreen)
        top_nav_bar = QWidget()
        top_nav_bar.setFixedHeight(60)
        top_nav_bar.setStyleSheet("background-color: #18181b;")
        top_nav_layout = QHBoxLayout()
        top_nav_layout.setContentsMargins(15, 10, 15, 10)
        top_nav_layout.setSpacing(10)

        top_nav_layout.addStretch(1)

        # Search bar with icon
        self.search_container = QWidget()
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(5)

        self.search_icon = QLabel()
        self.search_icon.setPixmap(QPixmap("imgs/search_icon.png").scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.search_icon.setFixedSize(24, 24)
        self.search_icon.setStyleSheet("""
            QLabel {
                background-color: #252528;
                border: none;
                border-radius: 6px;
                padding: 2px;
            }
            QLabel:hover {
                background-color: #3a3a3c;
            }
        """)
        search_layout.addWidget(self.search_icon)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.setFixedWidth(500)  # Adjusted for larger icon
        self.search_bar.setStyleSheet("""
            QLineEdit {
                color: #FFFFFF;
                background-color: #252528;
                border: none;
                border-radius: 6px;
                padding: 5px;
                font-size: 14px;
            }
            /*QLineEdit:focus {
                background-color: #3a3a3c;
            }*/
        """)
        self.search_bar.returnPressed.connect(self.add_search_query)
        self.search_bar.focusInEvent = self.show_search_history
        self.search_bar.focusOutEvent = self.hide_search_history
        search_layout.addWidget(self.search_bar)

        self.search_container.setLayout(search_layout)
        self.search_container.setStyleSheet("background-color: #252528; border-radius: 6px;")
        top_nav_layout.addWidget(self.search_container)

        top_nav_layout.addStretch(1)

        # Search history list
        self.search_history_list = QListWidget(top_nav_bar)  # Parent to top_nav_bar
        self.search_history_list.setStyleSheet("""
            QListWidget {
                background-color: #252528;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 5px;
            }
            QListWidget::item:hover {
                background-color: #3a3a3c;
            }
            QListWidget::item:selected {
                background-color: #4a4a4c;
            }
        """)
        self.search_history_list.setFixedWidth(190)  # Matches search_container width
        self.search_history_list.setMaximumHeight(200)  # Limit height for up to ~10 items
        self.search_history_list.hide()
        self.search_history_list.itemClicked.connect(self.select_search_history_item)
        top_nav_layout.addWidget(self.search_history_list)  # Add to layout

        top_nav_bar.setLayout(top_nav_layout)
        self.fullscreen_button = QPushButton()
        self.fullscreen_button.setIcon(QIcon("imgs/fullscreen.png"))
        self.fullscreen_button.setIconSize(QSize(30, 30))
        self.fullscreen_button.setFixedSize(40, 40)
        self.fullscreen_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #3a3a3c;
            }
            QPushButton:pressed {
                background-color: #4a4a4c;
            }
        """)
        self.fullscreen_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.fullscreen_button.clicked.connect(self.toggle_fullscreen)
        top_nav_layout.addWidget(self.fullscreen_button)

        content_layout.addWidget(top_nav_bar)

        # Content navigation bar (Movies, Anime, Series)
        self.content_nav = QWidget()
        self.content_nav.setFixedHeight(60)
        self.content_nav.setStyleSheet("background-color: #18181b;")
        content_nav_layout = QHBoxLayout()
        content_nav_layout.setSpacing(15)
        content_nav_layout.setContentsMargins(15, 10, 15, 10)

        # Content nav buttons
        self.content_nav_buttons = []
        for label in ["Movies", "Anime", "Series"]:
            btn = QPushButton(label)
            btn.setStyleSheet("""
                QPushButton {
                    color: #FFFFFF;
                    background-color: transparent;
                    border: none;
                    font-size: 16px;
                    font-weight: bold;
                    padding: 5px 15px;
                    border-top-left-radius: 5px;
                    border-top-right-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #252528;
                    border-radius: 6px;
                }
                QPushButton:checked {
                    background-color: #252528;
                    border-bottom: 2px solid #FFFFFF;
                }
            """)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.setCheckable(True)
            btn.clicked.connect(self.switch_content)
            content_nav_layout.addWidget(btn)
            self.content_nav_buttons.append(btn)
        content_nav_layout.addStretch()
        self.content_nav.setLayout(content_nav_layout)
        content_layout.addWidget(self.content_nav)

        # Apply rounded corners to central widget
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

        # Content stack
        self.content_stack = QStackedWidget()
        self.content_stack.addWidget(HomeWidget(self))          # Index 0: Home
        self.content_stack.addWidget(AnimeWidget(self))   # Index 1: Anime
        self.content_stack.addWidget(SeriesTVWidget(self))  # Index 2: Series
        self.content_stack.addWidget(DiscoverWidget())    # Index 3: Discover
        self.content_stack.addWidget(LibraryWidget())     # Index 4: Library
        self.content_stack.addWidget(CalendarWidget())    # Index 5: Calendar
        self.details_widget = SeriesWidget({}, {}, self) # Placeholder, updated dynamically
        self.content_stack.addWidget(self.details_widget) # Index 6: Details  
        content_layout.addWidget(self.content_stack, stretch=1)

        content_widget.setLayout(content_layout)
        content_main_layout.addWidget(content_widget, stretch=1)

        content_container.setLayout(content_main_layout)
        main_layout.addWidget(content_container, stretch=1)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Set initial state
        self.content_nav_buttons[0].setChecked(True)
        self.left_nav_buttons[0].setChecked(True)

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

    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
            self.maximize_button.setText("🗖")
            self.fullscreen_button.setIcon(QIcon("imgs/fullscreen.png"))
            self.is_fullscreen = False
        else:
            self.showMaximized()
            self.maximize_button.setText("🗗")
            self.fullscreen_button.setIcon(QIcon("imgs/fullscreen_exit.png"))  # Replace with your exit fullscreen icon
            self.is_fullscreen = True

    def toggle_fullscreen(self):
        if not self.is_fullscreen:
            self.showMaximized()
            self.maximize_button.setText("🗗")
            self.fullscreen_button.setIcon(QIcon("imgs/fullscreen_exit.png"))  # Replace with your exit fullscreen icon
            self.title_bar.hide()
            self.is_fullscreen = True
        else:
            self.showNormal()
            self.maximize_button.setText("🗖")
            self.fullscreen_button.setIcon(QIcon("imgs/fullscreen.png"))
            self.title_bar.show()
            self.is_fullscreen = False

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.title_bar.geometry().contains(event.pos()):
            self.dragging = True
            self.drag_position = event.globalPos() - self.pos()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            event.accept()

    def resizeEvent(self, event):
        # Adjust title bar width when window is resized
        self.title_bar.resize(self.width(), 40)
        super().resizeEvent(event)

    def navigate_left_nav_widget(self):
        sender = self.sender()
        index = self.left_nav_buttons.index(sender)
        # Map left nav buttons to content stack indices
        nav_mapping = {
            0: 0,  # Home -> Home
            1: 3,  # Discover -> Discover
            2: 4,  # Library -> Library
            3: 5   # Calendar -> Calendar
        }
        stack_index = nav_mapping.get(index, 0)
        for btn in self.left_nav_buttons:
            btn.setChecked(btn == sender)
        self.content_stack.setCurrentIndex(stack_index)
        # Reset content nav buttons when switching to non-content widgets
        if stack_index >= 3:  # Discover, Library, Calendar
            for btn in self.content_nav_buttons:
                btn.setChecked(False)

    def switch_content(self):
        sender = self.sender()
        index = self.content_nav_buttons.index(sender)
        for btn in self.content_nav_buttons:
            btn.setChecked(btn == sender)
        self.content_stack.setCurrentIndex(index)
        # Ensure left nav highlights Home when switching content
        for btn in self.left_nav_buttons:
            btn.setChecked(self.left_nav_buttons[0] == btn)

    def show_details(self, item):
        self.previous_index = self.content_stack.currentIndex()  # Save current index
        # Hide navigation bars and search bar
        self.button_container.hide()  # Hide left nav buttons (keep logo)
        self.content_nav.hide()  # Hide content nav bar
        self.search_container.hide()  # Hide search bar
        # Create a new SeriesWidget with the selected item
        self.content_stack.removeWidget(self.details_widget)
        self.details_widget = SeriesWidget(item, self.content_stack.widget(0).image_cache, self)
        self.content_stack.addWidget(self.details_widget)
        self.content_stack.setCurrentIndex(self.content_stack.count() - 1)  # Show details

    def add_search_query(self):
        query = self.search_bar.text().strip()
        if query and query not in self.search_history:
            self.search_history.append(query)
            if len(self.search_history) > 10:
                self.search_history.pop(0)
            self.update_search_history_list()
        # Placeholder for actual search functionality
        print(f"Searching for: {query}")

    def update_search_history_list(self):
        self.search_history_list.clear()
        # Add "Clear History" item
        clear_item = QListWidgetItem("Clear History")
        clear_item.setData(Qt.UserRole, "clear")
        self.search_history_list.addItem(clear_item)
        # Add search history items
        for query in reversed(self.search_history):  # Most recent first
            item = QListWidgetItem(query)
            item.setData(Qt.UserRole, query)
            self.search_history_list.addItem(item)

    def show_search_history(self, event):
        QLineEdit.focusInEvent(self.search_bar, event)  # Call base class method
        if self.search_history:
            self.update_search_history_list()
            # Position below search bar
            search_bar_pos = self.search_bar.mapToGlobal(self.search_bar.pos())
            top_nav_bar_pos = self.search_bar.parentWidget().parentWidget().mapToGlobal(self.search_bar.parentWidget().parentWidget().pos())
            x = search_bar_pos.x() - top_nav_bar_pos.x()
            y = search_bar_pos.y() - top_nav_bar_pos.y() + self.search_bar.height() + 5
            self.search_history_list.move(x, y)
            self.search_history_list.show()

    def hide_search_history(self, event):
        QLineEdit.focusOutEvent(self.search_bar, event)  # Call base class method
        # Delay hiding to allow clicking items
        QTimer.singleShot(200, self.search_history_list.hide)

    def select_search_history_item(self, item):
        data = item.data(Qt.UserRole)
        if data == "clear":
            self.search_history.clear()
            self.search_history_list.clear()
        else:
            self.search_bar.setText(data)
            self.search_bar.setFocus()
            # Placeholder for actual search
            print(f"Selected search: {data}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())





