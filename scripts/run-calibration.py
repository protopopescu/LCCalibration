#!/usr/bin/python

"""
"""

from calibration.CalibrationManager import CalibrationManager
from calibration.MipScaleStep import *
from calibration.EcalEnergyStep import *
from calibration.HcalEnergyStep import *
from calibration.PandoraMipScaleStep import *
from calibration.PandoraEMScaleStep import *

import os
import sys
from shutil import copyfile
import argparse
import logging

compactFile = ""
maxNIterations = 5
startStep = 0
endStep = sys.maxint
lcioPhotonFile = "ddsim-photon-calibration.slcio"
lcioKaon0LFile = "ddsim-kaon0L-calibration.slcio"
lcioMuonFile = "ddsim-muon-calibration.slcio"

ecalCalibrationAccuracy = 0.01
hcalCalibrationAccuracy = 0.01

inputCalibrationFile = ""
outputCalibrationFile = None

marlinSteeringFile = ""
pathToPandoraAnalysis = ""
maxRecordNumber = 0   # processes the whole file by default
hcalRingGeometryFactor = 1.



# Preconfigure logging before any other thing...
# Use a specific argparser for that
loggingLevels = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL]

parser = argparse.ArgumentParser("Running energy calibration:", formatter_class=argparse.RawTextHelpFormatter, add_help=False)

parser.add_argument("--logLevel", action="store", type=type(logging.DEBUG), default=logging.INFO, choices=loggingLevels,
                        help="The logging level (default INFO)", required = False)

parser.add_argument("--logFile", action="store", default="",
                        help="The log file (default : no log file)", required = False)

parsed, extra = parser.parse_known_args()

logformat = "%(asctime)s [%(levelname)s] - %(name)s : %(message)s"

if parsed.logFile:
    logging.basicConfig(filename=parsed.logFile, filemode='w', level=parsed.logLevel, format=logformat)
else:
    logging.basicConfig(level=parsed.logLevel, format=logformat)





# Create the calibration manager and configure it
manager = CalibrationManager()

# mip scale for all detectors
manager.addStep( MipScaleStep() )

# calorimeters (ecal + hcal) calibration
manager.addStep( EcalEnergyStep() )
manager.addStep( HcalEnergyStep() )

# advanced PandoraPFA calibration
manager.addStep( PandoraMipScaleStep() )
manager.addStep( PandoraEMScaleStep() )


parser = argparse.ArgumentParser("Running energy calibration:", formatter_class=argparse.RawTextHelpFormatter, add_help=False)\

parser.add_argument("--showSteps", action="store_true", default=False,
                        help="Show the registered steps and exit", required = False)

parsed, extra = parser.parse_known_args()

if parsed.showSteps :
    manager.printSteps()
    sys.exit(0)




# Create the full command line interface
parser = argparse.ArgumentParser("Running energy calibration:",
                                     formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument("--showSteps", action="store_true", default=False,
                        help="Show the registered steps and exit", required = False)

parser.add_argument("--logLevel", action="store", type=type(logging.DEBUG), default=logging.INFO, choices=loggingLevels,
                        help="The logging level (default INFO)", required = False)

parser.add_argument("--logFile", action="store", default="",
                        help="The log file (default : no log file)", required = False)

parser.add_argument("--compactFile", action="store", default=compactFile,
                        help="The compact XML file", required = True)

parser.add_argument("--steeringFile", action="store", default=marlinSteeringFile,
                        help="The Marlin steering file (please, look at ILDConfig package)", required = True)

parser.add_argument("--maxNIterations", action="store", default=maxNIterations,
                        help="The maximum number of Marlin reconstruction iterations for calibration", required = False)

parser.add_argument("--ecalCalibrationAccuracy", action="store", default=ecalCalibrationAccuracy,
                        help="The calibration constants accuracy for ecal calibration", required = False)

parser.add_argument("--hcalCalibrationAccuracy", action="store", default=hcalCalibrationAccuracy,
                        help="The calibration constants accuracy for hcal calibration", required = False)

parser.add_argument("--inputCalibrationFile", action="store", default=inputCalibrationFile,
                        help="The XML input calibration file", required = True)

parser.add_argument("--outputCalibrationFile", action="store", default=outputCalibrationFile,
                        help="The XML output calibration file", required = False)

parser.add_argument("--lcioPhotonFile", action="store", default=lcioPhotonFile,
                        help="The lcio input file containing photons to process", required = False)

parser.add_argument("--lcioKaon0LFile", action="store", default=lcioKaon0LFile,
                        help="The lcio input file containing kaon0L to process", required = False)

parser.add_argument("--lcioMuonFile", action="store", default=lcioMuonFile,
                        help="The lcio input file containing muons to process", required = False)

parser.add_argument("--pandoraAnalysis", action="store", default=pathToPandoraAnalysis,
                        help="The path to the PandoraAnalysis package", required = True)

parser.add_argument("--maxRecordNumber", action="store", default=maxRecordNumber,
                        help="The maximum number of events to process", required = False)

parser.add_argument("--startStep", action="store", default=startStep,
                        help="The step id to start from", required = False)

parser.add_argument("--endStep", action="store", default=endStep,
                        help="The step id to stop at", required = False)

parser.add_argument("--hcalRingGeometryFactor", action="store", default=hcalRingGeometryFactor,
                        help="The geometrical factor to apply for hcal ring factor computation (see documentation in the 'doc' directory)", required = False)

parsed = parser.parse_args()


# configure and run
manager.readCmdLine(parsed)
manager.run()

# write the output of each step here
manager.writeXml(parsed.outputCalibrationFile)


#
