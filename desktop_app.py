import webview
import threading
import time
import json
import os
import sys
from app import app

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton
from PyQt5.QtCore import Qt, QTimer # Adicionado QTimer
from PyQt5.QtGui import QFont

FLASK_PORT = 5001
FLASK_HOST = '127.0.0.1'

webview_window_instance = None
pyqt_app_instance = None
pyqt_control_window_instance = None
robot_data_for_pyqt_ui = None


class RobotControlWindow(QWidget):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data_received_area = None
        self.instructions_output_area = None
        self.video_result_area = None
        self.init_ui(data)

    def init_ui(self, data):
        self.setWindowTitle("SMAT - Controle e Saída do Robô (PyQt)")
        self.setGeometry(150, 150, 600, 550) # Posição e tamanho iniciais

        layout = QVBoxLayout()

        title_label = QLabel("Saída e Controle do Robô")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Área para "Dados JSON Recebidos dos Blocos"
        data_label = QLabel("JSON Gerado pelos Blocos:")
        layout.addWidget(data_label)
        self.data_received_area = QTextEdit()
        self.data_received_area.setReadOnly(True)
        self.data_received_area.setFixedHeight(100) # Altura limitada para o JSON
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
        self.video_result_area.setStyleSheet("color: #555;") # Cor mais suave para o TODO
        self.video_result_area.setFixedHeight(80)
        layout.addWidget(self.video_result_area)
        
        # Placeholder para imagem/vídeo (pode ser um QLabel)
        self.image_placeholder_label = QLabel("[Preview do Frame Atual do Robô Aqui]")
        self.image_placeholder_label.setAlignment(Qt.AlignCenter)
        self.image_placeholder_label.setMinimumHeight(100) # Espaço para a imagem
        self.image_placeholder_label.setStyleSheet("background-color: #ddd; border: 1px solid #aaa;")
        layout.addWidget(self.image_placeholder_label)


        capture_button = QPushButton("Próximo Passo / Capturar Foto (Simulado)")
        capture_button.clicked.connect(self.capture_and_display_image_pyqt)
        layout.addWidget(capture_button)
    
        exit_button = QPushButton("Fechar Janela de Controle")
        exit_button.clicked.connect(self.close) # Conecta ao método close do QWidget
        layout.addWidget(exit_button)

        self.setLayout(layout)
        self.update_contents(data) 
        self.show()

    def update_contents(self, new_data):
        if not self.isVisible():
            self.show()
        self.raise_()
        self.activateWindow()

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
                        # Aqui você simularia ou exibiria os passos que o robô tomaria
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
        # Em uma aplicação real, aqui você atualizaria o QLabel com um QPixmap

    def closeEvent(self, event):
        global pyqt_control_window_instance
        print("Janela de controle PyQt fechada pelo usuário.")
        pyqt_control_window_instance = None 
        event.accept()

def create_robot_control_ui_pyqt_instance(data): # Renomeado para evitar conflito e indicar instância
    global pyqt_control_window_instance
    if pyqt_control_window_instance: # Se já existe, apenas atualiza e mostra
        pyqt_control_window_instance.update_contents(data)
        pyqt_control_window_instance.show()
        pyqt_control_window_instance.raise_()
        pyqt_control_window_instance.activateWindow()
    else: # Cria nova instância
        pyqt_control_window_instance = RobotControlWindow(data)
    return pyqt_control_window_instance

class Api:
    def handle_robot_data(self, data_from_js):
        global robot_data_for_pyqt_ui, pyqt_app_instance
        
        current_thread_name = threading.current_thread().name
        print(f"API: handle_robot_data chamada no thread: {current_thread_name}")

        robot_data_for_pyqt_ui = data_from_js 
        print(f"API: Python recebeu dados do JS: {robot_data_for_pyqt_ui}")

        if not pyqt_app_instance:
            print("API ERRO: pyqt_app_instance não está definido.")
            return {"status": "error", "message": "Instância da aplicação PyQt não pronta."}

        # Usa QTimer.singleShot para garantir que a UI seja criada/atualizada no thread principal do Qt
        QTimer.singleShot(0, lambda: create_robot_control_ui_pyqt_instance(robot_data_for_pyqt_ui))
        
        return {"status": "success", "message": "Dados recebidos. UI de controle do robô (PyQt) acionada/atualizada."}

def run_flask():
    print(f"Iniciando servidor Flask em http://{FLASK_HOST}:{FLASK_PORT}")
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False, use_reloader=False)

if __name__ == '__main__':
    print("Iniciando aplicação desktop SMAT...")
    
    app_pyqt = QApplication.instance() 
    if app_pyqt is None:
        print("Criando nova QApplication.")
        app_pyqt = QApplication(sys.argv)
    else:
        print("Usando QApplication existente.")
    pyqt_app_instance = app_pyqt 

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print(f"Aguardando o servidor Flask (2s)...")
    time.sleep(2) 

    api_instance_for_webview = Api()
    try:
        webview_window_instance = webview.create_window(
            'SMAT - Programação em Blocos (Blockly)', 
            f'http://{FLASK_HOST}:{FLASK_PORT}/',
            width=900, 
            height=700, 
            resizable=True,
            js_api=api_instance_for_webview
        )
        print("Iniciando PyWebView com integração Qt (gui='qt')...")
        # webview.start() com gui='qt' integra e usa o loop de eventos do QApplication.
        # Ele bloqueará até que a janela PyWebView seja fechada.
        webview.start(gui='qt', debug=True) 

    except Exception as e:
        error_message = str(e)
        print(f"Ocorreu um erro ao iniciar o PyWebView: {error_message}")
        if "WebView2Loader.dll" in error_message or "WebView2 initialization failed" in error_message or "Não é possível carregar a DLL 'WebView2Loader.dll'" in error_message:
            print("\n*** ERRO CRÍTICO: Falha ao inicializar o WebView2 (Microsoft Edge) ***")
            print("Este programa requer o WebView2 Runtime.")
            print("Baixe e instale em: https://developer.microsoft.com/en-us/microsoft-edge/webview2/#download-section")
            sys.exit(1)
        else:
            print(f"\nOcorreu um erro inesperado com PyWebView: {e}")
            sys.exit(1)

    print("Janela PyWebView (Blockly) foi fechada.")
    # O loop de eventos do Qt continua se a janela de controle PyQt ainda estiver aberta.
    # QApplication sairá por padrão quando sua última janela visível for fechada.
    if pyqt_control_window_instance and pyqt_control_window_instance.isVisible():
        print("A janela de controle PyQt ainda está ativa. O aplicativo Python continuará até que ela seja fechada.")
        # Se o loop de eventos do Qt já não estiver sendo executado pelo PyWebView (o que deveria com gui='qt'),
        # você pode precisar chamar app_pyqt.exec_() aqui. Mas com gui='qt', isso geralmente não é necessário
        # pois webview.start() já o utilizou. O programa terminará quando a última janela Qt for fechada.
    else:
        print("Nenhuma janela de controle PyQt ativa. Encerrando a aplicação.")
    
    print("Aplicação SMAT desktop encerrada.")
