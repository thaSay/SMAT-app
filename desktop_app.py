import webview
import threading
import time
import json
import os
import sys
from app import app
import app as flask_app  # Importar o módulo app para acessar global_robot_data

from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QTextEdit, QPushButton, QMainWindow, QFrame)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl

FLASK_PORT = 5001
FLASK_HOST = '127.0.0.1'

webview_window_instance = None
pyqt_app_instance = None
main_window_instance = None
robot_data_for_pyqt_ui = None
# Remover global_robot_data local - vamos usar a do app.py


class RightPanelWidget(QWidget):
    """Painel direito customizável para futuras funcionalidades"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_received_area = None
        self.update_timer = None
        self.current_data = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        title_label = QLabel("Painel de Controle")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Área para "Dados JSON Recebidos dos Blocos"
        data_label = QLabel("JSON Gerado pelos Blocos:")
        layout.addWidget(data_label)
        self.data_received_area = QTextEdit()
        self.data_received_area.setReadOnly(True)
        layout.addWidget(self.data_received_area)
                # Área para "Video result"
        video_label = QLabel("Resultado do Vídeo:")
        layout.addWidget(video_label)
        self.video_result_area = QTextEdit() 
        self.video_result_area.setReadOnly(True)
        self.video_result_area.setStyleSheet("color: #555;")
        self.video_result_area.setFixedHeight(150)
        layout.addWidget(self.video_result_area)  

        self.setLayout(layout)
        
        # Inicializar com dados vazios
        self.update_contents(None)
        
        # Configurar timer para atualização a cada 5 segundos
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_contents_timer)
        self.update_timer.start(5000)  # 5000 ms = 5 segundos

    def update_contents(self, new_data):
        # Armazenar os dados para uso no timer
        if new_data is not None:
            self.current_data = new_data
        
        # Usar current_data se new_data for None (chamada do timer)
        data_to_display = new_data if new_data is not None else self.current_data
        
        self.data_received_area.setPlainText(json.dumps(data_to_display, indent=2) if data_to_display else "Nenhum dado recebido.")

    def update_contents_timer(self):
        """Método chamado pelo timer para atualizar a interface periodicamente"""
        # Usar a variável global do módulo app.py
        if flask_app.global_robot_data is not None:
            self.current_data = flask_app.global_robot_data
            flask_app.global_robot_data = None
            # Só atualizar a tela se houver dados novos
            self.update_contents(None)


class MainWindow(QMainWindow):
    """Janela principal que contém o WebView (esquerda) e painel PyQt (direita)"""
    def __init__(self):
        super().__init__()
        self.web_view = None
        self.right_panel = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("SMAT - Programação em Blocos e Controle do Robô")
        self.setGeometry(100, 100, 1400, 800)

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)        # Layout horizontal principal
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # Painel esquerdo - WebView
        left_frame = QFrame()
        left_frame.setFrameStyle(QFrame.StyledPanel)
        left_frame.setMinimumWidth(800)
        left_layout = QVBoxLayout()
        left_frame.setLayout(left_layout)
        
        # WebView para carregar o index.html (removido o título)
        self.web_view = QWebEngineView()
        url = f'http://{FLASK_HOST}:{FLASK_PORT}/'
        self.web_view.load(QUrl(url))
        left_layout.addWidget(self.web_view)

        # Painel direito - PyQt customizado
        right_frame = QFrame()
        right_frame.setFrameStyle(QFrame.StyledPanel)
        right_frame.setMinimumWidth(400)
        right_frame.setMaximumWidth(500)
        right_layout = QVBoxLayout()
        right_frame.setLayout(right_layout)
        
        self.right_panel = RightPanelWidget()
        right_layout.addWidget(self.right_panel)
          # Adicionar painéis ao layout principal
        main_layout.addWidget(left_frame, 2)  # 2/3 da largura        
        main_layout.addWidget(right_frame, 1)  # 1/3 da largura

        self.show()

    def update_robot_data(self, data):
        """Atualiza o painel direito com novos dados do robô"""
        # Agora usa a variável global do módulo app.py
        flask_app.global_robot_data = data


class Api:
    def handle_robot_data(self, data_from_js):
        global robot_data_for_pyqt_ui, main_window_instance
        
        robot_data_for_pyqt_ui = data_from_js 

        if not main_window_instance:
            return {"status": "error", "message": "Instância da janela principal não pronta."}

        # Usa QTimer.singleShot para garantir que a UI seja atualizada no thread principal do Qt
        QTimer.singleShot(0, lambda: main_window_instance.update_robot_data(robot_data_for_pyqt_ui))
        
        return {"status": "success", "message": "Dados recebidos. Painel de controle atualizado."}


def run_flask():
    # Configurar a referência global para evitar import circular
    import app as flask_app
    flask_app.app.main_window_ref = lambda: main_window_instance
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False, use_reloader=False)


if __name__ == '__main__':
    # Definir o atributo ANTES de criar QApplication
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts, True)

    app_pyqt = QApplication.instance()
    if app_pyqt is None:        app_pyqt = QApplication(sys.argv)
    pyqt_app_instance = app_pyqt

    # Iniciar Flask em thread separada
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    time.sleep(3)

    # Criar janela principal
    main_window_instance = MainWindow()
    
    # Agora configurar a referência para o Flask depois que a main_window existe
    import app as flask_app
    flask_app.app.main_window_ref = lambda: main_window_instance

    # Configurar API para comunicação JavaScript-Python
    api_instance = Api()
    
    try:
        sys.exit(app_pyqt.exec_())
    except Exception as e:
        sys.exit(1)
