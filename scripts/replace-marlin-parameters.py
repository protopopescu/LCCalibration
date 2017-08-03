#!/usr/bin/python

"""
"""
import os
import sys
from shutil import copyfile
import argparse
from lxml import etree

""" Helper function to get a specific xml element given a processor name and a parameter name
"""
def getProcessorParameter(tree, processor, name):
    elt = tree.xpath("//marlin/processor[@name='{0}']/parameter[@name='{1}']".format(processor, name))
    if not elt:
        raise RuntimeError("Parameter '{0}' for processor '{1}' not found in xml file".format(name, processor))
    return elt[0]


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

# open both xml file to read/write new calibration parameter
xmlParser = etree.XMLParser(remove_blank_text=True)
marlinXmlTree = etree.parse(parsed.steeringFile, xmlParser)
calibrationXmlTree = etree.parse(parsed.inputFile, xmlParser)

# Walk along the output parameters and update the marlin xml file
for parameter in calibrationXmlTree.xpath("//step/output/parameter"):

    processor = parameter.get("processor")
    name = parameter.get("name")
    value = parameter.text

    # Update parameter value
    marlinParameter = getProcessorParameter(marlinXmlTree, processor, name)
    marlinParameter.text = value

marlinXmlTree.write(outputFile, pretty_print=True)


#
