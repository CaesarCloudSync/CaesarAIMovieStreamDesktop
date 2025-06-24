from HomeWidgets.ContentWidget import ContentWidget
class SeriesTVWidget(ContentWidget):
    def __init__(self, main_window):
        super().__init__("tv/top_rated", main_window)