

import os
import subprocess


class PandoraAnalysisBinary(object) :
    def __init__(self, executable) :
        self._executable = executable
        self._arguments = {}

    def _createProcessArgs(self) :
        args = [self._executable]

        for param, value in self._arguments.iteritems() :
            args.append(param)
            args.append(value)

        return args

    def addArgument(self, parameter, value) :
        self._arguments[parameter] = value

    def run(self) :
        args = self._createProcessArgs()
        process = subprocess.Popen(args = args)#, stdin = None, stdout = None, stderr = None)
        if process.wait() :
            raise RuntimeError
        print "PandoraAnalysisBinary '"+os.path.split(self._executable)[1]+"' ended with status 0"
