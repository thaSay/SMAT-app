import webview
import threading
import time
import json
import os
import sys
from app import app

# Adicionado para PyQt5
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton, QFileDialog, QProgressDialog, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont # Para definir a fonte

# Nosso render
from render import VideoRenderer

# Define uma porta para o Flask rodar, idealmente uma que não entre em conflito
FLASK_PORT = 5001
FLASK_HOST = '127.0.0.1'

webview_window_instance = None
# Renomeado para refletir a mudança para PyQt
create_pyqt_ui_flag = False
robot_data_for_pyqt = None

class Api:
    def _destroy_webview_window(self):
        global webview_window_instance
        if webview_window_instance:
            print("Chamando webview_window_instance.destroy()")
            webview_window_instance.destroy()
            webview_window_instance = None

    def handle_robot_data(self, data_from_js):
        global create_pyqt_ui_flag, robot_data_for_pyqt # Atualizado nome da flag e var de dados
        print(f"Python (API) recebeu dados do JS: {data_from_js}")
        robot_data_for_pyqt = data_from_js
        create_pyqt_ui_flag = True
        
        print("Agendando destruição da janela PyWebView.")
        threading.Timer(0.1, self._destroy_webview_window).start()
        
        return {"status": "success", "message": "Dados recebidos. Iniciando UI nativa."}

api_instance = Api()

def export_video(window, fps=24):
    """
    Exporta os frames como MP4

    A verificação de se há frames para exportar é feita em render.py
    """
    
    # Dialogo do processo
    progress = QProgressDialog("Requisitando frames e renderizando vídeo...", "Cancelar", 0, 100, window)
    progress.setWindowTitle("Progresso da Renderização")
    progress.setWindowModality(Qt.WindowModal)
    progress.setValue(0)
    progress.show()

    # Função de callback para retornar o progresso
    def update_progress(value):
        progress.setValue(int(value))
        QApplication.processEvents()

    # Inicia o renderizador
    renderer = VideoRenderer()

    # Renderiza os frames
    success = renderer.render_video(fps = fps, update_callback=update_progress)

    progress.setValue(100)
    progress.close()

    if success:
        QMessageBox.information(
            window, 
            "Sucesso", 
            f"Vídeo renderizado com sucesso!"
        )
        print("Video renderizado com sucesso!")

    else:
        QMessageBox.critical(window, "Erro", "Falha ao renderizar o vídeo")

def create_robot_control_ui_pyqt(data):
    """Cria e exibe a interface de controle do robô com PyQt5."""
    # QApplication é gerenciado no bloco __main__

    window = QWidget()
    window.setWindowTitle("Controle do Robô e Visualização - PyQt5")
    window.setGeometry(150, 150, 800, 600) # x, y, largura, altura

    layout = QVBoxLayout()

    title_label = QLabel("Interface de Controle do Robô")
    title_label.setFont(QFont("Arial", 16))
    title_label.setAlignment(Qt.AlignCenter)
    layout.addWidget(title_label)

    data_label = QLabel("Dados Recebidos dos Blocos:")
    layout.addWidget(data_label)

    data_text_area = QTextEdit()
    data_text_area.setPlainText(json.dumps(data, indent=2) if data else "Nenhum dado recebido.")
    data_text_area.setReadOnly(True)
    layout.addWidget(data_text_area)

    image_placeholder_label = QLabel("[Área para exibir imagem do robô]")
    image_placeholder_label.setAlignment(Qt.AlignCenter)
    layout.addWidget(image_placeholder_label)

    def capture_and_display_image_pyqt():
        print("Simulando captura e exibição de imagem (PyQt)...")
        image_placeholder_label.setText("Imagem X capturada e exibida (simulado - PyQt)")

    capture_button = QPushButton("Próximo Passo / Capturar Foto")
    capture_button.clicked.connect(capture_and_display_image_pyqt)
    layout.addWidget(capture_button)
    
    # Exportar video
    export_video_button = QPushButton("Exportar Vídeo MP4")
    fps = data.get("fps", 24)
    export_video_button.clicked.connect(lambda: export_video(window, int(fps)))
    layout.addWidget(export_video_button)

    def close_app_pyqt():
        print("Fechando aplicação PyQt.")
        window.close() # Fecha esta janela. Se for a última, o app pode sair.

    exit_button = QPushButton("Fechar Controle do Robô")
    exit_button.clicked.connect(close_app_pyqt)
    layout.addWidget(exit_button)

    window.setLayout(layout)
    window.show()
    return window # Retorna a instância da janela para referência, se necessário

def run_flask():
    """Função para rodar o servidor Flask."""
    print(f"Iniciando servidor Flask em http://{FLASK_HOST}:{FLASK_PORT}")
    # use_reloader=False é importante para evitar problemas com múltiplas instâncias em threads
    # debug=False é recomendado para a versão "desktop"
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False, use_reloader=False)

if __name__ == '__main__':
    print("Iniciando aplicação desktop com PyQt...")
    
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    time.sleep(3) 

    webview_window_instance = webview.create_window(
        'SMAT Robô Blockly Interface', 
        f'http://{FLASK_HOST}:{FLASK_PORT}/',
        width=1200, 
        height=800, 
        resizable=True,
        js_api=api_instance
    )
    webview.start() # Bloqueia até a janela PyWebView ser fechada

    # Após webview.start() retornar:
    if create_pyqt_ui_flag:
        print("Transicionando para a UI PyQt5...")
        if robot_data_for_pyqt:
            # QApplication deve ser criado antes de qualquer QWidget
            # e só pode haver uma instância.
            app_pyqt = QApplication.instance() # Verifica se já existe
            if app_pyqt is None:
                app_pyqt = QApplication(sys.argv) # Cria se não existir
            
            control_window_pyqt = create_robot_control_ui_pyqt(robot_data_for_pyqt)
            # Inicia o loop de eventos do PyQt5. sys.exit garante uma saída limpa.
            sys.exit(app_pyqt.exec_()) 
        else:
            print("Nenhum dado do robô para exibir na UI PyQt. Algo deu errado.")
    
    print("Aplicação desktop principal encerrada.")
