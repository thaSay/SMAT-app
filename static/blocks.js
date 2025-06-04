console.log("Tentando carregar blocks.js...");

Blockly.Blocks["robo_pose"] = {
  init: function () {
    this.appendDummyInput().appendField("Robot");
    this.appendDummyInput()
      .appendField("Own Axis")
      .appendField(new Blockly.FieldNumber(0), "OwnAxis");
    this.appendDummyInput()
      .appendField("X")
      .appendField(new Blockly.FieldNumber(0), "X");
    this.appendDummyInput()
      .appendField("Y")
      .appendField(new Blockly.FieldNumber(50), "Y");
    this.appendDummyInput()
      .appendField("Right Arm")
      .appendField(new Blockly.FieldNumber(0), "BDireito");
    this.appendDummyInput()
      .appendField("Left Arm")
      .appendField(new Blockly.FieldNumber(0), "BEsquerdo");
    this.appendDummyInput()
      .appendField("Right Leg")
      .appendField(new Blockly.FieldNumber(0), "PDireito");
    this.appendDummyInput()
      .appendField("Left Leg")
      .appendField(new Blockly.FieldNumber(0), "PEsquerdo");
    this.setOutput(true, "RoboPose");
    this.setColour(230);
    this.setTooltip("Make the robot position.");
    this.setHelpUrl("");
  },
};

Blockly.Blocks["movimento_sequence"] = {
  init: function () {
    this.appendDummyInput().appendField("Movement");
    this.appendDummyInput()
      .appendField("FPS")
      .appendField(new Blockly.FieldNumber(10, 1), "FPS");
    this.appendDummyInput()
      .appendField("Duration (ms)") // Alterado de "Duração (s)" para "Duração (ms)" para corresponder ao gerador
      .appendField(new Blockly.FieldNumber(1000, 0), "Duracao");
    this.appendValueInput("Inicio")
      .setCheck("RoboPose")
      .appendField("Initial Position");
    this.appendValueInput("Fim")
      .setCheck("RoboPose")
      .appendField("Final Position");
    this.setPreviousStatement(true, null);
    this.setNextStatement(true, null);
    this.setColour(120);
    this.setTooltip("Make a movement sequence.");
    this.setHelpUrl("");
  },
};
