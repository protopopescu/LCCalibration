import linecache

def getHcalBarrelMip(calibFile) :
    line = linecache.getline(calibFile, 7)
    lineTokens = line.split()
    linecache.clearcache()
    return float(lineTokens[5])

def getHcalEndcapMip(calibFile) :
    line = linecache.getline(calibFile, 8)
    lineTokens = line.split()
    linecache.clearcache()
    return float(lineTokens[5])

def getHcalRingMip(calibFile) :
    line = linecache.getline(calibFile, 9)
    lineTokens = line.split()
    linecache.clearcache()
    return float(lineTokens[5])

def getEcalMip(calibFile) :
    line = linecache.getline(calibFile, 10)
    lineTokens = line.split()
    linecache.clearcache()
    return float(lineTokens[4])

def getTruePhotonEnergy(calibFile) :
    line = linecache.getline(calibFile, 4)
    lineTokens = line.split()
    linecache.clearcache()
    return float(lineTokens[4])

def getEcalDigiMean(calibFile) :
    line = linecache.getline(calibFile, 9)
    lineTokens = line.split()
    linecache.clearcache()
    return float(lineTokens[4])

def getEcalRescalingFactor(calibFile) :
    ten = getTruePhotonEnergy(calibFile)
    digi = getEcalDigiMean(calibFile)
    return ten/digi

def getHcalDigiMean(calibFile) :
    line = linecache.getline(calibFile, 9)
    lineTokens = line.split()
    linecache.clearcache()
    return float(lineTokens[5])

def getHcalRescalingFactor(calibFile, trueKaon0LEnergy) :
    hcalDigiMean = getHcalDigiMean(calibFile)
    return trueKaon0LEnergy / hcalDigiMean




#
