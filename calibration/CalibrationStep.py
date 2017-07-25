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

    def getParameter(self, config, name, step=None) :

        userInput = config.xpath("//input")
        stepElt = None

        if step is not None :
            stepElts = config.xpath("//step[@name='{0}']".format(step))

            if len(stepElts) :
                stepElt = stepElts[-1].find("output")

        if not len(userInput) and stepElt is None :
            raise RuntimeError("Couldn't get parameter '{0}' from input nor from step".format(name))

        if len(userInput) :
            userInput = userInput[0]

        # first look into the step element
        if stepElt :
            return stepElt.find(name).text

        # then look into user input element
        return userInput.find(name).text
#
