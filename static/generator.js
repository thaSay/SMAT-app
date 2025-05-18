console.log('Tentando carregar generator.js...');

Blockly.JavaScript['robo_pose'] = function(block) {
  console.log('Gerador robo_pose chamado.');
  var number_x = block.getFieldValue('X');
  var number_y = block.getFieldValue('Y');
  var number_bdireito = block.getFieldValue('BDireito');
  var number_besquerdo = block.getFieldValue('BEsquerdo');
  var number_pdireito = block.getFieldValue('PDireito');
  var number_pesquerdo = block.getFieldValue('PEsquerdo');
  var roboPose = {
    "X": number_x, // Estes já são retornados como números pelo getFieldValue
    "Y": number_y,
    "BDireito": number_bdireito,
    "BEsquerdo": number_besquerdo,
    "PDireito": number_pdireito,
    "PEsquerdo": number_pesquerdo
  };
  return [JSON.stringify(roboPose), Blockly.JavaScript.ORDER_ATOMIC];
};

Blockly.JavaScript['movimento_sequence'] = function(block) {
  console.log('Gerador movimento_sequence chamado.');
  var number_fps = block.getFieldValue('FPS'); // Já é número
  var number_duracao = block.getFieldValue('Duracao'); // Já é número
  var value_inicio_str = Blockly.JavaScript.valueToCode(block, 'Inicio', Blockly.JavaScript.ORDER_ATOMIC) || 'null';
  var value_fim_str = Blockly.JavaScript.valueToCode(block, 'Fim', Blockly.JavaScript.ORDER_ATOMIC) || 'null';
  
  let inicioObj = null;
  try {
    // Só tenta parsear se não for a string 'null' literalmente
    if (value_inicio_str && value_inicio_str !== 'null') {
      inicioObj = JSON.parse(value_inicio_str);
    }
  } catch (e) {
    console.warn('Falha ao fazer parse da Pose Inicial JSON string:', value_inicio_str, e);
    // inicioObj permanece null
  }

  let fimObj = null;
  try {
    // Só tenta parsear se não for a string 'null' literalmente
    if (value_fim_str && value_fim_str !== 'null') {
      fimObj = JSON.parse(value_fim_str);
    }
  } catch (e) {
    console.warn('Falha ao fazer parse da Pose Final JSON string:', value_fim_str, e);
    // fimObj permanece null
  }

  var movimento = {
    "tipo": "movimento_sequence", // Adicionado campo "tipo"
    "FPS": number_fps,
    "Duracao": number_duracao,   // Chave alterada de "Duração" para "Duracao"
    "Inicio": inicioObj,
    "Fim": fimObj
  };
  // Retorna apenas a string JSON. workspaceToCode irá concatenar múltiplas instâncias com \n\n.
  return JSON.stringify(movimento, null, 2); 
};

console.log('generator.js carregado e parseado completamente.');
console.log('Status de Blockly.JavaScript[\'movimento_sequence\'] após definição:', typeof Blockly.JavaScript['movimento_sequence']);
console.log('Objeto Blockly.JavaScript completo após generator.js:', Blockly.JavaScript);
