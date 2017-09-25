#!/usr/bin/python

""" Replace Marlin XML parameters by the parameter output from the calibration chain
    Note that for replacing the parameters, the xml file is not regenerated.
    By doing so, we avoid xml reformating by the lxml library that will gives
    a high number of GIT diffs when comparing before and after parameter replacement.
    Instead, the script is replacing the full line from the original Marlin xml file
    by a new one with the same indent and a new <parameter> xml element instead.
    @author Remi Ete, DESY
"""

import os
from tempfile import mkstemp
import sys
from shutil import move
import argparse
from calibration.XmlTools import etree

""" Helper function to get a specific xml element given a processor name and a parameter name
"""
def getProcessorParameter(tree, processor, name):
    elt = tree.xpath("//marlin/processor[@name='{0}']/parameter[@name='{1}']".format(processor, name))
    elt.extend( tree.xpath("//marlin/group/processor[@name='{0}']/parameter[@name='{1}']".format(processor, name)) )
    if not elt:
        raise RuntimeError("Parameter '{0}' for processor '{1}' not found in xml file".format(name, processor))
    return elt[0]

def whitespacePrefix(line):
    prefix = ""
    i = 0
    while 1:
        if len(line)-1 == i or not line[i].isspace():
            break
        prefix = prefix + " "
        i = i+1
    return prefix

# command line parsing
parser = argparse.ArgumentParser("Replace Marlin steering file parameters after calibration:",
                                     formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument("--steeringFile", action="store", default="",
                        help="The Marlin steering file", required = True)

parser.add_argument("--inputFile", action="store", default="",
                        help="The XML input calibration file", required = True)

parser.add_argument("--newSteeringFile", action="store", default="",
                        help="Write output in a new Marlin steering file", required = False)

parsed = parser.parse_args()

outputFile = parsed.steeringFile if not parsed.newSteeringFile else parsed.newSteeringFile

# open calibration and marlin xml files
xmlParser = etree.XMLParser(remove_blank_text=True)
marlinXmlTree = etree.parse(parsed.steeringFile, xmlParser)
calibrationXmlTree = etree.parse(parsed.inputFile, xmlParser)

# open marlin xml as raw file to replace just the needed lines
# write output in temporary file and move it when finished
marlinXmlRaw = open(parsed.steeringFile, 'r')
fd, tmpname = mkstemp()
marlinXmlOutput = open(tmpname, 'w')

# mapping line number and xml element
lineToParameter = {}

# Walk along the output parameters, replace with the new 
# values and map line number to xml element for future replacement
for parameter in calibrationXmlTree.xpath("//step/output/parameter"):

    processor = parameter.get("processor")
    name = parameter.get("name")
    value = parameter.text

    # Update parameter value
    marlinParameter = getProcessorParameter(marlinXmlTree, processor, name)
    marlinParameter.text = value
    lineToParameter[marlinParameter.sourceline] = marlinParameter

lineid = 1

# Walk along the marlin xml file, replace the line if needed
# and write down the result
for line in marlinXmlRaw:
    newLine = line
    if lineToParameter.get(lineid, None) is not None:
        element = lineToParameter.get(lineid)
        name = element.get("name")
        value = element.text
        newLine = whitespacePrefix(line) + "<parameter name=\"{0}\">{1}</parameter>\n".format(name, value)
    lineid = lineid+1
    marlinXmlOutput.write(newLine)

marlinXmlRaw.close()
marlinXmlOutput.close()

# rename temporary file to final marlin xml name
move(tmpname, outputFile)



#
