from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton
)

class EpisodeWidget(QWidget):
    def __init__(self, series_name, season_number, seriesid, episode, start_streaming, parent=None):
        super().__init__(parent)
        self.series_name = series_name
        self.season_number = season_number
        self.seriesid = seriesid
        self.episode = episode
        self.start_streaming = start_streaming

        layout = QHBoxLayout()
        button = QPushButton(f"Episode {episode}")
        button.setStyleSheet("""
            QPushButton {
                color: #FFFFFF;
                background-color: #252528;
                border: none;
                border-radius: 6px;
                padding: 5px;
                font-size: 14px;
                font-family: Arial, sans-serif;
            }
            QPushButton:hover {
                background-color: #3a3a3c;
            }
        """)
        button.clicked.connect(self.on_episode_clicked)
        layout.addWidget(button)
        self.setLayout(layout)

    def on_episode_clicked(self):
        self.start_streaming(self.season_number, self.episode)
