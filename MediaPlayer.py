import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QSlider, QComboBox, QLabel, QStackedWidget, QLineEdit
from PyQt5.QtCore import Qt, QTimer


class MediaPlayer(QWidget):
    def __init__(self, vlc_instance, vlc_player):
        super().__init__()
        self.player = vlc_player
        self.instance = vlc_instance
        self.is_fullscreen = False
        self.is_paused = False
        self.audio_tracks = []
        self.subtitle_tracks = []
        
        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # URL input
        self.url_input = QLineEdit()
        self.url_input.setText("https://100-4.download.real-debrid.com/d/HJAVFYQOHZGIG/S01E10-ReFulgent%20%5B305E66C5%5D.mkv")
        self.url_input.setStyleSheet("background-color: #2a2a2a; color: #FFFFFF; border: 1px solid #333333; border-radius: 5px; padding: 5px;")
        layout.addWidget(self.url_input)
        
        # Video frame
        self.video_frame = QFrame()
        self.video_frame.setStyleSheet("background-color: #000000; border: 1px solid #333333;")
        layout.addWidget(self.video_frame, stretch=1)
        
        # Playback controls container
        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)
        controls_layout.setSpacing(5)
        controls_layout.setContentsMargins(10, 5, 10, 5)
        
        # Seek slider and time label container
        slider_layout = QHBoxLayout()
        self.seek_slider = QSlider(Qt.Horizontal)
        self.seek_slider.setMinimum(0)
        self.seek_slider.setMaximum(1000)
        self.seek_slider.sliderMoved.connect(self.seek)
        slider_layout.addWidget(self.seek_slider)
        
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setStyleSheet("color: #e0e0e0; font-size: 12px; padding: 0 5px;")
        slider_layout.addWidget(self.time_label)
        
        controls_layout.addLayout(slider_layout)
        
        # Control buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.setAlignment(Qt.AlignCenter)
        
        self.play_pause_button = QPushButton("▶")
        self.play_pause_button.setFixedSize(40, 40)
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        button_layout.addWidget(self.play_pause_button)
        
        self.stop_button = QPushButton("⏹")
        self.stop_button.setFixedSize(40, 40)
        self.stop_button.clicked.connect(self.stop_media)
        button_layout.addWidget(self.stop_button)
        
        self.fullscreen_button = QPushButton("⛶")
        self.fullscreen_button.setFixedSize(40, 40)
        self.fullscreen_button.clicked.connect(self.toggle_fullscreen)
        button_layout.addWidget(self.fullscreen_button)
        
        button_layout.addStretch()
        
        # Audio and subtitle selection
        self.audio_label = QLabel("Audio Track:")
        self.audio_label.setStyleSheet("color: #e0e0e0; font-size: 12px;")
        button_layout.addWidget(self.audio_label)
        
        self.audio_combo = QComboBox()
        self.audio_combo.setFixedWidth(150)
        self.audio_combo.currentIndexChanged.connect(self.change_audio_track)
        button_layout.addWidget(self.audio_combo)
        
        self.subtitle_label = QLabel("Subtitle Track:")
        self.subtitle_label.setStyleSheet("color: #e0e0e0; font-size: 12px;")
        button_layout.addWidget(self.subtitle_label)
        
        self.subtitle_combo = QComboBox()
        self.subtitle_combo.setFixedWidth(150)
        self.subtitle_combo.currentIndexChanged.connect(self.change_subtitle_track)
        button_layout.addWidget(self.subtitle_combo)
        
        controls_layout.addLayout(button_layout)
        
        # Status label
        self.status_label = QLabel("Status: Stopped")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #e0e0e0; font-size: 12px; padding: 5px;")
        controls_layout.addWidget(self.status_label)
        
        layout.addWidget(controls_widget)
        
        # Timer for updating UI
        self.timer = QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_ui)
        
        self.setLayout(layout)

    def toggle_play_pause(self):
        if self.is_paused:
            # Resume from paused state
            self.player.set_pause(0)
            self.status_label.setText("Status: Playing")
            self.play_pause_button.setText("❚❚")
            self.is_paused = False
            self.timer.start()
        elif self.player.is_playing():
            # Pause current playback
            self.player.set_pause(1)
            self.status_label.setText("Status: Paused")
            self.play_pause_button.setText("▶")
            self.is_paused = True
        else:
            # Start new playback
            url = self.url_input.text()
            if url:
                try:
                    media = self.instance.media_new(url)
                    self.player.set_media(media)
                    if sys.platform.startswith('win'):
                        self.player.set_hwnd(self.video_frame.winId())
                    elif sys.platform.startswith('linux'):
                        self.player.set_xwindow(self.video_frame.winId())
                    elif sys.platform.startswith('darwin'):
                        self.player.set_nsobject(int(self.video_frame.winId()))
                    self.player.play()
                    self.status_label.setText("Status: Playing")
                    self.play_pause_button.setText("❚❚")
                    self.is_paused = False
                    self.timer.start()
                except Exception as e:
                    self.status_label.setText(f"Status: Error - {str(e)}")

    def stop_media(self):
        self.player.stop()
        self.timer.stop()
        self.seek_slider.setValue(0)
        self.time_label.setText("00:00 / 00:00")
        self.status_label.setText("Status: Stopped")
        self.play_pause_button.setText("▶")
        self.is_paused = False
        self.audio_combo.clear()
        self.subtitle_combo.clear()
        self.audio_tracks = []
        self.subtitle_tracks = []

    def seek(self, position):
        if self.player.is_playing() or self.is_paused:
            media_length = self.player.get_length()
            if media_length > 0:
                seek_pos = position / 1000.0
                self.player.set_position(seek_pos)

    def update_ui(self):
        if self.player.is_playing() or self.is_paused:
            self.populate_tracks()
            media_pos = self.player.get_position()
            self.seek_slider.setValue(int(media_pos * 1000))
            media_length = self.player.get_length() / 1000
            current_time = self.player.get_time() / 1000
            if media_length > 0:
                length_str = f"{int(media_length // 60):02d}:{int(media_length % 60):02d}"
                current_str = f"{int(current_time // 60):02d}:{int(current_time % 60):02d}"
                self.time_label.setText(f"{current_str} / {length_str}")
            else:
                current_str = f"{int(current_time // 60):02d}:{int(current_time % 60):02d}"
                self.time_label.setText(f"{current_str} / --:--")

    def populate_tracks(self):
        # Get current VLC tracks
        new_audio_tracks = self.player.audio_get_track_description() or []
        new_subtitle_tracks = self.player.video_get_spu_description() or []

        # Update audio tracks only if they have changed
        if new_audio_tracks != self.audio_tracks:
            self.audio_combo.blockSignals(True)
            current_audio_text = self.audio_combo.currentText() if self.audio_combo.count() > 0 else None
            self.audio_combo.clear()
            if new_audio_tracks:
                for track in new_audio_tracks:
                    track_name = track[1].decode('utf-8', errors='ignore') if track[1] else f"Track {track[0]}"
                    self.audio_combo.addItem(track_name, track[0])
            else:
                self.audio_combo.addItem("No audio tracks", -1)
            
            # Restore previous audio selection if possible
            if current_audio_text:
                index = self.audio_combo.findText(current_audio_text)
                if index >= 0:
                    self.audio_combo.setCurrentIndex(index)
            self.audio_combo.blockSignals(False)
            self.audio_tracks = new_audio_tracks

        # Update subtitle tracks only if they have changed
        if new_subtitle_tracks != self.subtitle_tracks:
            self.subtitle_combo.blockSignals(True)
            current_subtitle_text = self.subtitle_combo.currentText() if self.subtitle_combo.count() > 0 else None
            self.subtitle_combo.clear()
            if new_subtitle_tracks:
                self.subtitle_combo.addItem("None", -1)
                for track in new_subtitle_tracks:
                    if track[0] != -1:
                        track_name = track[1].decode('utf-8', errors='ignore') if track[1] else f"Subtitle {track[0]}"
                        self.subtitle_combo.addItem(track_name, track[0])
            else:
                self.subtitle_combo.addItem("No subtitles", -1)
            
            # Restore previous subtitle selection if possible
            if current_subtitle_text:
                index = self.subtitle_combo.findText(current_subtitle_text)
                if index >= 0:
                    self.subtitle_combo.setCurrentIndex(index)
            self.subtitle_combo.blockSignals(False)
            self.subtitle_tracks = new_subtitle_tracks

    def change_audio_track(self, index):
        track_id = self.audio_combo.itemData(index)
        if track_id is not None and track_id != -1:
            try:
                self.player.audio_set_track(track_id)
                self.status_label.setText(f"Status: Switched to audio track {self.audio_combo.currentText()}")
            except Exception as e:
                self.status_label.setText(f"Status: Audio track switch failed - {str(e)}")
        else:
            self.status_label.setText("Status: No valid audio track selected")

    def change_subtitle_track(self, index):
        track_id = self.subtitle_combo.itemData(index)
        if track_id is not None:
            try:
                self.player.video_set_spu(track_id)
                track_name = self.subtitle_combo.currentText()
                self.status_label.setText(f"Status: Switched to subtitle track {track_name}")
            except Exception as e:
                self.status_label.setText(f"Status: Subtitle track switch failed - {str(e)}")
        else:
            self.status_label.setText("Status: No valid subtitle track selected")

    def toggle_fullscreen(self):
        main_window = self.window()
        if not self.is_fullscreen:
            main_window.showFullScreen()
            self.fullscreen_button.setText("⛶")
            self.is_fullscreen = True
        else:
            main_window.showNormal()
            self.fullscreen_button.setText("⛶")
            self.is_fullscreen = False
