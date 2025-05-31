console.log('Tentando carregar generator.js...');
/**
 * 
{
  "command": [
    {
      "X": 0,
      "Y": 0,
      "BDireito": 0,
      "BEsquerdo": 0,
      "PDireito": 0,
      "PEsquerdo": 0
    },
    {
      "X": 1,
      "Y": 1,
      "BDireito": 1,
      "BEsquerdo": 0,
      "PDireito": 0,
      "PEsquerdo": 1
    }
  ]
}
 */

Blockly.JavaScript['robo_pose'] = function(block) {
  console.log('Gerador robo_pose chamado.');
  var number_x = block.getFieldValue('X');
  var number_y = block.getFieldValue('Y');
  var number_ownaxis = block.getFieldValue('OwnAxis');
  var number_bdireito = block.getFieldValue('BDireito');
  var number_besquerdo = block.getFieldValue('BEsquerdo');
  var number_pdireito = block.getFieldValue('PDireito');
  var number_pesquerdo = block.getFieldValue('PEsquerdo');
  var roboPose = {
    "OwnAxis": number_ownaxis,
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
  console.log('Gerador movimento_sequence chamado.');
  var number_fps = block.getFieldValue('FPS');
  var number_duracao = block.getFieldValue('Duracao');
  var value_inicio = Blockly.JavaScript.valueToCode(block, 'Inicio', Blockly.JavaScript.ORDER_ATOMIC);
  var value_fim = Blockly.JavaScript.valueToCode(block, 'Fim', Blockly.JavaScript.ORDER_ATOMIC);
  
  console.log('Dados do movimento_sequence:', {
    fps: number_fps,
    duracao: number_duracao,
    inicio: value_inicio,
    fim: value_fim
  });
  
  var movimento = {
    "tipo": "movimento_sequence",
    "FPS": number_fps,
    "Duracao": number_duracao,
    "Inicio": value_inicio ? JSON.parse(value_inicio) : {},
    "Fim": value_fim ? JSON.parse(value_fim) : {}
  };
  
  return JSON.stringify(movimento);
};

console.log('generator.js carregado e parseado completamente.');
console.log('Status de Blockly.JavaScript[\'movimento_sequence\'] após definição:', typeof Blockly.JavaScript['movimento_sequence']);
console.log('Objeto Blockly.JavaScript completo após generator.js:', Blockly.JavaScript);
