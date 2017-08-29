#!/usr/bin/python

"""
"""
import os
import sys
from shutil import copyfile
import argparse
from calibration.XmlTools import etree
from calibration.Marlin import *
from calibration.PandoraAnalysis import PandoraAnalysisBinary
import glob

# try to get from env vars
pathToPandoraAnalysis = os.environ["PANDORA_ANALYSIS_DIR"]

def writeNewPandoraSettings(pandoraSettingsFile, rootFile):
    xmlParser = etree.XMLParser(remove_blank_text=True)
    pandoraXmlTree = etree.parse(pandoraSettingsFile, xmlParser)
    elementList = pandoraXmlTree.xpath("//pandora/algorithm[@type='TrainingSoftwareCompensation']")

    if len(elementList) == 0:
        raise RuntimeError("Pandora steering file '{0}' doesn't seem to contain any TrainingSoftwareCompensation algorithm !".format(pandoraSettingsFile))
    
    softCompAlgorithm = elementList[0]
    
    rootOutputElement = softCompAlgorithm.find("MyRootFileName")
    if rootOutputElement is None:
        rootOutputElement = etree.Element("MyRootFileName")
        softCompAlgorithm.append(rootOutputElement)
    rootOutputElement.text = str(rootFile)
    
    treeNameElement = softCompAlgorithm.find("SoftCompTrainingTreeName")
    if treeNameElement is None:
        treeNameElement = etree.Element("SoftCompTrainingTreeName")
        softCompAlgorithm.append(treeNameElement)
    treeNameElement.text = "SoftwareCompensationTrainingTree"
    
    fhandle, tmpPandoraXmlFileName = tempfile.mkstemp(suffix=".xml")
    pandoraXmlTree.write(tmpPandoraXmlFileName)
    
    return tmpPandoraXmlFileName
        
        
        

parser = argparse.ArgumentParser("Run (optionally) the reconstruction chain on single kaon0L particles and calibrate PandoraPFA software compensation weights:",
                                     formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument("--compactFile", action="store",
                        help="The compact XML file", required = True)
                        
parser.add_argument("--steeringFile", action="store",
                        help="The Marlin steering file", required = True)
                        
parser.add_argument("--maxRecordNumber", action="store", default=0,
                        help="The maximum number of events to process", required = False)

parser.add_argument("--pandoraSettingsFile", action="store",
                        help="The PandoraPFA xml settings file for software compensation", required = True)

parser.add_argument("--calibrationOutputPath", action="store", default="./SoftComp_",
                        help="The output path for the software compensation calibration file", required = False)
                        
parser.add_argument("--energies", action="store",
                        help="The input mc energies for software compensation calibration", required = True)

parser.add_argument("--lcioFilePattern", action="store",
                        help="The LCIO input file pattern. Must contains '%%{energy}' string to match energy to file. Example : 'File_%%{energy}GeV*.slcio'", required = True)
# 
parser.add_argument("--rootFilePattern", action="store",
                        help="The root input/output file pattern. Must contains '%%{energy}' string to match energy to file. Example : 'SoftComp_%%{energy}GeV*.root'", required = True)

parser.add_argument("--runMarlin", action="store_true",
                        help="Whether to run marlin reconstruction before calibration of software compensation weights")
                        
parser.add_argument("--maxParallel", action="store", default=1,
                        help="The maximum number of marlin instance to run in parallel (process)")

parser.add_argument("--minimizeTrueEnergy", action="store_true",
                        help="Whether to use to mc energy in the software compensation minimizer program (or reconstructed energy)")

parsed = parser.parse_args()

rootFilePattern = parsed.rootFilePattern
if rootFilePattern.find("%{energy}") == -1 :
    raise RuntimeError("File pattern '{0}' : couldn't find '%{energy}' tag !".format(rootFilePattern))

if parsed.runMarlin :
    marlinMaster = ParallelMarlin()
    marlinMaster.setMaxNParallelInstances(int(parsed.maxParallel))

    energyList = parsed.energies.split()

    lcioFilePattern = parsed.lcioFilePattern
    if lcioFilePattern.find("%{energy}") == -1 :
        raise RuntimeError("File pattern '{0}' : couldn't find '%{energy}' tag !".format(lcioFilePattern))

    steeringFile = parsed.steeringFile
    pandoraSettingsFile = parsed.pandoraSettingsFile
        
    # loop over energies and create marlin instance to run in parallel
    for energy in energyList:
        lcioFilePattern = parsed.lcioFilePattern
        lcioFilesPattern = lcioFilePattern.replace("%{energy}", str(energy))
        lcioFiles = glob.glob(lcioFilesPattern)
        
        if len(lcioFiles) == 0:
            raise RuntimeError("File pattern '{0}' for energy {1}: no file found !".format(lcioFilesPattern, energy))
        
        rootFilePattern = parsed.rootFilePattern
        rootFile = rootFilePattern.replace("%{energy}", str(energy))
        newPandoraXmlFileName = writeNewPandoraSettings(pandoraSettingsFile, rootFile)
        
        marlin = Marlin(steeringFile)
        marlin.setCompactFile(parsed.compactFile)
        gearFile = marlin.convertToGear(parsed.compactFile)
        marlin.setGearFile(gearFile)
        marlin.setInputFiles(lcioFiles)
        marlin.setMaxRecordNumber(parsed.maxRecordNumber)
        marlin.setProcessorParameter("MyDDMarlinPandora", "PandoraSettingsXmlFile", str(newPandoraXmlFileName))
        
        marlinMaster.addMarlinInstance(marlin)

    marlinMaster.run()


softCompEnergies = ":".join(parsed.energies.split())
    
softwareCompensationCalibrator = PandoraAnalysisBinary(os.path.join(pathToPandoraAnalysis, "bin/PandoraPFACalibrate_SoftwareCompensation"))
softwareCompensationCalibrator.addArgument("-d", parsed.calibrationOutputPath)
softwareCompensationCalibrator.addArgument("-e", softCompEnergies)
softwareCompensationCalibrator.addArgument("-f", parsed.rootFilePattern)
softwareCompensationCalibrator.addArgument("-t", "SoftwareCompensationTrainingTree")

if bool(parsed.minimizeTrueEnergy):
    softwareCompensationCalibrator.addArgument("-g", "")
    
softwareCompensationCalibrator.run()


#
