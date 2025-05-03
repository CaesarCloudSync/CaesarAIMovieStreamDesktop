import sys
import os
import requests
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QLabel, QFrame, QPushButton, QStackedWidget
)
from PyQt5.QtCore import Qt, QTimer, QUrl, QSize
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt5.QtGui import QPixmap

# TMDb API key
TMDB_API_KEY = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJmZTlkOTQ4OWE1MzMwMGI4ZGE4NTBlNjM0OTQ3NWM1MiIsIm5iZiI6MTcwNTM1MDU2Ni44LCJzdWIiOiI2NWE1OTVhNmQwNWEwMzAwYzhhOWViYzYiLCJzY29wZXMiOlsiYXBpX3JlYWQiXSwidmVyc2lvbiI6MX0.Co9vbQKxQUwV5sbON3CzQ3jUPHBvwMRrkFVn3V8WNzE"

class MovieCard(QWidget):
    def __init__(self, film, parent=None):
        super().__init__(parent)
        self.film = film
        self.is_on_wishlist = False
        self.image_loaded = False

        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)

        self.poster_label = QFrame()
        self.poster_label.setFixedSize(200, 300)
        self.poster_label.setStyleSheet("""
            border-radius: 8px;
            background-color: #2a2a2a;
            border: 1px solid #333333;
        """)

        self.image_label = QLabel(self.poster_label)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setGeometry(0, 0, 200, 300)
        self.image_label.setStyleSheet("background-color: #2a2a2a;")

        self.network_manager = QNetworkAccessManager(self)
        self.network_manager.finished.connect(self.on_image_fetched)

        layout.addWidget(self.poster_label, alignment=Qt.AlignCenter)

        title_label = QLabel(film.get("title", "Unknown"))
        title_label.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        self.setLayout(layout)

    def fetch_image_async(self):
        if not self.image_loaded:
            image_url = f"https://image.tmdb.org/t/p/w500{self.film['poster_path']}"
            request = QNetworkRequest(QUrl(image_url))
            self.network_manager.get(request)
            self.image_loaded = True

    def on_image_fetched(self, reply):
        if reply.error() == QNetworkReply.NoError:
            image_data = reply.readAll()
            pixmap = QPixmap()
            pixmap.loadFromData(image_data)
            self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            print(f"Failed to load image: {reply.errorString()}")
        reply.deleteLater()

class Home(QWidget):
    def __init__(self):
        super().__init__()
        self.page_num = 1
        self.films = []
        self.is_loading = False
        self.image_cache = {}

        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("background-color: #1a1a1a; border: none;")
        self.scroll_area.verticalScrollBar().valueChanged.connect(self.on_scroll)

        self.carousel_widget = QWidget()
        self.carousel_layout = QVBoxLayout()
        self.carousel_layout.setSpacing(20)
        self.carousel_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.carousel_layout.setContentsMargins(10, 20, 10, 20)
        self.carousel_widget.setLayout(self.carousel_layout)
        self.scroll_area.setWidget(self.carousel_widget)

        layout.addWidget(self.scroll_area, stretch=1)
        self.setLayout(layout)

        self.load_films()

    def load_films(self):
        if self.is_loading:
            return
        self.is_loading = True
        try:
            response = requests.get(
                f"https://api.themoviedb.org/3/movie/popular?language=en-US&page={self.page_num}",
                headers={"Authorization": f"Bearer {TMDB_API_KEY}"}
            )
            response.raise_for_status()
            result = response.json()
            new_films = result.get("results", [])
            self.films.extend(new_films)
            self.update_carousel(new_films)
            self.page_num += 1
        except requests.RequestException as e:
            print(f"Failed to load films: {e}")
        finally:
            self.is_loading = False

    def update_carousel(self, new_films):
        for i in range(0, len(new_films), 5):  # 5 films per row
            row_films = new_films[i:i+5]
            row_widget = QWidget()
            row_layout = QHBoxLayout()
            row_layout.setSpacing(10)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setAlignment(Qt.AlignLeft)

            for j, film in enumerate(row_films):
                movie_card = MovieCard(film)
                row_layout.addWidget(movie_card)
                row_layout.setStretch(j, 1)  # Stretch cards to fill row

            while row_layout.count() < 5:
                row_layout.addStretch(1)

            row_widget.setLayout(row_layout)
            self.carousel_layout.addWidget(row_widget)

            for j in range(row_layout.count()):
                widget = row_layout.itemAt(j).widget()
                if isinstance(widget, MovieCard):
                    QTimer.singleShot(100 * (i + j), widget.fetch_image_async)

    def on_scroll(self):
        scroll_bar = self.scroll_area.verticalScrollBar()
        if scroll_bar.value() >= scroll_bar.maximum() - 100 and not self.is_loading:
            self.load_films()

class AnimeWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        placeholder_label = QLabel("Anime Content Placeholder")
        placeholder_label.setStyleSheet("color: #FFFFFF; font-size: 18px;")
        placeholder_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(placeholder_label)
        self.setLayout(layout)

class SeriesWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        placeholder_label = QLabel("Series Content Placeholder")
        placeholder_label.setStyleSheet("color: #FFFFFF; font-size: 18px;")
        placeholder_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(placeholder_label)
        self.setLayout(layout)
