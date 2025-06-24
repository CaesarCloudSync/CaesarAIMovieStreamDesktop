
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout,
    QLabel, QFrame)
from PyQt5.QtCore import Qt, QTimer, QUrl, pyqtSignal
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt5.QtGui import QPixmap, QPainter, QPainterPath
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
        title_label.setStyleSheet("color: #FFFFFF; font-size: 20px; font-weight: bold; font-family: Arial, sans-serif;")
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
