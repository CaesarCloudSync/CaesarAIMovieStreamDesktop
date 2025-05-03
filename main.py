import sys
import os
import requests
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QLabel, QFrame, QPushButton, QStackedWidget, QLineEdit, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt, QTimer, QUrl, QSize, pyqtSignal
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt5.QtGui import QPixmap, QPainter, QPainterPath, QIcon

# TMDb API key
TMDB_API_KEY = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJmZTlkOTQ4OWE1MzMwMGI4ZGE4NTBlNjM0OTQ3NWM1MiIsIm5iZiI6MTcwNTM1MDU2Ni44LCJzdWIiOiI2NWE1OTVhNmQwNWEwMzAwYzhhOWViYzYiLCJzY29wZXMiOlsiYXBpX3JlYWQiXSwidmVyc2lvbiI6MX0.Co9vbQKxQUwV5sbON3CzQ3jUPHBvwMRrkFVn3V8WNzE"

class ItemCard(QWidget):
    clicked = pyqtSignal(dict)  # Signal to emit item data when clicked

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
        self.poster_label.setCursor(Qt.PointingHandCursor)  # Indicate clickable

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
        title_label.setStyleSheet("color: #FFFFFF; font-size: 20px; font-weight: bold; font-family: 'Calibri';")
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

        # Make the poster clickable
        self.poster_label.mousePressEvent = self.on_poster_clicked

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

    def on_poster_clicked(self, event):
        self.clicked.emit(self.item)  # Emit the item data when clicked

class ContentWidget(QWidget):
    def __init__(self, api_endpoint, main_window):
        super().__init__()
        self.api_endpoint = api_endpoint
        self.main_window = main_window  # Reference to MainWindow
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
                background: #18181b;
                width: 8px;
                margin: 0px 0px 0px 0px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #4a4a4c;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #5a5a5c;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
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
                item_card.clicked.connect(self.main_window.show_details)  # Connect to MainWindow's show_details
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
        if scroll_bar.value() >= scroll_bar.maximum() - 200 and not self.is_loading:
            QTimer.singleShot(100, self.load_items)  # Add slight delay for smoother loading

class DetailsWidget(QWidget):
    def __init__(self, item, image_cache, main_window, parent=None):
        super().__init__(parent)
        self.item = item
        self.image_cache = image_cache
        self.main_window = main_window  # Reference to MainWindow

        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setAlignment(Qt.AlignTop)

        # Back button
        back_button = QPushButton("Back")
        back_button.setFixedWidth(100)
        back_button.setStyleSheet("""
            QPushButton {
                color: #FFFFFF;
                background-color: #252528;
                border: none;
                border-radius: 6px;
                padding: 8px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a3a3c;
            }
            QPushButton:pressed {
                background-color: #4a4a4c;
            }
        """)
        back_button.clicked.connect(self.go_back)
        layout.addWidget(back_button, alignment=Qt.AlignLeft)

        # Title
        title = item.get("title", item.get("name", "Unknown"))
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #FFFFFF; font-size: 28px; font-weight: bold; font-family: 'Calibri';")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        # Poster
        poster_frame = QFrame()
        poster_frame.setFixedSize(300, 450)
        poster_frame.setStyleSheet("""
            border-radius: 10px;
            background-color: #252528;
            border: none;
        """)

        poster_label = QLabel(poster_frame)
        poster_label.setAlignment(Qt.AlignCenter)
        poster_label.setGeometry(0, 0, 300, 450)
        poster_label.setScaledContents(True)
        poster_label.setStyleSheet("background-color: #252528; border-radius: 10px;")

        poster_path = self.item.get("poster_path", "")
        if poster_path in self.image_cache:
            self.set_rounded_image(poster_label, self.image_cache[poster_path])
        else:
            self.fetch_image_async(poster_label, poster_path)

        layout.addWidget(poster_frame, alignment=Qt.AlignCenter)

        # Description
        description = item.get("overview", "No description available.")
        description_label = QLabel(description)
        description_label.setStyleSheet("color: #FFFFFF; font-size: 16px; font-family: 'Calibri';")
        description_label.setAlignment(Qt.AlignCenter)
        description_label.setWordWrap(True)
        layout.addWidget(description_label)

        layout.addStretch()
        self.setLayout(layout)

    def set_rounded_image(self, label, pixmap, radius=10):
        scaled_pixmap = pixmap.scaled(
            label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        rounded = QPixmap(label.size())
        rounded.fill(Qt.transparent)

        painter = QPainter(rounded)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, label.width(), label.height(), radius, radius)
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, scaled_pixmap)
        painter.end()

        label.setPixmap(rounded)

    def fetch_image_async(self, label, poster_path):
        image_url = f"https://image.tmdb.org/t/p/w780{poster_path}"
        request = QNetworkRequest(QUrl(image_url))
        network_manager = QNetworkAccessManager(self)
        network_manager.finished.connect(lambda reply: self.on_image_fetched(reply, label, poster_path))
        network_manager.get(request)

    def on_image_fetched(self, reply, label, poster_path):
        if reply.error() == QNetworkReply.NoError:
            image_data = reply.readAll()
            pixmap = QPixmap()
            pixmap.loadFromData(image_data)
            self.image_cache[poster_path] = pixmap
            self.set_rounded_image(label, pixmap)
        else:
            print(f"Failed to load image: {reply.errorString()}")
        reply.deleteLater()

    def go_back(self):
        self.main_window.content_stack.setCurrentIndex(self.main_window.previous_index)  # Return to previous view
        self.main_window.button_container.show()  # Restore left nav buttons
        self.main_window.content_nav.show()  # Restore content nav bar
        self.main_window.search_container.show()  # Restore search bar

class Home(ContentWidget):
    def __init__(self, main_window):
        super().__init__("movie/popular", main_window)

class AnimeWidget(ContentWidget):
    def __init__(self, main_window):
        super().__init__("discover/tv?with_genres=16&with_keywords=210024|287501&first_air_date.gte=2015-03-10", main_window)

class SeriesWidget(ContentWidget):
    def __init__(self, main_window):
        super().__init__("tv/top_rated", main_window)

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
        self.previous_index = 0  # Track previous stack index
        self.search_history = []  # Store up to 10 search queries

        # Main widget and layout
        central_widget = QWidget()
        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

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
        main_layout.addWidget(self.left_nav)

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
        self.search_bar.setFixedWidth(166)  # Adjusted for larger icon
        self.search_bar.setStyleSheet("""
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
            btn.setCheckable(True)
            btn.clicked.connect(self.switch_content)
            content_nav_layout.addWidget(btn)
            self.content_nav_buttons.append(btn)
        content_nav_layout.addStretch()
        self.content_nav.setLayout(content_nav_layout)
        content_layout.addWidget(self.content_nav)

        # Content stack
        self.content_stack = QStackedWidget()
        self.content_stack.addWidget(Home(self))          # Index 0: Home
        self.content_stack.addWidget(AnimeWidget(self))   # Index 1: Anime
        self.content_stack.addWidget(SeriesWidget(self))  # Index 2: Series
        self.content_stack.addWidget(DiscoverWidget())    # Index 3: Discover
        self.content_stack.addWidget(LibraryWidget())     # Index 4: Library
        self.content_stack.addWidget(CalendarWidget())    # Index 5: Calendar
        self.details_widget = DetailsWidget({}, {}, self) # Placeholder, updated dynamically
        self.content_stack.addWidget(self.details_widget) # Index 6: Details
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
            self.is_fullscreen = True
        else:
            self.showNormal()
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

    def show_details(self, item):
        self.previous_index = self.content_stack.currentIndex()  # Save current index
        # Hide navigation bars and search bar
        self.button_container.hide()  # Hide left nav buttons (keep logo)
        self.content_nav.hide()  # Hide content nav bar
        self.search_container.hide()  # Hide search bar
        # Create a new DetailsWidget with the selected item
        self.content_stack.removeWidget(self.details_widget)
        self.details_widget = DetailsWidget(item, self.content_stack.widget(0).image_cache, self)
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
        super(QLineEdit, self.search_bar).focusInEvent(event)
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
        super(QLineEdit, self.search_bar).focusOutEvent(event)
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