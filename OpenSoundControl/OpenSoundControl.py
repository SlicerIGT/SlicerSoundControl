import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging

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
    self.parent.contributors = ["David Black (Fraunhofer Mevis)", "Julian Hettig (Uni. Magdeburg)", "Andras Lasso (PerkLab)"]
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

    # Launch PureData

    pureDataCollapsibleButton = ctk.ctkCollapsibleButton()
    pureDataCollapsibleButton.text = "PureData server"
    self.layout.addWidget(pureDataCollapsibleButton)
    pureDataFormLayout = qt.QFormLayout(pureDataCollapsibleButton)

    self.pureDataConfigFilePathSelector = ctk.ctkPathLineEdit()
    self.pureDataConfigFilePathSelector.settingKey = "OpenSoundControl/PureDataConfigurationFilePath"
    self.pureDataConfigFilePathSelector.setSizePolicy(qt.QSizePolicy.MinimumExpanding, qt.QSizePolicy.Preferred)
    self.pureDataConfigFilePathSelector.setToolTip("Set PureData configuration file that will be loaded when the server is launched.")
    pureDataFormLayout.addRow("PureData configuration:", self.pureDataConfigFilePathSelector)

    self.buttonStartServer = qt.QPushButton("Start server")
    self.buttonStartServer.toolTip = "Start PureData server that will receive OSC messages"
    self.buttonStartServer.connect('clicked()', self.startServer)

    self.buttonStopServer = qt.QPushButton("Stop server")
    self.buttonStopServer.toolTip = "Stop PureData server"
    self.buttonStopServer.connect('clicked()', self.stopServer)

    hbox = qt.QHBoxLayout()
    hbox.addWidget(self.buttonStartServer)
    hbox.addWidget(self.buttonStopServer)
    pureDataFormLayout.addRow(hbox)


    # Connection

    connectionCollapsibleButton = ctk.ctkCollapsibleButton()
    connectionCollapsibleButton.text = "Connection"
    self.layout.addWidget(connectionCollapsibleButton)
    connectionFormLayout = qt.QFormLayout(connectionCollapsibleButton)

    self.hostnameLineEdit = qt.QLineEdit("localhost")
    connectionFormLayout.addRow("Host name: ", self.hostnameLineEdit)

    self.portLineEdit = qt.QLineEdit("7400")
    self.portLineEdit.setValidator(qt.QIntValidator(0, 65535, self.portLineEdit))
    connectionFormLayout.addRow("Port: ", self.portLineEdit)

    self.buttonConnect = qt.QPushButton("Connect")
    self.buttonConnect.toolTip = "Connect to OSC module"
    connectionFormLayout.addWidget(self.buttonConnect)
    self.buttonConnect.connect('clicked()', self.connect)

    # Send message

    messageCollapsibleButton = ctk.ctkCollapsibleButton()
    messageCollapsibleButton.text = "Messaging"
    self.layout.addWidget(messageCollapsibleButton)
    messageFormLayout = qt.QFormLayout(messageCollapsibleButton)

    self.addressLineEdit = qt.QLineEdit()
    self.addressLineEdit.setText("/SoundNav/1")
    messageFormLayout.addRow("Address:", self.addressLineEdit)

    self.valueLineEdit = qt.QLineEdit()
    self.valueLineEdit.setText("")
    messageFormLayout.addRow("Value:", self.valueLineEdit)

    self.buttonSend = qt.QPushButton("Send")
    self.buttonSend.toolTip = "Send OSC message"
    messageFormLayout.addWidget(self.buttonSend)
    self.buttonSend.connect('clicked(bool)', self.sendMessage)

    #
    # Advanced area
    #
    self.advancedCollapsibleButton = ctk.ctkCollapsibleButton()
    self.advancedCollapsibleButton.text = "Advanced"
    self.advancedCollapsibleButton.collapsed = True
    self.layout.addWidget(self.advancedCollapsibleButton)
    advancedFormLayout = qt.QFormLayout(self.advancedCollapsibleButton)

    self.logDetailsCheckBox = qt.QCheckBox(" ")
    self.logDetailsCheckBox.checked = False
    self.logDetailsCheckBox.setToolTip("Add details about all sent messages to the application log. It may slow down the execution.")
    advancedFormLayout.addRow("Log messages:", self.logDetailsCheckBox)
    self.logDetailsCheckBox.connect("toggled(bool)", self.logic.setLoggingEnabled)

    self.pureDataExecutablePathSelector = ctk.ctkPathLineEdit()
    self.pureDataExecutablePathSelector.filters = ctk.ctkPathLineEdit.Executable + ctk.ctkPathLineEdit.Files
    from sys import platform
    self.pureDataExecutablePathSelector.nameFilters = ["PureData (pd.exe)" if platform == "win32" else "PureData (pd*)"]

    try:
      pureDataExecutablePath = self.logic.getPureDataExecutablePath()
      self.pureDataExecutablePathSelector.setCurrentPath(pureDataExecutablePath)
    except:
      self.advancedCollapsibleButton.collapsed = False

    self.pureDataExecutablePathSelector.setSizePolicy(qt.QSizePolicy.MinimumExpanding, qt.QSizePolicy.Preferred)
    self.pureDataExecutablePathSelector.setToolTip("Set PureData executable (pd) path.")
    advancedFormLayout.addRow("PureData executable:", self.pureDataExecutablePathSelector)
    self.pureDataExecutablePathSelector.connect('currentPathChanged(QString)', self.logic.setPureDataExecutablePath)

    self.showPureDataGUI = qt.QCheckBox(" ")
    self.showPureDataGUI.checked = False
    self.showPureDataGUI.setToolTip("Start PureData server with graphical user interface visible. Useful for development and troubleshooting.")
    advancedFormLayout.addRow("Start PureData with GUI:", self.showPureDataGUI)

    # Add vertical spacer
    self.layout.addStretch(1)

  def connect(self):
    with slicer.util.tryWithErrorDisplay("Connect to OSC server"):
      hostname = self.hostnameLineEdit.text.strip()
      port = int(self.portLineEdit.text.strip())
      with slicer.util.tryWithErrorDisplay(f"Connect to OSC server at {hostname}:{port}"):
        self.logic.oscConnect(hostname, port)

  def sendMessage(self):
    with slicer.util.tryWithErrorDisplay("Send OSC message"):
      self.logic.oscSendMessage(self.addressLineEdit.text, self.valueLineEdit.text)

  def startServer(self):
    with slicer.util.tryWithErrorDisplay("Start PureData server"):
      self.pureDataConfigFilePathSelector.addCurrentPathToHistory()
      self.logic.startPureData(self.pureDataConfigFilePathSelector.currentPath, self.showPureDataGUI.checked)

  def stopServer(self):
    with slicer.util.tryWithErrorDisplay("Stop PureData server"):
      self.logic.stopPureData()

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

    # Install python-osc if not installed already
    try:
      from pythonosc.udp_client import SimpleUDPClient
      print('python-osc is installed')
    except ModuleNotFoundError as e:
      slicer.util.pip_install('python-osc')

    self.pureDataExecutablePath = None
    self.pureDataExecutablePathSettingsKey = 'OpenSoundControl/PureDataExecutablePath'
    self.oscClient = None
    self.loggingEnabled = False
    self.pureDataProcess = None

  def setLoggingEnabled(self, enable):
    self.loggingEnabled = enable

  def oscConnect(self, hostname="localhost", port=7400):
    logging.info("Connect to OSC server at "+hostname+":"+str(port))
    from pythonosc.udp_client import SimpleUDPClient

    # Disconnect previous client
    if self.oscClient:
      self.oscClient = None

    self.oscClient = SimpleUDPClient(hostname, port)

  def oscSendMessage(self, address, content):
    if self.loggingEnabled:
      logging.info("Send OSC message to "+address+": "+str(content))
    if not self.oscClient:
      raise RuntimeError("OSC client is not connected.")
    self.oscClient.send_message(address, content)

  def getPureDataExecutablePath(self):
    if self.pureDataExecutablePath:
      return self.pureDataExecutablePath

    self.pureDataExecutablePath = self.getPureDataExecutablePathFromSettings()
    if self.pureDataExecutablePath and os.path.isfile(self.pureDataExecutablePath):
      return self.pureDataExecutablePath

    pureDataExecutablePathCandidates = [
      "c:/Program Files/Purr Data/bin/pd.exe",
      "c:/Program Files (x86)/pd/bin/pd.exe"
      ]

    for pureDataExecutablePathCandidate in pureDataExecutablePathCandidates:
      if os.path.isfile(pureDataExecutablePathCandidate):
        # executable
        self.pureDataExecutablePath = os.path.abspath(pureDataExecutablePathCandidate)
        return self.pureDataExecutablePath

    raise ValueError('PureData executable (pd) not found. Install Purr Data (https://github.com/agraef/purr-data/releases) and if not found automatically then set the path in Advanced section.')

  def getPureDataExecutablePathFromSettings(self):
    settings = qt.QSettings()
    if settings.contains(self.pureDataExecutablePathSettingsKey):
      return settings.value(self.pureDataExecutablePathSettingsKey)
    return ''

  def setPureDataExecutablePath(self, customPath):
    # don't save it if already saved
    settings = qt.QSettings()
    if settings.contains(self.pureDataExecutablePathSettingsKey):
      if customPath == settings.value(self.pureDataExecutablePathSettingsKey):
        return
    settings.setValue(self.pureDataExecutablePathSettingsKey, customPath)
    # Update PureData executable path
    self.pureDataExecutablePath = None
    self.getPureDataExecutablePath()

  def startPureData(self, configFilePath="", showGUI = True):
    import subprocess

    # Stop previously started instance
    self.stopPureData()

    # Start server
    logging.info("Start PureData server: "+self.getPureDataExecutablePath()+" with config file: "+configFilePath)
    args = []
    args.append(self.getPureDataExecutablePath())
    if not showGUI:
      logging.info("Hide PureData server GUI")
      args.append("-nogui")
    if configFilePath:
      args.append("-open")
      args.append(configFilePath)
    self.pureDataProcess = subprocess.Popen(args)

  def stopPureData(self):
    import subprocess

    if not self.pureDataProcess:
      return

    logging.info("Stopping PureData server")
    subprocess.Popen.terminate(self.pureDataProcess)
    self.pureDataProcess = None

  def hasImageData(self,volumeNode):
    """This is an example logic method that
    returns true if the passed in volume
    node has valid image data
    """
    if not volumeNode:
      logging.debug('hasImageData failed: no volume node')
      return False
    if volumeNode.GetImageData() is None:
      logging.debug('hasImageData failed: no image data in volume node')
      return False
    return True
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
