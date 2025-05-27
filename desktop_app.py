import webview
import threading
import time
import json
import os
import sys
from app import app

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


class RightPanelWidget(QWidget):
    """Painel direito customizável para futuras funcionalidades"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_received_area = None
        self.instructions_output_area = None
        self.video_result_area = None
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
        self.data_received_area.setFixedHeight(100)
        layout.addWidget(self.data_received_area)

        # Área para "Instructions sended to the robot"
        instructions_label = QLabel("Instruções Enviadas ao Robô:")
        layout.addWidget(instructions_label)
        self.instructions_output_area = QTextEdit()
        self.instructions_output_area.setReadOnly(True)
        layout.addWidget(self.instructions_output_area)
        
        # Área para "Video result"
        video_label = QLabel("Resultado do Vídeo:")
        layout.addWidget(video_label)
        self.video_result_area = QTextEdit() 
        self.video_result_area.setReadOnly(True)
        self.video_result_area.setStyleSheet("color: #555;")
        self.video_result_area.setFixedHeight(80)
        layout.addWidget(self.video_result_area)
        
        # Placeholder para imagem/vídeo
        self.image_placeholder_label = QLabel("[Preview do Frame Atual do Robô Aqui]")
        self.image_placeholder_label.setAlignment(Qt.AlignCenter)
        self.image_placeholder_label.setMinimumHeight(100)
        self.image_placeholder_label.setStyleSheet("background-color: #ddd; border: 1px solid #aaa;")
        layout.addWidget(self.image_placeholder_label)

        capture_button = QPushButton("Próximo Passo / Capturar Foto (Simulado)")
        capture_button.clicked.connect(self.capture_and_display_image_pyqt)
        layout.addWidget(capture_button)

        self.setLayout(layout)
        
        # Inicializar com dados vazios
        self.update_contents(None)

    def update_contents(self, new_data):
        self.data_received_area.setPlainText(json.dumps(new_data, indent=2) if new_data else "Nenhum dado recebido.")
        
        instructions_text = "Aguardando instruções...\n"
        if isinstance(new_data, list) and all(isinstance(item, dict) for item in new_data):
            instructions_text = "Instruções Geradas para o Robô:\n"
            for i, movement_block in enumerate(new_data):
                instructions_text += f"\n--- Bloco de Movimento {i+1} ---\n"
                if movement_block and 'type' in movement_block:
                    if movement_block['type'] == 'movimento_sequence':
                        fps = movement_block.get('fps', 'N/A')
                        duracao = movement_block.get('duracao', 'N/A')
                        inicio = movement_block.get('inicio', {})
                        fim = movement_block.get('fim', {})
                        instructions_text += f"  Tipo: Sequência de Movimento\n"
                        instructions_text += f"  FPS: {fps}, Duração (frames): {duracao}\n"
                        instructions_text += f"  Pose Inicial: {json.dumps(inicio)}\n"
                        instructions_text += f"  Pose Final: {json.dumps(fim)}\n"
                        
                        num_frames_val = 0
                        try:
                            num_frames_val = int(duracao)
                        except (ValueError, TypeError):
                            instructions_text += "  Duração inválida para simular frames.\n"

                        if num_frames_val > 0:
                            instructions_text += f"  Simulação de {num_frames_val} frames a serem gerados:\n"
                            for frame_idx in range(num_frames_val):
                                instructions_text += f"    - Frame {frame_idx + 1} (pose interpolada)\n"
                    elif movement_block['type'] == 'robo_pose':
                        instructions_text += f"  Tipo: Pose Única do Robô\n"
                        instructions_text += f"  Detalhes: {json.dumps(movement_block)}\n"
                    else:
                        instructions_text += f"  Tipo de Bloco: {movement_block['type']}\n"
                        instructions_text += f"  Dados: {json.dumps(movement_block)}\n"
                else:
                    instructions_text += f"  Bloco malformado ou sem tipo: {json.dumps(movement_block)}\n"
        elif new_data:
            instructions_text = f"Dados recebidos (formato não totalmente processado para instruções detalhadas):\n{json.dumps(new_data, indent=2)}"
        
        self.instructions_output_area.setPlainText(instructions_text)
        self.video_result_area.setPlainText("TODO: esta tela terá um ícone de carregamento a cada novo frame adicionado, e uma prévia da imagem com o estado atual do vídeo")

    def capture_and_display_image_pyqt(self):
        print("Simulando captura e exibição de imagem (PyQt)...")
        self.image_placeholder_label.setText(f"Imagem simulada capturada às {time.strftime('%H:%M:%S')}")


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
        self.setCentralWidget(central_widget)

        # Layout horizontal principal
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
        self.web_view.load(QUrl(f'http://{FLASK_HOST}:{FLASK_PORT}/'))
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
        if self.right_panel:
            self.right_panel.update_contents(data)


class Api:
    def handle_robot_data(self, data_from_js):
        global robot_data_for_pyqt_ui, main_window_instance
        
        current_thread_name = threading.current_thread().name
        print(f"API: handle_robot_data chamada no thread: {current_thread_name}")

        robot_data_for_pyqt_ui = data_from_js 
        print(f"API: Python recebeu dados do JS: {robot_data_for_pyqt_ui}")

        if not main_window_instance:
            print("API ERRO: main_window_instance não está definido.")
            return {"status": "error", "message": "Instância da janela principal não pronta."}

        # Usa QTimer.singleShot para garantir que a UI seja atualizada no thread principal do Qt
        QTimer.singleShot(0, lambda: main_window_instance.update_robot_data(robot_data_for_pyqt_ui))
        
        return {"status": "success", "message": "Dados recebidos. Painel de controle atualizado."}


def run_flask():
    print(f"Iniciando servidor Flask em http://{FLASK_HOST}:{FLASK_PORT}")
    # Configurar a referência global para evitar import circular
    import app as flask_app
    flask_app.main_window_ref = lambda: main_window_instance
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False, use_reloader=False)


if __name__ == '__main__':
    print("Iniciando aplicação desktop SMAT...")

    # Definir o atributo ANTES de criar QApplication
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts, True)

    app_pyqt = QApplication.instance()
    if app_pyqt is None:
        app_pyqt = QApplication(sys.argv)
        print("Criando nova QApplication.")
    else:
        print("Usando QApplication existente.")
    pyqt_app_instance = app_pyqt

    # Iniciar Flask em thread separada
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("Aguardando o servidor Flask (3s)...")
    time.sleep(3)

    # Criar janela principal
    main_window_instance = MainWindow()

    # Configurar API para comunicação JavaScript-Python
    api_instance = Api()
    
    # Injetar a API no WebView (isso requer uma abordagem diferente)
    # Por enquanto, a comunicação será feita via endpoints Flask se necessário
    
    print("Iniciando loop de eventos Qt...")
    try:
        sys.exit(app_pyqt.exec_())
    except Exception as e:
        print(f"Erro durante execução: {e}")
        sys.exit(1)
