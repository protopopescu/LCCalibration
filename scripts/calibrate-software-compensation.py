#!/usr/bin/python

""" Run the Marlin reconstruction for kaon0L needed for calibrating the software compensation (SC) weights.
    Run the SC weights minimizer on root file output from the PandoraPFA SC training algorithm.
    @author Remi Ete, DESY
"""
import os
import sys
from shutil import copyfile
import argparse
from calibration.XmlTools import etree
from calibration.Marlin import *
from calibration.PandoraXML import *
from calibration.PandoraAnalysis import PandoraSoftCompCalibrator
import glob
        

parser = argparse.ArgumentParser("Run the reconstruction chain on single kaon0L particles and calibrate PandoraPFA software compensation weights:",
                                     formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument("--compactFile", action="store",
                        help="The compact XML file", required = True)
                        
parser.add_argument("--steeringFile", action="store",
                        help="The Marlin steering file", required = True)
                        
parser.add_argument("--maxRecordNumber", action="store", default=0,
                        help="The maximum number of events to process", required = False)

parser.add_argument("--pandoraSettingsFile", action="store",
                        help="The PandoraPFA xml settings file for software compensation", required = True)
                        
parser.add_argument("--energies", action="store", nargs='+',
                        help="The input mc energies for software compensation calibration", required = True)

parser.add_argument("--lcioFilePattern", action="store",
                        help="The LCIO input file pattern. Must contains '%%{energy}' string to match energy to file. Example : 'File_%%{energy}GeV*.slcio'", required = True)
# 
parser.add_argument("--rootFilePattern", action="store",
                        help="The root input/output file pattern. Must contains '%%{energy}' string to match energy to file. Example : 'SoftComp_%%{energy}GeV*.root'", required = True)

parser.add_argument("--runMarlin", action="store_true",
                        help="Whether to run marlin reconstruction before calibration of software compensation weights")

parser.add_argument("--noMinimizer", action="store_true",
                        help="Whether to run software compensation weights minimization")
                        
parser.add_argument("--maxParallel", action="store", default=1,
                        help="The maximum number of marlin instance to run in parallel (process)")

parser.add_argument("--minimizeClusterEnergy", action="store_true",
                        help="Whether to use to cluster energy in the software compensation minimizer program (default: mc energy)")

parsed = parser.parse_args()

if not parsed.runMarlin and parsed.noMinimizer:
    parser.print_help()
    parser.exit(status=1, message="Incoherent options: 'runMarlin' not set and 'noMinimizer' set. Nothing to run !\n")

rootFilePattern = parsed.rootFilePattern
if rootFilePattern.find("%{energy}") == -1 :
    raise RuntimeError("File pattern '{0}' : couldn't find '%{energy}' tag !".format(rootFilePattern))

energyList = parsed.energies
    
if parsed.runMarlin :
    marlinMaster = ParallelMarlin()
    marlinMaster.setMaxNParallelInstances(int(parsed.maxParallel))

    lcioFilePattern = parsed.lcioFilePattern
    if lcioFilePattern.find("%{energy}") == -1 :
        raise RuntimeError("File pattern '{0}' : couldn't find '%{energy}' tag !".format(lcioFilePattern))

    steeringFile = parsed.steeringFile
    pandora = PandoraSettings(parsed.pandoraSettingsFile)
    pandora.setRemoveEnergyCorrections(True)
        
    # loop over energies and create marlin instance to run in parallel
    for energy in energyList:
        lcioFilePattern = parsed.lcioFilePattern
        lcioFilesPattern = lcioFilePattern.replace("%{energy}", str(energy))
        lcioFiles = glob.glob(lcioFilesPattern)
        
        if len(lcioFiles) == 0:
            raise RuntimeError("File pattern '{0}' for energy {1}: no file found !".format(lcioFilesPattern, energy))
        
        rootFilePattern = parsed.rootFilePattern
        rootFile = rootFilePattern.replace("%{energy}", str(energy))
        
        pandora.setSoftCompTrainingSettings(rootFile, "SoftwareCompensationTrainingTree")
        newPandoraXmlFileName = pandora.generateNewXmlFile()
        
        index = rootFile.rfind(".root")
        pfoAnalysisFile = rootFile[:index] + "_PfoAnalysis.root"
        
        marlin = Marlin(steeringFile)
        marlin.setCompactFile(parsed.compactFile)
        gearFile = marlin.convertToGear(parsed.compactFile)
        marlin.setGearFile(gearFile)
        marlin.setInputFiles(lcioFiles)
        marlin.setMaxRecordNumber(parsed.maxRecordNumber)
        marlin.setProcessorParameter("MyDDMarlinPandora", "PandoraSettingsXmlFile", str(newPandoraXmlFileName))
        try:
            marlin.setProcessorParameter("MyPfoAnalysis", "RootFile", str(pfoAnalysisFile))
        except:
            pass
        
        marlinMaster.addMarlinInstance(marlin)

    marlinMaster.run()


if not parsed.noMinimizer :
    softwareCompensationCalibrator = PandoraSoftCompCalibrator()
    softwareCompensationCalibrator.setEnergies(parsed.energies)
    softwareCompensationCalibrator.setDeleteOutputFile(False)
    softwareCompensationCalibrator.setRootFilePattern(parsed.rootFilePattern)
    softwareCompensationCalibrator.setRootTreeName("SoftwareCompensationTrainingTree")
    softwareCompensationCalibrator.setRunWithClusterEnergy(parsed.minimizeClusterEnergy)
    softwareCompensationCalibrator.run()

#
