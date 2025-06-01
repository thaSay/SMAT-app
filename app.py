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

                        distOwnAxis = end_pose['OwnAxis']-start_pose['OwnAxis']
                        frame_dict['OwnAxis'] = f_index*distOwnAxis/(frames-1)+start_pose['OwnAxis']               

                        distX = end_pose['X']-start_pose['X']
                        frame_dict['X'] = f_index*distX/(frames-1)+start_pose['X']                      
                        
                        distY = end_pose['Y']-start_pose['Y']
                        frame_dict['Y'] =f_index*distY/(frames-1)+start_pose['Y']                    
                        
                        distBDireito = end_pose['BDireito']-start_pose['BDireito']
                        frame_dict['BDireito'] = f_index*distBDireito/(frames-1)+start_pose['BDireito']                      
                        
                        distBEsquerdo = end_pose['BEsquerdo']-start_pose['BEsquerdo']
                        frame_dict['BEsquerdo'] = f_index*distBEsquerdo/(frames-1)+start_pose['BEsquerdo']                     
                        
                        distPDireito = end_pose['PDireito']-start_pose['PDireito']
                        frame_dict['PDireito'] = f_index*distPDireito/(frames-1)+start_pose['PDireito']                     
                        
                        distPEsquerdo = end_pose['PEsquerdo']-start_pose['PEsquerdo']
                        frame_dict['PEsquerdo'] = f_index*distPEsquerdo/(frames-1)+start_pose['PEsquerdo']                      
                        
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

        try:
            url = "http://localhost:5001/frames"
            payload = {"comando": final_json_output_list}
            response = requests.post(url, json=payload)
            print(response.status_code)  # Print the HTTP status code
            print(response.text)
        except Exception as pyqt_error:
            import traceback
            traceback.print_exc()

        return result

    except Exception as e:
        app.logger.error(f"Erro ao executar comandos: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e), "received_data": request.data.decode('utf-8', errors='ignore')}), 500

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

@app.route('/api/capture_photo', methods=['POST'])
def capture_photo():
    # This would interface with camera/robot in the future
    global current_control_data
    current_control_data["timestamp"] = datetime.now().isoformat()
    current_control_data["robot_image"] = f"Image captured at {datetime.now().strftime('%H:%M:%S')}"
    return jsonify({"success": True, "message": current_control_data["robot_image"]})

@app.route('/api/export_video', methods=['POST'])
def export_video_endpoint():
    global global_video_renderer
    
    try:
        # Try to get JSON data if present
        data = request.get_json()
        fps = data.get('FPS', 24)
        
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
                    
                global_video_renderer.render_video(fps=fps, output_filename=output_filename)
            except Exception as e:
                app.logger.error(f"Error in export thread: {e}")
                global_video_renderer.export_in_progress = False
                global_video_renderer.progress = 0
        
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

@app.route('/api/close_application', methods=['POST'])
def close_application():
    # This will only work in the desktop app context
    try:
        if app.main_window_ref and callable(app.main_window_ref):
            app_window = app.main_window_ref()
            if app_window:
                # Schedule closing the window
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(500, app_window.close)
                return jsonify({"success": True})
    except Exception as e:
        app.logger.error(f"Error closing application: {e}", exc_info=True)
    
    return jsonify({"success": False, "error": "Cannot close - not running in desktop mode"})

@app.route('/api/frame_load', methods=['POST'])
def frame_load():

    file = request.files['file']
    filename = file.filename
    file.save(filename)

    # nparr = np.fromstring(request.files['file'][1], np.uint8)
    # image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # cv2.imwrite(filename, image)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
