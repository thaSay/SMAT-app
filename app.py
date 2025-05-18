from flask import Flask, render_template, request, jsonify
import os
import json

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/execute', methods=['POST'])
def execute():
    data = request.json
    # O 'data' aqui será o JSON enviado pelo Blockly,
    # contendo a estrutura de Movimento e Robo que definimos.
    
    # Por enquanto, vamos apenas imprimir os dados recebidos no console do servidor
    # e retornar uma resposta de sucesso.
    # Em uma aplicação real, você processaria esses dados aqui
    # (ex: enviaria para um robô, salvaria em um formato específico, etc.)
    print("Dados recebidos do Blockly:")
    print(json.dumps(data, indent=2))
    
    # Simula o processamento dos dados e retorna um output
    # Você pode adaptar esta parte para o que precisa fazer com os dados
    processed_output = []
    if isinstance(data, list): # Espera uma lista de movimentos
        for i, item in enumerate(data):
            if isinstance(item, dict): # Cada item deve ser um dicionário (movimento)
                processed_output.append(f"Processando Movimento {i+1}: FPS={item.get('FPS')}, Duração={item.get('Duração')}")
                # Adicione mais lógica de processamento aqui conforme necessário
            else:
                # Se o item não for um dicionário, pode ser um JSON string de um único movimento
                try:
                    item_data = json.loads(item)
                    processed_output.append(f"Processando Movimento {i+1}: FPS={item_data.get('FPS')}, Duração={item_data.get('Duração')}")
                except json.JSONDecodeError:
                    processed_output.append(f"Movimento {i+1} em formato inesperado: {item}")

    elif isinstance(data, str): # Caso o frontend envie uma string JSON única
        try:
            parsed_data = json.loads(data)
            # Se for uma lista após o parse
            if isinstance(parsed_data, list):
                for i, item in enumerate(parsed_data):
                    if isinstance(item, dict):
                         processed_output.append(f"Processando Movimento {i+1}: FPS={item.get('FPS')}, Duração={item.get('Duração')}")
            elif isinstance(parsed_data, dict): # Se for um único objeto de movimento
                 processed_output.append(f"Processando Movimento: FPS={parsed_data.get('FPS')}, Duração={parsed_data.get('Duração')}")
            else:
                processed_output.append(f"Dados JSON em formato inesperado após parse: {type(parsed_data)}")

        except json.JSONDecodeError:
             processed_output.append(f"Erro ao decodificar JSON string: {data}")
    else:
        processed_output.append(f"Formato de dados inesperado: {type(data)}")


    try:
        # A lógica de execução agora é interpretar o JSON recebido
        # Removendo o antigo 'exec(code, ...)'

        return jsonify({
            'success': True,
            'message': 'Dados recebidos e processados (simulado).',
            'received_data': data, # opcional: retornar os dados recebidos para debug
            'processed_output': processed_output
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'received_data': data
        })

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
    app.run(debug=True)
