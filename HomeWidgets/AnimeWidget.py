
from HomeWidgets.ContentWidget import ContentWidget
class AnimeWidget(ContentWidget):
    def __init__(self, main_window):
        super().__init__("discover/tv?with_genres=16&with_keywords=210024|287501&first_air_date.gte=2015-03-10", main_window)

