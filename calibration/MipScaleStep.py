"""
"""

from calibration.CalibrationStep import CalibrationStep
from calibration.Marlin import Marlin
from calibration.PandoraAnalysis import *
from calibration.FileTools import *
import os, sys
from lxml import *
from subprocess import call


"""
"""
class MipScaleStep(CalibrationStep) :
    def __init__(self) :
        CalibrationStep.__init__(self, "MipScale")
        self._marlin = Marlin()
        self._mipCalibrator = None
        self._pfoOutputFile = "./PfoAnalysis_" + self._name + ".root"
        self._hcalBarrelMip = 0.
        self._hcalEndcapMip = 0.
        self._hcalRingMip = 0.
        self._ecalMip = 0.

    def description(self) :
        return "Calculate the mip values from SimCalorimeter collections in the muon lcio file. This outputs ecalMip, hcalBarrelMip, hcalEndcapMip and hcalRingMip"

    def readCmdLine(self, parsed) :
        # setup mip calibrator
        self._mipCalibrator = PandoraAnalysisBinary(os.path.join(parsed.pandoraAnalysis, "bin/SimCaloHitEnergyDistribution"))
        self._mipCalibrator.addArgument("-a", self._pfoOutputFile)
        self._mipCalibrator.addArgument("-b", '10')
        self._mipCalibrator.addArgument("-c", "./MipScale_")

        # setup marlin
        gearFile = self._marlin.convertToGear(parsed.compactFile)
        self._marlin.setGearFile(gearFile)
        self._marlin.setSteeringFile(parsed.steeringFile)
        self._marlin.setProcessorParameter("InitDD4hep", "DD4hepXMLFile", parsed.compactFile)
        self._marlin.setMaxRecordNumber(parsed.maxRecordNumber)
        self._marlin.setInputFiles(parsed.lcioMuonFile)
        self._marlin.setProcessorParameter("MyPfoAnalysis"   , "RootFile", self._pfoOutputFile)

    def init(self, config) :
        pass

    def run(self, config) :
        self._marlin.run()

        try :
            os.remove("./MipScale_Calibration.txt")
        except OSError:
            pass

        self._mipCalibrator.run()

        self._hcalBarrelMip = getHcalBarrelMip("./MipScale_Calibration.txt")
        self._hcalEndcapMip = getHcalEndcapMip("./MipScale_Calibration.txt")
        self._hcalRingMip = getHcalRingMip("./MipScale_Calibration.txt")
        self._ecalMip = getEcalMip("./MipScale_Calibration.txt")
        # since all PandoraAnalysis binaries write output with the same
        # file name and append the result to Calibration.txt file
        # it's better to delete this file after extracting the parameters of interest
        try :
            os.remove("./MipScale_Calibration.txt")
        except OSError:
            pass

    def writeOutput(self, config) :
        # replace previous exports
        self._cleanupElement(config)

        root = config.getroot()
        step = etree.Element("step", name=self._name)
        output = etree.Element("output")
        step.append(output)

        hbmElt = etree.Element("hcalBarrelMip")
        hbmElt.text = str(self._hcalBarrelMip)
        output.append(hbmElt)

        hemElt = etree.Element("hcalEndcapMip")
        hemElt.text = str(self._hcalEndcapMip)
        output.append(hemElt)

        hrmElt = etree.Element("hcalRingMip")
        hrmElt.text = str(self._hcalRingMip)
        output.append(hrmElt)

        emElt = etree.Element("ecalMip")
        emElt.text = str(self._ecalMip)
        output.append(emElt)

        root.append(step)

#
