"""class VLCPlayerApp(QMainWindow):
        # Base path for script or executable
        self.base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        self.vlc_dir = os.path.join(self.base_path, "vlc-3.0.21")

        # Download and extract VLC if not present
        if not os.path.exists(self.vlc_dir):
            self.download_vlc()

        # Add VLC directory to system PATH
        os.environ["PATH"] = f"{self.vlc_dir};{os.environ.get('PATH', '')}"
        import vlc
        os.environ['VLC_PATH'] = self.vlc_dir

        # VLC setup
        try:
            self.instance = vlc.Instance()
            self.player = self.instance.media_player_new()
        except Exception as e:
            raise RuntimeError(f"Failed to create VLC instance: {str(e)}")


    def download_vlc(self):
        try:
            vlc_url = "https://download.videolan.org/pub/videolan/vlc/3.0.21/win64/vlc-3.0.21-win64.zip"
            vlc_zip_path = os.path.join(self.base_path, "vlc.zip")
            response = requests.get(vlc_url, stream=True)
            response.raise_for_status()
            with open(vlc_zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            with zipfile.ZipFile(vlc_zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.base_path)
            os.remove(vlc_zip_path)
        except Exception as e:
            raise RuntimeError(f"Failed to download/extract VLC: {str(e)}")"""