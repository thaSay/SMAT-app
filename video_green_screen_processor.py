# Como usar em outra aplicação:
# from video_green_screen_processor import process_green_screen_video
# success = process_green_screen_video("input.mp4", "output.mp4", "background.jpg")

import cv2
import numpy as np
import os

def weightedGreens(img, mask):
    """
    Atribui peso aos pixels verdes baseado na distância euclidiana,
    com maior peso ao canal verde.
    
    Args:
        img: Imagem em formato HLS
        mask: Máscara binária onde processar
        
    Returns:
        Máscara com pesos de 0 a 1 para o canal verde
    """
    # Converte para BGR e float32 apenas uma vez
    aux = cv2.cvtColor(img, cv2.COLOR_HLS2BGR).astype(np.float32)
    # Calcula a máscara de verde apenas onde mask != 0
    green_mask = np.zeros(mask.shape, dtype=np.float32)
    idx = mask != 0
    # Peso maior para o canal verde
    b, g, r = aux[..., 0], aux[..., 1], aux[..., 2]
    dist = ((b[idx]**2 + (g[idx])**2 + r[idx]**2) - (b[idx]**2 + r[idx]**2)*1.5)**2
    green_mask[idx] = dist
    # Normaliza e poda o intervalo
    green_mask = cv2.normalize(green_mask, None, 0, 2, cv2.NORM_MINMAX)
    green_mask = np.clip(green_mask, 0, 1)
    return green_mask

def process_green_screen_video(input_video_path, output_video_path, background_image_path=None):
    """
    Processa um vídeo com tela verde, substituindo pelo background especificado.
    Utiliza algoritmo avançado de detecção de verde com bordas suaves.
    
    Args:
        input_video_path: Caminho para o vídeo de entrada
        output_video_path: Caminho para salvar o vídeo processado
        background_image_path: Caminho para a imagem de fundo
        
    Returns:
        True se o processamento foi bem sucedido, False caso contrário
    """
    if not os.path.exists(input_video_path):
        return False
    
    background_image = None
    if background_image_path and os.path.exists(background_image_path):
        background_image = cv2.imread(background_image_path)
    
    cap = cv2.VideoCapture(input_video_path)
    if not cap.isOpened():
        return False
    
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
    
    if not out.isOpened():
        cap.release()
        return False
    
    # Limites para canal verde no espaço HLS (Hue, Lightness, Saturation)
    LWR_G = np.array([25, 0, 0])   # Limite inferior (HLS)
    UPR_G = np.array([90, 255, 255]) # Limite superior (HLS)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Converte para HLS (em vez de HSV usado anteriormente)
        hls_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HLS)
        
        # Cria a máscara de verde inicial
        green_mask = cv2.inRange(hls_frame, LWR_G, UPR_G)
        
        # Calcula os pesos para pixels verdes (valor entre 0 e 1)
        w_mask = weightedGreens(hls_frame, green_mask)
        
        # Dimensiona o background para o tamanho do frame
        if background_image is not None:
            background_resized = cv2.resize(background_image, (frame.shape[1], frame.shape[0]))
        else:
            # Se não houver background, usa um fundo preto
            background_resized = np.zeros_like(frame)
        
        # Converte para float32 para operações de blending
        frame_float = frame.astype(np.float32)
        bg_float = background_resized.astype(np.float32)
        result = np.zeros_like(frame_float)
        
        # Máscaras booleanas para pixels verdes e não verdes
        not_green = w_mask <= 0.1
        is_green = ~not_green
        
        # Para pixels não verdes: copia o pixel original
        result[not_green] = frame_float[not_green]
        
        # Reduz o tom de verde nos pixels onde o verde é dominante mas não está na máscara
        green_dominant = (frame_float[...,1] > np.sqrt(frame_float[...,0]**2 + frame_float[...,2]**2)) & not_green
        result[green_dominant,1] = (frame_float[green_dominant,0] + frame_float[green_dominant,2]) / 2
        
        # Para pixels verdes: desverdeia e mescla com o fundo
        aux = frame_float.copy()
        aux[is_green,1] = (frame_float[is_green,0] + frame_float[is_green,2]) / 2
        
        # Expande w_mask para broadcast
        w_mask_exp = w_mask[...,None]
        result[is_green] = bg_float[is_green] * w_mask_exp[is_green] + aux[is_green] * (1 - w_mask_exp[is_green])
        
        # Detecta bordas para suavização
        sobelx = cv2.Sobel(w_mask, cv2.CV_64F, 1, 0, ksize=1)
        sobely = cv2.Sobel(w_mask, cv2.CV_64F, 0, 1, ksize=1)
        magnitude = cv2.magnitude(sobelx, sobely)
        magnitude = cv2.normalize(magnitude, None, 0, 1, cv2.NORM_MINMAX)
        
        # Aplica blur apenas nas bordas usando a magnitude como máscara de mistura
        result_aux = cv2.GaussianBlur(result, (3, 3), 0)
        mag_exp = magnitude[..., None]
        result = result_aux * mag_exp + result * (1 - mag_exp)
        
        # Converte de volta para uint8 para salvar no vídeo
        result = np.clip(result, 0, 255).astype(np.uint8)
        
        out.write(result)
    
    cap.release()
    out.release()
    return True