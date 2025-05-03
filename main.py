import sys
import os
import requests
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QLabel, QFrame, QPushButton, QStackedWidget, QLineEdit
)
from PyQt5.QtCore import Qt, QTimer, QUrl, QSize
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt5.QtGui import QPixmap, QPainter, QPainterPath, QIcon

# TMDb API key
TMDB_API_KEY = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJmZTlkOTQ4OWE1MzMwMGI4ZGE4NTBlNjM0OTQ3NWM1MiIsIm5iZiI6MTcwNTM1MDU2Ni44LCJzdWIiOiI2NWE1OTVhNmQwNWEwMzAwYzhhOWViYzYiLCJzY29wZXMiOlsiYXBpX3JlYWQiXSwidmVyc2lvbiI6MX0.Co9vbQKxQUwV5sbON3CzQ3jUPHBvwMRrkFVn3V8WNzE"

class ItemCard(QWidget):
    def __init__(self, item, image_cache, parent=None):
        super().__init__(parent)
        self.item = item
        self.image_cache = image_cache
        self.is_on_wishlist = False
        self.image_loaded = False

        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)

        self.poster_label = QFrame()
        self.poster_label.setFixedSize(260, 390)
        self.poster_label.setStyleSheet("""
            border-radius: 10px;
            background-color: #252528;
            border: none;
        """)

        self.image_label = QLabel(self.poster_label)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setGeometry(0, 0, 260, 390)
        self.image_label.setScaledContents(True)
        self.image_label.setStyleSheet("background-color: #252528; border-radius: 10px;")

        self.network_manager = QNetworkAccessManager(self)
        self.network_manager.finished.connect(self.on_image_fetched)

        layout.addWidget(self.poster_label, alignment=Qt.AlignCenter)

        title = item.get("title", item.get("name", "Unknown"))
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #FFFFFF; font-size: 20px; font-weight: bold;font-family: 'Calibri';")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        self.setLayout(layout)

        poster_path = self.item.get("poster_path", "")
        if poster_path in self.image_cache:
            self.set_rounded_image(self.image_cache[poster_path])
            self.image_loaded = True
        else:
            QTimer.singleShot(0, self.fetch_image_async)

    def set_rounded_image(self, pixmap, radius=10):
        scaled_pixmap = pixmap.scaled(
            self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        rounded = QPixmap(self.image_label.size())
        rounded.fill(Qt.transparent)

        painter = QPainter(rounded)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.image_label.width(), self.image_label.height(), radius, radius)
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, scaled_pixmap)
        painter.end()

        self.image_label.setPixmap(rounded)

    def fetch_image_async(self):
        if not self.image_loaded:
            image_url = f"https://image.tmdb.org/t/p/w780{self.item['poster_path']}"
            request = QNetworkRequest(QUrl(image_url))
            self.network_manager.get(request)
            self.image_loaded = True

    def on_image_fetched(self, reply):
        if reply.error() == QNetworkReply.NoError:
            image_data = reply.readAll()
            pixmap = QPixmap()
            pixmap.loadFromData(image_data)
            poster_path = self.item.get("poster_path", "")
            self.image_cache[poster_path] = pixmap
            self.set_rounded_image(pixmap)
        else:
            print(f"Failed to load image: {reply.errorString()}")
        reply.deleteLater()

class ContentWidget(QWidget):
    def __init__(self, api_endpoint):
        super().__init__()
        self.api_endpoint = api_endpoint
        self.page_num = 1
        self.items = []
        self.is_loading = False
        self.image_cache = {}
        self.preload_manager = QNetworkAccessManager(self)
        self.preload_manager.finished.connect(self.on_preload_fetched)

        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #18181b;
                border: none;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 0px;
            }
        """)
        self.scroll_area.verticalScrollBar().valueChanged.connect(self.on_scroll)

        self.carousel_widget = QWidget()
        self.carousel_layout = QVBoxLayout()
        self.carousel_layout.setSpacing(15)
        self.carousel_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.carousel_layout.setContentsMargins(8, 15, 8, 15)
        self.carousel_widget.setLayout(self.carousel_layout)
        self.scroll_area.setWidget(self.carousel_widget)

        layout.addWidget(self.scroll_area, stretch=1)
        self.setLayout(layout)

        self.load_items()

    def load_items(self):
        if self.is_loading:
            return
        self.is_loading = True
        try:
            response = requests.get(
                f"https://api.themoviedb.org/3/{self.api_endpoint}?language=en-US&page={self.page_num}",
                headers={"Authorization": f"Bearer {TMDB_API_KEY}"}
            )
            response.raise_for_status()
            result = response.json()
            new_items = result.get("results", [])
            self.items.extend(new_items)
            self.update_carousel(new_items)
            self.page_num += 1
            QTimer.singleShot(500, self.preload_next_page)
        except requests.RequestException as e:
            print(f"Failed to load items: {e}")
        finally:
            self.is_loading = False

    def preload_next_page(self):
        try:
            response = requests.get(
                f"https://api.themoviedb.org/3/{self.api_endpoint}?language=en-US&page={self.page_num}",
                headers={"Authorization": f"Bearer {TMDB_API_KEY}"}
            )
            response.raise_for_status()
            next_items = response.json().get("results", [])
            for item in next_items:
                poster_path = item.get("poster_path", "")
                if poster_path and poster_path not in self.image_cache:
                    image_url = f"https://image.tmdb.org/t/p/w780{poster_path}"
                    request = QNetworkRequest(QUrl(image_url))
                    self.preload_manager.get(request)
        except requests.RequestException as e:
            print(f"Failed to preload images: {e}")

    def on_preload_fetched(self, reply):
        if reply.error() == QNetworkReply.NoError:
            image_data = reply.readAll()
            pixmap = QPixmap()
            pixmap.loadFromData(image_data)
            url = reply.url().toString()
            poster_path = url.split("/w780")[-1]
            self.image_cache[poster_path] = pixmap
        reply.deleteLater()

    def update_carousel(self, new_items):
        for i in range(0, len(new_items), 5):
            row_items = new_items[i:i+5]
            row_widget = QWidget()
            row_layout = QHBoxLayout()
            row_layout.setSpacing(8)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setAlignment(Qt.AlignLeft)

            for j, item in enumerate(row_items):
                item_card = ItemCard(item, self.image_cache)
                row_layout.addWidget(item_card)
                row_layout.setStretch(j, 1)

            while row_layout.count() < 5:
                row_layout.addStretch(1)

            row_widget.setLayout(row_layout)
            self.carousel_layout.addWidget(row_widget)

            for j in range(row_layout.count()):
                widget = row_layout.itemAt(j).widget()
                if isinstance(widget, ItemCard) and not widget.image_loaded:
                    QTimer.singleShot(100 * (i + j), widget.fetch_image_async)

    def on_scroll(self):
        scroll_bar = self.scroll_area.verticalScrollBar()
        if scroll_bar.value() >= scroll_bar.maximum() - 100 and not self.is_loading:
            self.load_items()

class Home(ContentWidget):
    def __init__(self):
        super().__init__("movie/popular")

class AnimeWidget(ContentWidget):
    def __init__(self):
        super().__init__("discover/tv?with_genres=16&with_keywords=210024|287501&first_air_date.gte=2015-03-10")

class SeriesWidget(ContentWidget):
    def __init__(self):
        super().__init__("tv/top_rated")

class DiscoverWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        label = QLabel("Discover Widget")
        label.setStyleSheet("color: #FFFFFF; font-size: 24px;")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        self.setLayout(layout)

class LibraryWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        label = QLabel("Library Widget")
        label.setStyleSheet("color: #FFFFFF; font-size: 24px;")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        self.setLayout(layout)

class CalendarWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        label = QLabel("Calendar Widget")
        label.setStyleSheet("color: #FFFFFF; font-size: 24px;")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        self.setLayout(layout)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CaesarAIMoviesStream")
        self.setStyleSheet("background-color: #18181b;")
        self.setMinimumSize(1900, 1080)

        self.is_fullscreen = False

        # Main widget and layout
        central_widget = QWidget()
        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Left navigation bar
        left_nav = QWidget()
        left_nav.setFixedWidth(120)
        left_nav.setStyleSheet("background-color: #18181b;")

        # Button container for centered layout
        button_container = QWidget()
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
            btn.setIconSize(QSize(60, 60))
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

        button_container.setLayout(left_nav_layout)

        # Add button container to left nav
        main_left_nav_layout = QVBoxLayout()
        main_left_nav_layout.setContentsMargins(0, 0, 0, 0)
        main_left_nav_layout.addWidget(button_container)
        main_left_nav_layout.addStretch(1)
        left_nav.setLayout(main_left_nav_layout)
        main_layout.addWidget(left_nav)

        # Right content area
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setSpacing(0)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Top navigation bar (logo and search)
        top_nav_bar = QWidget()
        top_nav_bar.setFixedHeight(60)
        top_nav_bar.setStyleSheet("background-color: #18181b;")
        top_nav_layout = QHBoxLayout()
        top_nav_layout.setContentsMargins(15, 10, 15, 10)
        top_nav_layout.setSpacing(10)

        top_nav_layout.addStretch(1)

        # Search bar
        search_bar = QLineEdit()
        search_bar.setPlaceholderText("Search...")
        search_bar.setFixedWidth(200)
        search_bar.setStyleSheet("""
            QLineEdit {
                color: #FFFFFF;
                background-color: #252528;
                border: none;
                border-radius: 6px;
                padding: 5px;
                font-size: 14px;
            }
            QLineEdit:focus {
                background-color: #3a3a3c;
            }
        """)
        top_nav_layout.addWidget(search_bar)

        top_nav_layout.addStretch(1)

        top_nav_bar.setLayout(top_nav_layout)
        self.fullscreen_button = QPushButton("⛶")
        self.fullscreen_button.setStyleSheet("color:white;")
        self.fullscreen_button.setFixedSize(40, 40)
        self.fullscreen_button.clicked.connect(self.toggle_fullscreen)
        top_nav_layout.addWidget(self.fullscreen_button)

        content_layout.addWidget(top_nav_bar)

        # Content navigation bar (Movies, Anime, Series)
        content_nav = QWidget()
        content_nav.setFixedHeight(60)
        content_nav.setStyleSheet("background-color: #18181b;")
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
            btn.setCheckable(True)
            btn.clicked.connect(self.switch_content)
            content_nav_layout.addWidget(btn)
            self.content_nav_buttons.append(btn)
        content_nav_layout.addStretch()
        content_nav.setLayout(content_nav_layout)
        content_layout.addWidget(content_nav)

        # Content stack
        self.content_stack = QStackedWidget()
        self.content_stack.addWidget(Home())          # Index 0: Home
        self.content_stack.addWidget(AnimeWidget())   # Index 1: Anime
        self.content_stack.addWidget(SeriesWidget())  # Index 2: Series
        self.content_stack.addWidget(DiscoverWidget())# Index 3: Discover
        self.content_stack.addWidget(LibraryWidget()) # Index 4: Library
        self.content_stack.addWidget(CalendarWidget())# Index 5: Calendar
        content_layout.addWidget(self.content_stack, stretch=1)

        content_widget.setLayout(content_layout)
        main_layout.addWidget(content_widget, stretch=1)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Set initial state
        self.content_nav_buttons[0].setChecked(True)
        self.left_nav_buttons[0].setChecked(True)

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

    def toggle_fullscreen(self):
        if not self.is_fullscreen:
            self.showFullScreen()
            self.fullscreen_button.setText("⛶")
            self.is_fullscreen = True
        else:
            self.showNormal()
            self.fullscreen_button.setText("⛶")
            self.is_fullscreen = False

    def switch_content(self):
        sender = self.sender()
        index = self.content_nav_buttons.index(sender)
        for btn in self.content_nav_buttons:
            btn.setChecked(btn == sender)
        self.content_stack.setCurrentIndex(index)
        # Ensure left nav highlights Home when switching content
        for btn in self.left_nav_buttons:
            btn.setChecked(self.left_nav_buttons[0] == btn)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())