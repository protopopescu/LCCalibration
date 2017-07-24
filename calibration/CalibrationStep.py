"""
"""

from lxml import etree

class CalibrationStep(object) :
    def __init__(self, stepName) :
        self._name = stepName

    def readCmdLine(self, cmdLine) :
        pass

    def init(self, config) :
        pass

    def run(self, config) :
        pass

    def writeOutput(self, config) :
        pass

    def name(self):
        return self._name

    def description(self):
        return "No description available"

    def _cleanupElement(self, tree) :
        elts = tree.xpath("//step[@name='{0}']".format(self._name))
        # remove previous elements
        if elts :
            for elt in elts :
                tree.getroot().remove(elt)


#
