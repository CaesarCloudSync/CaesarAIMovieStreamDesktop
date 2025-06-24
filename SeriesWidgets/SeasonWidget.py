from SeriesWidgets.EpisodeWidget import EpisodeWidget
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout,
    QLabel,QGridLayout
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt5.QtGui import QPixmap,QCursor


class SeasonWidget(QWidget):
    def __init__(self, season, series_name, seriesid, start_streaming, parent=None):
        super().__init__(parent)
        self.season = season
        self.series_name = series_name
        self.seriesid = seriesid
        self.start_streaming = start_streaming

        layout = QVBoxLayout()
        self.poster = QLabel()
        self.load_poster(season.get("poster_path"))
        layout.addWidget(self.poster)
        name = QLabel(season.get("name", "Unknown"))
        name.setStyleSheet("color:white")
        release_date = QLabel(f"Release Date: {season.get('air_date', 'N/A')}")
        release_date.setStyleSheet("color:white")
        rating = QLabel(f"Rating: {season.get('vote_average', 'N/A')}")
        rating.setStyleSheet("color:white")
        layout.addWidget(name)
        layout.addWidget(release_date)
        layout.addWidget(rating)

        episode_container = QWidget()
        episode_layout = QGridLayout()
        episode_layout.setSpacing(10)
        for ep in range(1, season.get("episode_count", 0) + 1):
            ep_widget = EpisodeWidget(series_name, season.get("season_number"), seriesid, ep, start_streaming)
            ep_widget.setCursor(QCursor(Qt.PointingHandCursor))
            episode_layout.addWidget(ep_widget, (ep - 1) // 3, (ep - 1) % 3)
        episode_container.setLayout(episode_layout)
        layout.addWidget(episode_container)
        self.setLayout(layout)

    def load_poster(self, poster_path):
        if poster_path:
            url = f"https://image.tmdb.org/t/p/w780/{poster_path}"
            self.manager = QNetworkAccessManager()
            self.manager.finished.connect(self.on_poster_loaded)
            self.manager.get(QNetworkRequest(QUrl(url)))

    def on_poster_loaded(self, reply):
        pixmap = QPixmap()
        pixmap.loadFromData(reply.readAll())
        self.poster.setPixmap(pixmap.scaled(150, 250, Qt.KeepAspectRatio))
        reply.deleteLater()
