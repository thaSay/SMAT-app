from flask import Flask, render_template, request, jsonify, send_file
from datetime import datetime
import os
import json
import threading
from render import VideoRenderer
import requests
import cv2
import numpy as np

app = Flask(__name__)
global_robot_data = None  # Variável global para dados do robô
global_video_renderer = VideoRenderer()
current_control_data = {
    "timestamp": datetime.now().isoformat(),
    "json_data": None,
    "video_result": "No video results yet",
    "robot_image": "[Area to display robot image]"
}

@app.route('/')
def index():
    return render_template('index.html')

def interpolate_pose(start_pose, end_pose, factor):
    interpolated = {}
    if not isinstance(start_pose, dict) or not isinstance(end_pose, dict):
        return {}
    valid_keys_start = {k for k, v in start_pose.items() if isinstance(v, (int, float))}
    valid_keys_end = {k for k, v in end_pose.items() if isinstance(v, (int, float))}
    common_numeric_keys = valid_keys_start.intersection(valid_keys_end)

    all_keys = set(start_pose.keys()).union(set(end_pose.keys()))

    for key in all_keys:
        if key in common_numeric_keys:
            start_val = start_pose.get(key, 0)
            end_val = end_pose.get(key, 0)
            interpolated[key] = start_val + (end_val - start_val) * factor
        else:
            interpolated[key] = start_pose.get(key, end_pose.get(key))
            
    return interpolated

@app.route('/execute', methods=['POST'])
def execute():


    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "error": "Nenhum dado recebido", "received_data": data}), 400

        processed_outputs = []
        command_list = []

        if isinstance(data, list):
            command_list = data
        elif isinstance(data, dict):
            command_list = [data]
        else:
            return jsonify({"success": False, "error": "Formato de dados inválido. Esperava-se uma lista de comandos ou um único comando.", "received_data": data}), 400

        for command_sequence in command_list:
            if not isinstance(command_sequence, dict):
                processed_outputs.append({
                    "type": "error_processing_item",
                    "original_item": command_sequence,
                    "error_message": "Item na lista de comandos não é um objeto JSON válido."
                })
                continue

            if command_sequence.get("tipo") == "movimento_sequence":
                fps = command_sequence.get("FPS")
                duration_ms = command_sequence.get("Duracao")
                start_pose = command_sequence.get("Inicio")
                end_pose = command_sequence.get("Fim")

                if not all([
                    isinstance(fps, (int, float)) and fps > 0,
                    isinstance(duration_ms, (int, float)) and duration_ms >= 0,
                    isinstance(start_pose, dict),
                    isinstance(end_pose, dict)
                ]):
                    processed_outputs.append({
                        "type": "error_processing_sequence",
                        "original_command": command_sequence,
                        "error_message": "Dados incompletos ou inválidos para movimento_sequence (FPS, Duracao, Inicio, Fim). Verifique se as poses estão conectadas."
                    })
                    continue 
                
                sequence_frames = []
                if duration_ms <= 0:
                    current_pose = dict(start_pose) if start_pose else {}
                    if not current_pose and end_pose:
                        current_pose = dict(end_pose)
                    sequence_frames.append(current_pose)
                elif start_pose == end_pose:
                    sequence_frames.append(dict(start_pose))
                else:
                    duration_s = duration_ms / 1000.0
                    # sequence_frames.append(dict(start_pose))


                    frames = int(duration_s*fps)

                    for f_index in range(frames):
                        frame_dict = {}

                        distOwnAxis = int(end_pose['OwnAxis']) - int(start_pose['OwnAxis'])
                        frame_dict['OwnAxis'] = int(f_index * distOwnAxis / (frames - 1) + int(start_pose['OwnAxis']))

                        distX = int(end_pose['X']) - int(start_pose['X'])
                        frame_dict['X'] = int(f_index * distX / (frames - 1) + int(start_pose['X']))

                        distY = int(end_pose['Y']) - int(start_pose['Y'])
                        frame_dict['Y'] = int(f_index * distY / (frames - 1) + int(start_pose['Y']))

                        distBDireito = int(end_pose['BDireito']) - int(start_pose['BDireito'])
                        frame_dict['BDireito'] = int(f_index * distBDireito / (frames - 1) + int(start_pose['BDireito']))

                        distBEsquerdo = int(end_pose['BEsquerdo']) - int(start_pose['BEsquerdo'])
                        frame_dict['BEsquerdo'] = int(f_index * distBEsquerdo / (frames - 1) + int(start_pose['BEsquerdo']))

                        distPDireito = int(end_pose['PDireito']) - int(start_pose['PDireito'])
                        frame_dict['PDireito'] = int(f_index * distPDireito / (frames - 1) + int(start_pose['PDireito']))

                        distPEsquerdo = int(end_pose['PEsquerdo']) - int(start_pose['PEsquerdo'])
                        frame_dict['PEsquerdo'] = int(f_index * distPEsquerdo / (frames - 1) + int(start_pose['PEsquerdo']))
                        
                        sequence_frames.append(frame_dict)

                    # time_at_photo_tick = 1.0 / fps
                    # while time_at_photo_tick < duration_s:
                    #     factor = min(time_at_photo_tick / duration_s, 1.0)
                    #     sequence_frames.append(interpolate_pose(start_pose, end_pose, factor))
                    #     time_at_photo_tick += (1.0 / fps)
                    
                    # if not sequence_frames or sequence_frames[-1] != end_pose:
                    #     sequence_frames.append(dict(end_pose))

                logged_total_frames = len(sequence_frames)
                
                processed_outputs.append({
                    "type": "interpolated_movement",
                    "source_fps": fps,
                    "source_duration_ms": duration_ms,
                    "total_calculated_frames": logged_total_frames,
                    "frames": sequence_frames
                })
            else:                processed_outputs.append({
                    "type": "unknown_or_unprocessed_command",
                    "original_command": command_sequence
                })

        final_json_output_list = []
        can_flatten_all_frames = True

        if not processed_outputs:
            pass
        else:
            for item in processed_outputs:
                if item.get("type") == "interpolated_movement" and "frames" in item:
                    final_json_output_list.extend(item["frames"])
                else:
                    can_flatten_all_frames = False
                    break
            if not can_flatten_all_frames:
                final_json_output_list = processed_outputs
                
        result = jsonify({
            "success": True, 
            "message": "Comandos processados.", 
            "processed_output": final_json_output_list,
            "received_data": data
        })

        try:
            global global_robot_data
            # Enviar a resposta completa do endpoint para o PyQt
            global_robot_data = {
                "success": True, 
                "message": "Comandos processados.", 
                "processed_output": final_json_output_list,
                "received_data": data
            }
        except Exception as pyqt_error:
            import traceback
            traceback.print_exc()

        # Update the control data
        global current_control_data
        current_control_data = {
            "timestamp": datetime.now().isoformat(),
            "json_data": final_json_output_list,
            "video_result": "Commands processed successfully",
            "robot_image": current_control_data.get("robot_image", "[Area to display robot image]")
        }

        # try:
        #     url = "http://localhost:5001/frames"
        #     payload = {"comando": final_json_output_list}
        #     response = requests.post(url, json=payload)
        #     print(response.status_code)  # Print the HTTP status code
        #     print(response.text)
        # except Exception as pyqt_error:
        #     import traceback
        #     traceback.print_exc()

        return result

    except Exception as e:
        app.logger.error(f"Erro ao executar comandos: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e), "received_data": request.data.decode('utf-8', errors='ignore')}), 500

@app.route('/api/send_robot', methods=['POST'])
def send_robot():
    try:
        # Get data directly without extra processing
        data = request.get_json()
        
        # Prepare the command structure
        comandos = {"command": data}
        
        # Save to a temporary file
        with open("comandos.json", "w", encoding="utf-8") as f:
            json.dump(comandos, f, ensure_ascii=False, indent=4)
        
        # Send to the Raspberry Pi server
        try:
            ip = '192.168.0.21'  # Replace with your Raspberry Pi IP
            url = f'http://{ip}:5000/upload'
            
            # Two methods - try both file upload and direct JSON POST
            
            # Method 1: Send file
            with open("comandos.json", "rb") as f:
                files = {'file': ("comandos.json", f, 'application/json')}
                response = requests.post(url, files=files, timeout=5)
            
            # Method 2: If first fails, try direct JSON
            if response.status_code != 200:
                response = requests.post(
                    url, 
                    json=comandos,
                    headers={'Content-Type': 'application/json'},
                    timeout=5
                )
            
            return jsonify({
                "success": True,
                "status_code": response.status_code,
                "message": "Commands sent to robot successfully",
                "response": response.text
            })
            
        except requests.exceptions.RequestException as e:
            app.logger.error(f"Failed to connect to robot server: {str(e)}")
            return jsonify({
                "success": False, 
                "error": f"Failed to connect to robot at {ip}:5000. Error: {str(e)}"
            }), 500
            
    except Exception as e:
        app.logger.error(f"Error in send_robot: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500

@app.route('/save', methods=['POST'])
def save():
    blocks = request.json.get('blocks', '')
    
    try:
        with open('saved_blocks.json', 'w') as f:
            json.dump(blocks, f)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/load', methods=['GET'])
def load():
    try:
        if os.path.exists('saved_blocks.json'):
            with open('saved_blocks.json', 'r') as f:
                blocks = json.load(f)
            return jsonify({'success': True, 'blocks': blocks})
        else:
            return jsonify({'success': False, 'error': 'Nenhum arquivo salvo encontrado'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/get_control_data')
def get_control_data():
    global current_control_data
    return jsonify(current_control_data)

# @app.route('/api/capture_photo', methods=['POST'])
# def capture_photo():
#     # This would interface with camera/robot in the future
#     global current_control_data
#     current_control_data["timestamp"] = datetime.now().isoformat()
#     current_control_data["robot_image"] = f"Image captured at {datetime.now().strftime('%H:%M:%S')}"
#     return jsonify({"success": True, "message": current_control_data["robot_image"]})

@app.route('/api/export_video', methods=['POST'])
def export_video_endpoint():
    global global_video_renderer
    
    try:
        # Try to get JSON data if present
        data = request.get_json()

        json_list = type(data) == list and len(data) > 0

        # if type(data) != list or len(data) == 0:

        # fps = data.get('FPS', 24)
        fps = -1
        fps_blocks = []
        if json_list:
            fps_blocks = global_video_renderer.convert_json_to_fps_blocks(data)
        else:
            fps = data.get('FPS', 12) if type(data) != list else 12

        # Start export in background thread
        def run_export():
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"smat_animation_{timestamp}.mp4"
                
                if not global_video_renderer.request_frames():
                    global_video_renderer.progress = 0
                    global_video_renderer.export_in_progress = False
                    app.logger.error("No frames available for video export")
                    return

                if json_list:      
                    global_video_renderer.render_video_variable_fps(
                    fps_blocks=fps_blocks,
                    output_filename=output_filename
                )
                else:
                    global_video_renderer.render_video(fps=fps, output_filename=output_filename)

                # from moviepy import VideoFileClip
                # clip = VideoFileClip(output_filename)
                # clip.write_videofile(output_filename, codec='libx264', audio_codec='aac')
                # clip.close()

            except Exception as e:
                app.logger.error(f"Error in export thread: {e}")
                global_video_renderer.export_in_progress = False
                global_video_renderer.progress = 0

                return jsonify({"success": False, "error": str(e)}), 500
        
        # Start rendering in a background thread
        thread = threading.Thread(target=run_export)
        thread.daemon = True
        thread.start()
        
        return jsonify({"success": True, "message": "Video export started"})
    except Exception as e:
        app.logger.error(f"Error starting video export: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/export_progress')
def export_progress():
    global global_video_renderer
    return jsonify(global_video_renderer.get_progress())

@app.route('/api/delete_video', methods=['POST'])
def delete_video():
    import os
    from os import listdir
    from os.path import isfile, join
    path = './output_videos'
    onlyfiles = [f for f in listdir(path) if isfile(join(path, f))]
    onlyfiles.sort(reverse=True)

    os.remove(path+ '/' + onlyfiles[0])

    return jsonify({"success": True, "message": "Done." })

@app.route('/api/frame_load', methods=['POST'])
def frame_load():

    file = request.files['file']
    filename = file.filename
    file.save(filename)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'image' not in request.files:
        return jsonify({'message': 'Nenhuma imagem recebida'}), 400

    image = request.files['image']
    command_index = request.form.get('command_index', 'unknown')

    filename = f'command_{command_index}.jpg'
    filepath = os.path.join('./temp_frames', filename)
    image.save(filepath)

    print(f"Imagem salva em {filepath}")
    return jsonify({'message': f'Imagem recebida e salva como {filename}'}), 200

@app.route('/api/concat_videos', methods=['POST'])
def concat_videos():
    from moviepy import VideoFileClip, concatenate_videoclips

    def concat_videos(video_paths, output_path):
        """
        Concatenates multiple video files into a single video.

        Args:
            video_paths: A list of paths to the video files to be concatenated.
            output_path: The path where the concatenated video will be saved.
        """
        clips = [VideoFileClip(path) for path in video_paths]
        final_clip = concatenate_videoclips(clips)
        final_clip.write_videofile(output_path, codec='libx264')

    path = './output_videos'

    import os
    from os import listdir
    from os.path import isfile, join
    from datetime import datetime
    onlyfiles = [f for f in listdir(path) if isfile(join(path, f))]
    onlyfiles.sort()
    lgth=len(onlyfiles)

    if lgth < 2:
        return jsonify({"success": False, "error": "There are not videos enought for this operation"})

    video1_path = path + '/' + onlyfiles[lgth-2]  # Replace with your first video path
    video2_path = path + '/' + onlyfiles[lgth-1]  # Replace with your second video path

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"smat_animation_{timestamp}.mp4"
    output_video_path = path + '/' +  output_filename  # Replace with your desired output path

    concat_videos([video1_path, video2_path], output_video_path)
    os.remove(video1_path)
    os.remove(video2_path)

    import shutil
    shutil.copy(output_video_path, './static/videos/display_video.mp4')

    return jsonify({"success": True, "message": "Done." })

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

@app.route('/api/remove_background', methods=['POST'])
def remove_green_screen():
    import os
    from os import listdir
    from os.path import isfile, join

    if 'arquivo' not in request.files:
        return {'erro': 'Nenhum arquivo encontrado'}, 400

    file = request.files['arquivo']
    if file.filename == '':
        return {'erro': 'Nenhum arquivo selecionado'}, 400

    filepath = os.path.join('background', file.filename)
    file.save(filepath)

    path = './output_videos'
    onlyfiles = [f for f in listdir(path) if isfile(join(path, f))]
    onlyfiles.sort(reverse=True)

    input_path = path+ '/' + onlyfiles[0]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"smat_animation_{timestamp}.mp4"
    output_video_path = path + '/' +  output_filename  # Replace with your desired output path

    process_green_screen_video(input_path, output_video_path, background_image_path='./background/'+ file.filename)

    os.remove(input_path)

    from moviepy import VideoFileClip

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_file_name = f"smat_animation_{timestamp}.mp4"

    clip = VideoFileClip('./output_videos/'+output_filename)
    clip.write_videofile('./output_videos/'+new_file_name, codec='libx264', audio_codec='aac')
    clip.close()

    import shutil
    shutil.copy('./output_videos/'+new_file_name, './static/videos/display_video.mp4')

    return jsonify({"success": True, "message": "Done." })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
