

import os
import subprocess
import linecache

############################################################
############################################################
class PandoraAnalysisBinary(object) :
    def __init__(self, name) :
        self._pandoraAnalysisDir = os.environ["PANDORA_ANALYSIS_DIR"]
        self._name = name
        self._executable = os.path.join(self._pandoraAnalysisDir, "bin", self._name)
        self._arguments = {}
        self._calibrationFile = ""
        self._outputPath = ""

    def _createProcessArgs(self) :
        args = [self._executable]

        for param, value in self._arguments.iteritems() :
            args.append(param)
            args.append(value)

        return args

    def _setArgument(self, parameter, value=None) :
        if value is not None:
            self._arguments[parameter] = str(value)
        else :
            self._arguments[parameter] = ""
    
    def _removeFile(self, fname):
        try :
            os.remove(fname)
        except OSError:
            pass
    
    def _getCalibrationFileContent(self, fname, lid, tokenid):
        line = linecache.getline(fname, lid)
        lineTokens = line.split()
        linecache.clearcache()
        return lineTokens[tokenid]

    def _setOutputPath(self, arg, path):
        self._outputPath = path
        self._calibrationFile = path + "Calibration.txt"
        self._setArgument(arg, self._outputPath)

    def run(self) :
        args = self._createProcessArgs()
        print "Running: {0}".format(" ".join(args))
        process = subprocess.Popen(args = args)#, stdin = None, stdout = None, stderr = None)
        if process.wait() :
            raise RuntimeError
        print "PandoraAnalysisBinary '" + self._name + "' ended with status 0"

############################################################
############################################################
""" MipCalibrator class
    Implements the interface to the SimCaloHitEnergyDistribution binary
    from LCPandoraAnalysis package
"""
class MipCalibrator(PandoraAnalysisBinary):
    def __init__(self):
        PandoraAnalysisBinary.__init__("SimCaloHitEnergyDistribution")
        
        self._hcalBarrelMip = 0
        self._hcalEndcapMip = 0
        self._hcalRingMip = 0
        self._ecalMip = 0
        
        # default settings
        self.setMuonEnergy(10)
        self._setOutputPath("-c", "./SimCaloHitEnergyDistribution_")
    
    def getEcalMip(self):
        return self._ecalMip

    def getHcalBarrelMip(self):
        return self._hcalBarrelMip

    def getHcalEndcapMip(self):
        return self._hcalEndcapMip

    def getHcalRingMip(self):
        return self._hcalRingMip
    
    def setRootFile(self, rootFile):
        self._setArgument("-a", rootFile)
        
    def setMuonEnergy(self, energy):
        self._setArgument("-b", energy)    
    
    def run(self):
        # cleanup file
        self._removeFile(self._calibrationFile)
        # run binary
        PandoraAnalysisBinary.run()
        # extract variables
        self._hcalBarrelMip = float(getFileContent(self._calibrationFile, 7, 5))
        self._hcalEndcapMip = float(getFileContent(self._calibrationFile, 8, 5))
        self._hcalRingMip = float(getFileContent(self._calibrationFile, 9, 5))
        self._ecalMip = float(getFileContent(self._calibrationFile, 10, 4))
        # cleanup again
        self._removeFile(self._calibrationFile)
        
############################################################
############################################################
""" EcalCalibrator class
    Implements the interface to the ECalDigitisation_ContainedEvents binary
    from LCPandoraAnalysis package
"""
class EcalCalibrator(PandoraAnalysisBinary):
    def __init__(self):
        PandoraAnalysisBinary.__init__("ECalDigitisation_ContainedEvents")
        
        # set default values
        self.setPhotonEnergy(10)
        self._setOutputPath("-c", "./EcalEnergyCalibration_")
        self.setCosThetaRange(0, 1)
        
        # outputs
        self._ecalDigiMean = 0.

    def setRootFile(self, rootFile):
        self._setArgument("-a", rootFile)
        
    def setPhotonEnergy(self, energy):
        self._setArgument("-b", energy)
    
    def setDetectorRegion(self, region):
        self._setArgument("-g", region)
    
    def setCosThetaRange(self, minVal, maxVal):
        self._setArgument("-i", minVal)
        self._setArgument("-j", maxVal)
    
    def getEcalDigiMean(self):
        return self._ecalDigiMean
        
    def run(self):
        # cleanup file
        self._removeFile(self._calibrationFile)
        # run
        PandoraAnalysisBinary.run()
        # extract variables
        self._ecalDigiMean = float(getFileContent(self._calibrationFile, 11, 4))
        # cleanup again
        self._removeFile(self._calibrationFile)




        
############################################################
############################################################
""" EcalRingCalibrator class
    Implements the interface to the ECalDigitisation_DirectionCorrectionDistribution binary
    from LCPandoraAnalysis package
"""
class EcalRingCalibrator(PandoraAnalysisBinary):
    def __init__(self):
        PandoraAnalysisBinary.__init__("ECalDigitisation_DirectionCorrectionDistribution")
        
        # set default values
        self.setPhotonEnergy(10)
        self._setOutputPath("-c", "./EcalRingEnergyCalibration_")
        
        # outputs
        self._endcapMeanDirectionCorrection = 0.
        self._ringMeanDirectionCorrection = 0.

    def setRootFile(self, rootFile):
        self._setArgument("-a", rootFile)
        
    def setPhotonEnergy(self, energy):
        self._setArgument("-b", energy)
    
    def getEndcapMeanDirectionCorrection(self):
        return self._endcapMeanDirectionCorrection
        
    def getRingMeanDirectionCorrection(self):
        return self._ringMeanDirectionCorrection

    def run(self):
        # cleanup file
        self._removeFile(self._calibrationFile)
        # run
        PandoraAnalysisBinary.run()
        # extract variables
        self._endcapMeanDirectionCorrection = float(getFileContent(self._calibrationFile, 4, 5))
        self._ringMeanDirectionCorrection = float(getFileContent(self._calibrationFile, 9, 5))
        # cleanup again
        self._removeFile(self._calibrationFile)
    


############################################################
############################################################
""" HcalCalibrator class
    Implements the interface to the HCalDigitisation_ContainedEvents binary
    from LCPandoraAnalysis package
"""
class HcalCalibrator(PandoraAnalysisBinary):
    def __init__(self):
        PandoraAnalysisBinary.__init__("HCalDigitisation_ContainedEvents")
        
        # set default values
        self.setKaon0LEnergy(20)
        self._setOutputPath("-c", "./HcalEnergyCalibration_")
        self.setCosThetaRange(0, 1)
        
        # outputs
        self._hcalDigiMean = 0.

    def setRootFile(self, rootFile):
        self._setArgument("-a", rootFile)
        
    def setKaon0LEnergy(self, energy):
        self._setArgument("-b", energy)
    
    def setDetectorRegion(self, region):
        self._setArgument("-g", region)
    
    def setCosThetaRange(self, minVal, maxVal):
        self._setArgument("-i", minVal)
        self._setArgument("-j", maxVal)
    
    def getHcalDigiMean(self):
        return self._hcalDigiMean
        
    def run(self):
        # cleanup file
        self._removeFile(self._calibrationFile)
        # run
        PandoraAnalysisBinary.run()
        # extract variables
        self._hcalDigiMean = float(getFileContent(self._calibrationFile, 9, 5))
        # cleanup again
        self._removeFile(self._calibrationFile)
        

############################################################
############################################################
""" HcalRingCalibrator class
    Implements the interface to the HCalDigitisation_DirectionCorrectionDistribution binary
    from LCPandoraAnalysis package
"""
class HcalRingCalibrator(PandoraAnalysisBinary):
    def __init__(self):
        PandoraAnalysisBinary.__init__("HCalDigitisation_DirectionCorrectionDistribution")
        
        # set default values
        self.setKaon0LEnergy(20)
        self._setOutputPath("-c", "./HcalRingEnergyCalibration_")
        
        # outputs
        self._endcapMeanDirectionCorrection = 0.
        self._ringMeanDirectionCorrection = 0.

    def setRootFile(self, rootFile):
        self._setArgument("-a", rootFile)
        
    def setKaon0LEnergy(self, energy):
        self._setArgument("-b", energy)
    
    def getEndcapMeanDirectionCorrection(self):
        return self._endcapMeanDirectionCorrection
        
    def getRingMeanDirectionCorrection(self):
        return self._ringMeanDirectionCorrection

    def run(self):
        # cleanup file
        self._removeFile(self._calibrationFile)
        # run
        PandoraAnalysisBinary.run()
        # extract variables
        self._endcapMeanDirectionCorrection = float(getFileContent(self._calibrationFile, 4, 5))
        self._ringMeanDirectionCorrection = float(getFileContent(self._calibrationFile, 9, 5))
        # cleanup again
        self._removeFile(self._calibrationFile)    

############################################################
############################################################
""" PandoraMipScaleCalibrator class
    Implements the interface to the PandoraPFACalibrate_HadronicScale_ChiSquareMethod binary
    from LCPandoraAnalysis package
"""
class PandoraMipScaleCalibrator(PandoraAnalysisBinary):
    def __init__(self):
        PandoraAnalysisBinary.__init__("PandoraPFACalibrate_HadronicScale_ChiSquareMethod")
        
        # set default values
        self.setMuonEnergy(10)
        self._setOutputPath("-c", "./PandoraMipScale_")
        
        # outputs
        self._ecalToHadGeV = 0.

    def setRootFile(self, rootFile):
        self._setArgument("-a", rootFile)
        
    def setMuonEnergy(self, energy):
        self._setArgument("-b", energy)
    
    def getEcalToGeVMip(self):
        return self._ecalToGeVMip
        
    def getHcalToGeVMip(self):
        return self._hcalToGeVMip
        
    def getMuonToGeVMip(self):
        return self._muonToGeVMip 

    def run(self):
        # cleanup file
        self._removeFile(self._calibrationFile)
        # run
        PandoraAnalysisBinary.run()
        # extract variables
        self._ecalToGeVMip = float(getFileContent(self._calibrationFile, 8, 2))
        self._hcalToGeVMip = float(getFileContent(self._calibrationFile, 16, 2))
        self._muonToGeVMip = float(getFileContent(self._calibrationFile, 24, 2))
        # cleanup again
        self._removeFile(self._calibrationFile)  
        

############################################################
############################################################
""" PandoraEMScaleCalibrator class
    Implements the interface to the PandoraPFACalibrate_EMScale binary
    from LCPandoraAnalysis package
"""
class PandoraEMScaleCalibrator(PandoraAnalysisBinary):
    def __init__(self):
        PandoraAnalysisBinary.__init__("PandoraPFACalibrate_EMScale")
        
        # set default values
        self.setPhotonEnergy(10)
        self._setOutputPath("-d", "./PandoraEMScale_")
        
        # outputs
        self._ecalEMMean = 0.

    def setRootFile(self, rootFile):
        self._setArgument("-a", rootFile)
        
    def setPhotonEnergy(self, energy):
        self._setArgument("-b", energy)
    
    def getEcalToEMMean(self):
        return self._ecalEMMean

    def run(self):
        # cleanup file
        self._removeFile(self._calibrationFile)
        # run
        PandoraAnalysisBinary.run()
        # extract variables
        self._ecalEMMean = float(getFileContent(self._calibrationFile, 9, 3))
        # cleanup again
        self._removeFile(self._calibrationFile)  


############################################################
############################################################
""" PandoraHadScaleCalibrator class
    Implements the interface to the PandoraPFACalibrate_HadronicScale_ChiSquareMethod binary
    from LCPandoraAnalysis package
"""
class PandoraHadScaleCalibrator(PandoraAnalysisBinary):
    def __init__(self):
        PandoraAnalysisBinary.__init__("PandoraPFACalibrate_HadronicScale_ChiSquareMethod")
        
        # set default values
        self.setKaon0LEnergy(10)
        self._setOutputPath("-d", "./PandoraHadScale_")
        
        # outputs
        self._ecalToHadGeV = 0.
        self._hcalToHadGeV = 0.

    def setRootFile(self, rootFile):
        self._setArgument("-a", rootFile)
        
    def setKaon0LEnergy(self, energy):
        self._setArgument("-b", energy)
    
    def getEcalToHad(self):
        return self._ecalToHadGeV
    
    def getHcalToHad(self):
        return self._hcalToHadGeV

    def run(self):
        # cleanup file
        self._removeFile(self._calibrationFile)
        # run
        PandoraAnalysisBinary.run()
        # extract variables
        self._ecalToHadGeV = float(getFileContent(self._calibrationFile, 5, 2))
        self._hcalToHadGeV = float(getFileContent(self._calibrationFile, 6, 2))
        # cleanup again
        self._removeFile(self._calibrationFile)  



#