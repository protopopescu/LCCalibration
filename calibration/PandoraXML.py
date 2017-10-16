

from calibration.XmlTools import *
import os
import subprocess
import tempfile

############################################################
############################################################
""" PandoraXML class.
    Wrap a pandora XML settings file with special methods
    to activate/de-activated some features
"""
class PandoraXML(object) :
    def __init__(self, fileName=None):
        self._fileName = fileName
        self._xmlTree = None
        self._energyCorrections = False
        self._runSoftCompTraining = False
        self._softCompTrainingFile = None
        self._softCompTrainingTree = None
        
        if self._fileName:
            self._loadXmlFile()
    
    """ Set whether pandora has to be run with/without energy corrections
    """
    def setRemoveEnergyCorrections(self, remove=True):
        self._energyCorrections = remove

    """ Set the software compensation training settings.
        By settings these attributes, the training algorithm 
        will be appended at end of reconstruction
    """
    def setSoftCompTrainingSettings(self, rootFile=None, treeName=None):
        self._softCompTrainingFile = rootFile
        self._softCompTrainingTree = treeName
        self._runSoftCompTraining = True
        
    """ Set the xml file. The xml file is automatically loaded
    """
    def setXmlFile(self, fileName):
        self._fileName = fileName
        
        if self._fileName:
            self._loadXmlFile()

    """ Generate a new xml file with the current settings
    """
    def generateNewXmlFile(self):
        if not self._xmlTree:
            raise RuntimeError("PandoraXML.generateNewXmlFile: XML file not loaded yet !")
        
        if self._energyCorrections:
            self._removeEnergyCorrections()
        
        if self._runSoftCompTraining:
            self._addSoftCompTrainingAlgorithm()
        
        fhandle, fileName = tempfile.mkstemp(suffix=".xml")

        self._xmlTree.write(fileName, pretty_print=True)
        return fileName

    """ Add software compensation training settings at end of pandora algorithms
    """
    def _addSoftCompTrainingAlgorithm(self):
        # first of all, remove existing training algorithms
        elts = self._xmlTree.xpath("//pandora/algorithm[type='TrainingSoftwareCompensation']")
        
        for elt in elts:
            elt.getparent().remove(elt)
        
        # create, populate algorithm settings
        # and append element at end of reconstruction
        softCompTrainingElt = etree.Element("algorithm", type="TrainingSoftwareCompensation")
        
        if self._softCompTrainingFile:
            softCompTrainingFileElt = etree.Element("MyRootFileName")
            softCompTrainingFileElt.text = str(self._softCompTrainingFile)
            softCompTrainingElt.append(softCompTrainingFileElt)
        
        if self._softCompTrainingTree:
            softCompTrainingTreeElt = etree.Element("SoftCompTrainingTreeName")
            softCompTrainingTreeElt.text = str(self._softCompTrainingTree)
            softCompTrainingElt.append(softCompTrainingTreeElt)

        self._xmlTree.getroot().append(softCompTrainingElt)
    
    """ Load the pandora xml file
    """ 
    def _loadXmlFile(self) :
        xmlParser = createXMLParser()
        self._fileName = self._fileName.strip()
        self._xmlTree = etree.parse(self._fileName, xmlParser)
        
    """ Remove the energy correction settings from the xml tree
    """
    def _removeEnergyCorrections(self):
        if not self._xmlTree:
            raise RuntimeError("PandoraXML.removeEnergyCorrections: XML file not loaded yet !")
        
        elts = self._xmlTree.xpath("//pandora/HadronicEnergyCorrectionPlugins")
        
        for elt in elts:
            elt.getparent().remove(elt)
        
#