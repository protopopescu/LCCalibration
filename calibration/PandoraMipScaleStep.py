



from calibration.CalibrationStep import CalibrationStep
from calibration.Marlin import Marlin
from calibration.PandoraAnalysis import *
from calibration.FileTools import *
import os, sys
from lxml import *
from subprocess import call


class PandoraMipScaleStep(CalibrationStep) :
    def __init__(self) :
        CalibrationStep.__init__(self, "PandoraMipScale")
        self._marlin = Marlin()
        self._mipScaleCalibrator = None

        self._pfoOutputFile = "./PfoAnalysis_" + self._name + ".root"

        # step output
        self._outputEcalToGeVMip = None
        self._outputHcalToGeVMip = None
        self._outputMuonToGeVMip = None

    def description(self):
        return "Calculate the EcalToGeVMip, HcalToGeVMip and MuonToGeVMip that correspond to the mean reconstructed energy of mip calorimeter hit in the respective detectors"

    def readCmdLine(self, parsed) :
        # setup ecal energy calibrator
        self._mipScaleCalibrator = PandoraAnalysisBinary(os.path.join(parsed.pandoraAnalysis, "bin/PandoraPFACalibrate_MipResponse"))
        self._mipScaleCalibrator.addArgument("-a", self._pfoOutputFile)
        self._mipScaleCalibrator.addArgument("-b", '10')
        self._mipScaleCalibrator.addArgument("-c", "./PandoraMipScale_")

        # setup marlin
        gearFile = self._marlin.convertToGear(parsed.compactFile)
        self._marlin.setGearFile(gearFile)
        self._marlin.setSteeringFile(parsed.steeringFile)
        self._marlin.setProcessorParameter("InitDD4hep", "DD4hepXMLFile", parsed.compactFile)
        self._marlin.setMaxRecordNumber(parsed.maxRecordNumber)
        self._marlin.setInputFiles(parsed.lcioMuonFile)
        self._marlin.setProcessorParameter("MyPfoAnalysis", "RootFile", self._pfoOutputFile)

    def init(self, config) :

        ecalMip = float(self.getParameter(config, "ecalMip", "MipScale"))
        hcalBarrelMip = float(self.getParameter(config, "hcalBarrelMip", "MipScale"))
        hcalEndcapMip = float(self.getParameter(config, "hcalEndcapMip", "MipScale"))
        hcalRingMip = float(self.getParameter(config, "hcalRingMip", "MipScale"))
        inputEcalFactorsStr = self.getParameter(config, "ecalFactors", "EcalEnergy")
        inputHcalBarrelFactor = float(self.getParameter(config, "hcalBarrelFactor", "HcalEnergy"))
        inputHcalEndcapFactor = float(self.getParameter(config, "hcalEndcapFactor", "HcalEnergy"))
        inputHcalRingFactor = float(self.getParameter(config, "hcalRingFactor", "HcalEnergy"))
        inputMuonFactor = float(self.getParameter(config, "muonFactor"))

        # set the mip scale of all calorimeters
        self._marlin.setProcessorParameter("MyEcalBarrelDigi", "calibration_mip", str(ecalMip))
        self._marlin.setProcessorParameter("MyEcalEndcapDigi", "calibration_mip", str(ecalMip))
        self._marlin.setProcessorParameter("MyEcalRingDigi",   "calibration_mip", str(ecalMip))
        self._marlin.setProcessorParameter("MyHcalBarrelDigi", "calibration_mip", str(hcalBarrelMip))
        self._marlin.setProcessorParameter("MyHcalEndcapDigi", "calibration_mip", str(hcalEndcapMip))
        self._marlin.setProcessorParameter("MyHcalRingDigi",   "calibration_mip", str(hcalRingMip))

        # set the energy factors of all calorimeters
        self._marlin.setProcessorParameter("MyEcalBarrelReco", "calibration_factorsMipGev", inputEcalFactorsStr)
        self._marlin.setProcessorParameter("MyEcalEndcapReco", "calibration_factorsMipGev", inputEcalFactorsStr)
        self._marlin.setProcessorParameter("MyEcalRingReco",   "calibration_factorsMipGev", inputEcalFactorsStr)
        self._marlin.setProcessorParameter("MyHcalBarrelReco", "calibration_factorsMipGev", str(inputHcalBarrelFactor))
        self._marlin.setProcessorParameter("MyHcalEndcapReco", "calibration_factorsMipGev", str(inputHcalEndcapFactor))
        self._marlin.setProcessorParameter("MyHcalRingReco",   "calibration_factorsMipGev", str(inputHcalRingFactor))
        self._marlin.setProcessorParameter("MySimpleMuonDigi", "CalibrMUON",                str(inputMuonFactor))

    def run(self, config) :

        self._marlin.run()

        try :
            os.remove("./PandoraMipScale_Calibration.txt")
        except OSError:
            pass

        self._mipScaleCalibrator.run()

        self._outputEcalToGeVMip = getEcalToGeVMip("./PandoraMipScale_Calibration.txt")
        self._outputHcalToGeVMip = getHcalToGeVMip("./PandoraMipScale_Calibration.txt")
        self._outputMuonToGeVMip = getMuonToGeVMip("./PandoraMipScale_Calibration.txt")

        # since all PandoraAnalysis binaries write output with the same
        # file name and append the result to Calibration.txt file
        # it's better to delete this file after extracting the parameters of interest
        try :
            os.remove("./PandoraMipScale_Calibration.txt")
        except OSError:
            pass



    def writeOutput(self, config) :
        self._cleanupElement(config)

        root = config.getroot()
        step = etree.Element("step", name=self._name)
        output = etree.Element("output")
        step.append(output)
        root.append(step)

        ecalElt = etree.Element("ecalToGeVMip")
        ecalElt.text = str(self._outputEcalToGeVMip)
        output.append(ecalElt)

        hcalElt = etree.Element("hcalToGeVMip")
        hcalElt.text = str(self._outputHcalToGeVMip)
        output.append(hcalElt)

        muonElt = etree.Element("muonToGeVMip")
        muonElt.text = str(self._outputMuonToGeVMip)
        output.append(muonElt)
