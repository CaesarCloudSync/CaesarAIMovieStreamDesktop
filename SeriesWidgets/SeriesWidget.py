from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QLabel, QFrame, QPushButton, QStackedWidget, QLineEdit, QListWidget, QListWidgetItem,QDialog,QGridLayout,
    QDockWidget
)
from PyQt5.QtCore import Qt, QTimer, QUrl, QSize, pyqtSignal, QPoint
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt5.QtGui import QPixmap, QPainter, QPainterPath, QIcon,QCursor
from PyQt5.QtWebSockets import QWebSocket
from MediaPlayer import MediaPlayer
import requests
import json
from SeriesWidgets.SeasonWidget import SeasonWidget
from constants import Constants

class SeriesWidget(QWidget):
    def __init__(self, item, image_cache, main_window, parent=None):
        super().__init__(parent)
        self.item = item
        self.image_cache = image_cache
        self.main_window = main_window
        self.seasons = []
        self.description = ""
        self.number_of_episodes = 0
        self.streams = []
        self.total_streams = 0
        self.websocket = None
        self.current_season = None
        self.current_episode = None

        # Main layout for the widget
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Create a scroll area for the entire content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
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
        """)

        # Create a content widget to hold all the content
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setAlignment(Qt.AlignTop)

        # Back button
        back_button = QPushButton("Back")
        back_button.setFixedWidth(100)
        back_button.setCursor(QCursor(Qt.PointingHandCursor))
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
        """)
        back_button.clicked.connect(self.go_back)
        content_layout.addWidget(back_button, alignment=Qt.AlignLeft)

        # Title
        title = item.get("title", item.get("name", "Unknown"))
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #FFFFFF; font-size: 28px; font-weight: bold; font-family: Arial, sans-serif;")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setWordWrap(True)
        content_layout.addWidget(title_label)

        # Assuming Fullscreen button exists in main_window, placeholder comment
        # Fullscreen button is assumed to be added elsewhere in main_window

        # Horizontal layout for poster, description, episode count, and streams
        content_split_layout = QHBoxLayout()
        content_split_layout.setSpacing(20)

        # Left side: Poster, description, episode count
        left_container = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setSpacing(10)

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
        left_layout.addWidget(poster_frame, alignment=Qt.AlignCenter)

        # Description
        self.description_label = QLabel()
        self.description_label.setStyleSheet("color: #FFFFFF; font-size: 25px; font-family: Arial, sans-serif;")
        self.description_label.setAlignment(Qt.AlignCenter)
        self.description_label.setWordWrap(True)
        left_layout.addWidget(self.description_label)

        # Episode count
        self.episode_count_label = QLabel()
        self.episode_count_label.setStyleSheet("color: #FFFFFF; font-size: 16px; font-family: Arial, sans-serif;")
        self.episode_count_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.episode_count_label)

        # Add stretch to left_layout to push content up
        left_layout.addStretch(1)

        left_container.setLayout(left_layout)
        content_split_layout.addWidget(left_container, stretch=1)

        # Right side: Streams section
        self.streams_container = QWidget()
        self.streams_container.hide()
        streams_layout = QVBoxLayout()
        streams_layout.setSpacing(10)
        streams_layout.setContentsMargins(0, 0, 0, 0)

        # Custom exit and minimize buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        buttons_layout.setAlignment(Qt.AlignRight)

        exit_button = QPushButton("✖")
        exit_button.setFixedSize(30, 30)
        exit_button.setStyleSheet("""
            QPushButton {
                color: #FFFFFF;
                background-color: #ff3333;
                border: none;
                border-radius: 15px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #cc0000;
            }
        """)
        exit_button.clicked.connect(self.clear_streams)
        buttons_layout.addWidget(exit_button)

        self.minimize_button = QPushButton("−")
        self.minimize_button.setFixedSize(30, 30)
        self.minimize_button.setStyleSheet("""
            QPushButton {
                color: #FFFFFF;
                background-color: #ffcc00;
                border: none;
                border-radius: 15px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #cc9900;
            }
        """)
        self.minimize_button.clicked.connect(self.toggle_streams)
        buttons_layout.addWidget(self.minimize_button)

        streams_layout.addLayout(buttons_layout)

        # Streams title
        self.streams_title = QLabel(f"Streams for {title} S0E0 (Total: 0)")
        self.streams_title.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: bold;")
        streams_layout.addWidget(self.streams_title)

        # Streams scroll area
        self.streams_scroll_area = QScrollArea()
        self.streams_scroll_area.setWidgetResizable(True)
        self.streams_scroll_area.setMinimumWidth(300)
        self.streams_scroll_area.setMinimumHeight(0)
        self.streams_scroll_area.setStyleSheet("""
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
        """)

        streams_widget = QWidget()
        streams_widget_layout = QVBoxLayout()
        streams_widget_layout.setContentsMargins(0, 0, 0, 0)

        self.stream_list = QListWidget()
        self.stream_list.setStyleSheet("""
            background-color: #252528; 
            color: #FFFFFF; 
            border: none;
            border-radius: 6px;
        """)
        self.stream_list.itemClicked.connect(self.on_stream_selected)
        streams_widget_layout.addWidget(self.stream_list)

        streams_widget.setLayout(streams_widget_layout)
        self.streams_scroll_area.setWidget(streams_widget)
        streams_layout.addWidget(self.streams_scroll_area, stretch=1)

        self.streams_container.setLayout(streams_layout)
        left_layout.addWidget(self.streams_container, stretch=1)

        content_layout.addLayout(content_split_layout)

        # Seasons
        self.seasons_widget = QWidget()
        self.seasons_layout = QGridLayout()
        self.seasons_widget.setLayout(self.seasons_layout)
        content_layout.addWidget(self.seasons_widget, stretch=1)

        # Set the content layout to the content widget
        content_widget.setLayout(content_layout)

        # Set the content widget as the scroll area's widget
        scroll_area.setWidget(content_widget)

        # Add the scroll area to the main layout
        main_layout.addWidget(scroll_area, stretch=1)

        # Set the main layout for the SeriesWidget
        self.setLayout(main_layout)

        # Initialize streams visibility
        self.streams_visible = True
        self.stream_list.hide()  # Hide by default until streams are loaded
        self.streams_title.hide()

        # Fetch series details if it's a series
        if item.get("media_type") == "tv" or "first_air_date" in item:
            self.get_film_details()

    def set_rounded_image(self, label, pixmap, radius=10):
        scaled_pixmap = pixmap.scaled(label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
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
        self.close_websocket()
        self.clear_streams()
        self.main_window.content_stack.setCurrentIndex(self.main_window.previous_index)
        self.main_window.button_container.show()
        self.main_window.content_nav.show()
        self.main_window.search_container.show()

    def reorder_specials(self, seasons):
        specials = [s for s in seasons if "Special" in s.get("name", "")]
        seasons = [s for s in seasons if "Special" not in s.get("name", "")]
        return seasons + specials

    def get_film_details(self):
        headers = {"Authorization": f"Bearer {Constants.TMDB_API_KEY}"}
        try:
            response = requests.get(
                f"https://api.themoviedb.org/3/tv/{self.item.get('id')}?language=en-US",
                headers=headers
            )
            response.raise_for_status()
            result = response.json()
            self.number_of_episodes = result.get("number_of_episodes", 0)
            self.seasons = self.reorder_specials(result.get("seasons", []))
            self.description = result.get("overview", "No description available.")
            self.description_label.setText(self.description)
            self.episode_count_label.setText(f"Number of Episodes: {self.number_of_episodes}")
            self.update_seasons()
        except requests.RequestException as e:
            print(f"Error fetching details: {e}")

    def update_seasons(self):
        for i in range(self.seasons_layout.count()):
            self.seasons_layout.itemAt(i).widget().deleteLater()
        for index, season in enumerate(self.seasons):
            season_widget = SeasonWidget(season, self.item.get("name", "Unknown"), self.item.get("id"), self.start_streaming)
            self.seasons_layout.addWidget(season_widget, index // 2, index % 2)
        self.seasons_widget.setLayout(self.seasons_layout)

    def update_streams(self, streams):
        self.stream_list.clear()
        self.streams_scroll_area.setMinimumHeight(300)
        self.streams_container.show()
        for stream in streams:
            item = QListWidgetItem(f"Stream: {stream.get('title', 'Unknown')}")
            item.setData(Qt.UserRole, stream.get('magnet_link'))
            self.stream_list.addItem(item)
        self.streams_title.setText(f"Streams for {self.item.get('name')} S{self.current_season}E{self.current_episode} (Total: {self.total_streams})")
        self.stream_list.show()
        self.streams_title.show()

    def clear_streams(self):
        self.close_websocket()
        self.streams = []
        self.total_streams = 0
        self.stream_list.clear()
        self.stream_list.hide()
        self.streams_title.hide()

    def toggle_streams(self):
        self.streams_visible = not self.streams_visible
        if self.streams_visible:
            self.stream_list.show()
            self.streams_title.show()
            self.streams_scroll_area.setMinimumHeight(300)
        else:
            self.stream_list.hide()
            self.streams_title.hide()
            self.streams_scroll_area.setMinimumHeight(0)
            

    def start_streaming(self, season_number, episode):
        self.clear_streams()
        self.current_season = season_number
        self.current_episode = episode
        self.websocket = QWebSocket()
        self.websocket.connected.connect(self.on_websocket_connected)
        self.websocket.disconnected.connect(self.on_websocket_disconnected)
        self.websocket.textMessageReceived.connect(self.on_websocket_message)
        self.websocket.error.connect(self.on_websocket_error)
        ws_url = f"wss://movies.caesaraihub.org/api/v1/stream_get_episodews"
        self.websocket.open(QUrl(ws_url))
        self.streams_visible = True  # Ensure streams are visible when loading starts

    def on_websocket_connected(self):
        print("WebSocket connected")
        self.websocket.sendTextMessage(json.dumps({"title": self.item.get('name'), "season": self.current_season, "episode": self.current_episode}))

    def on_websocket_disconnected(self):
        print("WebSocket disconnected")
        self.websocket = None

    def on_websocket_message(self, message):
        try:
            data = json.loads(message)
            if data.get("event").get("episodes"):
                next_stream = data.get("event").get("episodes").get("data", {}).get("episodes")
                self.streams.append(next_stream)
                self.total_streams = data.get("total", 0)
                self.update_streams(self.streams)
            elif data.get("event").get("close"):
                print("WebSocket stream collection closed")
            else:
                print(data)
        except json.JSONDecodeError as e:
            print(f"WebSocket message parse error: {e}")

    def on_websocket_error(self, error):
        print(f"WebSocket error: {error}")
        self.close_websocket()

    def close_websocket(self):
        if self.websocket:
            self.websocket.close()
            self.websocket = None

    def on_stream_selected(self, item):
        magnet_link = item.data(Qt.UserRole)
        self.get_streaming_link(item, self.current_episode, self.current_season, magnet_link)
        self.clear_streams()

    def get_streaming_link(self, stream, episode, season, magnet_link):
        print("Torrenting...")
        response = requests.post("https://movies.caesaraihub.org/api/v1/torrent_magnet", json={"magnet_link": magnet_link})
        data = response.json()
        print("Finished Torrenting.")
        _id = data["id"]
        response = requests.get("https://movies.caesaraihub.org/api/v1/get_container_links", params={"_id": _id})
        streams_json = response.json()
        streams = streams_json["streams"]
        filtered = filter(lambda ep: ep["season"] == season and ep["episode"] == episode, streams)

        # Get the first match (there should only be one if it's unique)
        result = next(filtered, None)  # Will return None if no match is found

        # Get the streaming link value
        if result:
            streaming_url = result["download"]
            print(result["download"])
        else:
            filtered = filter(lambda ep: ep["season"] == season and ep["episode"] == "BATCH", streams)
            result = next(filtered, None)  # Will return None if no match is found
            if result:
                streaming_url = result["download"]
                print(result["download"])
            else:
                streaming_url = ""
                print("No match found")

        print(streaming_url)
        # Navigate to MediaPlayer widget
        if streaming_url:
            # Remove the old MediaPlayer widget if it exists
            for i in range(self.main_window.content_stack.count()):
                if isinstance(self.main_window.content_stack.widget(i), MediaPlayer):
                    self.main_window.content_stack.removeWidget(self.main_window.content_stack.widget(i))
                    break
            # Create a new MediaPlayer instance with the streaming URL
            media_player = MediaPlayer(self.main_window.instance, self.main_window.player, stream, streams, streaming_url, episode, season, self.main_window)
            self.main_window.content_stack.addWidget(media_player)
            self.main_window.content_stack.setCurrentIndex(self.main_window.content_stack.count() - 1)  # Switch to MediaPlayer

        self.close_websocket()