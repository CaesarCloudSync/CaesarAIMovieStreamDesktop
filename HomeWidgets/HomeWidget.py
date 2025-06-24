from HomeWidgets.ContentWidget import ContentWidget
class HomeWidget(ContentWidget):
    def __init__(self, main_window):
        super().__init__("movie/popular", main_window)
