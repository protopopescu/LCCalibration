
import os
from calibration.XmlTools import *
import subprocess


class GearConverter(object) :
    def __init__(self):
        self._compactFile = ""
        self._pluginName = "default"
    
    """ Set the Gear converter plugin to use for conversion
    """
    def setPluginName(self, plugin):
        self._pluginName = plugin
    
    """ Set the compact file to convert
    """
    def setCompactFile(self, compactFile):
        self._compactFile = compactFile
    
    """ Convert the compact file to gear file using 'convertToGear' utility
        Use force to force its generation. If the gear file is already present
        and the force option is activated, the file is not generated
    """
    def convertToGear(self, force=False) :
        gearFile = "gear_" + os.path.split(self._compactFile)[1]

        if os.path.isfile(gearFile) and not force:
            return gearFile

        args = ['convertToGear', self._pluginName, self._compactFile, gearFile]
        process = subprocess.Popen(args = args)
        if process.wait() :
            raise RuntimeError("Couldn't convert compact file to gear file")
        return gearFile