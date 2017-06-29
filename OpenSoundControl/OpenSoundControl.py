import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import OSC

#
# OpenSoundControl
#

class OpenSoundControl(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "Open Sound Control"
    self.parent.categories = ["IGT"]
    self.parent.dependencies = []
    self.parent.contributors = ["David Black (Fraunhofer Mevis)", "Julian Hettig (Uni. Magdeburg)", "Andras Lasso (PerkLab)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
This module allows sending messages to Pure Data (https://puredata.info/) through Open Sound Control (OSC) protocol
for generating sound effects.
"""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """
""" # replace with organization, grant and thanks.

#
# OpenSoundControlWidget
#

class OpenSoundControlWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent=None):
    ScriptedLoadableModuleWidget.__init__(self,parent)
    self.logic = OpenSoundControlLogic()

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Connection
    
    connectionCollapsibleButton = ctk.ctkCollapsibleButton()
    connectionCollapsibleButton.text = "Connection"
    self.layout.addWidget(connectionCollapsibleButton)
    connectionFormLayout = qt.QFormLayout(connectionCollapsibleButton)

    self.hostnameLineEdit = qt.QLineEdit()
    self.hostnameLineEdit.setText("127.0.0.1")
    connectionFormLayout.addRow("Host name: ", self.hostnameLineEdit)
    
    self.portLineEdit = qt.QLineEdit()
    self.portLineEdit.setText("5005")
    connectionFormLayout.addRow("Port: ", self.portLineEdit)
    
    self.buttonConnect = qt.QPushButton("Connect") 
    self.buttonConnect.toolTip = "Connect to OSC module" 
    connectionFormLayout.addWidget(self.buttonConnect) 
    self.buttonConnect.connect('clicked(bool)', self.connect)
    
    # Send message

    messageCollapsibleButton = ctk.ctkCollapsibleButton()
    messageCollapsibleButton.text = "Messaging"
    self.layout.addWidget(messageCollapsibleButton)
    messageFormLayout = qt.QFormLayout(messageCollapsibleButton)
    
    self.addressLineEdit = qt.QLineEdit()
    self.addressLineEdit.setText("/BlackLegend/1")
    messageFormLayout.addRow("Address:", self.addressLineEdit)

    self.valueLineEdit = qt.QLineEdit()
    self.valueLineEdit.setText("")
    messageFormLayout.addRow("Value:", self.valueLineEdit)
    
    self.buttonSend = qt.QPushButton("Send")
    self.buttonSend.toolTip = "Send OSC message" 
    messageFormLayout.addWidget(self.buttonSend) 
    self.buttonSend.connect('clicked(bool)', self.sendMessage)

    # Add vertical spacer
    self.layout.addStretch(1)

  def connect(self):
    self.logic.oscConnect(self.hostnameLineEdit.text, int(self.portLineEdit.text))

  def sendMessage(self):
    self.logic.oscSendMessage(self.addressLineEdit.text, self.valueLineEdit.text)

#
# OpenSoundControlLogic
#

class OpenSoundControlLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self):    
    ScriptedLoadableModuleLogic.__init__(self)
    #from OSC import OSCClient
    self.oscClient = OSC.OSCClient()

  def oscConnect(self, hostname, port):
    #from pythonosc import udp_client
    #from OSC import OSCClient, OSCClientError
    logging.info("Connect to OSC server at "+hostname+":"+str(port))
    try:
      #self.oscClient = udp_client.UDPClient(hostname, port)
      self.oscClient.connect((hostname, port))
    except OSC.OSCClientError:
      slicer.util.errorDisplay("Failed to connect to OSC server")

  def oscSendMessage(self, address, content):
    logging.info("Send OSC message to "+address+": "+str(content))
    
    osc_message = OSC.OSCMessage()        
    osc_message.setAddress(address)
    osc_message.append(content)
    self.oscClient.send(osc_message)

    
    # from pythonosc import osc_message_builder
    # from pythonosc import udp_client 
    # builder = osc_message_builder.OscMessageBuilder(address=address)
    # builder.add_arg(str(content),"s")
    # msg = builder.build()
    # self.oscClient.send(msg)

    # self.assertTrue(mock_socket.sendto.called)
    # mock_socket.sendto.assert_called_once_with(msg.dgram, ('::1', 31337)) 
    
    # oscMessage = OSCMessage()        
    # oscMessage.setAddress(address)
    # oscMessage.append(content)
    # self.oscClient.send(oscMessage)

#
# OpenSoundControlTest
#

class OpenSoundControlTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_OpenSoundControl1()

  def test_OpenSoundControl1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")
    #
    # first, get some data
    #
    import urllib
    downloads = (
        ('http://slicer.kitware.com/midas3/download?items=5767', 'FA.nrrd', slicer.util.loadVolume),
        )

    for url,name,loader in downloads:
      filePath = slicer.app.temporaryPath + '/' + name
      if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
        logging.info('Requesting download %s from %s...\n' % (name, url))
        urllib.urlretrieve(url, filePath)
      if loader:
        logging.info('Loading %s...' % (name,))
        loader(filePath)
    self.delayDisplay('Finished with download and loading')

    volumeNode = slicer.util.getNode(pattern="FA")
    logic = OpenSoundControlLogic()
    self.assertIsNotNone( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')
