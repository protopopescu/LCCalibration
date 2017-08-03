



from calibration.CalibrationStep import CalibrationStep
from calibration.Marlin import Marlin
from calibration.PandoraAnalysis import *
from calibration.FileTools import *
import os, sys
from lxml import *
from subprocess import call


class PandoraEMScaleStep(CalibrationStep) :
    def __init__(self) :
        CalibrationStep.__init__(self, "PandoraEMScale")
        self._marlin = Marlin()
        self._emScaleCalibrator = None

        self._maxNIterations = 5
        self._energyScaleAccuracy = 0.01

        # step input
        self._inputEcalToEMGeV = None
        self._inputHcalToEMGeV = None

        # step output
        self._outputEcalToEMGeV = None
        self._outputHcalToEMGeV = None
        self._outputPhotonEnergy = None
        self._outputEnergyRescale = None
        self._outputPrecision = None

    # def description(self):
    #     return "Calculate the EcalToGeVMip, HcalToGeVMip and MuonToGeVMip that correspond to the mean reconstructed energy of mip calorimeter hit in the respective detectors"

    def readCmdLine(self, parsed) :
        # setup ecal energy calibrator
        self._emScaleCalibrator = PandoraAnalysisBinary(os.path.join(parsed.pandoraAnalysis, "bin/PandoraPFACalibrate_EMScale"))
        self._emScaleCalibrator.addArgument("-b", '10')
        self._emScaleCalibrator.addArgument("-d", "./PandoraEMScale_")

        # setup marlin
        gearFile = self._marlin.convertToGear(parsed.compactFile)
        self._marlin.setGearFile(gearFile)
        self._marlin.setSteeringFile(parsed.steeringFile)
        self._marlin.setProcessorParameter("InitDD4hep", "DD4hepXMLFile", parsed.compactFile)
        self._marlin.setMaxRecordNumber(parsed.maxRecordNumber)
        self._marlin.setInputFiles(parsed.lcioPhotonFile)

        self._maxNIterations = int(parsed.maxNIterations)
        self._energyScaleAccuracy = float(parsed.ecalCalibrationAccuracy)

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
        ecalToGeVMip = float(self.getParameter(config, "ecalToGeVMip", "PandoraMipScale"))
        hcalToGeVMip = float(self.getParameter(config, "hcalToGeVMip", "PandoraMipScale"))
        muonToGeVMip = float(self.getParameter(config, "muonToGeVMip", "PandoraMipScale"))

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

        # set pandora parameters
        self._marlin.setProcessorParameter("MyDDMarlinPandora", "ECalToMipCalibration", str(ecalToGeVMip))
        self._marlin.setProcessorParameter("MyDDMarlinPandora", "HCalToMipCalibration", str(hcalToGeVMip))
        self._marlin.setProcessorParameter("MyDDMarlinPandora", "MuonToMipCalibration", str(muonToGeVMip))

        # constant to calibrate
        self._inputEcalToEMGeV = float(self.getParameter(config, "ecalToEMGeV"))
        self._inputHcalToEMGeV = float(self.getParameter(config, "hcalToEMGeV"))
        self._marlin.setProcessorParameter("MyDDMarlinPandora", "ECalToEMGeVCalibration", str(self._inputEcalToEMGeV))
        self._marlin.setProcessorParameter("MyDDMarlinPandora", "HCalToEMGeVCalibration", str(self._inputHcalToEMGeV))

    def run(self, config) :
        # cleanup xml tree to write new incoming iteration results
        self._cleanupElement(config)

        root = config.getroot()
        step = etree.Element("step", name=self._name)
        root.append(step)
        iterations = etree.Element("iterations")
        step.append(iterations)

        # loop variables
        currentPrecision = 0.
        calibrationRescaleFactor = 1.
        calibrationRescaleFactorCumul = 1.
        accuracyReached = False

        ecalToEMGeV = self._inputEcalToEMGeV
        hcalToEMGeV = self._inputHcalToEMGeV

        for iteration in range(self._maxNIterations) :

            # readjust iteration parameters
            ecalToEMGeV = ecalToEMGeV*calibrationRescaleFactor
            hcalToEMGeV = hcalToEMGeV*calibrationRescaleFactor
            pfoAnalysisFile = "./PfoAnalysis_{0}_iter{1}.root".format(self._name, iteration)

            # run marlin ...
            self._marlin.setProcessorParameter("MyDDMarlinPandora", "ECalToEMGeVCalibration", str(ecalToEMGeV))
            self._marlin.setProcessorParameter("MyDDMarlinPandora", "HCalToEMGeVCalibration", str(hcalToEMGeV))
            self._marlin.setProcessorParameter("MyPfoAnalysis"   ,  "RootFile", pfoAnalysisFile)
            self._marlin.run()

            # ... and calibration script
            try :
                os.remove("./PandoraEMScale_Calibration.txt")
            except OSError:
                pass

            self._emScaleCalibrator.addArgument("-a", pfoAnalysisFile)
            self._emScaleCalibrator.run()

            newPhotonEnergy = getEcalToEMMean("./PandoraEMScale_Calibration.txt")
            calibrationRescaleFactor = 10. / newPhotonEnergy
            calibrationRescaleFactorCumul = calibrationRescaleFactorCumul*calibrationRescaleFactor
            currentPrecision = abs(1 - 1. / calibrationRescaleFactor)

            os.rename("./PandoraEMScale_Calibration.txt", "./PandoraEMScale_iter{0}_Calibration.txt".format(iteration))

            # write down iteration results
            iterationElt = etree.Element("iteration", id=str(iteration))
            iterations.append(iterationElt)

            precisionElt = etree.Element("precision")
            precisionElt.text = str(currentPrecision)
            iterationElt.append(precisionElt)

            rescaleElt = etree.Element("rescale")
            rescaleElt.text = str(calibrationRescaleFactor)
            iterationElt.append(rescaleElt)

            photonEnergyElt = etree.Element("newPhotonEnergy")
            photonEnergyElt.text = str(newPhotonEnergy)
            iterationElt.append(photonEnergyElt)

            # are we accurate enough ??
            if currentPrecision < self._energyScaleAccuracy :

                print "{0}: ecal energy accuracy reached !".format(self._name)
                accuracyReached = True

                self._outputEcalToEMGeV = ecalToEMGeV
                self._outputHcalToEMGeV = hcalToEMGeV
                self._outputPhotonEnergy = newPhotonEnergy
                self._outputEnergyRescale = calibrationRescaleFactorCumul
                self._outputPrecision = currentPrecision

                break

        if not accuracyReached :
            raise RuntimeError("{0}: Couldn't reach the user accuracy ({1})".format(self._name, self._energyScaleAccuracy))

    def writeOutput(self, config) :
        step = config.xpath("//step[@name='{0}']".format(self._name))[0]
        output = etree.Element("output")
        step.append(output)

        ecalElt = etree.Element("ecalToEMGeV")
        ecalElt.text = str(self._outputEcalToEMGeV)
        output.append(ecalElt)

        hcalElt = etree.Element("hcalToEMGeV")
        hcalElt.text = str(self._outputHcalToEMGeV)
        output.append(hcalElt)

        photonEnergyElt = etree.Element("photonEnergy")
        photonEnergyElt.text = str(self._outputPhotonEnergy)
        output.append(photonEnergyElt)

        rescaleElt = etree.Element("rescale")
        rescaleElt.text = str(self._outputEnergyRescale)
        output.append(rescaleElt)

        precision = etree.Element("precision")
        precision.text = str(self._outputPrecision)
        output.append(precision)
