import threading
import time
import json
import os
import sys
from app import app
import app as flask_app

from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView

# Define a port for Flask to run on
FLASK_PORT = 5001
FLASK_HOST = '127.0.0.1'

class MainWindow(QMainWindow):
    """Main window that contains the WebView with both Blockly and control panel"""
    def __init__(self):
        super().__init__()
        self.web_view = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("SMAT - Block Programming and Robot Control")
        self.setGeometry(100, 100, 1400, 800)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # WebView to load the complete HTML interface
        self.web_view = QWebEngineView()
        url = f'http://{FLASK_HOST}:{FLASK_PORT}/'
        self.web_view.load(QUrl(url))
        main_layout.addWidget(self.web_view)

        self.show()

def run_flask():
    # Set up global reference to avoid circular import
    flask_app.app.main_window_ref = lambda: main_window_instance
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False, use_reloader=False)

if __name__ == '__main__':
    # Set attribute BEFORE creating QApplication
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts, True)

    app_qt = QApplication.instance()
    if app_qt is None:        
        app_qt = QApplication(sys.argv)

    # Start Flask in separate thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Wait a bit for Flask server to start
    time.sleep(1)

    # Create main window
    main_window_instance = MainWindow()
    
    # Ensure reference is set after main_window_instance is created
    if hasattr(flask_app.app, 'main_window_ref'):
        flask_app.app.main_window_ref = lambda: main_window_instance

    try:
        sys.exit(app_qt.exec_())
    except Exception as e:
        print(f"Error running application: {e}")
        sys.exit(1)
