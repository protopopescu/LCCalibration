import os
import subprocess


"""
Simple factory class to create DDSim instance for calibration purpose
"""
class DDSimCalibration(object) :
    def __init__(self) :
        self.steeringFile = ""
        self.compactFile = ""
        self.simulations = []

    def setSterringFile(self, steeringFile):
        self.steeringFile = steeringFile

    def setCompactFile(self, compactFile):
        self.compactFile = compactFile

    def addSimulation(self, parameters):
        self.simulations.append(parameters)

    def run(self):
        processes = []

        # run simulations in different processes
        for sim in self.simulations :
            args = self._createDDSimArgs(sim)
            args[:0] = ['ddsim']
            print "Args : " + str(args)
            process = subprocess.Popen(args = args)#, stdin = None, stdout = None, stderr = None)
            processes.append(process)

        for p in processes :
            p.wait()

        print "Simulation(s) done ..."

    def _createDDSimArgs(self, parameters) :
        args = []
        args.append("--compactFile")
        args.append(self.compactFile)
        args.append("--steeringFile")
        args.append(self.steeringFile)
        args.append("--gun.particle")
        args.append(parameters.get("particle"))
        args.append("--outputFile")
        args.append(parameters.get("outputFile"))
        args.append("--gun.energy")
        args.append(str(parameters.get("energy")))
        args.append("--physics.list")
        args.append(parameters.get("physicsList", "QGSP_BERT"))
        args.append("--numberOfEvents")
        args.append(str(parameters.get("numberOfEvents", 10000)))

        return args
