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
        self.export_in_progress = False
        
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

    def request_frames(self, server_url=None):
        """
        Checks for existing frames or requests them from the server.
        
        Returns:
            bool: True if frames are available, False otherwise.
        """
        logger.info("Checking for available frames")
        
        # Check for existing frames
        frame_files = [f for f in os.listdir(self.temp_dir) 
                      if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        if frame_files:
            logger.info(f"Found {len(frame_files)} existing frames in temp directory")
            return True
        
        # No frames found
        logger.warning("No frames found in temp directory")
        return False

    def render_video(self, fps=24, output_filename=None, update_callback=None):
        """
        Renderiza o video a partir dos frames na pasta
        """
        self.export_in_progress = True
        self.progress = 0
        
        # Verifica se o diretório temp está vazio
        frame_files = sorted([f for f in os.listdir(self.temp_dir) 
                             if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
                          
        if not frame_files:
            logger.error("No frames found in temp directory. Cannot render video.")
            self.export_in_progress = False
            return False

        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"smat_animation_{timestamp}.mp4"
        
        if not output_filename.endswith('.mp4'):
            output_filename += '.mp4'
        
        # Verifica se o caminho completo foi fornecido
        if os.path.dirname(output_filename):
            output_path = output_filename
            # Certifica de que o diretório existe
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
        else:
            output_path = os.path.join(self.output_dir, output_filename)

        try:
            # Read first frame to get dimensions
            first_frame_path = os.path.join(self.temp_dir, frame_files[0])
            first_frame = cv2.imread(first_frame_path)
            if first_frame is None:
                logger.error(f"Could not read first frame: {first_frame_path}")
                self.export_in_progress = False
                return False

            height, width, layers = first_frame.shape

            # Initialize video writer - REMOVED the improper with open() statement
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

            from moviepy import VideoFileClip

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_file_name = f"smat_animation_{timestamp}.mp4"

            clip = VideoFileClip('./output_videos/'+output_filename)
            clip.write_videofile('./output_videos/'+new_file_name, codec='libx264', audio_codec='aac')
            clip.close()
            
            import shutil
            shutil.copy('./output_videos/'+new_file_name, './static/videos/display_video.mp4')
            # os.remove('./output_videos/'+output_filename)

            logger.info(f"Video rendered successfully: {output_path}")
            self.export_in_progress = False
            return True
        except Exception as e:
            logger.error(f"Error rendering video: {e}")
            self.export_in_progress = False
            return False

    def get_progress(self):
        """
        Returns current progress percentage
        """
        return {
            "progress": self.progress,
            "complete": not self.export_in_progress and self.progress >= 100,
            "in_progress": self.export_in_progress
        }


