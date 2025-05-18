console.log('Tentando carregar blocks.js...');

Blockly.Blocks['robo_pose'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("Robo");
    this.appendDummyInput()
        .appendField("X")
        .appendField(new Blockly.FieldNumber(0), "X");
    this.appendDummyInput()
        .appendField("Y")
        .appendField(new Blockly.FieldNumber(0), "Y");
    this.appendDummyInput()
        .appendField("Braço Direito")
        .appendField(new Blockly.FieldNumber(0), "BDireito");
    this.appendDummyInput()
        .appendField("Braço Esquerdo")
        .appendField(new Blockly.FieldNumber(0), "BEsquerdo");
    this.appendDummyInput()
        .appendField("Perna Direita")
        .appendField(new Blockly.FieldNumber(0), "PDireito");
    this.appendDummyInput()
        .appendField("Perna Esquerda")
        .appendField(new Blockly.FieldNumber(0), "PEsquerdo");
    this.setOutput(true, "RoboPose");
    this.setColour(230);
    this.setTooltip("Define a pose do robô.");
    this.setHelpUrl("");
  }
};

Blockly.Blocks['movimento_sequence'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("Movimento");
    this.appendDummyInput()
        .appendField("FPS")
        .appendField(new Blockly.FieldNumber(12, 1), "FPS");
    this.appendDummyInput()
        .appendField("Duração (ms)") // Alterado de "Duração (s)" para "Duração (ms)" para corresponder ao gerador
        .appendField(new Blockly.FieldNumber(150, 0), "Duracao");
    this.appendValueInput("Inicio")
        .setCheck("RoboPose")
        .appendField("Pose Inicial");
    this.appendValueInput("Fim")
        .setCheck("RoboPose")
        .appendField("Pose Final");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(120);
    this.setTooltip("Define uma sequência de movimento.");
    this.setHelpUrl("");
  }
};
