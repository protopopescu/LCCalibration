

from calibration.DDSimCalibration import DDSimCalibration
import os
import argparse

compactFile = ""
numberOfEvents = 10000
physicsList = "QGSP_BERT"
steeringFile = ""

parser = argparse.ArgumentParser("Running DDsim for Pandora calibration:",
                                     formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument("--compactFile", action="store", default=compactFile,
                        help="The compact XML file", required = True)

parser.add_argument("--numberOfEvents", "-N", action="store", dest="numberOfEvents", default=numberOfEvents,
                        type=int, help="Number of events to simulate", required = False)

parser.add_argument("--physicsList", action="store", dest="physicsList", default=physicsList,
                    help="Physics list to use in simulation", required = False)

parser.add_argument("--steeringFile", action="store", dest="steeringFile", default=steeringFile,
                    help="DDSim steering file", required = True)

parsed = parser.parse_args()

commonParameters = {}
commonParameters["numberOfEvents"] = parsed.numberOfEvents
commonParameters["physicsList"] = parsed.physicsList

photonParameters = commonParameters.copy()
photonParameters["particle"] = "gamma"
photonParameters["energy"] = 10
photonParameters["outputFile"] = "ddsim-photon-calibration.slcio"

kaon0LParameters = commonParameters.copy()
kaon0LParameters["particle"] = "kaon0L"
kaon0LParameters["energy"] = 20
kaon0LParameters["outputFile"] = "ddsim-kaon0L-calibration.slcio"

muonParameters = commonParameters.copy()
muonParameters["particle"] = "mu-"
muonParameters["energy"] = 10
muonParameters["outputFile"] = "ddsim-muon-calibration.slcio"


simCalib = DDSimCalibration()
simCalib.setSterringFile(parsed.steeringFile)
simCalib.setCompactFile(parsed.compactFile)

simCalib.addSimulation(photonParameters)
simCalib.addSimulation(muonParameters)
simCalib.addSimulation(kaon0LParameters)

simCalib.run()


#
