
import os
import subprocess

class Marlin(object) :
    def __init__(self) :
        self._marlinParameters = {}
        self._steeringFile = ""
        self._inputFiles = []
        self._gearFile = ""
        self._skipNEvents = 0
        self._verbosity = "MESSAGE"
        self._maxRecordNumber = 0
        self._randomSeed = 1234567890


    def setProcessorParameter(self, processor, parameter, value) :
        if processor in self._marlinParameters :
            procParameters = self._marlinParameters[processor]
            procParameters[parameter] = value
        else :
            self._marlinParameters[processor] = {parameter : value}

    def setSteeringFile(self, steeringFile) :
        self._steeringFile = steeringFile

    def setInputFiles(self, inputFiles) :
        if type(inputFiles) is type(list) :
            self._inputFiles = list(inputFiles)
        else :
            self._inputFiles = [inputFiles]

    def setGearFile(self, gearFile) :
        self._gearFile = gearFile

    def setSkipNEvents(self, nEvents) :
        self._skipNEvents = nEvents

    def setVerbosity(self, verbosity) :
        self._verbosity = verbosity

    def setMaxRecordNumber(self, maxRecordNumber) :
        self._maxRecordNumber = maxRecordNumber

    def setRandomSeed(self, randomSeed) :
        self._randomSeed = randomSeed


    def run(self) :
        args = self._createProcessArgs()
        print "Marlin command line : " + " ".join(args)
        process = subprocess.Popen(args = args)#, stdin = None, stdout = None, stderr = None)
        if process.wait() :
            raise RuntimeError
        print "Marlin ended with status 0"

    def convertToGear(self, compactFile) :
        gearFile = "gear_" + os.path.split(compactFile)[1]
        args = ['convertToGear', 'default', compactFile, gearFile]
        process = subprocess.Popen(args = args)
        if process.wait() :
            raise RuntimeError
        return gearFile

    def _createProcessArgs(self) :
        args = ['Marlin']
        print self._marlinParameters
        for proc,params in self._marlinParameters.iteritems() :
            for param, value in params.iteritems() :
                args.append("--"+proc+"."+param+"="+value)

        if len(self._inputFiles) == 1 :
            lcioFiles = "--global.LCIOInputFiles=" + self._inputFiles[0]
            args.append(lcioFiles)
        else :
            lcioFiles = "--global.LCIOInputFiles=\"" + " ".join(self._inputFiles) + "\""
            args.append(lcioFiles)

        args.append("--global.GearXMLFile="+self._gearFile)
        args.append("--global.SkipNEvents="+str(self._skipNEvents))
        args.append("--global.Verbosity="+self._verbosity)
        args.append("--global.MaxRecordNumber="+str(self._maxRecordNumber))
        args.append("--global.RandomSeed="+str(self._randomSeed))
        args.append(self._steeringFile)

        return args



#
