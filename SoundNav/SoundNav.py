import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import math
import numpy as np

#
# SoundNav
#

class SoundNav(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "Sound Navigation" # TODO make this more human readable by adding spaces
    self.parent.categories = ["IGT"]
    self.parent.dependencies = ["OpenSoundControl"]
    self.parent.contributors = ["David Black (Fraunhofer Mevis)", "Julian Hettig (Uni. Magdeburg)", "Andras Lasso (PerkLab)"]
    self.parent.helpText = """
Send sound control messages with parameters depending on values in transforms.
"""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """
""" # replace with organization, grant and thanks.

#
# SoundNavWidget
#

class SoundNavWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent=None):
    ScriptedLoadableModuleWidget.__init__(self,parent)
    self.logic = SoundNavLogic()
    self.instrumentWidgets = []

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Connection

    connectionCollapsibleButton = ctk.ctkCollapsibleButton()
    connectionCollapsibleButton.text = "OSC server connection"
    self.layout.addWidget(connectionCollapsibleButton)
    connectionFormLayout = qt.QFormLayout(connectionCollapsibleButton)

    self.hostnameLineEdit = qt.QLineEdit("localhost")
    connectionFormLayout.addRow("Host name: ", self.hostnameLineEdit)

    self.portLineEdit = qt.QLineEdit("7400")
    self.portLineEdit.setValidator(qt.QIntValidator(0, 65535, self.portLineEdit))
    connectionFormLayout.addRow("Port: ", self.portLineEdit)

    self.addressRootLineEdit = qt.QLineEdit("SoundNav")
    self.addressRootLineEdit.setToolTip("OSC address root. Complete address: /<address root>/<instrument name>/<parameter name>.")
    connectionFormLayout.addRow("Address root: ", self.addressRootLineEdit)

    self.enableConnectionCheckBox = qt.QCheckBox()
    self.enableConnectionCheckBox.checked = False
    self.enableConnectionCheckBox.setToolTip("If checked, then transform changes will be immediately sent to specified OSC server.")
    connectionFormLayout.addRow("Transmission active: ", self.enableConnectionCheckBox)
    self.enableConnectionCheckBox.connect('stateChanged(int)', self.setTransmissionActive)

    # Parameters Area
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    parameterNode = self.logic.getParameterNode()

    maxNumberOfInstruments = int(parameterNode.GetParameter("MaxNumberOfInstruments"))
    for instrumentIndex in range(maxNumberOfInstruments):

      instrumentGroupBox = ctk.ctkCollapsibleGroupBox()
      instrumentGroupBox.title = "Instrument "+str(instrumentIndex+1)
      parametersFormLayout.addWidget(instrumentGroupBox)
      instrumentLayout = qt.QFormLayout(instrumentGroupBox)

      nameLineEdit = qt.QLineEdit()
      instrumentLayout.addRow("Instrument name: ", nameLineEdit)
      nameLineEdit.connect('editingFinished()', self.updateMRMLFromGUI)

      instrumentSourceSelector = slicer.qMRMLNodeComboBox()

      instrumentNodeTypes = ["vtkMRMLLinearTransformNode"]
      if hasattr(slicer.modules, 'breachwarning'):
        instrumentNodeTypes.append("vtkMRMLBreachWarningNode")
      instrumentSourceSelector.nodeTypes = instrumentNodeTypes
      instrumentSourceSelector.addEnabled = True
      instrumentSourceSelector.removeEnabled = True
      instrumentSourceSelector.noneEnabled = True
      instrumentSourceSelector.renameEnabled = True
      instrumentSourceSelector.setMRMLScene(slicer.mrmlScene)
      instrumentSourceSelector.setToolTip("Defines position and orientation of the instrument (transform or breach warning node)")
      instrumentLayout.addRow("Instrument node: ", instrumentSourceSelector)
      instrumentSourceSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateMRMLFromGUI)

      instrumentReferenceSelector = slicer.qMRMLNodeComboBox()
      instrumentReferenceSelector.nodeTypes = ["vtkMRMLLinearTransformNode"]
      instrumentReferenceSelector.addEnabled = True
      instrumentReferenceSelector.removeEnabled = True
      instrumentReferenceSelector.noneEnabled = True
      instrumentReferenceSelector.renameEnabled = True
      instrumentReferenceSelector.setMRMLScene(slicer.mrmlScene)
      instrumentReferenceSelector.setToolTip("Position and orientation is defined relative to this transform")
      instrumentLayout.addRow("Reference transform: ", instrumentReferenceSelector)
      instrumentReferenceSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateMRMLFromGUI)

      widgets = {}
      widgets['instrumentGroupBox'] = instrumentGroupBox
      widgets['nameLineEdit'] = nameLineEdit
      widgets['instrumentSourceSelector'] = instrumentSourceSelector
      widgets['instrumentReferenceSelector'] = instrumentReferenceSelector

      self.instrumentWidgets.append(widgets)

    self.updateGUIFromMRML()

    self.hostnameLineEdit.connect('editingFinished()', self.updateMRMLFromGUI)
    self.portLineEdit.connect('editingFinished()', self.updateMRMLFromGUI)
    self.addressRootLineEdit.connect('editingFinished()', self.updateMRMLFromGUI)

    for instrumentIndex in range(len(self.instrumentWidgets)):
      widgets = self.instrumentWidgets[instrumentIndex]
      # Collapse unused instrument groupboxes
      widgets['instrumentGroupBox'].collapsed = not widgets['nameLineEdit'].text
      # Observe widget changes to update MRML node immediately (this way always up-to-date values will be saved in the scene)
      widgets['nameLineEdit'].connect('editingFinished()', self.updateMRMLFromGUI)
      widgets['instrumentSourceSelector'].connect("currentNodeChanged(vtkMRMLNode*)", self.updateMRMLFromGUI)
      widgets['instrumentReferenceSelector'].connect("currentNodeChanged(vtkMRMLNode*)", self.updateMRMLFromGUI)

    self.parameterNodeObserverTag = parameterNode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.updateGUIFromMRML)

    # Add vertical spacer
    self.layout.addStretch(1)

  def __del__(self):
    super(SoundNavWidget,self).__del__()
    parameterNode.RemoveObserver(self.parameterNodeObserverTag)

  def updateGUIFromMRML(self, unused1=None, unused2=None):
    parameterNode = self.logic.getParameterNode()
    connectionActive = slicer.util.toBool(parameterNode.GetParameter("ConnectionActive"))

    wasBlocked = self.hostnameLineEdit.blockSignals(True)
    self.hostnameLineEdit.setText(parameterNode.GetParameter("ConnectionHostName"))
    self.hostnameLineEdit.blockSignals(wasBlocked)
    self.hostnameLineEdit.setEnabled(not connectionActive)

    wasBlocked = self.portLineEdit.blockSignals(True)
    self.portLineEdit.setText(parameterNode.GetParameter("ConnectionPort"))
    self.portLineEdit.blockSignals(wasBlocked)
    self.portLineEdit.setEnabled(not connectionActive)

    wasBlocked = self.addressRootLineEdit.blockSignals(True)
    self.addressRootLineEdit.setText(parameterNode.GetParameter("AddressRoot"))
    self.addressRootLineEdit.blockSignals(wasBlocked)
    self.addressRootLineEdit.setEnabled(not connectionActive)

    for instrumentIndex in range(len(self.instrumentWidgets)):
      widgets = self.instrumentWidgets[instrumentIndex]

      wasBlocked = widgets['nameLineEdit'].blockSignals(True)
      widgets['nameLineEdit'].setText(parameterNode.GetParameter("InstrumentName"+str(instrumentIndex)))
      widgets['nameLineEdit'].blockSignals(wasBlocked)

      wasBlocked = widgets['instrumentSourceSelector'].blockSignals(True)
      widgets['instrumentSourceSelector'].setCurrentNode(parameterNode.GetNodeReference("InstrumentSource"+str(instrumentIndex)))
      widgets['instrumentSourceSelector'].blockSignals(wasBlocked)

      wasBlocked = widgets['instrumentReferenceSelector'].blockSignals(True)
      widgets['instrumentReferenceSelector'].setCurrentNode(parameterNode.GetNodeReference("InstrumentReference"+str(instrumentIndex)))
      instrumentSourceNode = widgets['instrumentSourceSelector'].currentNode()
      widgets['instrumentReferenceSelector'].setEnabled(instrumentSourceNode and instrumentSourceNode.IsA("vtkMRMLTransformNode"))
      widgets['instrumentReferenceSelector'].blockSignals(wasBlocked)

      widgets['instrumentGroupBox'].setEnabled(not connectionActive)

    self.enableConnectionCheckBox.checked = connectionActive

  def updateMRMLFromGUI(self):
    parameterNode = self.logic.getParameterNode()

    parameterNode.SetParameter("ConnectionHostName", self.hostnameLineEdit.text)
    parameterNode.SetParameter("ConnectionPort", self.portLineEdit.text)
    parameterNode.SetParameter("AddressRoot", self.addressRootLineEdit.text)

    for instrumentIndex in range(len(self.instrumentWidgets)):
      widgets = self.instrumentWidgets[instrumentIndex]
      parameterNode.SetParameter("InstrumentName"+str(instrumentIndex), widgets['nameLineEdit'].text)
      parameterNode.SetNodeReferenceID("InstrumentSource"+str(instrumentIndex), widgets['instrumentSourceSelector'].currentNodeID)
      parameterNode.SetNodeReferenceID("InstrumentReference"+str(instrumentIndex), widgets['instrumentReferenceSelector'].currentNodeID)

    parameterNode.SetParameter("ConnectionActive", "true" if self.enableConnectionCheckBox.checked else "false")

  def setTransmissionActive(self, state):
    parameterNode = self.logic.getParameterNode()
    parameterNode.SetParameter("ConnectionActive", "true" if state else "false")
    if state:
      self.logic.startTransmission()
    else:
      self.logic.stopTransmission()

#
# SoundNavLogic
#

class SoundNavLogic(ScriptedLoadableModuleLogic):
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

    self.instrumentNodeObserverTags = []
    self.instrumentOscAddress = []

    import OpenSoundControl
    self.oscLogic = OpenSoundControl.OpenSoundControlLogic()

    # Logging can be enabled for debugging
    #self.oscLogic.loggingEnabled = True

  def __del__(self):
    ScriptedLoadableModuleLogic.__del__(self)
    self.removeAllInstrumentNodeObservers()

  def addInstrumentNodeObservers(self):
    parameterNode = self.getParameterNode()
    # Address consists of several components, construct them here so that we don't need to regenerate on each update
    self.instrumentOscAddress = []
    addressRoot = parameterNode.GetParameter("AddressRoot")
    # Make sure the address root starts with /
    if not addressRoot or addressRoot[0] != "/":
      addressRoot = "/" + addressRoot
    # Make sure the address root ends with /
    if addressRoot[-1:] != "/":
      addressRoot += "/"

    for instrumentIndex in range(int(parameterNode.GetParameter("MaxNumberOfInstruments"))):
      instrumentName = parameterNode.GetParameter("InstrumentName"+str(instrumentIndex))
      self.instrumentOscAddress.append(addressRoot+instrumentName+"/")
      if not instrumentName:
        continue
      instrumentNode = parameterNode.GetNodeReference("InstrumentSource"+str(instrumentIndex))
      if not instrumentName:
        continue
      if instrumentNode.IsA("vtkMRMLTransformNode"):
        self.instrumentNodeObserverTags.append(
          [instrumentNode, instrumentNode.AddObserver(slicer.vtkMRMLTransformableNode.TransformModifiedEvent,
          lambda unused1, unused2, instrumentIndex = instrumentIndex: self.instrumentNodeUpdated(instrumentIndex))])
      elif instrumentNode.IsA("vtkMRMLBreachWarningNode"):
        self.instrumentNodeObserverTags.append(
          [instrumentNode, instrumentNode.AddObserver(vtk.vtkCommand.ModifiedEvent,
          lambda unused1, unused2, instrumentIndex = instrumentIndex: self.instrumentNodeUpdated(instrumentIndex))])
      referenceNode = parameterNode.GetNodeReference("InstrumentReference"+str(instrumentIndex))
      if referenceNode:
        self.instrumentNodeObserverTags.append(
          [referenceNode, referenceNode.AddObserver(slicer.vtkMRMLTransformableNode.TransformModifiedEvent,
          lambda unused1, unused2, instrumentIndex = instrumentIndex: self.instrumentNodeUpdated(instrumentIndex))])

  def removeAllInstrumentNodeObservers(self):
    for nodeTagPair in self.instrumentNodeObserverTags:
      nodeTagPair[0].RemoveObserver(nodeTagPair[1])

  def createParameterNode(self):
    parameterNode = ScriptedLoadableModuleLogic.createParameterNode(self)
    parameterNode.SetParameter("MaxNumberOfInstruments", "3")
    parameterNode.SetParameter("ConnectionHostName", "localhost")
    parameterNode.SetParameter("ConnectionPort", "7400")
    parameterNode.SetParameter("AddressRoot", "SoundNav")
    parameterNode.SetParameter("InstrumentName0", "Instrument")
    return parameterNode

  def startTransmission(self):
    self.removeAllInstrumentNodeObservers()
    parameterNode = self.getParameterNode()
    self.oscLogic.oscConnect(parameterNode.GetParameter("ConnectionHostName"), int(parameterNode.GetParameter("ConnectionPort")))
    self.addInstrumentNodeObservers()

  def stopTransmission(self):
    self.removeAllInstrumentNodeObservers()

  def instrumentNodeUpdated(self, instrumentIndex):
    parameterNode = self.getParameterNode()
    instrumentNode = parameterNode.GetNodeReference("InstrumentSource"+str(instrumentIndex))
    address = self.instrumentOscAddress[instrumentIndex]

    if instrumentNode.IsA("vtkMRMLTransformNode"):

      instrumentToReferenceMatrix = vtk.vtkMatrix4x4()
      slicer.vtkMRMLTransformNode.GetMatrixTransformBetweenNodes(
        instrumentNode,
        parameterNode.GetNodeReference("InstrumentReference"+str(instrumentIndex)),
        instrumentToReferenceMatrix)

      instrumentToReference = vtk.vtkTransform()
      instrumentToReference.SetMatrix(instrumentToReferenceMatrix)

      translation = instrumentToReference.GetPosition()
      orientation = instrumentToReference.GetOrientation()
      orientationWXYZ = instrumentToReference.GetOrientationWXYZ()
      self.oscLogic.oscSendMessage(address+"TranslationX", translation[0])
      self.oscLogic.oscSendMessage(address+"TranslationY", translation[1])
      self.oscLogic.oscSendMessage(address+"TranslationZ", translation[2])
      self.oscLogic.oscSendMessage(address+"Distance", vtk.vtkMath.Norm(translation))
      self.oscLogic.oscSendMessage(address+"OrientationX", orientation[0])
      self.oscLogic.oscSendMessage(address+"OrientationY", orientation[1])
      self.oscLogic.oscSendMessage(address+"OrientationZ", orientation[2])
      self.oscLogic.oscSendMessage(address+"Orientation", orientationWXYZ[0])

    elif instrumentNode.IsA("vtkMRMLBreachWarningNode"):

      signedDistance = instrumentNode.GetClosestDistanceToModelFromToolTip()
      self.oscLogic.oscSendMessage(address+"Distance", signedDistance)

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


class SoundNavTest(ScriptedLoadableModuleTest):
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
    self.test_SoundNav1()

  def test_SoundNav1(self):
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
    logic = SoundNavLogic()
    self.assertIsNotNone( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')
