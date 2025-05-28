import os
import cv2
import time
import shutil
import requests
import logging
from datetime import datetime
from pathlib import Path

# Configura Logging (mantém o progresso da renderização)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger('smat_render')

class VideoRenderer:
    def __init__(self, temp_dir='temp_frames', output_dir='output_videos'):
        
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.temp_dir = os.path.join(self.base_path, temp_dir)
        self.output_dir = os.path.join(self.base_path, output_dir)

        # Cria os diretórios se eles não existirem
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

        # Contador de frames e tracker do progresso
        self.frame_counter = 0
        self.progress = 0
        self.frames = []

        logger.info(f"VideoRenderer initialized. Temp dir: {self.temp_dir}, Output dir: {self.output_dir}")

    def clear_temp_directory(self):
        """ Remove todos os arquivos temporários"""
        if os.path.exists(self.temp_dir):
            for file in os.listdir(self.temp_dir):
                file_path = os.path.join(self.temp_dir, file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    logger.error(f'Error clearing temp file {file_path}: {e}')
        
        self.frame_counter = 0
        self.progress = 0
        self.frames = []
        logger.info("Temporary directory cleared")

    def request_frames(self):
        """
        AINDA NÃO FOI IMPLEMENTADO, NECESSITA DE DEVIDA IMPLEMENTAÇÃO
        presumidamente, a aplicação principal requisita ao rasp as imagens
        uma vez finalizada pode seguir para o render_video
        """
        ##self.clear_temp_directory()

    def render_video(self, fps=24, output_filename=None, update_callback=None):
        """
        Renderiza o video a partir dos frames na pasta
        """
        # Verifica se o diretório temp está vazio
        if not os.listdir(self.temp_dir):
            logger.error("No frames found in temp directory. Cannot render video.")
            return False

        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"smat_animation_{timestamp}"

        if not output_filename.endswith('.mp4'):
            output_filename += '.mp4'

        output_path = os.path.join(self.output_dir, output_filename)

        try:
            with open(output_path, 'w') as f:
                frame_files = sorted([f for f in os.listdir(self.temp_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])

                # Read first frame to get dimensions
                first_frame_path = os.path.join(self.temp_dir, frame_files[0])
                first_frame = cv2.imread(first_frame_path)
                if first_frame is None:
                    logger.error(f"Could not read first frame: {first_frame_path}")
                    return False

                height, width, layers = first_frame.shape

                # Initialize video writer
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                video_writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

                # Process each frame
                total_frames = len(frame_files)
                for i, frame_file in enumerate(frame_files):
                    frame_path = os.path.join(self.temp_dir, frame_file)
                    frame = cv2.imread(frame_path)
                    
                    if frame is not None:
                        video_writer.write(frame)
                        self.progress = int((i + 1) / total_frames * 100)
                        
                        if update_callback:
                            update_callback(self.progress)
                        
                        logger.info(f"Processed frame {i + 1}/{total_frames} ({self.progress}%)")
                    else:
                        logger.warning(f"Could not read frame: {frame_path}")

                video_writer.release()
                logger.info(f"Video rendered successfully: {output_path}")
                return True
        except Exception as e:
            logger.error(f"Error rendering video: {e}")
            return None

        
