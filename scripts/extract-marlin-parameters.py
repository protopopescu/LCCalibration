#!/usr/bin/python

""" Extract, from Marlin steering file, parameters that will be used for running the calibration chain
    @author Remi Ete, DESY
"""

import os
import sys
from shutil import copyfile
import argparse
from calibration.XmlTools import etree

def getProcessorParameter(tree, processor, name):
    elt = tree.xpath("//marlin/processor[@name='{0}']/parameter[@name='{1}']".format(processor, name))
    if not elt:
        raise RuntimeError("Parameter '{0}' for processor '{1}' not found in xml file".format(name, processor))
    return elt[0].text

def createCalibrationParameter(tree, processor, name):
    param = getProcessorParameter(tree, processor, name)
    element = etree.Element("parameter", processor=processor, name=name)
    element.text = param
    return element

parser = argparse.ArgumentParser("Extract Marlin steering file parameters for calibration purpose:",
                                     formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument("--parameterFile", action="store",
                        help="A python file containing the parameter list to extract from Marlin xml file", required = True)

parser.add_argument("--steeringFile", action="store",
                        help="The Marlin steering file", required = True)

parser.add_argument("--outputFile", action="store",
                        help="The XML output calibration file", required = True)

parsed = parser.parse_args()

userParameters = []

try:
    execfile(parsed.parameterFile)
    userParameters = list(calibrationParameters)
except NameError as e:
    print "Couldn't find user parameters in input python file. Definition of 'calibrationParameter' variable is required !"
    raise e
except:
    raise RuntimeError("Error while import user python file !")
    

xmlParser = etree.XMLParser(remove_blank_text=True)
xmlTree = etree.parse(parsed.steeringFile, xmlParser)

rootOutput = etree.Element("calibration")
inputElement = etree.Element("input")
rootOutput.append(inputElement)

for param in userParameters:
    processor = param[0]
    parameter = param[1]
    try:
        inputElement.append(createCalibrationParameter(xmlTree, processor, parameter))
    except RuntimeError as e:
        print "!!WARNING!! Processor parameter '{0}/{1}' not found in Marlin xml file. Skipping ...".format(processor, parameter)

# write to output file
outputTree = etree.ElementTree(rootOutput)
outputTree.write(parsed.outputFile, pretty_print=True)

#
