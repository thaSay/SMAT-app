# Como usar em outra aplicação:
# from video_green_screen_processor import process_green_screen_video
# success = process_green_screen_video("input.mp4", "output.mp4", "background.jpg")

import cv2
import numpy as np
import os

def process_green_screen_video(input_video_path, output_video_path, background_image_path=None):
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
    
    lower_green = np.array([40, 50, 50])
    upper_green = np.array([80, 255, 255])
    chroma_lower = np.array([40, 70, 40])
    chroma_upper = np.array([80, 255, 255])
    kernel = np.ones((3,3), np.uint8)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        mask = cv2.inRange(hsv_frame, lower_green, upper_green)
        chroma_mask = cv2.inRange(hsv_frame, chroma_lower, chroma_upper)
        mask = cv2.bitwise_or(mask, chroma_mask)
        
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.GaussianBlur(mask, (5, 5), 0)
        
        mask_inv = cv2.bitwise_not(mask)
        
        if background_image is not None:
            background_resized = cv2.resize(background_image, (frame.shape[1], frame.shape[0]))
            foreground = cv2.bitwise_and(frame, frame, mask=mask_inv)
            background_masked = cv2.bitwise_and(background_resized, background_resized, mask=mask)
            result = cv2.add(foreground, background_masked)
        else:
            result = cv2.bitwise_and(frame, frame, mask=mask_inv)
        
        out.write(result)
    
    cap.release()
    out.release()
    return True
