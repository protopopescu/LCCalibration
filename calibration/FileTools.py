import linecache
import os

def getFileContent(fname, lid, tokenid) :
    line = linecache.getline(fname, lid)
    lineTokens = line.split()
    linecache.clearcache()
    return lineTokens[tokenid]

def removeFile(fname):
    try :
        os.remove(fname)
    except OSError:
        pass

def getHcalBarrelMip(calibFile) :
    return float(getFileContent(calibFile, 7, 5))

def getHcalEndcapMip(calibFile) :
    return float(getFileContent(calibFile, 8, 5))

def getHcalRingMip(calibFile) :
    return float(getFileContent(calibFile, 9, 5))

def getEcalMip(calibFile) :
    return float(getFileContent(calibFile, 10, 4))

def getTruePhotonEnergy(calibFile) :
    return float(getFileContent(calibFile, 6, 4))

def getEcalDigiMean(calibFile) :
    return float(getFileContent(calibFile, 11, 4))

def getEcalRescalingFactor(calibFile) :
    ten = getTruePhotonEnergy(calibFile)
    digi = getEcalDigiMean(calibFile)
    return ten/digi

def getHcalDigiMean(calibFile) :
    return float(getFileContent(calibFile, 9, 5))

def getHcalRescalingFactor(calibFile, trueKaon0LEnergy) :
    hcalDigiMean = getHcalDigiMean(calibFile)
    return trueKaon0LEnergy / hcalDigiMean

def getMeanDirCorrHcalEndcap(calibFile) :
    return float(getFileContent(calibFile, 4, 5))

def getMeanDirCorrHcalRing(calibFile) :
    return float(getFileContent(calibFile, 9, 5))

def getMeanDirCorrEcalEndcap(calibFile) :
    return float(getFileContent(calibFile, 4, 5))

def getMeanDirCorrEcalRing(calibFile) :
    return float(getFileContent(calibFile, 9, 5))

def getEcalToGeVMip(calibFile) :
    return float(getFileContent(calibFile, 8, 2))

def getHcalToGeVMip(calibFile) :
    return float(getFileContent(calibFile, 16, 2))

def getMuonToGeVMip(calibFile) :
    return float(getFileContent(calibFile, 24, 2))

def getEcalToEMMean(calibFile) :
    return float(getFileContent(calibFile, 9, 3))

def getEcalToHadMean(calibFile) :
    return float(getFileContent(calibFile, 5, 2))

def getHcalToHadMean(calibFile) :
    return float(getFileContent(calibFile, 6, 2))
    
def getSoftwareCompensationWeights(calibFile, nWeights=9):
    weights = []
    for w in range(0, nWeights):
        weight = getFileContent(calibFile, 8+w, 3)
        weights.append(weight)
    return weights
#
