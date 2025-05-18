Blockly.JavaScript['robo_pose'] = function(block) {
  var number_x = block.getFieldValue('X');
  var number_y = block.getFieldValue('Y');
  var number_bdireito = block.getFieldValue('BDireito');
  var number_besquerdo = block.getFieldValue('BEsquerdo');
  var number_pdireito = block.getFieldValue('PDireito');
  var number_pesquerdo = block.getFieldValue('PEsquerdo');
  var roboPose = {
    "X": number_x,
    "Y": number_y,
    "BDireito": number_bdireito,
    "BEsquerdo": number_besquerdo,
    "PDireito": number_pdireito,
    "PEsquerdo": number_pesquerdo
  };
  return [JSON.stringify(roboPose), Blockly.JavaScript.ORDER_ATOMIC];
};

Blockly.JavaScript['movimento_sequence'] = function(block) {
  var number_fps = block.getFieldValue('FPS');
  var number_duracao = block.getFieldValue('Duracao');
  var value_inicio = Blockly.JavaScript.valueToCode(block, 'Inicio', Blockly.JavaScript.ORDER_ATOMIC) || 'null';
  var value_fim = Blockly.JavaScript.valueToCode(block, 'Fim', Blockly.JavaScript.ORDER_ATOMIC) || 'null';
  
  // Tenta fazer o parse dos JSONs de Inicio e Fim, se não conseguir, mantém como string (ou null)
  let inicioObj, fimObj;
  try {
    inicioObj = JSON.parse(value_inicio);
  } catch (e) {
    inicioObj = value_inicio; 
  }
  try {
    fimObj = JSON.parse(value_fim);
  } catch (e) {
    fimObj = value_fim;
  }

  var movimento = {
    "FPS": number_fps,
    "Duração": number_duracao,
    "Inicio": inicioObj,
    "Fim": fimObj
  };
  return JSON.stringify(movimento, null, 2);
};
