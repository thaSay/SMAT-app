from flask import Flask, render_template, request, jsonify
import os
import json

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

def interpolate_pose(start_pose, end_pose, factor):
    interpolated = {}
    if not isinstance(start_pose, dict) or not isinstance(end_pose, dict):
        # Retorna um dicionário vazio ou lança um erro se as poses não forem dicionários
        # Isso ajuda a evitar erros NoneType mais tarde se as poses não forem fornecidas corretamente
        return {}
    valid_keys_start = {k for k, v in start_pose.items() if isinstance(v, (int, float))}
    valid_keys_end = {k for k, v in end_pose.items() if isinstance(v, (int, float))}
    common_numeric_keys = valid_keys_start.intersection(valid_keys_end)

    all_keys = set(start_pose.keys()).union(set(end_pose.keys()))

    for key in all_keys:
        if key in common_numeric_keys:
            start_val = start_pose.get(key, 0) # Padrão para 0 se ausente, embora common_numeric_keys deva garantir presença
            end_val = end_pose.get(key, 0)
            interpolated[key] = start_val + (end_val - start_val) * factor
        else:
            # Para chaves não numéricas ou não comuns, priorize start_pose, depois end_pose, ou None
            interpolated[key] = start_pose.get(key, end_pose.get(key))
            
    return interpolated

@app.route('/execute', methods=['POST'])
def execute():
    try:
        data = request.get_json()
        app.logger.info(f"Dados recebidos do Blockly: {json.dumps(data, indent=2)}")

        if not data:
            return jsonify({"success": False, "error": "Nenhum dado recebido", "received_data": data}), 400

        processed_outputs = []
        command_list = []

        if isinstance(data, list):
            command_list = data
        elif isinstance(data, dict):
            command_list = [data] # Trata um único objeto JSON como uma lista de um comando
        else:
            return jsonify({"success": False, "error": "Formato de dados inválido. Esperava-se uma lista de comandos ou um único comando.", "received_data": data}), 400

        for command_sequence in command_list:
            if not isinstance(command_sequence, dict): # Verifica se cada item na lista é um dicionário
                processed_outputs.append({
                    "type": "error_processing_item",
                    "original_item": command_sequence,
                    "error_message": "Item na lista de comandos não é um objeto JSON válido."
                })
                continue

            if command_sequence.get("tipo") == "movimento_sequence":
                fps = command_sequence.get("FPS")
                duration_ms = command_sequence.get("Duracao") # Corrigido de "Duração"
                start_pose = command_sequence.get("Inicio")
                end_pose = command_sequence.get("Fim")

                # Validação robusta dos dados recebidos
                if not all([
                    isinstance(fps, (int, float)) and fps > 0,
                    isinstance(duration_ms, (int, float)) and duration_ms >= 0, # Permite duration_ms = 0
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
                    # Se a duração é zero ou negativa, apenas a pose inicial (ou final, se inicial for nula)
                    current_pose = dict(start_pose) if start_pose else {}
                    if not current_pose and end_pose: # Fallback para end_pose se start_pose não existir
                        current_pose = dict(end_pose)
                    sequence_frames.append(current_pose)
                elif start_pose == end_pose:
                    # Se as poses são iguais, apenas uma pose, independentemente da duração
                    sequence_frames.append(dict(start_pose))
                else:
                    # Movimento real com duração > 0 e poses diferentes
                    duration_s = duration_ms / 1000.0
                    sequence_frames.append(dict(start_pose)) # Adiciona a pose inicial (foto em t=0)

                    # Adiciona poses para os ticks de FPS intermediários
                    time_at_photo_tick = 1.0 / fps
                    while time_at_photo_tick < duration_s:
                        # Fator de interpolação não deve exceder 1.0
                        factor = min(time_at_photo_tick / duration_s, 1.0)
                        sequence_frames.append(interpolate_pose(start_pose, end_pose, factor))
                        time_at_photo_tick += (1.0 / fps)
                    
                    # Adiciona a end_pose se não for já a última na lista
                    # Isso garante que o movimento sempre termina na end_pose especificada.
                    if not sequence_frames or sequence_frames[-1] != end_pose:
                        sequence_frames.append(dict(end_pose))

                # logged_total_frames agora reflete o número de frames na lista gerada
                logged_total_frames = len(sequence_frames)
                
                processed_outputs.append({
                    "type": "interpolated_movement",
                    "source_fps": fps,
                    "source_duration_ms": duration_ms,
                    "total_calculated_frames": logged_total_frames, # Mantém o significado original
                    "frames": sequence_frames
                })
            else:
                processed_outputs.append({
                    "type": "unknown_or_unprocessed_command",
                    "original_command": command_sequence
                })

        # Determine the structure of processed_output for the JSON response
        final_json_output_list = []
        can_flatten_all_frames = True

        if not processed_outputs: # No commands processed or input was empty
            pass # final_json_output_list is already [], which is fine
        else:
            for item in processed_outputs:
                if item.get("type") == "interpolated_movement" and "frames" in item:
                    final_json_output_list.extend(item["frames"])
                else:
                    can_flatten_all_frames = False
                    break # Found an item that doesn't fit the flat frame list model
        
            if not can_flatten_all_frames:
                # If unable to flatten (e.g., mixed command types, errors),
                # use the original list of dictionaries.
                final_json_output_list = processed_outputs

        result = jsonify({
            "success": True, 
            "message": "Comandos processados.", 
            "processed_output": final_json_output_list, # Use the potentially transformed list
            "received_data": data
        })

        return result

    except Exception as e:
        app.logger.error(f"Erro ao executar comandos: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e), "received_data": request.data.decode('utf-8', errors='ignore')}), 500

@app.route('/save', methods=['POST'])
def save():
    blocks = request.json.get('blocks', '')
    
    # Salvar os blocos em um arquivo
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)
